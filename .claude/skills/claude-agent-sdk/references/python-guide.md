# Python Implementation Guide

Complete guide to implementing Claude Agent SDK in Python.

## Installation

```bash
pip install claude-agent-sdk
```

## Basic Setup

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

# Set API key
import os
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'

async def main():
    async for message in query(
        prompt="What files are in this directory?",
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

## Message Types

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(prompt="Task"):
        if message.type == "text":
            print(f"Claude says: {message.text}")

        elif message.type == "tool_use":
            print(f"Calling {message.name} with {message.input}")

        elif message.type == "result":
            if message.subtype == "success":
                print(f"Result: {message.result}")
            else:
                print(f"Error: {message.subtype}")

asyncio.run(main())
```

## Configuration Options

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    # Model selection
    model="claude-sonnet-4-6",  # or "opus", "haiku"
    effort="medium",  # "low", "medium", "high", "max"

    # Tools
    allowed_tools=["Read", "Edit", "Grep"],
    disallowed_tools=["Bash"],

    # Permissions
    permission_mode="acceptEdits",  # "default", "acceptEdits", "bypassPermissions", "plan"

    # Limits
    max_turns=50,
    max_budget_usd=1.0,

    # Context
    cwd="/path/to/project",
    system_prompt="You are a security expert",

    # Session
    continue_session=True,
    resume="session-id",
    fork_session=False
)

async def main():
    async for message in query(prompt="Task", options=options):
        # Process messages
        pass

asyncio.run(main())
```

## Creating Custom MCP Tools

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions
from pydantic import BaseModel, Field
import httpx

# Define tool schema with Pydantic
class WeatherArgs(BaseModel):
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")

# Define tool handler
async def get_weather(args: WeatherArgs):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": args.latitude,
                    "longitude": args.longitude,
                    "current": "temperature_2m"
                }
            )
            data = response.json()

            return {
                "content": [{
                    "type": "text",
                    "text": f"Temperature: {data['current']['temperature_2m']}°F"
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
    description="Get current temperature for a location",
    parameters=WeatherArgs,
    handler=get_weather
)

# Create MCP server
weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[weather_tool]
)

# Use in agent (requires streaming input)
async def generate_messages():
    yield {"role": "user", "content": "What is the weather in San Francisco?"}

async def main():
    async for message in query(
        prompt=generate_messages(),
        options=ClaudeAgentOptions(
            mcp_servers={"weather": weather_server},
            allowed_tools=["mcp__weather__get_weather"]
        )
    ):
        if message.type == "result":
            print(message.result)

asyncio.run(main())
```

## Session Management

### Continue Most Recent Session

```python
async def main():
    # First query
    async for message in query(prompt="Analyze the auth module"):
        pass

    # Continue from most recent
    async for message in query(
        prompt="Now refactor it",
        options=ClaudeAgentOptions(continue_session=True)
    ):
        pass

asyncio.run(main())
```

### Resume Specific Session

```python
async def main():
    session_id = None

    # First query - capture session ID
    async for message in query(prompt="Analyze code"):
        if message.type == "result":
            session_id = message.session_id

    # Resume later
    async for message in query(
        prompt="Continue analysis",
        options=ClaudeAgentOptions(resume=session_id)
    ):
        pass

asyncio.run(main())
```

### ClaudeSDKClient for Automatic Continuation

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    async with ClaudeSDKClient(ClaudeAgentOptions()) as client:
        # First task
        await client.query("Analyze the auth module")
        async for message in client.receive_response():
            if message.type == "text":
                print(message.text)

        # Automatically continues same session
        await client.query("Now refactor it")
        async for message in client.receive_response():
            if message.type == "text":
                print(message.text)

asyncio.run(main())
```

## Multi-Agent Orchestration

```python
async def main():
    async for message in query(
        prompt="Review this codebase",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Agent"],
            agents={
                "security-reviewer": {
                    "description": "Security expert for vulnerability analysis",
                    "prompt": "Analyze code for security vulnerabilities",
                    "tools": ["Read", "Grep"],
                    "model": "opus",
                    "system_prompt": "You are a security expert"
                },
                "performance-reviewer": {
                    "description": "Performance optimization expert",
                    "prompt": "Identify performance bottlenecks",
                    "tools": ["Read", "Bash"],
                    "model": "sonnet"
                }
            }
        )
    ):
        if message.type == "result":
            print(message.result)

asyncio.run(main())
```

## Hooks

### can_use_tool Hook

```python
async def can_use_tool_hook(tool_name: str, tool_input: dict):
    # Block dangerous commands
    if tool_name == "Bash" and "rm -rf" in tool_input.get("command", ""):
        return {"behavior": "block", "message": "Dangerous command blocked"}

    # Log file writes
    if tool_name == "Write":
        print(f"Writing to {tool_input.get('file_path')}")

    return {"behavior": "allow"}

async def main():
    async for message in query(
        prompt="Task",
        options=ClaudeAgentOptions(can_use_tool=can_use_tool_hook)
    ):
        pass

asyncio.run(main())
```

### before_tool_use / after_tool_use Hooks

```python
async def before_tool_use(tool_name: str, tool_input: dict):
    print(f"Calling {tool_name}")

async def after_tool_use(tool_name: str, tool_input: dict, result):
    print(f"{tool_name} completed")

async def main():
    async for message in query(
        prompt="Task",
        options=ClaudeAgentOptions(
            before_tool_use=before_tool_use,
            after_tool_use=after_tool_use
        )
    ):
        pass

asyncio.run(main())
```

## Error Handling

```python
async def main():
    async for message in query(prompt="Task"):
        if message.type == "result":
            if message.subtype == "success":
                print(f"Success: {message.result}")
            elif message.subtype == "error_max_turns":
                print("Hit turn limit")
            elif message.subtype == "error_max_budget_usd":
                print("Hit budget limit")
            elif message.subtype == "error_during_execution":
                print("Execution error")
            else:
                print(f"Unknown error: {message.subtype}")

asyncio.run(main())
```

## FastAPI Server Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from claude_agent_sdk import query, ClaudeAgentOptions

app = FastAPI()

class AgentRequest(BaseModel):
    prompt: str

@app.post("/agent")
async def run_agent(request: AgentRequest):
    result = []

    try:
        async for message in query(
            prompt=request.prompt,
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "WebSearch"],
                max_budget_usd=0.5
            )
        ):
            if message.type == "text":
                result.append(message.text)
            elif message.type == "result":
                if message.subtype == "success":
                    return {
                        "result": "\n".join(result),
                        "cost": message.total_cost_usd
                    }
                else:
                    raise HTTPException(status_code=500, detail=message.subtype)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

