import os
import sys
import json
from openai import OpenAI

def main():
    # Get question from command line
    if len(sys.argv) < 2:
        print("Error: No question provided", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Get config from environment variables
    api_key = os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("LLM_API_BASE")
    model = os.environ.get("LLM_MODEL", "qwen3-coder-plus")
    
    if not api_key or not api_base:
        print("Error: LLM_API_KEY and LLM_API_BASE must be set", file=sys.stderr)
        sys.exit(1)
    
    # Call LLM
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    
    # Output JSON
    result = {
        "answer": response.choices[0].message.content,
        "tool_calls": []
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
