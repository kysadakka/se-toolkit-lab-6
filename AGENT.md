# Task 2: Documentation Agent

## Tools
- `read_file(path)`: read file contents
- `list_files(path)`: list directory contents

## Security
Both tools block paths containing ".." to prevent directory traversal.

## Usage
```bash
uv run agent.py "How do I resolve a merge conflict?"
