# Python SDK Reference

Complete guide to building MCP servers with Python using FastMCP and the core MCP SDK.

## Installation

```bash
# FastMCP (recommended for most use cases)
pip install "mcp[cli]"
# or with uv
uv add "mcp[cli]"

# Core SDK only (advanced use cases)
pip install mcp
```

**Requirements**: Python 3.10 or higher

---

## FastMCP (Recommended)

FastMCP provides a high-level API with automatic schema generation from type hints and docstrings.

### Basic Server Setup

```python
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("my-server")

# Run with stdio transport
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Implementing Tools

Tools are functions decorated with `@mcp.tool()`. FastMCP automatically generates schemas from type hints and docstrings.

```python
@mcp.tool()
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
    """
    try:
        result = eval(expression)  # Use safe_eval in production
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

**Key Points**:
- Use `async def` for async operations (recommended)
- Type hints are required for schema generation
- Docstring becomes tool description
- Args section documents parameters
- Return string or structured data

### Structured Output

Return Pydantic models, TypedDicts, or dataclasses for structured responses:

```python
from pydantic import BaseModel
from typing import TypedDict

class WeatherResult(BaseModel):
    temperature: float
    conditions: str
    humidity: int

@mcp.tool()
async def get_weather(location: str) -> WeatherResult:
    """Get current weather for a location."""
    # Fetch weather data
    return WeatherResult(
        temperature=72.5,
        conditions="Partly cloudy",
        humidity=65
    )
```

### Implementing Resources

Resources expose data via URI patterns:

```python
@mcp.resource("file://documents/{name}")
async def read_document(name: str) -> str:
    """Read a document by name.

    Args:
        name: Document filename
    """
    with open(f"documents/{name}", "r") as f:
        return f.read()
```

**URI Patterns**:
- Use `{param}` for path parameters
- Parameters are extracted and passed to function
- Return string content or structured data

### Implementing Prompts

Prompts are reusable templates:

```python
@mcp.prompt()
async def code_review(language: str, focus: str = "best practices") -> str:
    """Generate a code review prompt.

    Args:
        language: Programming language
        focus: What to focus on in the review
    """
    return f"""Review this {language} code focusing on {focus}.

Provide specific, actionable feedback on:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
"""
```

### Context Access

Access server context for progress reporting, logging, and session info:

```python
from mcp.server.fastmcp import Context
from mcp.types import ServerSession, LifespanContext

@mcp.tool()
async def long_operation(
    data: str,
    ctx: Context[ServerSession, LifespanContext]
) -> str:
    """Perform a long-running operation with progress updates."""

    # Report progress
    await ctx.report_progress(0.0, "Starting operation")

    # Log messages
    ctx.info("Processing data")
    ctx.debug(f"Data length: {len(data)}")

    # Perform work
    for i in range(10):
        await ctx.report_progress(i / 10, f"Step {i+1}/10")
        # Do work

    await ctx.report_progress(1.0, "Complete")
    return "Operation completed successfully"
```

**Context Methods**:
- `ctx.report_progress(progress, message)` - Report progress (0.0 to 1.0)
- `ctx.info(message)` - Log info message
- `ctx.debug(message)` - Log debug message
- `ctx.error(message)` - Log error message
- `ctx.session` - Access session metadata

### Lifecycle Management

Handle server startup and shutdown:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Startup
    db = await connect_database()
    app.state.db = db
    yield
    # Shutdown
    await db.close()

mcp = FastMCP("my-server", lifespan=lifespan)

@mcp.tool()
async def query_db(sql: str) -> str:
    """Execute a database query."""
    db = mcp.state.db
    result = await db.execute(sql)
    return str(result)
```

### HTTP Transport

Run server with HTTP transport for remote access:

```python
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        port=8000,
        host="0.0.0.0"
    )
```

**CORS Configuration**:
```python
mcp.run(
    transport="streamable-http",
    port=8000,
    cors_origins=["https://example.com"]
)
```

---

## Core MCP SDK (Advanced)

For advanced use cases requiring full control over the protocol.

### Basic Server Setup

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create server
server = Server("my-server")

# Define tools
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculate",
            description="Evaluate mathematical expressions",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "calculate":
        result = eval(arguments["expression"])
        return [TextContent(type="text", text=f"Result: {result}")]
    raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Tool Implementation

```python
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name == "get_weather":
        location = arguments["location"]
        # Fetch weather
        return [
            TextContent(
                type="text",
                text=f"Weather in {location}: 72°F, sunny"
            )
        ]
```

### Resource Implementation

```python
from mcp.types import Resource, ResourceContents

@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="file://documents/readme.txt",
            name="README",
            description="Project README file",
            mimeType="text/plain"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> ResourceContents:
    if uri == "file://documents/readme.txt":
        with open("readme.txt", "r") as f:
            content = f.read()
        return ResourceContents(
            contents=[
                TextContent(type="text", text=content)
            ]
        )
```

---

## Error Handling Best Practices

### Input Validation

```python
@mcp.tool()
async def process_data(data: str, limit: int = 100) -> str:
    """Process data with validation."""

    # Validate inputs
    if not data:
        raise ValueError("Data cannot be empty")

    if limit < 1 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")

    # Process
    result = data[:limit]
    return result
```

### Exception Handling

```python
import logging

@mcp.tool()
async def external_api_call(endpoint: str) -> str:
    """Call external API with proper error handling."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, timeout=30.0)
            response.raise_for_status()
            return response.text

    except httpx.TimeoutException:
        logging.error(f"Timeout calling {endpoint}")
        return "Request timed out. Please try again."

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error {e.response.status_code}: {endpoint}")
        return f"API error: {e.response.status_code}"

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "An unexpected error occurred."
```

---

## Logging Configuration

### STDIO Transport (Critical)

**NEVER use `print()` without `file=sys.stderr`** - it corrupts JSON-RPC messages.

```python
import sys
import logging

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Safe printing
print("Server starting", file=sys.stderr)

# Use logging (writes to stderr by default)
logging.info("Server started")
logging.debug("Debug information")
logging.error("Error occurred")
```

### HTTP Transport

Standard logging is fine:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.info("HTTP server started on port 8000")
```

---

## Complete Example: Weather Server

```python
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make request to NWS API with error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # Get forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get forecast
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format periods
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Testing

### Unit Testing Tools

```python
import pytest
from your_server import mcp

@pytest.mark.asyncio
async def test_calculate_tool():
    result = await mcp.call_tool("calculate", {"expression": "2 + 3"})
    assert "5" in result
```

### Integration Testing

```python
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_server_integration():
    async with stdio_client("python", ["server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0

            # Call tool
            result = await session.call_tool("calculate", {"expression": "10 * 5"})
            assert "50" in result.content[0].text
```

---

## Performance Tips

1. **Use async/await** - Don't block the event loop
2. **Connection pooling** - Reuse HTTP clients and database connections
3. **Caching** - Cache expensive operations
4. **Batch operations** - Process multiple items together
5. **Timeouts** - Always set timeouts on external calls

```python
# Connection pooling
client = httpx.AsyncClient()

@mcp.tool()
async def fetch_data(url: str) -> str:
    """Fetch data using pooled connection."""
    response = await client.get(url, timeout=10.0)
    return response.text

# Cleanup on shutdown
@asynccontextmanager
async def lifespan(app):
    yield
    await client.aclose()

mcp = FastMCP("my-server", lifespan=lifespan)
```
