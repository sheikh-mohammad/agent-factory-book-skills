# Core Concepts

Fundamental concepts for building agents with Google ADK.

## Agent

The core building block - an AI agent powered by Gemini models.

### Basic Agent Structure

```python
from google.adk import Agent

agent = Agent(
    name="assistant",                    # Unique identifier
    model="gemini-2.5-flash",           # Gemini model to use
    instruction="You are a helpful assistant.",  # System prompt
    description="A simple assistant",    # Agent description
    tools=[],                           # Tools available to agent
)
```

### Agent Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Unique agent identifier |
| `model` | str | Yes | Gemini model name (e.g., `gemini-2.5-flash`) |
| `instruction` | str | Yes | System prompt defining agent behavior |
| `description` | str | No | Human-readable description |
| `tools` | list | No | List of tools (functions, OpenAPI, MCP) |
| `sub_agents` | list | No | Child agents for multi-agent systems |
| `generate_content_config` | Config | No | Model parameters (temperature, etc.) |
| `before_model_callback` | callable | No | Pre-model execution hook |
| `after_model_callback` | callable | No | Post-model execution hook |
| `on_model_error_callback` | callable | No | Model error handler |
| `before_tool_callback` | callable | No | Pre-tool execution hook |
| `after_tool_callback` | callable | No | Post-tool execution hook |
| `on_tool_error_callback` | callable | No | Tool error handler |

### Agent Types

**LlmAgent** - Standard agent powered by Gemini:
```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
)
```

**BaseAgent** - Abstract base for custom agent implementations:
```python
from google.adk.agents import BaseAgent

class CustomAgent(BaseAgent):
    async def run(self, context):
        # Custom agent logic
        pass
```

## Runner

Manages agent execution, sessions, and service integration.

### InMemoryRunner (Development)

Lightweight runner for testing and development:

```python
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(
    agent=agent,
    app_name="my_app",
)

# Synchronous execution
for event in runner.run(
    user_id="user123",
    session_id="session456",
    new_message=types.UserContent(parts=[types.Part(text="Hello!")]),
):
    if event.content:
        print(event.content)

# Async execution
async for event in runner.run_async(
    user_id="user123",
    session_id="session456",
    new_message=types.UserContent(parts=[types.Part(text="Hello!")]),
):
    if event.is_final_response():
        print(event.content)

# Debug mode
await runner.run_debug("Hello!", verbose=True)
```

### Runner (Production)

Full-featured runner with managed services:

```python
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService

runner = Runner(
    app_name="production_app",
    agent=agent,
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
)
```

### Runner Methods

| Method | Use Case | Returns |
|--------|----------|---------|
| `run()` | Synchronous execution | Iterator of events |
| `run_async()` | Async execution | Async iterator of events |
| `run_debug()` | Quick testing with minimal boilerplate | List of events |

## Tools

Functions that agents can call to perform actions.

### Function Tools

Python functions wrapped as tools:

```python
def get_weather(city: str) -> str:
    """Get weather for a city.

    Args:
        city: The city name.

    Returns:
        Weather information.
    """
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(
    name="weather_assistant",
    model="gemini-2.5-flash",
    tools=[get_weather],
)
```

**Requirements:**
- Docstring with description
- Type hints for parameters
- Clear return type

### Tool Context

Access session state and services within tools:

```python
from google.adk.tools import ToolContext

def stateful_tool(param: str, tool_context: ToolContext) -> str:
    """Tool with access to session state."""
    # Access state
    value = tool_context.state.get("key", "default")

    # Modify state
    tool_context.state["key"] = "new_value"

    # Search memory
    results = await tool_context.search_memory("query")

    return f"Processed {param}"
```

## Sessions

Maintain conversation context across interactions.

### Session Structure

```python
from google.adk.sessions import Session

session = Session(
    app_name="my_app",
    user_id="user123",
    session_id="session456",
    state={"preference": "brief"},  # Session-specific state
    history=[],                      # Conversation history
)
```

