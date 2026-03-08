# Testing and Debugging

Guide for testing and debugging Google ADK agents.

## Debug Mode

ADK provides `run_debug` for quick testing and experimentation.

### Basic Debug Usage

```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner
import asyncio

agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
)

runner = InMemoryRunner(agent=agent, app_name="test_app")

async def test():
    # Simple debug run
    await runner.run_debug("Hello! What can you do?")

asyncio.run(test())
```

### Verbose Mode

Show detailed tool calls and responses:

```python
# Enable verbose output
await runner.run_debug("What's the weather in London?", verbose=True)

# Output shows:
# - User message
# - Tool calls with arguments
# - Tool results
# - Agent responses
```

### Quiet Mode

Suppress output for programmatic processing:

```python
# Get events without printing
events = await runner.run_debug("Query", quiet=True)

# Process events programmatically
for event in events:
    if event.is_final_response():
        print(f"Final response: {event.content}")
```

### Multiple Queries

Test conversation flow:

```python
await runner.run_debug([
    "Hello!",
    "What's the weather?",
    "Thanks!"
])
```

### Custom Session

Maintain context across debug runs:

```python
# First query
await runner.run_debug(
    "My name is Alice",
    user_id="alice",
    session_id="test_session"
)

# Follow-up query (remembers context)
await runner.run_debug(
    "What's my name?",
    user_id="alice",
    session_id="test_session"
)
```

### Custom Run Config

```python
from google.adk.agents.run_config import RunConfig

config = RunConfig(
    support_cfc=False,  # Disable certain features
)

await runner.run_debug("Query", run_config=config)
```

## Unit Testing

Test individual components.

### Testing Tools

```python
import pytest
from google.adk.tools import ToolContext

def test_add_to_cart():
    """Test add_to_cart tool."""
    # Create mock context
    context = ToolContext(
        state={},
        user_id="test_user",
        session_id="test_session"
    )

    # Call tool
    result = add_to_cart("Widget", 2, context)

    # Assert results
    assert "Added 2x Widget" in result
    assert context.state["cart"] == [{"item": "Widget", "quantity": 2}]

def test_add_to_cart_multiple():
    """Test adding multiple items."""
    context = ToolContext(state={}, user_id="test", session_id="test")

    add_to_cart("Widget", 2, context)
    add_to_cart("Gadget", 1, context)

    cart = context.state["cart"]
    assert len(cart) == 2
    assert cart[0]["item"] == "Widget"
    assert cart[1]["item"] == "Gadget"

def test_add_to_cart_error():
    """Test error handling."""
    context = ToolContext(state={}, user_id="test", session_id="test")

    # Test with invalid quantity
    result = add_to_cart("Widget", -1, context)
    assert "error" in result
```

### Testing Agents

```python
import pytest
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

@pytest.mark.asyncio
async def test_agent_basic_response():
    """Test agent responds to basic query."""
    agent = Agent(
        name="test_agent",
        model="gemini-2.5-flash",
        instruction="You are a test assistant.",
    )

    runner = InMemoryRunner(agent=agent, app_name="test")

    events = await runner.run_debug("Hello", quiet=True)

    # Check we got a response
    assert len(events) > 0
    final_event = [e for e in events if e.is_final_response()][0]
    assert final_event.content is not None

@pytest.mark.asyncio
async def test_agent_with_tool():
    """Test agent uses tool correctly."""
    def get_weather(city: str) -> str:
        """Get weather for city."""
        return f"Weather in {city}: Sunny"

    agent = Agent(
        name="weather_agent",
        model="gemini-2.5-flash",
        instruction="Use get_weather tool to answer weather questions.",
        tools=[get_weather],
    )

    runner = InMemoryRunner(agent=agent, app_name="test")

    events = await runner.run_debug(
        "What's the weather in London?",
        quiet=True,
        verbose=True
    )

    # Check tool was called
    tool_events = [e for e in events if hasattr(e, 'tool_name')]
    assert len(tool_events) > 0
    assert any('get_weather' in str(e) for e in tool_events)
```

### Mocking External Services

