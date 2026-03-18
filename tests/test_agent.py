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


def test_read_file_tool_called_for_code_question():
    """Test that the agent uses read_file for questions about source code."""
    env = os.environ.copy()
    env["LLM_API_KEY"] = "my-secret-qwen-key"
    env["LLM_API_BASE"] = "http://10.93.25.207:42005/v1"
    env["LLM_MODEL"] = "qwen3-coder-plus"

    result = subprocess.run(
        ["uv", "run", "agent.py", "What framework does the backend use?"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env
    )

    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    output = json.loads(result.stdout)
    
    # Check that read_file was called
    tools_used = [tc.get("tool") for tc in output.get("tool_calls", [])]
    assert "read_file" in tools_used, f"Expected read_file to be called, but got tools: {tools_used}"
    
    # Check that the answer mentions FastAPI
    assert "fastapi" in output.get("answer", "").lower(), f"Answer should mention FastAPI: {output.get('answer')}"


def test_query_api_tool_called_for_data_question():
    """Test that the agent uses query_api for questions about live data."""
    env = os.environ.copy()
    env["LLM_API_KEY"] = "my-secret-qwen-key"
    env["LLM_API_BASE"] = "http://10.93.25.207:42005/v1"
    env["LLM_MODEL"] = "qwen3-coder-plus"
    env["LMS_API_KEY"] = "my-secret-api-key"

    result = subprocess.run(
        ["uv", "run", "agent.py", "How many items are in the database?"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env
    )

    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    output = json.loads(result.stdout)
    
    # Check that query_api was called
    tools_used = [tc.get("tool") for tc in output.get("tool_calls", [])]
    assert "query_api" in tools_used, f"Expected query_api to be called, but got tools: {tools_used}"
    
    # Check that the answer contains a number
    import re
    answer = output.get("answer", "")
    numbers = re.findall(r"\d+", answer)
    assert len(numbers) > 0, f"Answer should contain a number: {answer}"