### Session Services

**InMemorySessionService** - For development:
```python
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
```

**VertexAiSessionService** - For production:
```python
from google.adk.sessions import VertexAiSessionService

session_service = VertexAiSessionService(
    project_id="your-project",
    location="us-central1",
)
```

**PostgreSQL Session Service** - For self-hosted:
```python
from google.adk.sessions import PostgresSessionService

session_service = PostgresSessionService(
    connection_url="postgresql+asyncpg://user:pass@host:5432/db",
)
```

### Session Operations

```python
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

# List sessions
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

## Memory

Long-term storage for information across sessions.

### Memory Services

**InMemoryMemoryService** - For development:
```python
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()
```

**VertexAiRagMemoryService** - For production:
```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    project_id="your-project",
    location="us-central1",
)
```

### Memory Operations

```python
# Search memory
async def recall_information(query: str, tool_context: ToolContext) -> str:
    """Search memory for relevant information."""
    results = await tool_context.search_memory(query)

    if not results.memories:
        return "No relevant memories found."

    memories = [f"- {m.content}" for m in results.memories]
    return "Found memories:\n" + "\n".join(memories)
```

## Events

Events represent the flow of agent execution.

### Event Types

| Event Type | Description |
|------------|-------------|
| `agent_response` | Agent's text response |
| `tool_code_execution` | Tool being called |
| `tool_code_output` | Tool execution result |
| `error` | Error occurred |
| `final_response` | Last event in sequence |

### Processing Events

```python
async for event in runner.run_async(...):
    if event.is_final_response():
        # Process final response
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
```

## Configuration

### Generate Content Config

Control model behavior:

```python
from google.genai import types

config = types.GenerateContentConfig(
    temperature=0.7,        # Randomness (0.0-1.0)
    top_p=0.95,            # Nucleus sampling
    top_k=40,              # Top-k sampling
    max_output_tokens=8192, # Max response length
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
    ],
)

agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    generate_content_config=config,
)
```

### Run Config

Control execution behavior:

```python
from google.adk.agents.run_config import RunConfig

run_config = RunConfig(
    support_cfc=False,  # Disable certain features
)

await runner.run_debug("Query", run_config=run_config)
```

## Callbacks

Hooks for customizing agent and tool behavior.

### Callback Types

| Callback | When | Use Case |
|----------|------|----------|
| `before_model_callback` | Before model call | Rate limiting, request modification |
| `after_model_callback` | After model call | Logging, response modification |
| `on_model_error_callback` | Model error | Error recovery, fallback responses |
| `before_tool_callback` | Before tool call | Argument validation, logging |
| `after_tool_callback` | After tool call | Result logging, modification |
| `on_tool_error_callback` | Tool error | Error handling, retry logic |

### Callback Example

```python
from google.adk.agents import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

async def log_requests(
    ctx: CallbackContext,
    request: LlmRequest,
) -> Optional[LlmResponse]:
    """Log all model requests."""
    logger.info(f"Model request: {request}")
    return None  # Continue with normal execution

agent = Agent(
    name="monitored_assistant",
    model="gemini-2.5-flash",
    before_model_callback=[log_requests],
)
```

## Best Practices

### Agent Design
- Write clear, specific instructions
- Define agent's role and capabilities
- Specify when to use tools vs. direct responses
- Include examples in instructions for complex behaviors

### Tool Design
- One tool = one clear purpose
- Comprehensive docstrings
- Type hints for all parameters
- Handle errors gracefully within tools
- Return structured, parseable results

### Session Management
- Use consistent user_id and session_id
- Store minimal state (avoid large objects)
- Clean up old sessions periodically
- Use managed services in production

### Memory Usage
- Store facts, not conversations
- Use semantic search for retrieval
- Implement memory pruning strategies
- Consider privacy implications

### Performance
- Use `gemini-2.5-flash` for speed
- Use `gemini-2.5-pro` for complex reasoning
- Implement caching for repeated queries
- Use async execution for concurrency
