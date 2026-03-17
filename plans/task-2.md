# Task 2: Documentation Agent - Implementation Plan

## Tools
- `read_file(path)`: read file contents
- `list_files(path)`: list directory contents

## Security
- Block paths containing ".." or starting with "/"

## Agent Loop
1. Send question + tool definitions to LLM
2. If tool calls → execute, add results, repeat
3. If no tool calls → output JSON with answer, source, tool_calls
4. Max 10 iterations

## Output Format
{
  "answer": "the answer",
  "source": "wiki/file.md",
  "tool_calls": [
    {"tool": "read_file", "args": {"path": "..."}, "result": "..."}
  ]
}

## Tests
- Test 1: question requiring read_file
- Test 2: question requiring list_files