```python
import pytest
from claude_agent_sdk import query, ClaudeAgentOptions

@pytest.mark.asyncio
async def test_agent_completes_task():
    messages = []

    async for message in query(
        prompt="List files in current directory",
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"])
    ):
        messages.append(message)

    result = next(m for m in messages if m.type == "result")
    assert result.subtype == "success"

@pytest.mark.asyncio
async def test_respects_budget_limits():
    async for message in query(
        prompt="Complex task",
        options=ClaudeAgentOptions(max_budget_usd=0.01)
    ):
        if message.type == "result":
            assert message.subtype == "error_max_budget_usd"
```

## Type Hints

```python
from typing import AsyncIterator, Union
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    TextMessage,
    ToolUseMessage,
    ResultMessage
)

# Message types
Message = Union[TextMessage, ToolUseMessage, ResultMessage]

# Result subtypes
ResultSubtype = Union[
    "success",
    "error_max_turns",
    "error_max_budget_usd",
    "error_during_execution",
    "error_max_structured_output_retries"
]

# Permission behaviors
PermissionBehavior = Union["allow", "block", "prompt"]

# Permission modes
PermissionMode = Union["default", "acceptEdits", "bypassPermissions", "plan"]
```

## Best Practices

1. **Always use asyncio**: All SDK functions are async
2. **Set budget limits**: `max_budget_usd=1.0`
3. **Use type hints**: Import types for better IDE support
4. **Handle all result subtypes**: Check `message.subtype` before reading `message.result`
5. **Use streaming input for MCP**: Async generator required
6. **Capture session IDs**: Store `message.session_id` for resumption
7. **Use ClaudeSDKClient**: For automatic session continuation
8. **Return errors as dict in tools**: Don't raise in tool handlers

## Official Documentation

For the latest Python patterns and API reference:
- **Agent SDK API Reference**: https://platform.claude.com/docs/en/agent-sdk/api-reference
- **Python Examples**: https://platform.claude.com/docs/en/agent-sdk/overview

For patterns not covered here, use fetch-library-docs to get the latest official documentation.
