Task 3: The System Agent - Implementation Plan

1. New Tool: `query_api`
- **Purpose**: Call the deployed backend API.
- **Parameters**: `method` (GET, POST...), `path` (e.g., `/items/`), `body` (optional JSON string), `auth` (optional boolean for authentication).
- **Authentication**: Uses `LMS_API_KEY` from environment variables.
- **Base URL**: Reads `AGENT_API_BASE_URL` from env (default `http://localhost:42002`).

2. Agent Updates
- Add `query_api` to the existing `TOOLS` list with a clear schema.
- Update the system prompt to instruct the LLM:
  - Use `read_file`/`list_files` for code/wiki questions.
  - Use `query_api` for questions about the *live system* (data counts, status codes, errors).
  - Chain tools if needed: e.g., get an API error, then `read_file` to diagnose the bug.
- Add source tracking to set the `source` field based on files read or API calls.
- Add intermediate commentary detection to handle LLM returning thoughts instead of answers.

3. Environment Variables
Agent must read all config from env, **never hardcode**:
- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` (from `.env.agent.secret`)
- `LMS_API_KEY` (from `.env.docker.secret`)
- `AGENT_API_BASE_URL` (default `http://localhost:42002`)

4. Initial Benchmark Run
**Command:** `uv run run_eval.py`
**Initial Score:** 0/10
**First Failures (examples):**
- Q0-Q3: Failed because environment variables weren't loaded.
- Q4 (item count): Failed because `query_api` tool wasn't called.
- Q5 (status code): Failed because agent returned 200 instead of 401 (auth header always sent).
- Q6-Q7: Failed because source field wasn't set correctly.
- Q8-Q9: Failed because LLM returned intermediate thoughts instead of final answer.

5. Iteration Strategy & Fixes Applied
1.  **Environment Loading**: Added `_load_env()` function to load `.env`, `.env.agent.secret`, `.env.docker.secret`.
2.  **Tool Schema**: Added `auth` parameter to `query_api` for unauthenticated requests.
3.  **Source Tracking**: Added `files_read` list to track files and set source accordingly.
4.  **Intermediate Commentary Detection**: Added detection for phrases like "Let me check" to force final answers.
5.  **System Prompt Refinement**: Added explicit rules for bug diagnosis (first query_api, then read_file).
6.  **Tool Choice**: Used `tool_choice="auto"` to let LLM decide when to use tools.

6. Final Benchmark Results
**Command:** `uv run run_eval.py`
**Final Score:** 10/10 (All local questions passed)

| Question | Type | Tools Required | Status |
|----------|------|----------------|--------|
| 0 | Wiki lookup (branch protection) | `read_file` | ✓ |
| 1 | Wiki lookup (SSH) | `read_file` | ✓ |
| 2 | Code lookup (framework) | `read_file` | ✓ |
| 3 | List routers | `list_files`, `read_file` | ✓ |
| 4 | Item count | `query_api` | ✓ |
| 5 | Unauthenticated status | `query_api` (auth=false) | ✓ |
| 6 | Division by zero bug | `query_api`, `read_file` | ✓ |
| 7 | NoneType bug | `query_api`, `read_file` | ✓ |
| 8 | Request lifecycle | `read_file` | ✓ |
| 9 | ETL idempotency | `read_file` | ✓ |

7. Tests Added
- `test_read_file_tool_called_for_code_question`: Verifies read_file is used for code questions.
- `test_query_api_tool_called_for_data_question`: Verifies query_api is used for data questions.
