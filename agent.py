import os
import sys
import json
from openai import OpenAI

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

# Tool schemas for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    }
]

def main():
    if len(sys.argv) < 2:
        print("Error: No question provided", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Get config
    api_key = os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("LLM_API_BASE")
    model = os.environ.get("LLM_MODEL", "qwen3-coder-plus")
    
    if not api_key or not api_base:
        print("Error: Missing API config", file=sys.stderr)
        sys.exit(1)
    
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    # System prompt
    system_prompt = """You are a documentation assistant. 
Use tools to find information. Always include the source.
Strategy:
1. Use list_files('wiki') to see what's available
2. Use read_file to read relevant files
3. Provide answer with source reference"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    tool_calls_log = []
    max_iter = 10
    
    for _ in range(max_iter):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS
        )
        
        msg = response.choices[0].message
        
        # If no tool calls, we're done
        if not msg.tool_calls:
            result = {
                "answer": msg.content or "No answer found",
                "source": "wiki/",
                "tool_calls": tool_calls_log
            }
            print(json.dumps(result))
            return
        
        # Process tool calls
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            # Execute tool
            if name == "read_file":
                result = read_file(args.get("path", ""))
            elif name == "list_files":
                result = list_files(args.get("path", ""))
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
    result = {
        "answer": "Maximum iterations reached",
        "source": "wiki/",
        "tool_calls": tool_calls_log
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