```python
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_api_tool_with_mock():
    """Test tool with mocked API."""
    def fetch_user(user_id: str) -> dict:
        """Fetch user from API."""
        response = requests.get(f"https://api.example.com/users/{user_id}")
        return response.json()

    # Mock the requests.get call
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"id": "123", "name": "Alice"}
        mock_get.return_value = mock_response

        result = fetch_user("123")

        assert result["name"] == "Alice"
        mock_get.assert_called_once_with("https://api.example.com/users/123")
```

## Integration Testing

Test complete workflows.

### Testing Multi-Agent Systems

```python
@pytest.mark.asyncio
async def test_agent_team():
    """Test multi-agent coordination."""
    researcher = LlmAgent(
        name="researcher",
        model="gemini-2.5-flash",
        instruction="Research topics.",
        tools=[search_tool],
    )

    writer = LlmAgent(
        name="writer",
        model="gemini-2.5-flash",
        instruction="Write content.",
    )

    coordinator = LlmAgent(
        name="coordinator",
        model="gemini-2.5-flash",
        instruction="Coordinate research and writing.",
        sub_agents=[researcher, writer],
    )

    runner = InMemoryRunner(agent=coordinator, app_name="test")

    events = await runner.run_debug(
        "Research and write about AI agents",
        quiet=True
    )

    # Verify both agents were involved
    # (check events for sub-agent activity)
    assert len(events) > 0
```

### Testing Session Persistence

```python
@pytest.mark.asyncio
async def test_session_persistence():
    """Test session state persists across queries."""
    def remember(key: str, value: str, tool_context: ToolContext) -> str:
        """Remember information."""
        tool_context.state[key] = value
        return f"Remembered {key}"

    def recall(key: str, tool_context: ToolContext) -> str:
        """Recall information."""
        value = tool_context.state.get(key)
        return f"{key}: {value}" if value else f"No memory of {key}"

    agent = Agent(
        name="memory_agent",
        model="gemini-2.5-flash",
        instruction="Remember and recall information.",
        tools=[remember, recall],
    )

    runner = InMemoryRunner(agent=agent, app_name="test")

    # Store information
    await runner.run_debug(
        "Remember that my favorite color is blue",
        user_id="alice",
        session_id="test",
        quiet=True
    )

    # Recall information
    events = await runner.run_debug(
        "What's my favorite color?",
        user_id="alice",
        session_id="test",
        quiet=True
    )

    # Verify recall worked
    # (check events contain "blue")
```

## Debugging Techniques

### Enable Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# ADK-specific logging
adk_logger = logging.getLogger("google.adk")
adk_logger.setLevel(logging.DEBUG)

# Tool logging
tool_logger = logging.getLogger("google.adk.tools")
tool_logger.setLevel(logging.DEBUG)
```

### Inspect Events

```python
async def debug_events():
    """Inspect all events from agent run."""
    events = await runner.run_debug("Query", quiet=True)

    for i, event in enumerate(events):
        print(f"\nEvent {i}:")
        print(f"  Type: {type(event).__name__}")
        print(f"  Content: {event.content if hasattr(event, 'content') else 'N/A'}")
        print(f"  Is final: {event.is_final_response()}")

asyncio.run(debug_events())
```

### Debug State

```python
def debug_state_tool(tool_context: ToolContext) -> str:
    """Debug tool to inspect current state."""
    import json
    state = dict(tool_context.state)
    return f"Current state:\n{json.dumps(state, indent=2)}"

# Add to agent for debugging
agent = Agent(
    name="debug_agent",
    model="gemini-2.5-flash",
    tools=[debug_state_tool, ...],
)
```

### Callback Logging

```python
async def log_all_callbacks(
    ctx: CallbackContext,
    request: LlmRequest,
) -> Optional[LlmResponse]:
    """Log all model requests."""
    logger.debug(f"Model request: {request}")
    return None

