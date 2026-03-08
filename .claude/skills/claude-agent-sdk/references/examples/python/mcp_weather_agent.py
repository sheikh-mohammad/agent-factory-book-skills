# MCP Weather Agent Example
# Demonstrates creating custom MCP tools and using them in an agent

import asyncio
import httpx
from claude_agent_sdk import query, tool, create_sdk_mcp_server, ClaudeAgentOptions
from pydantic import BaseModel, Field

# Define tool schema with Pydantic
class WeatherArgs(BaseModel):
    latitude: float = Field(description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(description="Longitude coordinate (-180 to 180)")

# Define tool handler
async def get_weather(args: WeatherArgs):
    try:
        print(f"Fetching weather for {args.latitude}, {args.longitude}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": args.latitude,
                    "longitude": args.longitude,
                    "current": "temperature_2m,weathercode"
                }
            )

            if response.status_code != 200:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"API error: {response.status_code} {response.reason_phrase}"
                    }]
                }

            data = response.json()

            return {
                "content": [{
                    "type": "text",
                    "text": str({
                        "temperature": f"{data['current']['temperature_2m']}°C",
                        "weatherCode": data['current']['weathercode'],
                        "location": {"latitude": args.latitude, "longitude": args.longitude}
                    })
                }]
            }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to fetch weather: {str(e)}"
            }]
        }

# Create tool
weather_tool = tool(
    name="get_weather",
    description="Get current temperature and conditions for a location",
    parameters=WeatherArgs,
    handler=get_weather
)

# Create MCP server
weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[weather_tool]
)

# Streaming input generator (required for MCP)
async def generate_messages():
    yield {
        "role": "user",
        "content": "What is the weather like in San Francisco (37.7749, -122.4194) and New York (40.7128, -74.0060)?"
    }

async def main():
    print("Starting weather agent with custom MCP tool...\n")

    async for message in query(
        prompt=generate_messages(),
        options=ClaudeAgentOptions(
            mcp_servers={"weather": weather_server},
            allowed_tools=["mcp__weather__get_weather"],
            max_budget_usd=0.5
        )
    ):
        if message.type == "text":
            print(f"Claude: {message.text}")

        if message.type == "tool_use":
            print(f"\n[Tool] {message.name} {message.input}")

        if message.type == "result":
            print("\n--- Result ---")
            if message.subtype == "success":
                print("Status: Success")
                print(f"Cost: ${message.total_cost_usd:.4f}")
            else:
                print(f"Error: {message.subtype}")

if __name__ == "__main__":
    asyncio.run(main())
