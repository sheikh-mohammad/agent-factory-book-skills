# Error Handling

Robust error handling patterns for production agent systems.

## Error Handler Types

The SDK provides error handlers for specific failure scenarios.

### Max Turns Error

Prevent infinite loops by limiting agent iterations:

```python
from agents import Agent, Runner, RunErrorHandlerInput, RunErrorHandlerResult

def on_max_turns(_data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I couldn't complete this task within the turn limit. Please simplify your request or break it into smaller steps.",
        include_in_history=False,
    )

result = await Runner.run(
    agent,
    "Complex multi-step query",
    max_turns=10,
    error_handlers={"max_turns": on_max_turns},
)
```

**Parameters**:
- `final_output`: Message returned to user
- `include_in_history`: Whether to add to conversation history

### Tool Failure Errors

Handle tool execution failures gracefully:

```python
from agents import function_tool, RunContextWrapper

def tool_error_handler(ctx: RunContextWrapper, error: Exception) -> str:
    """Provide user-friendly error message to LLM."""
    if isinstance(error, ConnectionError):
        return "The external service is temporarily unavailable. Please try again later."
    elif isinstance(error, ValueError):
        return f"Invalid input: {str(error)}"
    elif isinstance(error, TimeoutError):
        return "The operation timed out. Please try with a smaller request."
    else:
        return f"An unexpected error occurred: {type(error).__name__}"

@function_tool(failure_error_function=tool_error_handler)
def call_external_api(endpoint: str) -> str:
    """Call external API with error handling."""
    # Implementation that might fail
    pass
```

**Key points**:
- Error handler receives context and exception
- Returns string message sent to LLM (not user directly)
- LLM decides how to communicate error to user

## Common Error Patterns

### API Rate Limiting

```python
import time
from functools import wraps

def with_retry(max_retries=3, backoff=1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff * (2 ** attempt)
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    return decorator

@function_tool
@with_retry(max_retries=3)
async def call_rate_limited_api(query: str) -> str:
    """Call API with automatic retry on rate limits."""
    # API call implementation
    pass
```

### Network Failures

```python
import httpx

@function_tool
async def fetch_data(url: str) -> str:
    """Fetch data with network error handling."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        raise TimeoutError("Request timed out")
    except httpx.HTTPStatusError as e:
        raise ConnectionError(f"HTTP {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise ConnectionError(f"Network error: {str(e)}")
```

### Database Errors

```python
import asyncpg

@function_tool
async def query_database(sql: str) -> str:
    """Query database with error handling."""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=5.0)
        rows = await conn.fetch(sql)
        return str(rows)
    except asyncpg.PostgresError as e:
        raise ValueError(f"Database error: {e.message}")
    except asyncio.TimeoutError:
        raise TimeoutError("Database connection timed out")
    finally:
        if conn:
            await conn.close()
```

### File System Errors

```python
import aiofiles
from pathlib import Path

@function_tool
async def read_file(path: str) -> str:
    """Read file with error handling."""
    file_path = Path(path)

    # Validate path
    if not file_path.exists():
        raise ValueError(f"File not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {path}")

    # Check size
    if file_path.stat().st_size > 10_000_000:  # 10MB limit
        raise ValueError("File too large (max 10MB)")

    try:
        async with aiofiles.open(file_path, 'r') as f:
            return await f.read()
    except PermissionError:
        raise ValueError(f"Permission denied: {path}")
    except UnicodeDecodeError:
        raise ValueError(f"Cannot read file (not text): {path}")
```

