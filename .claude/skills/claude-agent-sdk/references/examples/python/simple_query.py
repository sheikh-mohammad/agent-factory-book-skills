# Simple Query Example
# Demonstrates basic agent usage with built-in tools

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    print("Starting simple agent query...\n")

    async for message in query(
        prompt="Analyze the files in the current directory and summarize what this project does",
        options=ClaudeAgentOptions(
            allowed_tools=["Bash", "Glob", "Read"],
            max_budget_usd=0.5,
            max_turns=20
        )
    ):
        # Log text responses
        if message.type == "text":
            print(f"Claude: {message.text}")

        # Log tool usage
        if message.type == "tool_use":
            print(f"\n[Tool] {message.name}")

        # Handle final result
        if message.type == "result":
            print("\n--- Result ---")

            if message.subtype == "success":
                print("Status: Success")
                print(f"Result: {message.result}")
                print(f"Cost: ${message.total_cost_usd:.4f}")
                print(f"Turns: {message.turn_count}")
            else:
                print("Status: Error")
                print(f"Error type: {message.subtype}")

if __name__ == "__main__":
    asyncio.run(main())
