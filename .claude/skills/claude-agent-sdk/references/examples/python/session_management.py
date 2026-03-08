# Session Management Example
# Demonstrates continue, resume, and fork patterns

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def demonstrate_continue():
    print("=== Demonstrating Continue ===\n")

    # First query
    print("Query 1: Analyze auth module")
    async for message in query(
        prompt="Read and analyze the authentication module",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Grep"])
    ):
        if message.type == "result" and message.subtype == "success":
            print("Analysis complete\n")

    # Continue from most recent session
    print("Query 2: Continue with refactoring")
    async for message in query(
        prompt="Now refactor it to use OAuth2",
        options=ClaudeAgentOptions(
            continue_session=True,
            allowed_tools=["Read", "Edit"]
        )
    ):
        if message.type == "result" and message.subtype == "success":
            print("Refactoring complete\n")

async def demonstrate_resume():
    print("=== Demonstrating Resume ===\n")

    session_id = None

    # First query - capture session ID
    print("Starting initial analysis...")
    async for message in query(
        prompt="Analyze the codebase structure",
        options=ClaudeAgentOptions(allowed_tools=["Glob", "Read"])
    ):
        if message.type == "result":
            session_id = message.session_id
            print(f"Session ID: {session_id}\n")

    # Simulate doing other work...
    print("Doing other work...\n")

    # Resume specific session later
    print("Resuming previous session...")
    async for message in query(
        prompt="Based on your previous analysis, suggest improvements",
        options=ClaudeAgentOptions(
            resume=session_id,
            allowed_tools=["Read"]
        )
    ):
        if message.type == "result" and message.subtype == "success":
            print("Suggestions complete\n")

async def demonstrate_fork():
    print("=== Demonstrating Fork ===\n")

    original_session_id = None

    # Original implementation
    print("Original: Implementing with JWT")
    async for message in query(
        prompt="Implement authentication using JWT",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Write"])
    ):
        if message.type == "result":
            original_session_id = message.session_id
            print("JWT implementation complete\n")

    # Fork to try OAuth2
    print("Fork 1: Trying OAuth2 instead")
    async for message in query(
        prompt="Try implementing with OAuth2 instead",
        options=ClaudeAgentOptions(
            resume=original_session_id,
            fork_session=True,
            allowed_tools=["Read", "Write"]
        )
    ):
        if message.type == "result" and message.subtype == "success":
            print("OAuth2 implementation complete\n")

    # Fork to try session-based
    print("Fork 2: Trying session-based auth")
    async for message in query(
        prompt="Try implementing with session-based authentication",
        options=ClaudeAgentOptions(
            resume=original_session_id,
            fork_session=True,
            allowed_tools=["Read", "Write"]
        )
    ):
        if message.type == "result" and message.subtype == "success":
            print("Session-based implementation complete\n")

    print("All three approaches preserved in separate sessions!")

async def main():
    try:
        await demonstrate_continue()
        await demonstrate_resume()
        await demonstrate_fork()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
