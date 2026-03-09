# ChatKit Architecture Patterns

Five proven architectures for different conversational AI use cases.

---

## Pattern Selection Guide

| Use Case | Pattern | Complexity | Setup Time |
|----------|---------|------------|------------|
| Simple Q&A, greetings, FAQs | Simple Agent | Low | 15 min |
| Document search, citations, RAG | Knowledge Assistant | Medium | 30 min |
| API calls, database queries, actions | Tool-Augmented Agent | Medium | 45 min |
| Multiple domains, handoffs, escalation | Multi-Agent System | High | 2 hours |
| Complex workflows with knowledge + tools | Hybrid System | High | 3 hours |

---

## 1. Simple Agent {#simple}

**When to Use**: Single-purpose conversational bot without external data or actions.

**Examples**:
- Greeting bot
- FAQ responder
- Simple information provider
- Conversational interface for static content

**Architecture**:
```
User Input → FastAPI Backend → OpenAI Agent → Response → Frontend
```

**Backend Setup** (`app/main.py`):
```python
from fastapi import FastAPI
from openai import OpenAI

app = FastAPI()
client = OpenAI()

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

**Frontend Setup** (`src/main.js`):
```javascript
async function sendMessage(message) {
    const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message})
    });
    return await response.json();
}
```

**Pros**: Fast setup, minimal dependencies, easy to understand
**Cons**: No external knowledge, no actions, limited capabilities

---

## 2. Knowledge Assistant {#knowledge}

**When to Use**: Document search, knowledge retrieval, citation-backed responses.

**Examples**:
- Policy document assistant
- Technical documentation bot
- Research assistant
- Compliance checker

**Architecture**:
```
User Input → FastAPI Backend → OpenAI Agent + Vector Store → RAG Response → Frontend
```

**Backend Setup** (`app/main.py`):
```python
from fastapi import FastAPI
from openai import OpenAI
import os

app = FastAPI()
client = OpenAI()

VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

@app.post("/chat")
async def chat(message: str, thread_id: str = None):
    # Create or use existing thread
    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id

    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    # Run assistant with vector store
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

    # Get response
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return {
        "response": messages.data[0].content[0].text.value,
        "thread_id": thread_id,
        "citations": extract_citations(messages.data[0])
    }

def extract_citations(message):
    """Extract file citations from message annotations."""
    citations = []
    for annotation in message.content[0].text.annotations:
        if hasattr(annotation, 'file_citation'):
            citations.append({
                "file_id": annotation.file_citation.file_id,
                "quote": annotation.file_citation.quote
            })
    return citations
```

**Vector Store Setup**:
```bash
# 1. Create vector store at platform.openai.com/storage/vector_stores
# 2. Upload documents (PDF, DOCX, TXT, MD)
# 3. Copy vector store ID
# 4. Set environment variable: KNOWLEDGE_VECTOR_STORE_ID=vs_...
```

**Pros**: Grounded responses, citations, handles large knowledge bases
**Cons**: Requires vector store setup, slower responses, costs for embeddings

---

## 3. Tool-Augmented Agent {#tools}

**When to Use**: Agent needs to take actions or query external systems.

**Examples**:
- Customer support (query orders, update tickets)
- Sales assistant (CRM integration, prospect research)
- IT helpdesk (check system status, restart services)
- Booking assistant (check availability, make reservations)

**Architecture**:
```
User Input → FastAPI Backend → OpenAI Agent → Tool Execution → Response → Frontend
                                      ↓
                              Custom Tools (API, DB, Files)
```

**Backend Setup** (`app/main.py`):
```python
from fastapi import FastAPI
from openai import OpenAI
import json

app = FastAPI()
client = OpenAI()

# Define custom tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_order_status",
            "description": "Query the status of a customer order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to query"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_customer_info",
            "description": "Update customer information in the database",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "field": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["customer_id", "field", "value"]
            }
        }
    }
]

# Tool implementations
def query_order_status(order_id: str) -> dict:
    """Query order status from database."""
    # Implementation: query your database
    return {"order_id": order_id, "status": "shipped", "eta": "2026-03-12"}

def update_customer_info(customer_id: str, field: str, value: str) -> dict:
    """Update customer information."""
    # Implementation: update your database
    return {"success": True, "customer_id": customer_id}

