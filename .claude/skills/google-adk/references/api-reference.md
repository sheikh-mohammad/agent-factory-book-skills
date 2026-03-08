# API Reference

Complete API reference for Google ADK core classes and methods.

## Agent

Core agent class for creating AI agents.

### Constructor

```python
Agent(
    name: str,
    model: str,
    instruction: str,
    description: str = "",
    tools: list = [],
    sub_agents: list = [],
    generate_content_config: Optional[GenerateContentConfig] = None,
    before_model_callback: Optional[list[Callable]] = None,
    after_model_callback: Optional[list[Callable]] = None,
    on_model_error_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
    on_tool_error_callback: Optional[Callable] = None,
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Unique agent identifier |
| `model` | str | Yes | Gemini model name (e.g., "gemini-2.5-flash") |
| `instruction` | str | Yes | System prompt defining agent behavior |
| `description` | str | No | Human-readable description |
| `tools` | list | No | List of tools (functions, OpenAPI, MCP) |
| `sub_agents` | list | No | Child agents for multi-agent systems |
| `generate_content_config` | GenerateContentConfig | No | Model parameters |
| `before_model_callback` | list[Callable] | No | Pre-model execution hooks |
| `after_model_callback` | list[Callable] | No | Post-model execution hooks |
| `on_model_error_callback` | Callable | No | Model error handler |
| `before_tool_callback` | Callable | No | Pre-tool execution hook |
| `after_tool_callback` | Callable | No | Post-tool execution hook |
| `on_tool_error_callback` | Callable | No | Tool error handler |

**Example:**

```python
from google.adk import Agent

agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
    description="A general-purpose assistant",
    tools=[get_weather, search_database],
)
```

## Runner

Manages agent execution with managed services.

### Constructor

```python
Runner(
    app_name: str,
    agent: Agent,
    session_service: Optional[SessionService] = None,
    memory_service: Optional[MemoryService] = None,
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `app_name` | str | Yes | Application identifier |
| `agent` | Agent | Yes | Agent to run |
| `session_service` | SessionService | No | Session storage service |
| `memory_service` | MemoryService | No | Long-term memory service |

**Example:**

```python
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService

runner = Runner(
    app_name="my_app",
    agent=agent,
    session_service=VertexAiSessionService(
        project_id="your-project",
        location="us-central1",
    ),
)
```

### Methods

#### run_async

```python
async def run_async(
    user_id: str,
    session_id: str,
    new_message: UserContent,
    run_config: Optional[RunConfig] = None,
) -> AsyncIterator[Event]
```

Execute agent asynchronously.

**Parameters:**
- `user_id`: User identifier
- `session_id`: Session identifier
- `new_message`: User message
- `run_config`: Optional run configuration

**Returns:** Async iterator of events

**Example:**

```python
from google.genai import types

async for event in runner.run_async(
    user_id="user123",
    session_id="session456",
    new_message=types.UserContent(
        parts=[types.Part(text="Hello!")]
    ),
):
    if event.is_final_response():
        print(event.content)
```

## InMemoryRunner

Lightweight runner for development and testing.

### Constructor

```python
InMemoryRunner(
    agent: Agent,
    app_name: str,
)
```

**Parameters:**
- `agent`: Agent to run
- `app_name`: Application identifier

**Example:**

```python
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(
    agent=agent,
    app_name="dev_app",
)
```

### Methods

#### run_debug

```python
async def run_debug(
    user_messages: str | list[str],
    user_id: str = "debug_user_id",
    session_id: str = "debug_session_id",
    run_config: Optional[RunConfig] = None,
    quiet: bool = False,
    verbose: bool = False,
) -> List[Event]
```

Simplified agent interaction for debugging.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_messages` | str \| list[str] | Required | Message(s) to process |
| `user_id` | str | "debug_user_id" | User identifier |
| `session_id` | str | "debug_session_id" | Session identifier |
| `run_config` | RunConfig | None | Run configuration |
| `quiet` | bool | False | Suppress console output |
| `verbose` | bool | False | Show detailed tool calls |

**Returns:** List of events

**Example:**

```python
# Simple usage
await runner.run_debug("Hello!")

# Multiple messages
await runner.run_debug(["Hello!", "How are you?"])

# Verbose mode
await runner.run_debug("Query", verbose=True)

# Quiet mode for programmatic processing
events = await runner.run_debug("Query", quiet=True)
```

## ToolContext

Context object passed to tools for accessing state and services.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `state` | dict | Session state dictionary |
| `user_id` | str | Current user ID |
| `session_id` | str | Current session ID |

### Methods

#### search_memory

```python
async def search_memory(query: str) -> MemorySearchResult
```

Search long-term memory.

**Parameters:**
- `query`: Search query

**Returns:** Memory search results

**Example:**

```python
async def recall_info(query: str, tool_context: ToolContext) -> str:
    results = await tool_context.search_memory(query)
    if results.memories:
        return "\n".join(m.content for m in results.memories)
    return "No memories found"
```

## CallbackContext

Context object passed to callbacks.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `state` | dict | Session state dictionary |
| `user_id` | str | Current user ID |
| `session_id` | str | Current session ID |

**Example:**

```python
async def log_callback(
    ctx: CallbackContext,
    request: LlmRequest,
) -> Optional[LlmResponse]:
    logger.info(f"User {ctx.user_id} in session {ctx.session_id}")
    return None
```

## GenerateContentConfig

Configuration for model generation parameters.

### Constructor

```python
from google.genai import types

config = types.GenerateContentConfig(
    temperature: float = 0.7,
    top_p: float = 0.95,
    top_k: int = 40,
    max_output_tokens: int = 8192,
    safety_settings: list[SafetySetting] = [],
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | float | 0.7 | Randomness (0.0-1.0) |
| `top_p` | float | 0.95 | Nucleus sampling |
| `top_k` | int | 40 | Top-k sampling |
| `max_output_tokens` | int | 8192 | Max response length |
| `safety_settings` | list | [] | Safety filters |

**Example:**

```python
from google.genai import types

config = types.GenerateContentConfig(
    temperature=0.9,
    max_output_tokens=4096,
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
    ],
)

agent = Agent(
    name="creative_agent",
    model="gemini-2.5-flash",
    generate_content_config=config,
)
```

## Session Services

### InMemorySessionService

```python
from google.adk.sessions import InMemorySessionService

service = InMemorySessionService()
```

In-memory session storage for development.

### VertexAiSessionService

```python
from google.adk.sessions import VertexAiSessionService

service = VertexAiSessionService(
    project_id: str,
    location: str,
)
```

Managed session storage on Vertex AI.

### PostgresSessionService

```python
from google.adk.sessions import PostgresSessionService

service = PostgresSessionService(
    connection_url: str,
)
```

PostgreSQL session storage for self-hosted deployments.

### Session Methods

All session services implement:

```python
async def create_session(
    app_name: str,
    user_id: str,
    session_id: str,
    state: dict = {},
) -> Session

async def get_session(
    app_name: str,
    user_id: str,
    session_id: str,
) -> Session

async def list_sessions(
    app_name: str,
    user_id: str,
) -> SessionList

async def delete_session(
    app_name: str,
    user_id: str,
    session_id: str,
) -> None
```

## Memory Services

### InMemoryMemoryService

```python
from google.adk.memory import InMemoryMemoryService

service = InMemoryMemoryService()
```

In-memory long-term memory for development.

### VertexAiRagMemoryService

```python
from google.adk.memory import VertexAiRagMemoryService

service = VertexAiRagMemoryService(
    project_id: str,
    location: str,
)
```

Managed RAG-based memory on Vertex AI.

## Tool Types

### Function Tools

Python functions with docstrings and type hints:

```python
def tool_name(param: str, tool_context: ToolContext) -> str:
    """Tool description.

    Args:
        param: Parameter description.
        tool_context: Context with state access.

    Returns:
        Result description.
    """
    return "result"
```

### OpenAPI Tools

```python
from google.adk.tools import OpenApiToolset

tools = OpenApiToolset(
    spec_url: str,
    spec_path: Optional[str] = None,
    tool_filter: Optional[list[str]] = None,
    auth_config: Optional[dict] = None,
)
```

### MCP Tools

```python
from google.adk.tools import McpToolset
from mcp import StdioServerParameters

tools = McpToolset(
    connection_params: StdioServerParameters | SseConnectionParams,
    tool_filter: Optional[list[str]] = None,
)
```

## Authentication

### AuthenticatedFunctionTool

```python
from google.adk.tools import AuthenticatedFunctionTool

tool = AuthenticatedFunctionTool(
    function: Callable,
    credential_exchanger: BaseCredentialExchanger,
)
```

### ApiKeyCredentialExchanger

```python
from google.adk.tools.authentication import ApiKeyCredentialExchanger

exchanger = ApiKeyCredentialExchanger(
    api_key: str,
    header_name: str = "Authorization",
    prefix: str = "",
)
```

### OAuth2CredentialExchanger

```python
from google.adk.tools.authentication import OAuth2CredentialExchanger

exchanger = OAuth2CredentialExchanger(
    client_id: str,
    client_secret: str,
    token_url: str,
    scopes: Optional[list[str]] = None,
)
```

## Events

### Event Types

Events returned from agent execution:

| Event Type | Description | Properties |
|------------|-------------|------------|
| `agent_response` | Agent text response | `content` |
| `tool_code_execution` | Tool being called | `tool_name`, `arguments` |
| `tool_code_output` | Tool result | `tool_name`, `output` |
| `error` | Error occurred | `error` |

### Event Methods

```python
event.is_final_response() -> bool  # Check if final event
event.content -> Content | None     # Get event content
```

## CLI Commands

### adk run

```bash
adk run <agent_file.py>
```

Run agent directly from Python file.

### adk web

```bash
adk web [agent_directory]
```

Launch web UI for agent interaction.

### adk api_server

```bash
adk api_server [agent_directory]
```

Start API server for agents.

### adk deploy

```bash
adk deploy cloud_run \
  --project=<project_id> \
  --region=<region> \
  --service_name=<name> \
  [--with_ui] \
  [--a2a] \
  <agent_directory>
```

Deploy agent to Google Cloud Run.

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI Studio API key | `AIza...` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Vertex AI (1) or AI Studio (0) | `1` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `my-project` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `POSTGRES_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |

## Type Hints

Common type hints used in ADK:

```python
from typing import Optional, Callable, AsyncIterator
from google.adk import Agent
from google.adk.tools import ToolContext
from google.adk.agents import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

# Tool signature
def tool(param: str, tool_context: ToolContext) -> str:
    pass

# Callback signatures
async def before_model(
    ctx: CallbackContext,
    request: LlmRequest,
) -> Optional[LlmResponse]:
    pass

async def after_model(
    ctx: CallbackContext,
    response: LlmResponse,
) -> Optional[LlmResponse]:
    pass

async def on_model_error(
    ctx: CallbackContext,
    request: LlmRequest,
    error: Exception,
) -> Optional[LlmResponse]:
    pass
```

## Official Documentation

- [Google ADK Python Repository](https://github.com/google/adk-python)
- [Google ADK Documentation](https://github.com/google/adk-docs)
- [Context7 ADK Reference](https://context7.com/google/adk-python/llms.txt)
