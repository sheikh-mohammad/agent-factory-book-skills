# Function Tools

Create custom tools that agents can use to perform actions and access external data.

## Basic Function Tool

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: The city name to get weather for.
    """
    # Your implementation
    return f"The weather in {city} is sunny, 72°F"
```

**Key points**:
- Use `@function_tool` decorator
- Docstring becomes tool description for LLM
- Type hints define parameter types
- Return type must be serializable (str, int, dict, list, etc.)

## Parameters

### Required vs Optional

```python
@function_tool
def search_database(
    query: str,           # Required parameter
    limit: int = 10,      # Optional with default
    filters: dict = {},   # Optional with default
) -> str:
    """Search the database for matching records.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.
        filters: Optional filters to apply.
    """
    return f"Found {limit} results for '{query}'"
```

### Parameter Constraints with Pydantic

```python
from typing import Annotated
from pydantic import Field

@function_tool
def rate_item(
    item_id: str,
    score: Annotated[int, Field(ge=1, le=5, description="Rating from 1 to 5")]
) -> str:
    """Rate an item with a score.

    Args:
        item_id: The unique identifier of the item.
        score: Rating score between 1 and 5.
    """
    return f"Item {item_id} rated with score {score}"
```

**Pydantic constraints**:
- `ge` / `le`: Greater/less than or equal
- `gt` / `lt`: Greater/less than
- `min_length` / `max_length`: String length
- `regex`: Pattern matching

### Complex Types

```python
from typing_extensions import TypedDict

class Location(TypedDict):
    lat: float
    long: float

@function_tool
def fetch_weather(location: Location) -> str:
    """Fetch weather for a location.

    Args:
        location: The location coordinates.
    """
    return f"Weather at {location['lat']}, {location['long']}: sunny"
```

## Async Tools

Use async for I/O operations (API calls, database queries, file operations):

```python
import httpx

@function_tool
async def fetch_user_data(user_id: str) -> str:
    """Fetch data for a specific user.

    Args:
        user_id: The unique identifier of the user.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()
```

**When to use async**:
- API calls (HTTP requests)
- Database queries
- File I/O operations
- Any operation that waits for external resources

**When to use sync**:
- Pure computation
- In-memory operations
- Simple data transformations

## Context Access

Access agent context for advanced use cases:

```python
from agents import function_tool, RunContextWrapper

@function_tool
async def fetch_user_data(ctx: RunContextWrapper, user_id: str) -> str:
    """Fetch data for a specific user.

    Args:
        user_id: The unique identifier of the user.
    """
    # Access agent context
    agent_name = ctx.agent.name

    # Your implementation
    return f"User data for {user_id} (requested by {agent_name})"
```

**Context provides**:
- `ctx.agent`: Current agent instance
- `ctx.history`: Conversation history
- Custom data passed via context

**Note**: Context parameter must be first, not included in docstring Args.

## Timeouts

Set execution timeouts for long-running operations:

```python
@function_tool(timeout=5.0)  # 5 second timeout
async def slow_operation(data: str) -> str:
    """Process data with a timeout.

    Args:
        data: The data to process.
    """
    import asyncio
    await asyncio.sleep(2)
    return f"Processed: {data}"
```

**Best practices**:
- Set timeouts for all external API calls
- Use shorter timeouts for user-facing operations
- Use longer timeouts for batch processing
- Handle timeout errors gracefully

## Error Handling

### Custom Error Messages

```python
from agents import function_tool, RunContextWrapper

def custom_error_handler(ctx: RunContextWrapper, error: Exception) -> str:
    """Provide user-friendly error message."""
    if isinstance(error, ValueError):
        return "Invalid input provided. Please check your parameters."
    elif isinstance(error, ConnectionError):
        return "Service temporarily unavailable. Please try again later."
    else:
        return f"An error occurred: {type(error).__name__}"

@function_tool(failure_error_function=custom_error_handler)
def risky_operation(value: int) -> str:
    """An operation that might fail.

    Args:
        value: The value to process.
    """
    if value < 0:
        raise ValueError("Value must be positive")
    return f"Result: {value * 2}"
```

**Error handler receives**:
- `ctx`: Agent context
- `error`: The exception that occurred

**Error handler returns**:
- String message sent to LLM (not user directly)
- LLM decides how to communicate to user

### Validation

```python
@function_tool
def process_order(order_id: str, amount: float) -> str:
    """Process an order.

    Args:
        order_id: The order identifier.
        amount: The order amount in USD.
    """
    # Validate inputs
    if not order_id.startswith("ORD-"):
        raise ValueError("Invalid order ID format")

    if amount <= 0:
        raise ValueError("Amount must be positive")

    if amount > 10000:
        raise ValueError("Amount exceeds maximum limit")

    # Process order
    return f"Order {order_id} processed for ${amount}"