# Tool dispatcher
TOOL_FUNCTIONS = {
    "query_order_status": query_order_status,
    "update_customer_info": update_customer_info
}

@app.post("/chat")
async def chat(message: str, thread_id: str = None):
    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=tools
    )

    # Handle tool calls
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

            # Submit tool outputs
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return {
        "response": messages.data[0].content[0].text.value,
        "thread_id": thread_id
    }
```

**Pros**: Can take actions, integrate with existing systems, powerful capabilities
**Cons**: Requires tool implementation, error handling complexity, security considerations

---

## 4. Multi-Agent System {#multi-agent}

**When to Use**: Multiple specialized domains, handoffs, escalation workflows.

**Examples**:
- Enterprise support (L1 → L2 → L3 escalation)
- Sales pipeline (SDR → AE → CSM handoff)
- Healthcare (triage → specialist → billing)
- Multi-department workflows

**Architecture**:
```
User Input → Router Agent → Specialist Agent 1 (Sales)
                         → Specialist Agent 2 (Support)
                         → Specialist Agent 3 (Billing)
                         → Escalation Agent
```

**Backend Setup** (`app/main.py`):
```python
from fastapi import FastAPI
from openai import OpenAI
import os

app = FastAPI()
client = OpenAI()

# Define specialized agents
AGENTS = {
    "router": os.getenv("ROUTER_ASSISTANT_ID"),
    "sales": os.getenv("SALES_ASSISTANT_ID"),
    "support": os.getenv("SUPPORT_ASSISTANT_ID"),
    "billing": os.getenv("BILLING_ASSISTANT_ID")
}

# Handoff tool for routing
handoff_tool = {
    "type": "function",
    "function": {
        "name": "handoff_to_agent",
        "description": "Transfer conversation to specialized agent",
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["sales", "support", "billing"],
                    "description": "Which agent to hand off to"
                },
                "context": {
                    "type": "string",
                    "description": "Summary of conversation so far"
                }
            },
            "required": ["agent", "context"]
        }
    }
}

@app.post("/chat")
async def chat(message: str, thread_id: str = None, current_agent: str = "router"):
    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=AGENTS[current_agent],
        tools=[handoff_tool] if current_agent == "router" else []
    )

    # Handle handoffs
    while run.status in ["queued", "in_progress", "requires_action"]:
        if run.status == "requires_action":
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "handoff_to_agent":
                    args = json.loads(tool_call.function.arguments)
                    return {
                        "handoff": True,
                        "next_agent": args["agent"],
                        "context": args["context"],
                        "thread_id": thread_id
                    }

        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return {
        "response": messages.data[0].content[0].text.value,
        "thread_id": thread_id,
        "current_agent": current_agent
    }
```

**Pros**: Specialized expertise, scalable, clear separation of concerns
**Cons**: Complex setup, requires multiple assistants, handoff logic complexity

---

## 5. Hybrid System {#hybrid}

**When to Use**: Complex workflows requiring knowledge retrieval + tools + multiple agents.

**Examples**:
- Enterprise AI assistant (knowledge base + CRM + multi-department)
- Manufacturing intelligence (equipment data + maintenance tools + specialist routing)
- Healthcare platform (patient records + clinical tools + specialist handoffs)

**Architecture**:
```
User Input → Router Agent → Sales Agent (CRM tools + product knowledge)
                         → Support Agent (ticketing tools + policy docs)
                         → Technical Agent (system tools + technical docs)
```

**Backend Setup**: Combines patterns 2, 3, and 4:
- Each specialized agent has its own vector store
- Each agent has domain-specific tools
- Router handles handoffs between agents

**Implementation**: See `assets/templates/hybrid-system/` for complete example.

**Pros**: Maximum flexibility, handles complex enterprise scenarios
**Cons**: High complexity, longer setup time, requires careful architecture planning

---

## Pattern Migration Path

Start simple, scale as needed:

```
Simple Agent → Add Knowledge (Pattern 2) → Add Tools (Pattern 3) → Add Agents (Pattern 4) → Hybrid (Pattern 5)
```

Most projects should start with Pattern 1 or 2, then evolve based on requirements.
