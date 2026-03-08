# Tools Integration

Comprehensive guide for integrating tools with Google ADK agents.

## Overview

Tools enable agents to perform actions beyond text generation. ADK supports multiple tool types:

| Tool Type | Use Case | Example |
|-----------|----------|---------|
| **Function Tools** | Custom Python logic | Database queries, calculations, file operations |
| **OpenAPI Tools** | REST API integration | Third-party APIs, internal services |
| **MCP Tools** | Model Context Protocol | Filesystem, databases, external systems |
| **Google Cloud Tools** | GCP services | BigQuery, Cloud Storage, Vertex AI |
| **Built-in Tools** | Pre-configured utilities | Search, code execution |

## Function Tools

Python functions wrapped as agent tools.

### Basic Function Tool

```python
def get_weather(city: str) -> str:
    """Get weather for a city.

    Args:
        city: The city name to get weather for.

    Returns:
        Weather information string.
    """
    # Implementation
    return f"The weather in {city} is sunny, 72°F"

agent = Agent(
    name="weather_assistant",
    model="gemini-2.5-flash",
    instruction="Use the get_weather tool to provide weather information.",
    tools=[get_weather],
)
```

### Function Tool Requirements

**Must have:**
- Docstring with description (first line)
- Args section documenting each parameter
- Returns section describing return value
- Type hints for all parameters and return value

**Example with all requirements:**
```python
def search_database(query: str, limit: int = 10) -> list[dict]:
    """Search the database for records.

    Args:
        query: Search query string.
        limit: Maximum number of results to return. Defaults to 10.

    Returns:
        List of matching records as dictionaries.
    """
    # Implementation
    return [
        {"id": 1, "name": "Result 1"},
        {"id": 2, "name": "Result 2"},
    ]
```

### Stateful Function Tools

Access session state using ToolContext:

```python
from google.adk.tools import ToolContext

def add_to_cart(
    item_name: str,
    quantity: int,
    tool_context: ToolContext
) -> str:
    """Add item to shopping cart.

    Args:
        item_name: Name of the item.
        quantity: Number of items to add.
        tool_context: Context with session state access.

    Returns:
        Confirmation message.
    """
    # Get current cart from session state
    cart = tool_context.state.get("cart", [])

    # Add item
    cart.append({"item": item_name, "quantity": quantity})

    # Update state
    tool_context.state["cart"] = cart

    total_items = sum(item["quantity"] for item in cart)
    return f"Added {quantity}x {item_name}. Cart now has {total_items} items."

def get_cart_summary(tool_context: ToolContext) -> str:
    """Get shopping cart summary.

    Args:
        tool_context: Context with session state access.

    Returns:
        Cart contents summary.
    """
    cart = tool_context.state.get("cart", [])
    if not cart:
        return "Your cart is empty."

    items = [f"- {item['item']} x{item['quantity']}" for item in cart]
    return "Cart contents:\n" + "\n".join(items)
```

### Async Function Tools

For I/O-bound operations:

```python
import httpx

async def fetch_data(url: str) -> dict:
    """Fetch data from a URL.

    Args:
        url: The URL to fetch data from.

    Returns:
        JSON response as dictionary.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Memory-Aware Tools

Access long-term memory:

```python
async def recall_information(
    query: str,
    tool_context: ToolContext
) -> str:
    """Search memory for relevant information.

    Args:
        query: What to search for in memory.
        tool_context: Context with memory access.

    Returns:
        Relevant memories or indication that nothing was found.
    """
    results = await tool_context.search_memory(query)

    if not results.memories:
        return "No relevant memories found."

    memories = [f"- {memory.content}" for memory in results.memories]
    return "Found memories:\n" + "\n".join(memories)
```

## OpenAPI Tools

Automatically generate tools from OpenAPI specifications.

### Basic OpenAPI Integration

```python
from google.adk.tools import OpenApiToolset

# From URL
api_tools = OpenApiToolset(
    spec_url="https://api.example.com/openapi.json",
)

# From local file
api_tools = OpenApiToolset(
    spec_path="./openapi.yaml",
)

agent = Agent(
    name="api_assistant",
    model="gemini-2.5-flash",
    instruction="Use the API tools to help users.",
    tools=[api_tools],
)
```

### Filtering Tools

Select specific operations:

```python
api_tools = OpenApiToolset(
    spec_url="https://api.example.com/openapi.json",
    tool_filter=["get_user", "create_order", "update_order"],
)
```

### OpenAPI with Authentication

See authentication.md for detailed patterns. Quick example:

```python
from google.adk.tools import AuthenticatedFunctionTool
from google.adk.tools.authentication import ApiKeyCredentialExchanger