async def log_tool_calls(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    """Log all tool calls."""
    logger.debug(f"Tool call: {tool.name}({args})")
    return None

agent = Agent(
    name="logged_agent",
    model="gemini-2.5-flash",
    before_model_callback=[log_all_callbacks],
    before_tool_callback=log_tool_calls,
)
```

## Common Issues

### Issue: Tool Not Being Called

**Symptoms:**
- Agent doesn't use available tool
- Responds without calling tool

**Debug:**
```python
# Enable verbose mode
await runner.run_debug("Query", verbose=True)

# Check:
# 1. Tool docstring is complete
# 2. Tool name is descriptive
# 3. Agent instruction mentions tool
```

**Solutions:**
- Improve tool docstring
- Make instruction more explicit about when to use tool
- Verify tool is in agent's tools list

### Issue: Tool Errors

**Symptoms:**
- Tool execution fails
- Error messages in output

**Debug:**
```python
# Test tool directly
from google.adk.tools import ToolContext

context = ToolContext(state={}, user_id="test", session_id="test")
result = your_tool("test_arg", context)
print(result)
```

**Solutions:**
- Add error handling in tool
- Validate inputs
- Use `on_tool_error_callback`

### Issue: Session State Not Persisting

**Symptoms:**
- State lost between queries
- Agent doesn't remember context

**Debug:**
```python
# Check session IDs match
await runner.run_debug("First", user_id="alice", session_id="test1")
await runner.run_debug("Second", user_id="alice", session_id="test1")  # Same ID

# Inspect state
def check_state(tool_context: ToolContext) -> str:
    return f"State: {dict(tool_context.state)}"
```

**Solutions:**
- Use consistent user_id and session_id
- Verify session service is configured
- Check state is being saved correctly

### Issue: Slow Responses

**Symptoms:**
- Long wait times
- Timeouts

**Debug:**
```python
import time

async def timed_debug():
    start = time.time()
    await runner.run_debug("Query")
    elapsed = time.time() - start
    print(f"Took {elapsed:.2f}s")
```

**Solutions:**
- Use `gemini-2.5-flash` instead of `gemini-2.5-pro`
- Optimize tool execution
- Implement caching
- Use async for I/O operations

### Issue: Output Truncation

**Symptoms:**
- Long tool responses cut off
- Incomplete output

**Debug:**
```python
# Use quiet mode to get full output
events = await runner.run_debug("Query", quiet=True)

# Process events for full content
for event in events:
    if event.content:
        print(event.content)
```

**Solutions:**
- Use `quiet=True` for programmatic access
- Process events instead of relying on printed output
- Implement pagination for large results

## Performance Testing

### Load Testing

```python
import asyncio
import time

async def load_test(num_requests: int = 100):
    """Test agent under load."""
    agent = Agent(
        name="load_test_agent",
        model="gemini-2.5-flash",
        instruction="You are a test assistant.",
    )

    runner = InMemoryRunner(agent=agent, app_name="load_test")

    start = time.time()

    # Run concurrent requests
    tasks = [
        runner.run_debug(f"Query {i}", quiet=True)
        for i in range(num_requests)
    ]

    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start
    rps = num_requests / elapsed

    print(f"Completed {num_requests} requests in {elapsed:.2f}s")
    print(f"Requests per second: {rps:.2f}")

asyncio.run(load_test(100))
```

### Profiling

```python
import cProfile
import pstats

def profile_agent():
    """Profile agent execution."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run agent
    asyncio.run(runner.run_debug("Query", quiet=True))

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

profile_agent()
```

## Best Practices

### Testing

**Do:**
- Write unit tests for tools
- Test error cases
- Mock external services
- Test session persistence
- Use verbose mode for debugging
- Test multi-agent coordination

**Don't:**
- Test against production APIs
- Hardcode test data in production code
- Skip error case testing
- Ignore flaky tests

### Debugging

**Do:**
- Enable logging for troubleshooting
- Use verbose mode to see tool calls
- Inspect events programmatically
- Test tools in isolation
- Use debug tools to inspect state

**Don't:**
- Leave debug logging enabled in production
- Ignore error messages
- Skip reproduction steps
- Debug in production

## Official Documentation

- [ADK Testing Guide](https://github.com/google/adk-docs/blob/main/docs/testing/)
- [Runner Debug Example](https://github.com/google/adk-python/blob/main/contributing/samples/runner_debug_example/README.md)
