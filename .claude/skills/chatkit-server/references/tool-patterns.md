# Custom Tool Development Guide

Comprehensive guide for implementing custom tools in ChatKit applications.

---

## Tool Development Workflow

```
1. Define Tool Schema → 2. Implement Function → 3. Register with Agent → 4. Test → 5. Handle Errors
```

---

## Tool Schema Definition

### Basic Tool Schema

```python
tool_schema = {
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "Clear description of what the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of parameter"
                },
                "param2": {
                    "type": "integer",
                    "description": "Another parameter",
                    "enum": [1, 2, 3]  # Optional: restrict values
                }
            },
            "required": ["param1"]  # Required parameters
        }
    }
}
```

### Parameter Types

| Type | JSON Schema | Python Type | Example |
|------|-------------|-------------|---------|
| String | `"type": "string"` | `str` | `"hello"` |
| Integer | `"type": "integer"` | `int` | `42` |
| Number | `"type": "number"` | `float` | `3.14` |
| Boolean | `"type": "boolean"` | `bool` | `true` |
| Array | `"type": "array"` | `list` | `[1, 2, 3]` |
| Object | `"type": "object"` | `dict` | `{"key": "value"}` |

### Advanced Schema Features

```python
advanced_tool = {
    "type": "function",
    "function": {
        "name": "search_products",
        "description": "Search product catalog with filters",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "category": {
                    "type": "string",
                    "enum": ["electronics", "clothing", "books"],
                    "description": "Product category"
                },
                "price_range": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "number"},
                        "max": {"type": "number"}
                    },
                    "description": "Price range filter"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                }
            },
            "required": ["query"]
        }
    }
}
```

---

## Tool Implementation Patterns

### Pattern 1: Simple Data Retrieval

```python
def get_user_info(user_id: str) -> dict:
    """Retrieve user information from database."""
    try:
        # Query database
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"error": "User not found", "user_id": user_id}

        return {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "status": user.status
        }
    except Exception as e:
        return {"error": str(e)}
```

### Pattern 2: External API Call

```python
import requests
from typing import Optional

def fetch_weather(city: str, units: str = "metric") -> dict:
    """Fetch weather data from external API."""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        url = f"https://api.weather.com/v1/current"

        response = requests.get(
            url,
            params={"city": city, "units": units, "apikey": api_key},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        return {
            "city": city,
            "temperature": data["temp"],
            "condition": data["weather"],
            "humidity": data["humidity"]
        }
    except requests.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

### Pattern 3: Data Modification

```python
def update_order_status(order_id: str, new_status: str) -> dict:
    """Update order status in database."""
    try:
        # Validate status
        valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        if new_status not in valid_statuses:
            return {"error": f"Invalid status. Must be one of: {valid_statuses}"}

        # Update database
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Order not found", "order_id": order_id}

        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.commit()

        # Log change
        log_status_change(order_id, old_status, new_status)

        return {
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": order.updated_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
```

### Pattern 4: Complex Workflow

```python
def process_refund(order_id: str, amount: float, reason: str) -> dict:
    """Process customer refund with multiple steps."""
    try:
        # Step 1: Validate order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Order not found"}

        if order.status not in ["delivered", "cancelled"]:
            return {"error": "Order not eligible for refund"}

        # Step 2: Validate amount
        if amount > order.total:
            return {"error": "Refund amount exceeds order total"}

        # Step 3: Process payment refund
        payment_result = payment_gateway.refund(
            transaction_id=order.transaction_id,
            amount=amount
        )

        if not payment_result.success:
            return {"error": f"Payment refund failed: {payment_result.error}"}

        # Step 4: Update order
        order.refund_amount = amount
        order.refund_reason = reason
        order.status = "refunded"
        db.commit()

        # Step 5: Send notification
        send_refund_notification(order.customer_email, amount)

        return {
            "success": True,
            "order_id": order_id,
            "refund_amount": amount,
            "refund_id": payment_result.refund_id,
            "status": "completed"
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Refund processing failed: {str(e)}"}
```

### Pattern 5: Async Operations

```python
import asyncio

async def send_bulk_notifications(user_ids: list, message: str) -> dict:
    """Send notifications to multiple users asynchronously."""
    try:
        async def send_single(user_id: str):
            try:
                await notification_service.send(user_id, message)
                return {"user_id": user_id, "status": "sent"}
            except Exception as e:
                return {"user_id": user_id, "status": "failed", "error": str(e)}

        # Send all notifications concurrently
        results = await asyncio.gather(*[send_single(uid) for uid in user_ids])

        sent = sum(1 for r in results if r["status"] == "sent")
        failed = len(results) - sent

        return {
            "total": len(user_ids),
            "sent": sent,
            "failed": failed,
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}
```

---

## Tool Registration

### Basic Registration

```python
from openai import OpenAI
import json

client = OpenAI()

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get user information by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    }
]

# Tool function mapping
TOOL_FUNCTIONS = {
    "get_user_info": get_user_info
}

# Use in chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    # ... create thread and add message ...

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=tools
    )

    # Handle tool execution
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

            # Submit outputs
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    # ... return response ...
```

### Modular Tool Organization

```python
# app/tools/__init__.py
from .user_tools import get_user_info, update_user_profile
from .order_tools import get_order_status, update_order
from .notification_tools import send_email, send_sms

# Export all tools
ALL_TOOLS = [
    # User tools
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get user information",
            "parameters": {...}
        }
    },
    # Order tools
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get order status",
            "parameters": {...}
        }
    },
    # ... more tools
]

