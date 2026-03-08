# Streaming

Stream agent responses in real-time for better user experience.

## Basic Streaming

```python
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

agent = Agent(name="Assistant", instructions="Be helpful.")

# Stream responses
result = Runner.run_streamed(agent, "Tell me a story")
async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

# Access final result after stream completes
print(f"\n\nFinal: {result.final_output}")
```

**Key points**:
- Use `Runner.run_streamed()` instead of `Runner.run()`
- Iterate over `result.stream_events()` to get events
- Filter for `ResponseTextDeltaEvent` to get text tokens
- Final result available after stream completes

## Event Types

### Raw Response Events

Token-by-token text from the LLM:

```python
async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            # Stream text token
            print(event.data.delta, end="", flush=True)
```

**Use for**: Immediate text display to users

### Run Item Events

High-level structured events:

```python
from agents import ItemHelpers

async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        if event.item.type == "tool_call_item":
            print(f"\n[Tool: {event.item.name}]")

        elif event.item.type == "tool_call_output_item":
            print(f"\n[Output: {event.item.output}]")

        elif event.item.type == "message_output_item":
            text = ItemHelpers.text_message_output(event.item)
            print(f"\n[Message: {text}]")
```

**Use for**: Structured logging, UI state updates

### Agent Events

Track agent changes in multi-agent systems:

```python
async for event in result.stream_events():
    if event.type == "agent_updated_stream_event":
        print(f"\n[Switched to: {event.new_agent.name}]")
```

**Use for**: Multi-agent workflow visualization

## Complete Streaming Example

```python
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, ItemHelpers

async def stream_with_events():
    agent = Agent(
        name="Assistant",
        instructions="Be helpful and use tools when needed.",
        tools=[search_tool, calculate_tool],
    )

    result = Runner.run_streamed(agent, "Search for Python and calculate 2+2")

    print("Streaming response:\n")

    async for event in result.stream_events():
        # Text tokens
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

        # Tool calls
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print(f"\n\n🔧 Calling tool: {event.item.name}")

            elif event.item.type == "tool_call_output_item":
                print(f"✓ Tool result: {event.item.output[:100]}...")

        # Agent changes
        elif event.type == "agent_updated_stream_event":
            print(f"\n\n👤 Agent: {event.new_agent.name}")

    print(f"\n\n--- Final Output ---\n{result.final_output}")

if __name__ == "__main__":
    asyncio.run(stream_with_events())
```

## UI Integration Patterns

### Web Application (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

app = FastAPI()

@app.get("/stream")
async def stream_response(query: str):
    agent = Agent(name="Assistant", instructions="Be helpful.")

    async def generate():
        result = Runner.run_streamed(agent, query)
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    yield event.data.delta

    return StreamingResponse(generate(), media_type="text/plain")
```

### WebSocket

```python
from fastapi import WebSocket
import json

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        query = await websocket.receive_text()

        result = Runner.run_streamed(agent, query)
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    await websocket.send_json({
                        "type": "token",
                        "data": event.data.delta
                    })

            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    await websocket.send_json({
                        "type": "tool_call",
                        "tool": event.item.name
                    })

        await websocket.send_json({"type": "done"})
```

### Server-Sent Events (SSE)

```python
from fastapi.responses import StreamingResponse

@app.get("/sse")
async def sse_stream(query: str):
    async def event_generator():
        result = Runner.run_streamed(agent, query)
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    yield f"data: {event.data.delta}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

## CLI Integration

### Simple Progress

```python
import sys

async def stream_to_cli():
    result = Runner.run_streamed(agent, "Tell me a story")

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                sys.stdout.write(event.data.delta)
                sys.stdout.flush()

    print("\n")
```

### Rich Progress Indicators

```python
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

console = Console()

async def stream_with_rich():
    result = Runner.run_streamed(agent, "Explain quantum computing")

    text = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    text += event.data.delta
                    live.update(Markdown(text))
```

## Error Handling

### Stream Errors

```python
async def stream_with_error_handling():
    result = Runner.run_streamed(agent, "query")

    try:
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
    except Exception as e:
        print(f"\n\nStream error: {e}")
        # Fallback to non-streaming
        result = await Runner.run(agent, "query")
        print(result.final_output)
```

### Timeout Handling

```python
import asyncio

async def stream_with_timeout():
    result = Runner.run_streamed(agent, "query")

    try:
        async with asyncio.timeout(30):  # 30 second timeout
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    if isinstance(event.data, ResponseTextDeltaEvent):
                        print(event.data.delta, end="", flush=True)
    except asyncio.TimeoutError:
        print("\n\nStream timed out")
```

## Performance Optimization

### Buffering

Buffer tokens for smoother display:

```python
async def stream_with_buffering():
    result = Runner.run_streamed(agent, "query")

    buffer = []
    buffer_size = 5  # Buffer 5 tokens

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                buffer.append(event.data.delta)

                if len(buffer) >= buffer_size:
                    print("".join(buffer), end="", flush=True)
                    buffer = []

    # Flush remaining buffer
    if buffer:
        print("".join(buffer), end="", flush=True)
```

### Debouncing

Reduce UI update frequency:

```python
import time

async def stream_with_debounce():
    result = Runner.run_streamed(agent, "query")

    text = ""
    last_update = 0
    debounce_ms = 100  # Update every 100ms

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                text += event.data.delta

                now = time.time() * 1000
                if now - last_update > debounce_ms:
                    update_ui(text)
                    last_update = now

    # Final update
    update_ui(text)
```

## Best Practices

### When to Stream
- Long-form content generation
- User-facing chat interfaces
- Real-time feedback needed
- Multi-step operations with tools

### When NOT to Stream
- Batch processing
- Background jobs
- API integrations (unless client supports streaming)
- Short responses (overhead not worth it)

### UI Considerations
- Show typing indicators during streaming
- Display tool calls as they happen
- Handle stream interruptions gracefully
- Provide stop/cancel functionality

### Error Handling
- Always wrap stream iteration in try/except
- Implement timeout mechanisms
- Fallback to non-streaming on errors
- Log stream failures for debugging

### Performance
- Buffer tokens for smoother display
- Debounce UI updates
- Use WebSocket for bidirectional communication
- Consider SSE for one-way streaming

## Testing Streaming

### Unit Testing

```python
import pytest
from agents import Agent, Runner

@pytest.mark.asyncio
async def test_streaming():
    agent = Agent(name="Test", instructions="Be brief.")

    result = Runner.run_streamed(agent, "Say hello")

    tokens = []
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                tokens.append(event.data.delta)

    assert len(tokens) > 0
    assert result.final_output is not None
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_stream_with_tools():
    agent = Agent(
        name="Test",
        instructions="Use tools.",
        tools=[test_tool],
    )

    result = Runner.run_streamed(agent, "Use the tool")

    tool_called = False
    async for event in result.stream_events():
        if event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                tool_called = True

    assert tool_called
```

## Troubleshooting

### No events received
- Check async iteration syntax
- Verify agent is configured correctly
- Test with non-streaming first
- Check network/API connectivity

### Incomplete streams
- Implement timeout handling
- Check for exceptions in stream loop
- Verify final_output after stream
- Log all events for debugging

### Performance issues
- Implement buffering
- Reduce UI update frequency
- Use debouncing
- Check network latency

### UI flickering
- Buffer tokens before display
- Debounce updates
- Use smooth scrolling
- Batch DOM updates
