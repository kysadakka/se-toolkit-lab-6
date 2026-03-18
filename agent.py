import os
import sys
import json
import requests
from openai import OpenAI
from pathlib import Path


def _load_env():
    """Load variables from .env files (simple key=value parser)."""
    for env_file in [".env", ".env.agent.secret", ".env.docker.secret"]:
        path = Path(env_file)
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# Load environment variables before anything else
_load_env()

# ---------- Tools ----------
def read_file(path):
    """Read a file, prevent directory traversal."""
    if '..' in path or path.startswith('/'):
        return "Error: Invalid path"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

def list_files(path):
    """List directory contents, prevent directory traversal."""
    if '..' in path or path.startswith('/'):
        return "Error: Invalid path"
    try:
        files = os.listdir(path)
        return '\n'.join(f for f in files if not f.startswith('.'))
    except Exception as e:
        return f"Error: {str(e)}"

def query_api(method, path, body=None, auth=True):
    """Call the deployed backend API.
    
    Args:
        method: HTTP method (GET or POST)
        path: API path (e.g., '/items/')
        body: Optional JSON body for POST requests
        auth: Whether to include authentication header (default True). Set to False to test unauthenticated access.
    """
    base_url = os.environ.get("AGENT_API_BASE_URL", "http://localhost:42002")
    api_key = os.environ.get("LMS_API_KEY")

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {"Content-Type": "application/json"}
    
    # Only add auth header if requested
    if auth and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif auth and not api_key:
        return json.dumps({"status_code": 500, "body": "Error: LMS_API_KEY not set"})

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            data = json.loads(body) if body else {}
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return json.dumps({"status_code": 400, "body": f"Unsupported method: {method}"})

        return json.dumps({
            "status_code": response.status_code,
            "body": response.text
        })
    except requests.exceptions.ConnectionError:
        return json.dumps({"status_code": 503, "body": "Error: Could not connect to the API"})
    except Exception as e:
        return json.dumps({"status_code": 500, "body": f"Error: {str(e)}"})

# Tool schemas for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project. Use relative paths from the project root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file, e.g., 'backend/app/routers/items.py'"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory. Use relative paths from the project root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the directory, e.g., 'backend/app/routers'"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Query the deployed backend API. Use this to get live data from the system, like item counts, status codes, or errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST"],
                        "description": "HTTP method (GET for retrieving data, POST for actions)"
                    },
                    "path": {
                        "type": "string",
                        "description": "API path, e.g., '/items/' or '/analytics/completion-rate?lab=lab-99'"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON body for POST requests"
                    },
                    "auth": {
                        "type": "boolean",
                        "description": "Whether to include authentication header (default true). Set to false to test unauthenticated access."
                    }
                },
                "required": ["method", "path"]
            }
        }
    }
]

def main():
    question = sys.argv[1]
    
    if not question:
        print("Error: Empty question provided", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print("Error: No question provided", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Get LLM config
    api_key = os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("LLM_API_BASE")
    model = os.environ.get("LLM_MODEL", "qwen3-coder-plus")
    
    if not api_key or not api_base:
        print("Error: LLM_API_KEY and LLM_API_BASE must be set", file=sys.stderr)
        sys.exit(1)
    
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    # System prompt - concise and focused on tool usage
    system_prompt = """You are a system agent for a software project. Answer questions using tools.

Tools:
- `list_files(path)`: List directory contents. Use relative paths like "backend/app/routers".
- `read_file(path)`: Read a file. Use relative paths like "backend/app/routers/items.py".
- `query_api(method, path, body)`: Call the live API for data questions. By default includes auth header.

Rules:
1. ALWAYS use tools to gather information before answering.
2. For "list" or "find all" questions: use list_files, then read_file on each relevant file.
3. For wiki/documentation questions: list_files("wiki"), then read_file on relevant .md files.
4. For code questions: navigate to the right directory, then read the source files.
5. For live data questions (counts, status codes): use query_api.
6. For bug diagnosis questions (API errors): FIRST use query_api to see the error, THEN use read_file to find the buggy code.
7. For questions about unauthenticated access: use query_api with auth=false.
8. Provide complete answers based on tool results.
9. When reporting errors, include both the error message AND the exception type (e.g., "ZeroDivisionError: division by zero").
10. NEVER output phrases like "Let me check", "Let me see", "I'll look" - just use tools and provide the final answer.

Backend routers are in: backend/app/routers/
Backend Dockerfile is at: Dockerfile (in project root)"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    tool_calls_log = []
    max_iter = 10
    files_read = []  # Track files read for source tracking
    
    for _ in range(max_iter):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        # If no tool calls, we're done
        if not msg.tool_calls:
            # Check if this looks like intermediate commentary (not a final answer)
            content = msg.content or ""
            intermediate_phrases = [
                "let me check", "let me see", "let me look", "let me read",
                "i'll check", "i'll look", "i'll see", "i'll read",
                "now i need", "now let me", "let me explore", "let me find",
                "let me open", "i'll open", "let me navigate", "let me go to"
            ]
            is_intermediate = any(phrase in content.lower() for phrase in intermediate_phrases)
            
            # If it looks like intermediate commentary and we haven't maxed out iterations,
            # force another iteration by adding a user message prompting for the answer
            if is_intermediate and len(tool_calls_log) < max_iter:
                messages.append({
                    "role": "user",
                    "content": "Please provide the final answer based on the information you've gathered. Do not use more tools - just give the complete answer."
                })
                continue
            
            # Determine source based on files read or API calls
            source = "wiki/"
            if files_read:
                # Use the last file read as source, or mention all files
                source = files_read[-1] if files_read else "wiki/"
            elif tool_calls_log:
                # Check if any tool call was query_api
                for tc in tool_calls_log:
                    if tc.get("tool") == "query_api":
                        args = tc.get("args", {})
                        source = f"API: {args.get('path', '')}"
                        break

            result = {
                "answer": msg.content or "No answer found",
                "source": source,
                "tool_calls": tool_calls_log
            }
            print(json.dumps(result))
            return

        # Add the assistant message with tool calls to the conversation
        assistant_msg = {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        }
        messages.append(assistant_msg)

        # Process tool calls
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Execute tool
            if name == "read_file":
                path = args.get("path", "")
                result = read_file(path)
                if path and not result.startswith("Error:"):
                    files_read.append(path)
            elif name == "list_files":
                result = list_files(args.get("path", ""))
            elif name == "query_api":
                result = query_api(
                    method=args.get("method", "GET"),
                    path=args.get("path", ""),
                    body=args.get("body"),
                    auth=args.get("auth", True)
                )
            else:
                result = f"Unknown tool: {name}"

            # Log tool call
            tool_calls_log.append({
                "tool": name,
                "args": args,
                "result": result[:200] + "..." if len(result) > 200 else result
            })

            # Add to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
    
    # Max iterations reached
    # Determine source based on files read or API calls
    source = "wiki/"
    if files_read:
        source = files_read[-1] if files_read else "wiki/"
    elif tool_calls_log:
        for tc in tool_calls_log:
            if tc.get("tool") == "query_api":
                args = tc.get("args", {})
                source = f"API: {args.get('path', '')}"
                break
    
    result = {
        "answer": "Maximum iterations reached",
        "source": source,
        "tool_calls": tool_calls_log
    }
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Любая неожиданная ошибка
        error_result = {
            "answer": f"Internal agent error: {str(e)}",
            "source": "wiki/",
            "tool_calls": []
        }
        print(json.dumps(error_result), file=sys.stdout)
        sys.exit(1)