"""
Streaming Response Template

Demonstrates real-time streaming of agent responses.
"""

import asyncio
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent


async def main():
    # Create agent
    agent = Agent(
        name="Storyteller",
        instructions="You tell engaging stories. Be creative and descriptive.",
    )

    print("Streaming response:\n")

    # Run with streaming
    result = Runner.run_streamed(agent, "Tell me a short story about a robot learning to paint")

    # Stream events
    async for event in result.stream_events():
        # Stream text tokens
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

        # Show tool calls (if any)
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print(f"\n\n[Tool called: {event.item.name}]")

        # Show agent changes (if multi-agent)
        elif event.type == "agent_updated_stream_event":
            print(f"\n\n[Agent switched to: {event.new_agent.name}]")

    # Final output available after stream completes
    print(f"\n\n{'='*60}")
    print(f"Stream complete!")
    print(f"Final output length: {len(result.final_output)} characters")


if __name__ == "__main__":
    asyncio.run(main())
