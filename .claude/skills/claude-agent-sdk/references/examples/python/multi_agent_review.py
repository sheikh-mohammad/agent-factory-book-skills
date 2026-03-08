# Multi-Agent Code Review Example
# Demonstrates orchestrating multiple specialized subagents

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    print("Starting multi-agent code review...\n")

    async for message in query(
        prompt="Perform a comprehensive code review of this project. Use specialized reviewers for security, performance, and code quality.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            max_budget_usd=2.0,
            max_turns=100,

            # Define specialized subagents
            agents={
                "security-reviewer": {
                    "description": "Security expert for vulnerability analysis - use for security reviews",
                    "prompt": "Analyze code for security vulnerabilities including SQL injection, XSS, authentication issues, and insecure dependencies",
                    "tools": ["Read", "Grep", "Glob"],
                    "model": "opus",
                    "system_prompt": "You are a security expert with 10 years of experience in application security"
                },

                "performance-reviewer": {
                    "description": "Performance optimization expert - use for performance analysis",
                    "prompt": "Identify performance bottlenecks, inefficient algorithms, and optimization opportunities",
                    "tools": ["Read", "Grep", "Bash"],
                    "model": "sonnet",
                    "system_prompt": "You are a performance optimization expert"
                },

                "code-quality-reviewer": {
                    "description": "Code quality and maintainability expert - use for code quality review",
                    "prompt": "Review code quality, readability, maintainability, and adherence to best practices",
                    "tools": ["Read", "Grep", "Glob"],
                    "model": "sonnet",
                    "system_prompt": "You are a senior software engineer focused on code quality"
                }
            }
        )
    ):
        if message.type == "text":
            print(f"\n{message.text}")

        if message.type == "tool_use":
            if message.name == "Agent":
                print(f"\n[Subagent] Invoking: {message.input.get('description', 'unknown')}")
            else:
                print(f"[Tool] {message.name}")

        if message.type == "result":
            print("\n=== Review Complete ===")

            if message.subtype == "success":
                print("Status: Success")
                print(f"Total Cost: ${message.total_cost_usd:.4f}")
                print(f"Total Turns: {message.turn_count}")
                print("\nFinal Report:")
                print(message.result)
            else:
                print(f"Error: {message.subtype}")

if __name__ == "__main__":
    asyncio.run(main())