# For individual authenticated endpoints
auth_tool = AuthenticatedFunctionTool(
    function=api_call_function,
    credential_exchanger=ApiKeyCredentialExchanger(
        api_key="your_api_key",
        header_name="X-API-Key",
    ),
)
```

## MCP Tools

Model Context Protocol tools for standardized integrations.

### Filesystem MCP Server

```python
from google.adk.tools import McpToolset
from mcp import StdioServerParameters

filesystem_tools = McpToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    ),
    tool_filter=["read_file", "write_file", "list_directory"],
)

agent = Agent(
    name="filesystem_assistant",
    model="gemini-2.5-flash",
    instruction="Help users manage files using the filesystem tools.",
    tools=[filesystem_tools],
)
```

### MCP with Timeout

```python
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

filesystem_tools = McpToolset(
    connection_params=StdioConnectionParams(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        timeout=30,  # 30 second timeout
    ),
)
```

### SSE MCP Server

For HTTP-based MCP servers:

```python
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

mcp_tools = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:3000/sse",
    ),
)
```

### Starting MCP Servers

**Filesystem server:**
```bash
npx -y @modelcontextprotocol/server-filesystem /path/to/directory
```

**Custom MCP server with SSE:**
```bash
uvx --from 'git+https://github.com/modelcontextprotocol/python-sdk.git#subdirectory=examples/servers/simple-tool' \
    mcp-simple-tool --transport sse --port 3000
```

## Google Cloud Tools

Integration with Google Cloud services.

### BigQuery Tools

```python
from google.adk.tools import BigQueryToolset

bq_tools = BigQueryToolset(
    project_id="your-project-id",
)

agent = Agent(
    name="data_analyst",
    model="gemini-2.5-flash",
    instruction="Help users query and analyze data using BigQuery.",
    tools=[bq_tools],
)
```

### Cloud Storage Tools

```python
from google.adk.tools import CloudStorageToolset

gcs_tools = CloudStorageToolset(
    project_id="your-project-id",
)

agent = Agent(
    name="storage_assistant",
    model="gemini-2.5-flash",
    tools=[gcs_tools],
)
```

## Built-in Tools

Pre-configured tools provided by ADK.

### Google Search

```python
from google.adk.tools import google_search

agent = Agent(
    name="search_assistant",
    model="gemini-2.5-flash",
    instruction="Answer questions using Google Search when needed.",
    tools=[google_search],
)
```

### Code Execution

```python
from google.adk.tools import code_execution

agent = Agent(
    name="code_assistant",
    model="gemini-2.5-flash",
    instruction="Help users with code execution and analysis.",
    tools=[code_execution],
)
```

## Tool Design Best Practices

### Single Responsibility

Each tool should do one thing well:

```python
# Good - focused tools
def get_user(user_id: str) -> dict:
    """Get user by ID."""
    pass

def create_user(name: str, email: str) -> dict:
    """Create a new user."""
    pass

# Bad - tool does too much
def manage_user(action: str, user_id: str = None, name: str = None) -> dict:
    """Manage users (get, create, update, delete)."""
    pass
```

### Clear Documentation

```python
def process_order(
    order_id: str,
    action: str,
    payment_method_id: str = None
) -> dict:
    """Process an order action.

    Args:
        order_id: The order ID (format: W0000000).
        action: Action to perform (cancel, modify, return).
        payment_method_id: Payment method ID for refunds (format: credit_card_0000000).
            Required for return action.

    Returns:
        Dictionary with:
            - status: Action status (success, failed)
            - message: Human-readable message
            - order: Updated order details

    Raises:
        ValueError: If order_id format is invalid.
        PermissionError: If action not allowed for order status.
    """
    pass
