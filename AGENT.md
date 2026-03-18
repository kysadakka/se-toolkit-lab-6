# System Agent Documentation

## Overview

This agent answers questions about a software project by using tools to gather information from files, documentation, and the live backend API. The agent uses function calling with an LLM to decide which tools to use based on the question.

## Architecture

### Tools

The agent has three tools:

1. **`read_file(path)`**: Reads the contents of a file at the specified relative path. Blocks paths containing ".." or starting with "/" to prevent directory traversal.

2. **`list_files(path)`**: Lists the contents of a directory at the specified relative path. Also blocks directory traversal attempts.

3. **`query_api(method, path, body, auth)`**: Calls the deployed backend API.
   - `method`: HTTP method (GET or POST)
   - `path`: API endpoint path (e.g., `/items/`, `/analytics/completion-rate?lab=lab-99`)
   - `body`: Optional JSON body for POST requests
   - `auth`: Whether to include authentication header (default: true). Set to false to test unauthenticated access.
   - Authenticates using `LMS_API_KEY` from environment
   - Uses `AGENT_API_BASE_URL` from environment (defaults to `http://localhost:42002`)

### Environment Variables

The agent reads all configuration from environment variables:

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key for query_api | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Base URL for query_api (optional) | Defaults to `http://localhost:42002` |

### System Prompt Strategy

The system prompt guides the LLM's tool selection:
- **File tools** (`read_file`, `list_files`): For questions about static code, configuration files, or wiki documentation
- **API tool** (`query_api`): For questions requiring live data (item counts, status codes, API errors)
- **Bug diagnosis**: First use `query_api` to see the error, then `read_file` to find the buggy code
- **Tool chaining**: The agent can chain multiple tool calls to gather information before answering

### Source Tracking

The agent tracks which files were read during execution and sets the `source` field in the output accordingly:
- If files were read: uses the last file path as source
- If only API was called: uses `API: <path>` as source
- Default: `wiki/`

### Intermediate Commentary Detection

The agent detects when the LLM returns intermediate thoughts (phrases like "Let me check", "Let me see") instead of a final answer. When detected, it prompts the LLM to provide the final answer without using more tools.

## Usage

```bash
# Run the agent with a question
uv run agent.py "How many items are in the database?"

# Run the evaluation benchmark
uv run run_eval.py

# Run a single evaluation question (for debugging)
uv run run_eval.py --index 5
```

## Output Format

The agent outputs JSON with three fields:

```json
{
  "answer": "The answer to the question",
  "source": "backend/app/routers/analytics.py",
  "tool_calls": [
    {
      "tool": "query_api",
      "args": {"method": "GET", "path": "/analytics/completion-rate?lab=lab-99"},
      "result": "{\"status_code\": 500, \"body\": \"...\"}"
    },
    {
      "tool": "read_file",
      "args": {"path": "backend/app/routers/analytics.py"},
      "result": "\"\"\"Router for analytics endpoints...\""
    }
  ]
}
```

## Benchmark Results

- **Initial Score:** 0/10 (Failed on all questions involving `query_api` and complex reasoning)
- **Final Score:** 10/10 (All local questions passed)

### Question Coverage

| # | Question Type | Tools Required | Status |
|---|--------------|----------------|--------|
| 0 | Wiki lookup (branch protection) | `read_file` | ✓ |
| 1 | Wiki lookup (SSH connection) | `read_file` | ✓ |
| 2 | Code lookup (web framework) | `read_file` | ✓ |
| 3 | List router modules | `list_files`, `read_file` | ✓ |
| 4 | Database item count | `query_api` | ✓ |
| 5 | Unauthenticated status code | `query_api` (auth=false) | ✓ |
| 6 | Bug diagnosis (division by zero) | `query_api`, `read_file` | ✓ |
| 7 | Bug diagnosis (NoneType error) | `query_api`, `read_file` | ✓ |
| 8 | Request lifecycle (LLM judge) | `read_file` | ✓ |
| 9 | ETL idempotency (LLM judge) | `read_file` | ✓ |

## Lessons Learned

1. **Tool Descriptions Matter**: The LLM would not use `query_api` unless its description explicitly mentioned "live data", "API", and "status codes". Vague descriptions led it to guess answers or use the wrong tool.

2. **Authentication is Critical**: Forgetting to pass the `LMS_API_KEY` in the `Authorization` header caused all API calls to fail with 401/403 errors. The agent must report these errors correctly.

3. **Handling `None` Content**: An early bug occurred when the LLM responded with `content: null` while making a tool call. This was fixed by using `(msg.content or "")` to safely handle the `None` value.

4. **Chaining is Hard**: Getting the agent to correctly diagnose a bug by first calling the API to see an error, then reading the source code required a very clear system prompt that explicitly allowed for multiple tool calls in a single session.

5. **Environment Variables**: The autochecker runs with different URLs and keys. Ensuring the agent read `AGENT_API_BASE_URL` and `LMS_API_KEY` from the environment, with sensible defaults for local testing, was crucial.

6. **Source Tracking**: The evaluation checks not just the answer but also the source field. The agent must track which files were read and set the source accordingly.

7. **Intermediate Commentary**: The LLM model sometimes returns intermediate thoughts ("Let me check...") instead of final answers. The agent detects this pattern and prompts for a final answer.

8. **Tool Choice Parameter**: Using `tool_choice="auto"` allows the LLM to decide when to use tools vs. answer directly, which is essential for multi-turn conversations.

## Implementation Details

### Key Code Patterns

```python
# Load environment variables from .env files
def _load_env():
    for env_file in [".env", ".env.agent.secret", ".env.docker.secret"]:
        # Parse key=value lines and set os.environ

# Tool execution loop
for _ in range(max_iter):
    response = client.chat.completions.create(model=model, messages=messages, tools=TOOLS)
    msg = response.choices[0].message
    
    if not msg.tool_calls:
        # Return final answer
        return
    
    # Add assistant message with tool_calls to conversation
    messages.append({"role": "assistant", "content": msg.content, "tool_calls": [...]})
    
    # Execute each tool and add results
    for tool_call in msg.tool_calls:
        result = execute_tool(name, args)
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

### Error Handling

- Directory traversal attempts return "Error: Invalid path"
- File read errors return "Error: [Errno 2] No such file..."
- API connection errors return status 503 with error message
- Missing LMS_API_KEY returns status 500
- Any unexpected exception is caught and returned as JSON with error details