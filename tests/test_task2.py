import subprocess
import json
import os

def test_agent_has_tools():
    """Test that agent defines required tools."""
    env = os.environ.copy()
    env["LLM_API_KEY"] = "test-key"
    env["LLM_API_BASE"] = "http://test/v1"
    
    result = subprocess.run(
        ["uv", "run", "agent.py", "test"],
        capture_output=True,
        text=True,
        env=env
    )
    
    # Just check that it runs and returns JSON
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "answer" in output
    assert "source" in output
    assert "tool_calls" in output

def test_read_file_tool():
    """Test read_file function directly."""
    from agent import read_file
    
    # Create test file
    with open("test.txt", "w") as f:
        f.write("test content")
    
    result = read_file("test.txt")
    assert "test content" in result
    
    # Clean up
    os.remove("test.txt")
    
    # Test path traversal prevention
    result = read_file("../../../etc/passwd")
    assert "Error" in result

def test_list_files_tool():
    """Test list_files function directly."""
    from agent import list_files
    
    result = list_files(".")
    assert "agent.py" in result
    
    # Test path traversal prevention
    result = list_files("../../../etc")
    assert "Error" in result