```

### Error Handling

Handle errors gracefully within tools:

```python
def fetch_user_data(user_id: str) -> dict:
    """Fetch user data from API.

    Args:
        user_id: The user ID.

    Returns:
        User data dictionary or error information.
    """
    try:
        response = requests.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"User {user_id} not found"}
        elif e.response.status_code == 403:
            return {"error": "Permission denied"}
        else:
            return {"error": f"API error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}
```

### Structured Returns

Return structured data that's easy to parse:

```python
from typing import TypedDict

class SearchResult(TypedDict):
    id: int
    title: str
    score: float

def search_products(query: str, limit: int = 10) -> list[SearchResult]:
    """Search products.

    Args:
        query: Search query.
        limit: Maximum results.

    Returns:
        List of search results with id, title, and relevance score.
    """
    # Implementation
    return [
        {"id": 1, "title": "Product 1", "score": 0.95},
        {"id": 2, "title": "Product 2", "score": 0.87},
    ]
```

### Validation

Validate inputs before processing:

```python
def create_order(
    user_id: str,
    items: list[dict],
    payment_method_id: str
) -> dict:
    """Create a new order.

    Args:
        user_id: User ID.
        items: List of items with product_id and quantity.
        payment_method_id: Payment method ID.

    Returns:
        Created order details or error.
    """
    # Validate inputs
    if not user_id or not user_id.startswith("user_"):
        return {"error": "Invalid user_id format"}

    if not items or len(items) == 0:
        return {"error": "Order must contain at least one item"}

    for item in items:
        if "product_id" not in item or "quantity" not in item:
            return {"error": "Each item must have product_id and quantity"}
        if item["quantity"] <= 0:
            return {"error": "Quantity must be positive"}

    # Process order
    # ...
```

## Tool Combinations

### Multiple Tool Types

Combine different tool types:

```python
from google.adk.tools import OpenApiToolset, McpToolset, google_search

# Custom function tools
def calculate_total(items: list[dict]) -> float:
    """Calculate order total."""
    return sum(item["price"] * item["quantity"] for item in items)

# OpenAPI tools
api_tools = OpenApiToolset(spec_url="https://api.example.com/openapi.json")

# MCP tools
fs_tools = McpToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    ),
)

# Combine all tools
agent = Agent(
    name="multi_tool_assistant",
    model="gemini-2.5-flash",
    instruction="Use all available tools to help users.",
    tools=[
        calculate_total,
        api_tools,
        fs_tools,
        google_search,
    ],
)
```

### Tool Dependencies

When one tool depends on another:

```python
def get_user_details(user_id: str) -> dict:
    """Get user details including payment methods."""
    return {
        "user_id": user_id,
        "name": "John Doe",
        "payment_methods": [
            {"id": "credit_card_0000001", "type": "credit_card"},
            {"id": "paypal_0000001", "type": "paypal"},
        ],
    }

def process_payment(user_id: str, payment_method_id: str, amount: float) -> dict:
    """Process payment.

    Note: Use get_user_details first to get valid payment_method_id.
    """
    # Validate payment method exists for user
    user = get_user_details(user_id)
    valid_methods = [pm["id"] for pm in user["payment_methods"]]

    if payment_method_id not in valid_methods:
        return {
            "error": f"Invalid payment_method_id. Valid methods: {valid_methods}"
        }

    # Process payment
    return {"status": "success", "transaction_id": "txn_123"}
```

## Performance Considerations

### Caching

Cache expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_product_info(product_id: str) -> dict:
    """Get product information (cached)."""
    # Expensive API call
    return fetch_from_api(product_id)
```

### Async for I/O

Use async for I/O-bound operations:

```python
import asyncio
import httpx

async def fetch_multiple_users(user_ids: list[str]) -> list[dict]:
    """Fetch multiple users concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://api.example.com/users/{uid}")
            for uid in user_ids
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

### Timeouts

Set timeouts for external calls:

```python
import httpx

def fetch_with_timeout(url: str, timeout: int = 10) -> dict:
    """Fetch data with timeout."""
    try:
        response = httpx.get(url, timeout=timeout)
        return response.json()
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
```

## Troubleshooting

### Tool Not Being Called

**Issue:** Agent doesn't use the tool

**Solutions:**
- Check docstring is complete and clear
- Verify type hints are present
- Make instruction explicit about when to use tool
- Test with verbose mode: `runner.run_debug("query", verbose=True)`

### Tool Errors

**Issue:** Tool execution fails

**Solutions:**
- Add error handling within tool
- Use `on_tool_error_callback` for recovery
- Log tool inputs and outputs
- Validate inputs before processing

### Authentication Failures

**Issue:** Authenticated tools fail

**Solutions:**
- Verify credentials are correct
- Check token expiration
- Ensure proper scopes/permissions
- See authentication.md for detailed troubleshooting
