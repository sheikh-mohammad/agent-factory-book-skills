# API Reference

Complete API reference for OpenAI Agents SDK.

## Agent

### Constructor

```python
Agent(
    name: str,
    instructions: str = "",
    model: str = "gpt-4o",
    model_settings: ModelSettings | None = None,
    tools: list[FunctionTool] = [],
    handoffs: list[Agent | Handoff] = [],
    mcp_servers: list[MCPServer] = [],
    handoff_description: str = "",
)
```

**Parameters**:
- `name` (str, required): Identifier for the agent
- `instructions` (str): System prompt defining agent behavior
- `model` (str): Model to use (default: "gpt-4o")
- `model_settings` (ModelSettings): Model configuration
- `tools` (list): Function tools available to agent
- `handoffs` (list): Other agents this agent can delegate to
- `mcp_servers` (list): MCP servers providing tools
- `handoff_description` (str): Description for handoff routing

### Methods

**clone()**:
```python
agent.clone(
    name: str | None = None,
    instructions: str | None = None,
    model: str | None = None,
    tools: list | None = None,
    handoffs: list | None = None,
) -> Agent
```
Create a copy of the agent with modifications.

## Runner

### run()

```python
await Runner.run(
    agent: Agent,
    input: str,
    max_turns: int = 100,
    error_handlers: dict | None = None,
) -> RunResult
```

**Parameters**:
- `agent` (Agent): The agent to run
- `input` (str): User query or input
- `max_turns` (int): Maximum agent iterations (default: 100)
- `error_handlers` (dict): Error handling callbacks

**Returns**: `RunResult` object

### run_sync()

```python
Runner.run_sync(
    agent: Agent,
    input: str,
    max_turns: int = 100,
    error_handlers: dict | None = None,
) -> RunResult
```

Synchronous version of `run()`. Use for simple scripts.

### run_streamed()

```python
Runner.run_streamed(
    agent: Agent,
    input: str,
    max_turns: int = 100,
    error_handlers: dict | None = None,
) -> StreamedRunResult
```

Returns streaming result for real-time responses.

## RunResult

Result object from agent execution.

**Attributes**:
- `final_output` (str): Final text response
- `last_agent` (Agent): Agent that completed the run
- `history` (list): Full conversation history
- `error` (Exception | None): Error if run failed

## StreamedRunResult

Result object for streaming execution.

**Methods**:

**stream_events()**:
```python
async for event in result.stream_events():
    # Process events
    pass
```

**Attributes**:
- `final_output` (str): Available after stream completes
- `last_agent` (Agent): Agent that completed the run
- `history` (list): Full conversation history

## ModelSettings

Configuration for model behavior.

```python
ModelSettings(
    temperature: float = 0.7,
    top_p: float = 1.0,
    max_tokens: int | None = None,
)
```

**Parameters**:
- `temperature` (float): Randomness (0.0-1.0, default: 0.7)
- `top_p` (float): Nucleus sampling (0.0-1.0, default: 1.0)
- `max_tokens` (int): Maximum response length

## function_tool

Decorator to create function tools.

```python
@function_tool(
    name_override: str | None = None,
    timeout: float | None = None,
    failure_error_function: Callable | None = None,
)
def my_tool(param: str) -> str:
    """Tool description."""
    pass
```

**Parameters**:
- `name_override` (str): Custom tool name
- `timeout` (float): Execution timeout in seconds
- `failure_error_function` (Callable): Custom error handler

**Function signature**:
- First parameter can be `ctx: RunContextWrapper` for context access
- Other parameters define tool inputs
- Return type must be serializable
- Docstring becomes tool description

## handoff

Create custom handoff configuration.

```python
handoff(
    agent: Agent,
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    on_handoff: Callable | None = None,
    input_type: type | None = None,
    input_filter: Callable | None = None,
    is_enabled: bool | Callable = True,
)
```

**Parameters**:
- `agent` (Agent): Target agent for handoff
- `tool_name_override` (str): Custom tool name
- `tool_description_override` (str): Custom description
- `on_handoff` (Callable): Callback when handoff occurs
- `input_type` (type): Structured input type (Pydantic model)
- `input_filter` (Callable): Filter input before handoff
- `is_enabled` (bool | Callable): Enable/disable handoff dynamically

## RunContextWrapper

Context object passed to tools and callbacks.

**Attributes**:
- `agent` (Agent): Current agent
- `history` (list): Conversation history
- Custom data passed via context

## RunErrorHandlerInput

Input to error handler functions.

**Attributes**:
- `agent` (Agent): Agent that encountered error
- `error` (Exception): The error that occurred
- `history` (list): Conversation history

## RunErrorHandlerResult

Return value from error handlers.

```python
RunErrorHandlerResult(
    final_output: str,
    include_in_history: bool = True,
)
```

**Parameters**:
- `final_output` (str): Message to return to user
- `include_in_history` (bool): Add to conversation history

