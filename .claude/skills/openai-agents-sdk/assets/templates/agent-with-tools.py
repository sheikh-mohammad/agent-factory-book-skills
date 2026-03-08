"""
Agent with Custom Tools Template

Demonstrates how to create an agent with custom function tools.
"""

import asyncio
from agents import Agent, Runner, function_tool


# Define custom tools
@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: The city name to get weather for.
    """
    # In production, call a real weather API
    return f"The weather in {city} is sunny and 72°F"


@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: The mathematical expression to evaluate (e.g., "2 + 2").
    """
    try:
        # Safe evaluation (in production, use ast.literal_eval or similar)
        result = eval(expression, {"__builtins__": {}})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
async def search_database(query: str, limit: int = 10) -> str:
    """Search the database for matching records.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.
    """
    # In production, query your actual database
    await asyncio.sleep(0.1)  # Simulate async operation
    return f"Found {limit} results for '{query}'"


async def main():
    # Create agent with tools
    agent = Agent(
        name="Assistant with Tools",
        instructions="""You are a helpful assistant with access to tools.
        - Use get_weather to check weather in cities
        - Use calculate for math operations
        - Use search_database to find information
        Be helpful and use tools when appropriate.""",
        tools=[get_weather, calculate, search_database],
    )

    # Example queries
    queries = [
        "What's the weather in Tokyo?",
        "Calculate 15 * 23",
        "Search for Python tutorials",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        result = await Runner.run(agent, query)
        print(f"Response: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