```

## Tool Naming

### Default Naming

By default, tool name is the function name:

```python
@function_tool
def search_database(query: str) -> str:
    """Search the database."""
    pass

# Tool name: "search_database"
```

### Custom Naming

Override the tool name:

```python
@function_tool(name_override="search")
def search_database(query: str) -> str:
    """Search the database."""
    pass

# Tool name: "search"
```

**When to override**:
- Simplify long function names
- Match existing API conventions
- Avoid naming conflicts

## Tool Organization

### Single File

For small projects:

```python
# tools.py
from agents import function_tool

@function_tool
def tool1():
    pass

@function_tool
def tool2():
    pass

# main.py
from agents import Agent
from tools import tool1, tool2

agent = Agent(name="Assistant", tools=[tool1, tool2])
```

### Multiple Files

For larger projects:

```python
# tools/database.py
@function_tool
def search_database():
    pass

# tools/api.py
@function_tool
def call_api():
    pass

# main.py
from tools.database import search_database
from tools.api import call_api

agent = Agent(name="Assistant", tools=[search_database, call_api])
```

### Tool Registry

For dynamic tool loading:

```python
# tools/registry.py
TOOLS = {}

def register_tool(func):
    TOOLS[func.__name__] = func
    return function_tool(func)

@register_tool
def tool1():
    pass

@register_tool
def tool2():
    pass

# main.py
from tools.registry import TOOLS

agent = Agent(name="Assistant", tools=list(TOOLS.values()))
```

## Testing Tools

### Unit Testing

```python
import pytest
from tools import search_database

def test_search_database():
    result = search_database("test query", limit=5)
    assert "5 results" in result

def test_search_database_validation():
    with pytest.raises(ValueError):
        search_database("", limit=-1)
```

### Integration Testing

```python
import pytest
from agents import Agent, Runner

@pytest.mark.asyncio
async def test_agent_uses_tool():
    agent = Agent(
        name="Test Agent",
        instructions="Use search_database to find information.",
        tools=[search_database],
    )

    result = await Runner.run(agent, "Search for Python tutorials")
    assert result.final_output is not None
    # Verify tool was called by checking history
```

## Common Patterns

### Database Query Tool

```python
import asyncpg

@function_tool
async def query_database(sql: str) -> str:
    """Execute a SQL query.

    Args:
        sql: The SQL query to execute.
    """
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(sql)
        return str(rows)
    finally:
        await conn.close()
```

### API Call Tool

```python
import httpx

@function_tool
async def call_external_api(endpoint: str, method: str = "GET") -> str:
    """Call an external API.

    Args:
        endpoint: The API endpoint path.
        method: HTTP method (GET, POST, etc.).
    """
    async with httpx.AsyncClient() as client:
        response = await client.request(method, f"{API_BASE_URL}/{endpoint}")
        return response.json()
```

### File Operation Tool

```python
import aiofiles

@function_tool
async def read_file(path: str) -> str:
    """Read contents of a file.

    Args:
        path: The file path to read.
    """
    async with aiofiles.open(path, 'r') as f:
        content = await f.read()
    return content
```

### Calculation Tool

```python
@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: The expression to evaluate (e.g., "2 + 2").
    """
    try:
        # Safe evaluation (use ast.literal_eval or similar in production)
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")
```

## Best Practices

### Docstrings
- First line: Clear, concise description
- Args section: Describe each parameter
- Include examples for complex tools
- Mention side effects or requirements

### Error Handling
- Validate all inputs
- Provide clear error messages
- Use custom error handlers for user-facing errors
- Log errors for debugging

### Performance
- Use async for I/O operations
- Set appropriate timeouts
- Cache results when possible
- Avoid expensive operations in tools

### Security
- Validate and sanitize all inputs
- Never execute arbitrary code
- Limit access to sensitive resources
- Use environment variables for credentials

### Testing
- Unit test each tool independently
- Test error cases and edge cases
- Integration test with agents
- Mock external dependencies

## Troubleshooting

### Tool not being called
- Check docstring is clear and descriptive
- Verify tool is in agent's tools list
- Review agent instructions mention the tool
- Test tool independently first

### Tool errors not handled
- Add `failure_error_function` parameter
- Validate inputs before processing
- Use try/except for external calls
- Log errors for debugging

### Tool timeouts
- Increase timeout parameter
- Optimize tool implementation
- Use async for I/O operations
- Consider breaking into smaller tools

### Type errors
- Use proper type hints
- Validate complex types with Pydantic
- Test with various input types
- Check return type is serializable
