Task 3: The System Agent - Implementation Plan

1. New Tool: `query_api`
- **Purpose**: Call the deployed backend API.
- **Parameters**: `method` (GET, POST...), `path` (e.g., `/items/`), `body` (optional JSON string).
- **Authentication**: Uses `LMS_API_KEY` from environment variables.
- **Base URL**: Reads `AGENT_API_BASE_URL` from env (default `http://localhost:42002`).

2. Agent Updates
- Add `query_api` to the existing `TOOLS` list with a clear schema.
- Update the system prompt to instruct the LLM:
  - Use `read_file`/`list_files` for code/wiki questions.
  - Use `query_api` for questions about the *live system* (data counts, status codes, errors).
  - Chain tools if needed: e.g., get an API error, then `read_file` to diagnose the bug.

3. Environment Variables 
Agent must read all config from env, **never hardcode**:
- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` (from `.env.agent.secret`)
- `LMS_API_KEY` (from `.env.docker.secret`)
- `AGENT_API_BASE_URL` (default `http://localhost:42002`)

4. Initial Benchmark Run
**Command:** `uv run run_eval.py`
**Initial Score:** 0/10
**First Failures (examples):**
- Q4 (item count): Failed because `query_api` tool wasn't called.
- Q5 (status code): Failed because `query_api` tool wasn't called.
- Q8 (request lifecycle): Failed because answer lacked detail.

5. Iteration Strategy
1.  Implement `query_api` tool and update prompt.
2.  Run benchmark, focus on one failing question at a time.
3.  Debug by checking tool calls, return values, and prompt clarity.
4.  Aim to pass all 10 local questions before creating the PR.
