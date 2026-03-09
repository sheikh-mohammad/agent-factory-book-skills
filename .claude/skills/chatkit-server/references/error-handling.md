# Error Handling Patterns

Comprehensive error handling strategies for ChatKit applications.

---

## Error Handling Principles

1. **Fail Gracefully**: Never crash, always return meaningful responses
2. **Log Everything**: Capture errors for debugging
3. **User-Friendly Messages**: Don't expose internal errors to users
4. **Retry Logic**: Handle transient failures automatically
5. **Circuit Breakers**: Prevent cascading failures

---

## OpenAI API Error Handling

### Common API Errors

| Error Type | Status Code | Cause | Solution |
|------------|-------------|-------|----------|
| `AuthenticationError` | 401 | Invalid API key | Check OPENAI_API_KEY |
| `RateLimitError` | 429 | Too many requests | Implement backoff |
| `APIConnectionError` | N/A | Network issues | Retry with timeout |
| `APIError` | 500+ | OpenAI service issues | Retry with backoff |
| `InvalidRequestError` | 400 | Bad request parameters | Validate inputs |

### Retry with Exponential Backoff

```python
import time
from openai import OpenAI, RateLimitError, APIConnectionError, APIError

def call_openai_with_retry(func, max_retries=3, base_delay=1):
    """Call OpenAI API with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Rate limit hit, retrying in {delay}s...")
            time.sleep(delay)
        except (APIConnectionError, APIError) as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"API error, retrying in {delay}s...")
            time.sleep(delay)
        except Exception as e:
            # Don't retry on other errors
            raise

# Usage
def create_completion():
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )

response = call_openai_with_retry(create_completion)
```

### Comprehensive Error Handler

```python
from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIError,
    InvalidRequestError
)
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def safe_openai_call(func, *args, **kwargs):
    """Safely call OpenAI API with comprehensive error handling."""
    try:
        return await func(*args, **kwargs)

    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Service configuration error. Please contact support."
        )

    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail="Service is busy. Please try again in a moment."
        )

    except InvalidRequestError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request. Please check your input."
        )

    except APIConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again."
        )

    except APIError as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Service error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred."
        )
```

---

## FastAPI Error Handling

### Global Exception Handler

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

### Custom Error Responses

```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    error_code: str
    details: dict | None = None
    request_id: str | None = None

@app.post("/chat")
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())

    try:
        response = await process_chat(request)
        return response

    except ValueError as e:
        return ErrorResponse(
            error=str(e),
            error_code="INVALID_INPUT",
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"Request {request_id} failed: {str(e)}")
        return ErrorResponse(
            error="An error occurred processing your request",
            error_code="PROCESSING_ERROR",
            request_id=request_id
        )
```

---

## Tool Execution Error Handling

### Safe Tool Execution

```python
import json
from typing import Callable, Dict, Any

def execute_tool_safely(
    tool_name: str,
    tool_func: Callable,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute tool with comprehensive error handling."""
    try:
        # Validate arguments
        if not isinstance(args, dict):
            return {
                "success": False,
                "error": "Invalid arguments format",
                "error_code": "INVALID_ARGS"
            }

        # Execute tool
        result = tool_func(**args)

        # Validate result
        if result is None:
            return {
                "success": False,
                "error": "Tool returned no result",
                "error_code": "NO_RESULT"
            }

        return {
            "success": True,
            "data": result
        }

    except TypeError as e:
        logger.error(f"Tool {tool_name} type error: {str(e)}")
        return {
            "success": False,
            "error": f"Invalid parameters for {tool_name}",
            "error_code": "TYPE_ERROR"
        }

    except ValueError as e:
        logger.error(f"Tool {tool_name} value error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "VALUE_ERROR"
        }

    except Exception as e:
        logger.error(f"Tool {tool_name} execution failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Tool execution failed: {tool_name}",
            "error_code": "EXECUTION_ERROR"
        }

# Usage in tool handler
for tool_call in run.required_action.submit_tool_outputs.tool_calls:
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    result = execute_tool_safely(
        function_name,
        TOOL_FUNCTIONS[function_name],
        function_args
    )

    tool_outputs.append({
        "tool_call_id": tool_call.id,
        "output": json.dumps(result)
    })
```