## MCP Servers

### MCPServerStdio

Local subprocess MCP server.

```python
MCPServerStdio(
    name: str,
    params: dict,
)
```

**params dict**:
- `command` (str): Command to execute
- `args` (list[str]): Command arguments

**Usage**:
```python
async with MCPServerStdio(name="Server", params={...}) as server:
    # Use server
    pass
```

### MCPServerStreamableHttp

Remote HTTP MCP server.

```python
MCPServerStreamableHttp(
    name: str,
    params: dict,
    cache_tools_list: bool = False,
)
```

**params dict**:
- `url` (str): Server URL
- `headers` (dict): HTTP headers
- `timeout` (int): Request timeout

**Usage**:
```python
async with MCPServerStreamableHttp(name="Server", params={...}) as server:
    # Use server
    pass
```

### MCPServerManager

Manage multiple MCP servers.

```python
MCPServerManager(
    servers: list[MCPServer],
    strict: bool = False,
    connection_timeout: float = 10.0,
)
```

**Parameters**:
- `servers` (list): List of MCP servers
- `strict` (bool): Fail if any server fails (default: False)
- `connection_timeout` (float): Timeout per server

**Attributes**:
- `active_servers` (list): Successfully connected servers
- `failed_servers` (list): Servers that failed to connect

**Usage**:
```python
async with MCPServerManager(servers) as manager:
    agent = Agent(mcp_servers=manager.active_servers)
```

### HostedMCPTool

OpenAI-hosted MCP server.

```python
HostedMCPTool(
    tool_config: dict,
)
```

**tool_config dict**:
- `type` (str): Always "mcp"
- `server_label` (str): Server identifier
- `server_url` (str): Hosted server URL
- `require_approval` (str): "never", "always", or "auto"

## Event Types

### Stream Events

**raw_response_event**:
- `event.type` = "raw_response_event"
- `event.data` = `ResponseTextDeltaEvent` (token-by-token text)

**run_item_stream_event**:
- `event.type` = "run_item_stream_event"
- `event.item.type` = "tool_call_item" | "tool_call_output_item" | "message_output_item"

**agent_updated_stream_event**:
- `event.type` = "agent_updated_stream_event"
- `event.new_agent` = Agent that was switched to

## ItemHelpers

Utility functions for working with run items.

**text_message_output()**:
```python
ItemHelpers.text_message_output(item) -> str
```
Extract text from message output item.

## Constants

### RECOMMENDED_PROMPT_PREFIX

```python
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
```

Recommended prefix for handoff-aware agent instructions.

## Type Hints

```python
from typing import Annotated
from pydantic import Field

# Parameter with constraints
param: Annotated[int, Field(ge=1, le=100, description="Value between 1 and 100")]

# Complex types
from typing_extensions import TypedDict

class Location(TypedDict):
    lat: float
    long: float
```

## Error Types

Common exceptions:

- `ValueError`: Invalid input or configuration
- `TimeoutError`: Operation timed out
- `ConnectionError`: Network or connection failure
- `RateLimitError`: API rate limit exceeded

## Best Practices

### Type Hints
Always use type hints for function tools:
```python
@function_tool
def my_tool(param: str, count: int = 10) -> str:
    pass
```

### Async/Await
Use async for I/O operations:
```python
@function_tool
async def fetch_data(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### Error Handling
Always handle errors in tools:
```python
@function_tool
def risky_operation(value: int) -> str:
    if value < 0:
        raise ValueError("Value must be positive")
    return str(value * 2)
```

### Context Management
Use `async with` for MCP servers:
```python
async with MCPServerStdio(name="Server", params={...}) as server:
    agent = Agent(mcp_servers=[server])
    result = await Runner.run(agent, "query")
```

## Examples

### Basic Agent
```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful.")
result = await Runner.run(agent, "Hello!")
print(result.final_output)
```

### Agent with Tools
```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"Weather in {city}: sunny"

agent = Agent(name="Assistant", tools=[get_weather])
result = await Runner.run(agent, "What's the weather in Tokyo?")
```

### Multi-Agent System
```python
from agents import Agent, Runner

specialist = Agent(name="Specialist", instructions="Handle specialized tasks")
triage = Agent(name="Triage", handoffs=[specialist])

result = await Runner.run(triage, "Complex query")
print(f"Handled by: {result.last_agent.name}")
```

### Streaming
```python
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

agent = Agent(name="Assistant")
result = Runner.run_streamed(agent, "Tell me a story")

async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
```

### MCP Integration
```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="Filesystem",
    params={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]}
) as server:
    agent = Agent(name="Assistant", mcp_servers=[server])
    result = await Runner.run(agent, "List files")
```

## Version Information

This reference is for OpenAI Agents SDK (Python).

For the latest documentation, visit: https://github.com/openai/openai-agents-python
