General:
    - Provider: Qwen Code API (self-hosted on my VM)
    - Model: `qwen3-coder-plus`
    - Reason: Qwen provides 1000 free requests per day, works from Russia, and requires no credit card.

Output: 
    - stdout: print JSON response as '{"answer": "...", "tool_calls": []}`
    - stderr: debug/progress
 
Exit:
    - 0 on success

Agent Structure:
    - Read question
    - Load `.env.agent.secret`
    - Call LLM
    - Send request to LLM
    - Print JSON

- agent.md: provider, setup, usage