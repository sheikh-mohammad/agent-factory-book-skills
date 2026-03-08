# State and Memory Management

Guide for managing session state and long-term memory in Google ADK agents.

## Overview

ADK provides two types of persistence:

| Type | Scope | Lifetime | Use Case |
|------|-------|----------|----------|
| **Session State** | Single session | Until session ends | Shopping cart, conversation context, temporary data |
| **Long-term Memory** | Cross-session | Persistent | User preferences, learned facts, historical data |

## Session State

Temporary data stored within a conversation session.

### Accessing Session State

Use `ToolContext` to access state within tools:

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
        quantity: Number of items.
        tool_context: Context with state access.

    Returns:
        Confirmation message.
    """
    # Get current cart (or empty list if not exists)
    cart = tool_context.state.get("cart", [])

    # Add item
    cart.append({"item": item_name, "quantity": quantity})

    # Update state
    tool_context.state["cart"] = cart

    total_items = sum(item["quantity"] for item in cart)
    return f"Added {quantity}x {item_name}. Cart has {total_items} items."
```

### Reading Session State

```python
def get_cart_summary(tool_context: ToolContext) -> str:
    """Get shopping cart summary.

    Args:
        tool_context: Context with state access.

    Returns:
        Cart contents or empty message.
    """
    cart = tool_context.state.get("cart", [])

    if not cart:
        return "Your cart is empty."

    items = [f"- {item['item']} x{item['quantity']}" for item in cart]
    total = sum(item["quantity"] for item in cart)

    return f"Cart ({total} items):\n" + "\n".join(items)
```

### Modifying Session State

```python
def clear_cart(tool_context: ToolContext) -> str:
    """Clear shopping cart.

    Args:
        tool_context: Context with state access.

    Returns:
        Confirmation message.
    """
    tool_context.state["cart"] = []
    return "Cart cleared."

def update_preferences(
    preference: str,
    value: str,
    tool_context: ToolContext
) -> str:
    """Update user preferences.

    Args:
        preference: Preference name.
        value: Preference value.
        tool_context: Context with state access.

    Returns:
        Confirmation message.
    """
    prefs = tool_context.state.get("preferences", {})
    prefs[preference] = value
    tool_context.state["preferences"] = prefs

    return f"Updated {preference} to {value}"
```

### State in Callbacks

Access state in agent callbacks:

```python
from google.adk.agents import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

async def inject_user_context(
    ctx: CallbackContext,
    request: LlmRequest,
) -> Optional[LlmResponse]:
    """Inject user preferences into request.

    Args:
        ctx: Callback context with state access.
        request: LLM request to modify.

    Returns:
        None to continue with modified request.
    """
    # Access session state
    prefs = ctx.state.get("user_preferences", {})

    if prefs.get("language"):
        # Modify request based on preferences
        # (implementation depends on use case)
        pass

    return None  # Continue with request

agent = Agent(
    name="context_aware_agent",
    model="gemini-2.5-flash",
    before_model_callback=[inject_user_context],
)
```

## Session Services

Manage session persistence and storage.

### InMemorySessionService (Development)

For local development and testing:

```python
from google.adk.sessions import InMemorySessionService
from google.adk import Runner

session_service = InMemorySessionService()

runner = Runner(
    app_name="dev_app",
    agent=agent,
    session_service=session_service,
)
```

**Characteristics:**
- Fast, no external dependencies
- Data lost on restart
- Not suitable for production
- Good for testing

### VertexAiSessionService (Production)

For production deployments on GCP:

```python
from google.adk.sessions import VertexAiSessionService

session_service = VertexAiSessionService(
    project_id="your-project-id",
    location="us-central1",
)

runner = Runner(
    app_name="production_app",
    agent=agent,
    session_service=session_service,
)
```

**Characteristics:**
- Managed by Google Cloud
- Persistent across restarts
- Auto-scaling
- Built-in backup and recovery

### PostgresSessionService (Self-hosted)

For self-hosted deployments:

```python
from google.adk.sessions import PostgresSessionService

session_service = PostgresSessionService(
    connection_url="postgresql+asyncpg://user:pass@host:5432/db",
)

runner = Runner(
    app_name="self_hosted_app",
    agent=agent,
    session_service=session_service,
)
```

**Setup PostgreSQL:**
```bash
# Install PostgreSQL
# Create database
createdb adk_sessions

# Set connection URL
export POSTGRES_URL="postgresql+asyncpg://user:pass@localhost:5432/adk_sessions"
```

### Session Operations

```python
from google.adk.sessions import Session

# Create session
session = await session_service.create_session(
    app_name="my_app",
    user_id="user123",
    session_id="session456",
    state={"preference": "brief"},
)

# Get session
session = await session_service.get_session(
    app_name="my_app",
    user_id="user123",
    session_id="session456",
)

# List user sessions
sessions = await session_service.list_sessions(
    app_name="my_app",
    user_id="user123",
)

# Delete session
await session_service.delete_session(
    app_name="my_app",
    user_id="user123",
    session_id="session456",
)
```

## Long-term Memory

Persistent storage across sessions.

### Memory Services

**InMemoryMemoryService** - Development:
```python
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()
```

**VertexAiRagMemoryService** - Production:
```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    project_id="your-project-id",
    location="us-central1",
)
```

### Memory-Aware Tools

Create tools that search memory:

```python
async def recall_information(
    query: str,
    tool_context: ToolContext
) -> str:
    """Search memory for relevant information.

    Args:
        query: What to search for.
        tool_context: Context with memory access.

    Returns:
        Relevant memories or not found message.
    """
    results = await tool_context.search_memory(query)

    if not results.memories:
        return "No relevant memories found."

    memories = []
    for memory in results.memories:
        memories.append(f"- {memory.content}")

    return "Found memories:\n" + "\n".join(memories)
```

### Storing Memories

Memories are automatically stored from conversation history:

```python
runner = Runner(
    app_name="memory_app",
    agent=agent,
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
)

# Conversations are automatically stored in memory
await runner.run_async(
    user_id="user123",
    session_id="session1",
    new_message=types.UserContent(
        parts=[types.Part(text="My favorite color is blue")]
    ),
)

# Later, in a different session
await runner.run_async(
    user_id="user123",
    session_id="session2",
    new_message=types.UserContent(
        parts=[types.Part(text="What's my favorite color?")]
    ),
)
# Agent can recall from memory
```

### Memory Configuration

```python
agent = Agent(
    name="memory_assistant",
    model="gemini-2.5-flash",
    instruction="""You are an assistant with long-term memory.
    Use the recall_information tool to find relevant past information.
    Remember important facts about users across conversations.""",
    tools=[recall_information],
)
```

## State Management Patterns

### Pattern: Multi-step Workflow

Track progress through multi-step processes:

```python
def start_order(tool_context: ToolContext) -> str:
    """Start order process."""
    tool_context.state["order_step"] = "items"
    tool_context.state["order_data"] = {"items": [], "total": 0}
    return "Order started. Add items to your order."

def add_item(item: str, price: float, tool_context: ToolContext) -> str:
    """Add item to order."""
    if tool_context.state.get("order_step") != "items":
        return "No active order. Start an order first."

    order_data = tool_context.state["order_data"]
    order_data["items"].append({"item": item, "price": price})
    order_data["total"] += price

    tool_context.state["order_data"] = order_data
    return f"Added {item} (${price}). Total: ${order_data['total']}"

def checkout(tool_context: ToolContext) -> str:
    """Proceed to checkout."""
    if tool_context.state.get("order_step") != "items":
        return "No active order."

    tool_context.state["order_step"] = "payment"
    return "Proceeding to payment. Provide payment method."

def complete_order(payment_method: str, tool_context: ToolContext) -> str:
    """Complete order."""
    if tool_context.state.get("order_step") != "payment":
        return "Not ready for payment."

    order_data = tool_context.state["order_data"]
    # Process payment...

    # Clear state
    tool_context.state["order_step"] = "complete"
    return f"Order complete! Total: ${order_data['total']}"
```

### Pattern: User Preferences

Store and apply user preferences:

```python
def set_preference(key: str, value: str, tool_context: ToolContext) -> str:
    """Set user preference."""
    prefs = tool_context.state.get("preferences", {})
    prefs[key] = value
    tool_context.state["preferences"] = prefs
    return f"Preference {key} set to {value}"

def get_preference(key: str, tool_context: ToolContext) -> str:
    """Get user preference."""
    prefs = tool_context.state.get("preferences", {})
    value = prefs.get(key)

    if value:
        return f"{key}: {value}"
    else:
        return f"No preference set for {key}"

# Use preferences in agent instruction
agent = Agent(
    name="personalized_assistant",
    model="gemini-2.5-flash",
    instruction="""You are a personalized assistant.
    Check user preferences before responding.
    Adapt your responses based on preferences like:
    - response_length (brief, detailed)
    - language (en, es, fr)
    - formality (casual, formal)""",
    tools=[set_preference, get_preference],
)
```

### Pattern: Conversation Context

Maintain conversation context:

```python
def remember_context(key: str, value: str, tool_context: ToolContext) -> str:
    """Remember conversation context."""
    context = tool_context.state.get("conversation_context", {})
    context[key] = value
    tool_context.state["conversation_context"] = context
    return f"Remembered: {key} = {value}"

def recall_context(key: str, tool_context: ToolContext) -> str:
    """Recall conversation context."""
    context = tool_context.state.get("conversation_context", {})
    value = context.get(key)

    if value:
        return f"Recalled: {key} = {value}"
    else:
        return f"No context for {key}"
```

## Best Practices

### Session State

**Do:**
- Store temporary, session-specific data
- Keep state size small (avoid large objects)
- Use clear, descriptive keys
- Clean up state when no longer needed
- Validate state before using

**Don't:**
- Store sensitive data without encryption
- Store large files or binary data
- Use state for cross-session data (use memory instead)
- Assume state persists forever (sessions can expire)

### Long-term Memory

**Do:**
- Store facts, not conversations
- Use semantic search for retrieval
- Implement memory pruning strategies
- Consider privacy implications
- Document what's stored in memory

**Don't:**
- Store PII without user consent
- Store everything (be selective)
- Assume perfect recall (memory search is semantic)
- Ignore data retention policies

### State Size

Keep state manageable:

```python
# Good - minimal state
tool_context.state["cart_item_count"] = 5

# Bad - large state
tool_context.state["all_products"] = [...]  # Thousands of items
```

### State Validation

Validate state before use:

```python
def process_cart(tool_context: ToolContext) -> str:
    """Process cart with validation."""
    cart = tool_context.state.get("cart")

    # Validate state exists
    if not cart:
        return "Cart is empty"

    # Validate state structure
    if not isinstance(cart, list):
        tool_context.state["cart"] = []
        return "Cart was corrupted and has been reset"

    # Validate items
    valid_items = []
    for item in cart:
        if isinstance(item, dict) and "item" in item and "quantity" in item:
            valid_items.append(item)

    tool_context.state["cart"] = valid_items
    return f"Processing {len(valid_items)} items"
```

### Session Cleanup

Clean up old sessions:

```python
import asyncio
from datetime import datetime, timedelta

async def cleanup_old_sessions():
    """Clean up sessions older than 30 days."""
    cutoff = datetime.now() - timedelta(days=30)

    # List all sessions
    all_sessions = await session_service.list_all_sessions()

    for session in all_sessions:
        if session.created_at < cutoff:
            await session_service.delete_session(
                app_name=session.app_name,
                user_id=session.user_id,
                session_id=session.session_id,
            )

# Run periodically
asyncio.create_task(cleanup_old_sessions())
```

## Debugging State Issues

### Inspect State

```python
def debug_state(tool_context: ToolContext) -> str:
    """Debug tool to inspect current state."""
    import json
    state = dict(tool_context.state)
    return f"Current state:\n{json.dumps(state, indent=2)}"
```

### Log State Changes

```python
async def log_state_changes(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    result: dict,
) -> Optional[dict]:
    """Log state changes after tool execution."""
    logger.info(f"State after {tool.name}: {dict(tool_context.state)}")
    return None

agent = Agent(
    name="debug_agent",
    model="gemini-2.5-flash",
    after_tool_callback=log_state_changes,
)
```

## Official Documentation

- [ADK Sessions Documentation](https://github.com/google/adk-docs/blob/main/docs/sessions/)
- [ADK Memory Documentation](https://github.com/google/adk-docs/blob/main/docs/memory/)