TOOL_FUNCTIONS = {
    "get_user_info": get_user_info,
    "update_user_profile": update_user_profile,
    "get_order_status": get_order_status,
    "update_order": update_order,
    "send_email": send_email,
    "send_sms": send_sms
}
```

---

## Error Handling Best Practices

### 1. Always Return Structured Errors

```python
def safe_tool_execution(tool_name: str, **kwargs) -> dict:
    """Wrapper for safe tool execution."""
    try:
        result = TOOL_FUNCTIONS[tool_name](**kwargs)
        return {"success": True, "data": result}
    except KeyError:
        return {"success": False, "error": f"Tool '{tool_name}' not found"}
    except TypeError as e:
        return {"success": False, "error": f"Invalid parameters: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Execution failed: {str(e)}"}
```

### 2. Validate Inputs

```python
def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email_tool(to: str, subject: str, body: str) -> dict:
    """Send email with validation."""
    # Validate inputs
    if not validate_email(to):
        return {"error": "Invalid email address"}

    if not subject or len(subject) > 200:
        return {"error": "Subject must be 1-200 characters"}

    if not body or len(body) > 10000:
        return {"error": "Body must be 1-10000 characters"}

    # Send email
    try:
        email_service.send(to, subject, body)
        return {"success": True, "message_id": "msg_123"}
    except Exception as e:
        return {"error": str(e)}
```

### 3. Implement Timeouts

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    """Context manager for timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError("Operation timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def long_running_tool(param: str) -> dict:
    """Tool with timeout protection."""
    try:
        with timeout(30):  # 30 second timeout
            result = expensive_operation(param)
            return {"success": True, "result": result}
    except TimeoutError:
        return {"error": "Operation timed out after 30 seconds"}
    except Exception as e:
        return {"error": str(e)}
```

---

## Testing Tools

### Unit Tests

```python
import pytest
from app.tools.user_tools import get_user_info

def test_get_user_info_success():
    """Test successful user retrieval."""
    result = get_user_info("user_123")
    assert result["user_id"] == "user_123"
    assert "name" in result
    assert "email" in result

def test_get_user_info_not_found():
    """Test user not found."""
    result = get_user_info("nonexistent")
    assert "error" in result
    assert result["error"] == "User not found"

def test_get_user_info_invalid_input():
    """Test invalid input handling."""
    result = get_user_info("")
    assert "error" in result
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_tool_execution_in_chat():
    """Test tool execution through chat endpoint."""
    response = client.post(
        "/chat",
        json={
            "message": "Get info for user user_123",
            "thread_id": None
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "user_123" in data["response"]
```

---

## Performance Optimization

### 1. Caching

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_product_info(product_id: str) -> dict:
    """Get product info with caching."""
    # Expensive database query
    return db.query(Product).filter(Product.id == product_id).first()

# Cache with TTL
cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cached_data(key: str) -> dict:
    """Get data with TTL cache."""
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return data

    # Fetch fresh data
    data = fetch_from_database(key)
    cache[key] = (data, time.time())
    return data
```

### 2. Batch Operations

```python
def get_multiple_users(user_ids: list) -> dict:
    """Get multiple users in single query."""
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return {
        "users": [
            {"id": u.id, "name": u.name, "email": u.email}
            for u in users
        ]
    }
```

### 3. Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Configure connection pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)
```

---

## Security Best Practices

### 1. Input Sanitization

```python
import html
import re

def sanitize_input(text: str) -> str:
    """Sanitize user input."""
    # Remove HTML tags
    text = html.escape(text)
    # Remove SQL injection attempts
    text = re.sub(r'[;\'"\\]', '', text)
    return text.strip()

def safe_search_tool(query: str) -> dict:
    """Search with sanitized input."""
    clean_query = sanitize_input(query)
    results = search_database(clean_query)
    return {"results": results}
```

### 2. Rate Limiting

```python
from collections import defaultdict
import time

rate_limits = defaultdict(list)
MAX_CALLS_PER_MINUTE = 10

def rate_limited_tool(user_id: str, **kwargs) -> dict:
    """Tool with rate limiting."""
    now = time.time()

    # Clean old entries
    rate_limits[user_id] = [
        t for t in rate_limits[user_id]
        if now - t < 60
    ]

    # Check limit
    if len(rate_limits[user_id]) >= MAX_CALLS_PER_MINUTE:
        return {"error": "Rate limit exceeded. Try again later."}

    # Record call
    rate_limits[user_id].append(now)

    # Execute tool
    return execute_tool(**kwargs)
```

### 3. Permission Checks

```python
def check_permission(user_id: str, action: str) -> bool:
    """Check if user has permission."""
    user = get_user(user_id)
    return action in user.permissions

def protected_tool(user_id: str, action: str, **kwargs) -> dict:
    """Tool with permission check."""
    if not check_permission(user_id, action):
        return {"error": "Permission denied"}

    return execute_action(action, **kwargs)
```

---

## Tool Development Checklist

- [ ] Clear, descriptive tool name
- [ ] Comprehensive description for AI understanding
- [ ] Well-defined parameter schema with types
- [ ] Input validation implemented
- [ ] Error handling with structured responses
- [ ] Timeout protection for long operations
- [ ] Security measures (sanitization, rate limiting, permissions)
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Performance optimized (caching, batching)
- [ ] Logging added for debugging
- [ ] Documentation updated
