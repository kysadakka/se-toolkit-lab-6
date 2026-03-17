CLI agent that sends questions to LLM and returns JSON.

## Configuration
Uses environment variables:
- `LLM_API_KEY`: your Qwen API key
- `LLM_API_BASE`: http://10.93.25.207:42005/v1
- `LLM_MODEL`: qwen3-coder-plus (default)

## Usage
```bash
export LLM_API_KEY=my-secret-qwen-key
export LLM_API_BASE=http://10.93.25.207:42005/v1
uv run agent.py "Your question"

