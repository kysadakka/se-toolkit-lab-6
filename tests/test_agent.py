import subprocess
import json
import os

def test_agent_returns_json():
    # Set environment variables for the test
    env = os.environ.copy()
    env["LLM_API_KEY"] = "my-secret-qwen-key"
    env["LLM_API_BASE"] = "http://10.93.25.207:42005/v1"
    env["LLM_MODEL"] = "qwen3-coder-plus"
    
    result = subprocess.run(
        ["uv", "run", "agent.py", "What is 2+2?"],
        capture_output=True,
        text=True,
        timeout=30,
        env=env
    )
    
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "answer" in output
    assert "tool_calls" in output
