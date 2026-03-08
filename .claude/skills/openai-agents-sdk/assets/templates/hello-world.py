"""
Hello World - OpenAI Agents SDK

The simplest possible agent implementation.
"""

import asyncio
from agents import Agent, Runner


async def main():
    # Create a basic agent
    agent = Agent(
        name="Hello World Agent",
        instructions="You are a friendly assistant. Keep responses brief and helpful.",
    )

    # Run the agent
    result = await Runner.run(agent, "Hello! What can you help me with?")

    # Print the response
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
