"""
Production-Ready Agent Template

Demonstrates production patterns: error handling, logging, monitoring, caching.
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, RunErrorHandlerInput, RunErrorHandlerResult

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom error handler
def on_max_turns(data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    """Handle max turns exceeded."""
    logger.warning(f"Max turns exceeded for agent: {data.agent.name}")
    return RunErrorHandlerResult(
        final_output="I couldn't complete this task within the turn limit. Please simplify your request.",
        include_in_history=False,
    )


# Tool with error handling
def tool_error_handler(ctx, error: Exception) -> str:
    """Handle tool errors gracefully."""
    logger.error(f"Tool error: {error}")
    return f"Service temporarily unavailable: {type(error).__name__}"


@function_tool(failure_error_function=tool_error_handler, timeout=10.0)
async def fetch_data(query: str) -> str:
    """Fetch data with error handling and timeout.

    Args:
        query: The search query.
    """
    try:
        # Simulate API call
        await asyncio.sleep(0.5)
        return f"Data for query: {query}"
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise


async def run_agent_with_monitoring(agent: Agent, query: str):
    """Run agent with monitoring and error handling."""
    start_time = datetime.now()

    logger.info(f"Starting agent: {agent.name}")
    logger.info(f"Query: {query}")

    try:
        result = await Runner.run(
            agent,
            query,
            max_turns=10,
            error_handlers={"max_turns": on_max_turns},
        )

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"Agent completed successfully")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Final agent: {result.last_agent.name}")

        return result

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Agent failed after {duration:.2f}s: {e}")
        raise


async def main():
    # Validate environment
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable required")

    # Create production agent
    agent = Agent(
        name="Production Assistant",
        instructions="""You are a production assistant with robust error handling.
        Use available tools carefully and handle errors gracefully.""",
        model="gpt-4o-mini",  # Cost-effective for production
        tools=[fetch_data],
    )

    # Test queries
    queries = [
        "Fetch data about Python",
        "What is machine learning?",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        try:
            result = await run_agent_with_monitoring(agent, query)
            print(f"Response: {result.final_output}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