## Validation Patterns

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class SearchParams(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

@function_tool
def search_database(params: SearchParams) -> str:
    """Search with validated parameters."""
    # Implementation
    pass
```

### Output Validation

```python
@function_tool
async def fetch_user_data(user_id: str) -> str:
    """Fetch user data with output validation."""
    data = await api_call(user_id)

    # Validate response
    if not data:
        raise ValueError("No data returned")

    if 'id' not in data:
        raise ValueError("Invalid response format")

    # Sanitize sensitive data
    data.pop('password', None)
    data.pop('ssn', None)

    return json.dumps(data)
```

## Logging and Monitoring

### Structured Logging

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@function_tool
async def monitored_operation(param: str) -> str:
    """Operation with structured logging."""
    start_time = datetime.now()

    try:
        logger.info(json.dumps({
            "event": "tool_start",
            "tool": "monitored_operation",
            "param": param,
            "timestamp": start_time.isoformat(),
        }))

        result = await perform_operation(param)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(json.dumps({
            "event": "tool_success",
            "tool": "monitored_operation",
            "duration": duration,
        }))

        return result

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(json.dumps({
            "event": "tool_error",
            "tool": "monitored_operation",
            "error": str(e),
            "error_type": type(e).__name__,
            "duration": duration,
        }))
        raise
```

### Error Tracking

```python
import sentry_sdk

def track_error_handler(ctx: RunContextWrapper, error: Exception) -> str:
    """Error handler with tracking."""
    # Send to error tracking service
    sentry_sdk.capture_exception(error)

    # Log context
    logger.error(f"Tool error in {ctx.agent.name}: {error}")

    # Return user-friendly message
    return "An error occurred. Our team has been notified."

@function_tool(failure_error_function=track_error_handler)
def tracked_operation(param: str) -> str:
    """Operation with error tracking."""
    pass
```

## Graceful Degradation

### Fallback Tools

```python
@function_tool
async def primary_search(query: str) -> str:
    """Primary search with fallback."""
    try:
        return await search_primary_api(query)
    except Exception as e:
        logger.warning(f"Primary search failed: {e}")
        try:
            return await search_backup_api(query)
        except Exception as e2:
            logger.error(f"Backup search failed: {e2}")
            return "Search temporarily unavailable. Please try again later."
```

### Partial Results

```python
@function_tool
async def batch_operation(items: list[str]) -> str:
    """Process items with partial success handling."""
    results = []
    errors = []

    for item in items:
        try:
            result = await process_item(item)
            results.append({"item": item, "status": "success", "result": result})
        except Exception as e:
            errors.append({"item": item, "status": "error", "error": str(e)})

    return json.dumps({
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    })
```

## Circuit Breaker Pattern

Prevent cascading failures:

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func):
        if self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func()
            if self.state == "half_open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise

breaker = CircuitBreaker()

@function_tool
async def protected_api_call(endpoint: str) -> str:
    """API call protected by circuit breaker."""
    return breaker.call(lambda: api_call(endpoint))
```

## Testing Error Handling

### Unit Tests

```python
import pytest
from agents import function_tool

@function_tool
def failing_tool(should_fail: bool) -> str:
    if should_fail:
        raise ValueError("Intentional failure")
    return "Success"

def test_tool_error_handling():
    # Test success case
    result = failing_tool(False)
    assert result == "Success"

    # Test error case
    with pytest.raises(ValueError):
        failing_tool(True)
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_agent_error_recovery():
    agent = Agent(
        name="Test Agent",
        instructions="Handle errors gracefully.",
        tools=[failing_tool],
    )

    # Test with error handler
    def error_handler(_data):
        return RunErrorHandlerResult(
            final_output="Error handled",
            include_in_history=False,
        )

    result = await Runner.run(
        agent,
        "Use the failing tool",
        max_turns=3,
        error_handlers={"max_turns": error_handler},
    )

    assert result.final_output is not None
```

## Best Practices

### Error Messages
- Be specific about what went wrong
- Suggest corrective actions
- Don't expose sensitive information
- Log detailed errors, show simple messages to users

### Retries
- Use exponential backoff
- Set maximum retry attempts
- Only retry transient errors
- Log retry attempts

### Timeouts
- Set timeouts for all external calls
- Use appropriate timeout values
- Handle timeout errors gracefully
- Consider operation complexity

### Validation
- Validate inputs before processing
- Validate outputs before returning
- Use type hints and Pydantic models
- Sanitize sensitive data

### Monitoring
- Log all errors with context
- Track error rates and patterns
- Set up alerts for critical errors
- Monitor tool execution times

## Troubleshooting

### Errors not being caught
- Check error handler is registered
- Verify exception types match
- Review error handler return format
- Test error scenarios explicitly

### Too many retries
- Reduce max retry attempts
- Increase backoff time
- Check if errors are transient
- Consider circuit breaker pattern

### Unclear error messages
- Add more context to errors
- Log full error details
- Improve error handler logic
- Test with various error scenarios

### Performance degradation
- Review retry logic
- Check timeout values
- Monitor error rates
- Optimize error handling code
