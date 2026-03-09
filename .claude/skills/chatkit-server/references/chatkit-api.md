# ChatKit API Reference

Core API patterns extracted from OpenAI ChatKit official documentation.

---

## Environment Setup

### Required Environment Variables

```bash
# Backend
export OPENAI_API_KEY="sk-proj-your-key-here"
export KNOWLEDGE_VECTOR_STORE_ID="vs_abc123..."  # Optional: for knowledge assistants

# Frontend
export VITE_CHATKIT_API_DOMAIN_KEY="your-domain-key"
export VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY="your-domain-key"  # Per-example keys
export VITE_KNOWLEDGE_CHATKIT_API_DOMAIN_KEY="your-domain-key"
```

### Package Manager

ChatKit uses `uv` for Python dependency management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt
```

---

## Project Structure

Standard ChatKit project layout:

```
project-name/
├── app/
│   ├── main.py           # FastAPI backend entry point
│   ├── tools/            # Custom tool implementations
│   └── config.py         # Configuration
├── src/
│   ├── main.js           # Vite frontend entry point
│   ├── components/       # UI components
│   └── api/              # API client
├── package.json          # npm scripts
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (gitignored)
```

---

## Backend API Patterns

### Basic FastAPI Setup

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5170"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
async def root():
    return {"status": "ChatKit backend running"}
```

### Chat Endpoint (Simple)

```python
@app.post("/chat")
async def chat(message: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )
    return {"response": response.choices[0].message.content}
```

### Chat Endpoint (Threaded)

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

@app.post("/chat")
async def chat(request: ChatRequest):
    # Create or reuse thread
    if not request.thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
    else:
        thread_id = request.thread_id

    # Add user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=request.message
    )

    # Run assistant
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID")
    )

    # Get response
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    latest_message = messages.data[0]

    return {
        "response": latest_message.content[0].text.value,
        "thread_id": thread_id
    }
```

### Streaming Responses

```python
from fastapi.responses import StreamingResponse
import json

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message}
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Frontend API Patterns

### Basic Fetch

```javascript
async function sendMessage(message) {
    const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    });

    const data = await response.json();
    return data.response;
}
```

### Streaming with EventSource

```javascript
function streamMessage(message, onChunk, onComplete) {
    const eventSource = new EventSource(
        `http://localhost:8000/chat/stream?message=${encodeURIComponent(message)}`
    );

    eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
            eventSource.close();
            onComplete();
            return;
        }

        const data = JSON.parse(event.data);
        onChunk(data.content);
    };

    eventSource.onerror = (error) => {
        console.error('Stream error:', error);
        eventSource.close();
    };
}
```

### Thread Management

```javascript
class ChatSession {
    constructor() {
        this.threadId = null;
    }

    async sendMessage(message) {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                thread_id: this.threadId
            })
        });

        const data = await response.json();
        this.threadId = data.thread_id;  // Store for next message
        return data.response;
    }

    reset() {
        this.threadId = null;  // Start new conversation
    }
}
```

---

## Running Services

### Development Mode

```bash
# Start both backend and frontend
npm start

# This runs:
# - Backend: uvicorn app.main:app --reload --port 8000
# - Frontend: vite dev server on http://localhost:5170
```

### Separate Services

```bash
# Terminal 1 - Backend
npm run backend
# Runs: uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
npm run frontend
# Runs: vite dev server
```

### Custom Ports

Edit `package.json`:

```json
{
  "scripts": {
    "backend": "uvicorn app.main:app --reload --port 8001",
    "frontend": "vite --port 5171"
  }
}
```

---

## Port Assignments (Official Examples)

| Example | Backend Port | Frontend Port |
|---------|--------------|---------------|
| Basic | 8000 | 5170 |
| Customer Support | 8001 | 5171 |
| Knowledge Assistant | 8002 | 5172 |
| Marketing Assets | 8003 | 5173 |

---

## Vector Store Integration

### Creating Vector Store

```bash
# 1. Go to https://platform.openai.com/storage/vector_stores
# 2. Click "Create vector store"
# 3. Upload documents (PDF, DOCX, TXT, MD)
# 4. Copy the vector store ID (vs_...)
```

### Using Vector Store in Backend

```python
import os

VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
    else:
        thread_id = request.thread_id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=request.message
    )

    # Run with file search tool
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [VECTOR_STORE_ID]
            }
        }
    )

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return {
        "response": messages.data[0].content[0].text.value,
        "thread_id": thread_id
    }
```

---

## Tool Integration

### Defining Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]
```

### Implementing Tool Functions

```python
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get weather data from external API."""
    # Implementation: call weather API
    return {
        "location": location,
        "temperature": 22,
        "unit": unit,
        "condition": "sunny"
    }

TOOL_FUNCTIONS = {
    "get_weather": get_weather
}
```

### Handling Tool Calls

```python
import json

@app.post("/chat")
async def chat(request: ChatRequest):
    # ... create thread and add message ...

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=tools
    )

    # Poll until complete or requires action
    while run.status in ["queued", "in_progress", "requires_action"]:
        if run.status == "requires_action":
            tool_outputs = []

            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Execute tool
                result = TOOL_FUNCTIONS[function_name](**function_args)

                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })

            # Submit tool outputs back to assistant
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        # Refresh run status
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return {
        "response": messages.data[0].content[0].text.value,
        "thread_id": thread_id
    }
```

---

## Error Handling

### Backend Error Handling

```python
from fastapi import HTTPException

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # ... chat logic ...
        return {"response": response, "thread_id": thread_id}

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Error Handling

```javascript
async function sendMessage(message) {
    try {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response;

    } catch (error) {
        console.error('Chat error:', error);
        return "Sorry, I encountered an error. Please try again.";
    }
}
```

---

## Official Examples Reference

### Customer Support Example

```bash
export OPENAI_API_KEY="sk-proj-your-key"
export VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY="your-domain-key"

cd examples/customer-support
npm start

# Try: "Move me to seat 14C on flight OA476"
```

**Features**: Itinerary management, seat changes, flight queries

### Knowledge Assistant Example

```bash
export OPENAI_API_KEY="sk-proj-your-key"
export KNOWLEDGE_VECTOR_STORE_ID="vs_abc123..."
export VITE_KNOWLEDGE_CHATKIT_API_DOMAIN_KEY="your-domain-key"

cd examples/knowledge-assistant
npm start

# Try: "Summarise the September 2025 policy decision with citations"
```

**Features**: Document search, citations, RAG

### Marketing Assets Example

```bash
export OPENAI_API_KEY="sk-proj-your-key"
export VITE_CHATKIT_API_DOMAIN_KEY="your-domain-key"

cd examples/marketing-assets
npm start

# Try: "Draft headline and image prompt for a productivity app launch"
```

**Features**: Creative workflows, AI image generation prompts

---

## Best Practices

1. **Always use environment variables** for API keys (never hardcode)
2. **Enable CORS** for local development
3. **Use threads** for conversation continuity
4. **Implement error handling** at both backend and frontend
5. **Use streaming** for better UX on long responses
6. **Validate tool inputs** before execution
7. **Log errors** for debugging
8. **Test with official examples** before customizing