### Tool Timeout Protection

```python
import signal
from contextlib import contextmanager

class TimeoutError(Exception):
    pass

@contextmanager
def timeout(seconds: int):
    """Context manager for timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Cancel alarm
        signal.alarm(0)

def execute_tool_with_timeout(tool_func: Callable, args: dict, timeout_seconds: int = 30):
    """Execute tool with timeout protection."""
    try:
        with timeout(timeout_seconds):
            return tool_func(**args)
    except TimeoutError as e:
        logger.error(f"Tool execution timed out: {str(e)}")
        return {
            "success": False,
            "error": "Operation timed out",
            "error_code": "TIMEOUT"
        }
```

---

## Database Error Handling

### Transaction Management

```python
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

def safe_database_operation(func):
    """Decorator for safe database operations."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.commit()
            return {"success": True, "data": result}

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error: {str(e)}")
            return {
                "success": False,
                "error": "Data constraint violation",
                "error_code": "INTEGRITY_ERROR"
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            return {
                "success": False,
                "error": "Database operation failed",
                "error_code": "DB_ERROR"
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "Operation failed",
                "error_code": "UNKNOWN_ERROR"
            }

    return wrapper

@safe_database_operation
def update_user_record(user_id: str, data: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    for key, value in data.items():
        setattr(user, key, value)

    return user
```

---

## Circuit Breaker Pattern

### Prevent Cascading Failures

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker opened due to failures")

    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True

        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)

# Usage
openai_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def call_openai_with_circuit_breaker():
    """Call OpenAI API with circuit breaker."""
    return openai_circuit_breaker.call(
        client.chat.completions.create,
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
```

---

## Graceful Degradation

### Fallback Responses

```python
def chat_with_fallback(message: str) -> dict:
    """Chat with fallback to simpler responses."""
    try:
        # Try primary method (GPT-4)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message}]
        )
        return {"response": response.choices[0].message.content, "source": "gpt-4"}

    except Exception as e:
        logger.warning(f"GPT-4 failed, falling back to GPT-3.5: {str(e)}")

        try:
            # Fallback to GPT-3.5
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            return {"response": response.choices[0].message.content, "source": "gpt-3.5"}

        except Exception as e:
            logger.error(f"All AI models failed: {str(e)}")

            # Final fallback to static response
            return {
                "response": "I'm experiencing technical difficulties. Please try again later.",
                "source": "fallback"
            }
```

---

## Error Monitoring

### Structured Error Logging

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_error(self, error: Exception, context: dict = None):
        """Log error with structured data."""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        self.logger.error(json.dumps(error_data))

# Usage
structured_logger = StructuredLogger(__name__)

try:
    result = process_chat(request)
except Exception as e:
    structured_logger.log_error(e, {
        "user_id": user_id,
        "request_id": request_id,
        "endpoint": "/chat"
    })
```

### Error Metrics

```python
from prometheus_client import Counter, Histogram

# Define metrics
error_counter = Counter(
    'chatkit_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

error_duration = Histogram(
    'chatkit_error_duration_seconds',
    'Time to handle errors'
)

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await process_chat(request)
        return response

    except Exception as e:
        error_counter.labels(
            error_type=type(e).__name__,
            endpoint="/chat"
        ).inc()

        raise
```

---

## Error Handling Checklist

- [ ] OpenAI API errors handled with retry logic
- [ ] Exponential backoff implemented for rate limits
- [ ] Global exception handlers configured
- [ ] Custom error responses defined
- [ ] Tool execution errors caught and logged
- [ ] Timeout protection for long-running operations
- [ ] Database transactions wrapped with error handling
- [ ] Circuit breaker implemented for external services
- [ ] Graceful degradation with fallback responses
- [ ] Structured error logging configured
- [ ] Error metrics tracked
- [ ] User-friendly error messages (no internal details exposed)
- [ ] All errors logged for debugging
- [ ] Error monitoring and alerting set up
