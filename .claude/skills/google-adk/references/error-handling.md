# Error Handling and Recovery

Comprehensive guide for handling errors and implementing recovery strategies in Google ADK agents.

## Overview

Robust error handling is critical for production agents. ADK provides multiple mechanisms:

| Mechanism | Scope | Use Case |
|-----------|-------|----------|
| **Callbacks** | Agent/Tool lifecycle | Intercept and handle errors |
| **Try-Catch in Tools** | Individual tools | Handle tool-specific errors |
| **Recovery Workflows** | Business logic | Implement retry and fallback strategies |
| **Validation** | Input/Output | Prevent errors before they occur |

## Error Types

### Model Errors

Errors from Gemini API calls:

```python
from google.adk.agents import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
import logging

logger = logging.getLogger(__name__)

async def handle_model_error(
    ctx: CallbackContext,
    request: LlmRequest,
    error: Exception,
) -> Optional[LlmResponse]:
    """Handle model errors gracefully.

    Args:
        ctx: Callback context.
        request: The failed request.
        error: The error that occurred.

    Returns:
        Fallback response or None to propagate error.
    """
    logger.error(f"Model error: {error}")

    # Return fallback response
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text="I encountered an error. Please try again.")]
        )
    )

agent = Agent(
    name="resilient_agent",
    model="gemini-2.5-flash",
    on_model_error_callback=handle_model_error,
)
```

### Tool Errors

Errors during tool execution:

```python
from google.adk.tools import BaseTool, ToolContext

async def handle_tool_error(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    error: Exception,
) -> Optional[dict]:
    """Handle tool errors.

    Args:
        tool: The tool that failed.
        args: Arguments passed to tool.
        tool_context: Tool context.
        error: The error that occurred.

    Returns:
        Error result or None to propagate error.
    """
    logger.error(f"Tool '{tool.name}' error: {error}")

    return {
        "error": str(error),
        "tool": tool.name,
        "message": "Tool execution failed. Please try again."
    }

agent = Agent(
    name="resilient_agent",
    model="gemini-2.5-flash",
    on_tool_error_callback=handle_tool_error,
)
```

## Lifecycle Callbacks

Callbacks for customizing error handling behavior.

### Before Model Callback

Intercept and modify requests, or short-circuit execution:

```python
async def rate_limit_check(
    ctx: CallbackContext,
    request: LlmRequest,
) -> Optional[LlmResponse]:
    """Check rate limits before calling model.

    Args:
        ctx: Callback context with state access.
        request: The LLM request.

    Returns:
        Early response if rate limited, None to continue.
    """
    call_count = ctx.state.get("call_count", 0)

    if call_count >= 100:
        # Return early response without calling model
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Rate limit exceeded. Please try again later.")]
            )
        )

    ctx.state["call_count"] = call_count + 1
    return None  # Continue with model call

agent = Agent(
    name="rate_limited_agent",
    model="gemini-2.5-flash",
    before_model_callback=[rate_limit_check],
)
```

### After Model Callback

Log or modify responses:

```python
async def log_model_response(
    ctx: CallbackContext,
    response: LlmResponse,
) -> Optional[LlmResponse]:
    """Log model responses for analytics.

    Args:
        ctx: Callback context.
        response: The model response.

    Returns:
        Modified response or None to use original.
    """
    if response.content and response.content.parts:
        text = "".join(p.text or "" for p in response.content.parts)
        logger.info(f"Model response length: {len(text)} chars")

    return None  # Use original response

agent = Agent(
    name="logged_agent",
    model="gemini-2.5-flash",
    after_model_callback=[log_model_response],
)
```

### Before Tool Callback

Validate arguments before execution:

```python
async def validate_tool_args(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    """Validate tool arguments before execution.

    Args:
        tool: The tool to execute.
        args: Arguments to validate.
        tool_context: Tool context.

    Returns:
        Override result or None to continue.
    """
    logger.info(f"Calling tool '{tool.name}' with args: {args}")

    # Example: Validate required arguments
    if tool.name == "process_payment" and "amount" in args:
        if args["amount"] <= 0:
            return {
                "error": "Invalid amount",
                "message": "Amount must be positive"
            }

    return None  # Continue with tool execution

agent = Agent(
    name="validated_agent",
    model="gemini-2.5-flash",
    before_tool_callback=validate_tool_args,
)
```

### After Tool Callback

Log or modify tool results:

```python
async def log_tool_result(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    result: dict,
) -> Optional[dict]:
    """Log tool execution results.

    Args:
        tool: The executed tool.
        args: Arguments used.
        tool_context: Tool context.
        result: Tool result.

    Returns:
        Modified result or None to use original.
    """
    logger.info(f"Tool '{tool.name}' returned: {result}")
    return None  # Use original result

agent = Agent(
    name="logged_agent",
    model="gemini-2.5-flash",
    after_tool_callback=log_tool_result,
)
```

## Error Recovery Workflows

Implement business logic for error recovery.

### API Error Recovery

```python
def get_user_details(user_id: str) -> dict:
    """Get user details with error recovery.

    Args:
        user_id: The user ID.

    Returns:
        User details or error information.
    """
    try:
        response = requests.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "error": "user_not_found",
                "message": f"User {user_id} not found",
                "recovery": "Please verify the user ID"
            }
        elif e.response.status_code == 403:
            return {
                "error": "permission_denied",
                "message": "Permission denied",
                "recovery": "Contact administrator for access"
            }
        else:
            return {
                "error": "api_error",
                "message": f"API error: {e}",
                "recovery": "Please try again later"
            }

    except requests.Timeout:
        return {
            "error": "timeout",
            "message": "Request timed out",
            "recovery": "Please try again"
        }

    except Exception as e:
        logger.exception("Unexpected error in get_user_details")
        return {
            "error": "unexpected_error",
            "message": "An unexpected error occurred",
            "recovery": "Please contact support"
        }
```

### Retry with Exponential Backoff

```python
import time
from typing import Callable, TypeVar, Optional

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> Optional[T]:
    """Retry function with exponential backoff.

    Args:
        func: Function to retry.
        max_retries: Maximum number of retries.
        initial_delay: Initial delay in seconds.
        backoff_factor: Backoff multiplier.

    Returns:
        Function result or None if all retries failed.
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} retries failed: {e}")
                return None

            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= backoff_factor

    return None

# Usage in tool
def fetch_data_with_retry(url: str) -> dict:
    """Fetch data with automatic retry."""
    def fetch():
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    result = retry_with_backoff(fetch, max_retries=3)

    if result is None:
        return {"error": "Failed after multiple retries"}

    return result
```

### Fallback Chain

```python
def get_weather_with_fallback(city: str) -> dict:
    """Get weather with fallback providers.

    Args:
        city: City name.

    Returns:
        Weather data from first successful provider.
    """
    providers = [
        ("primary", lambda: fetch_from_primary_api(city)),
        ("secondary", lambda: fetch_from_secondary_api(city)),
        ("cache", lambda: fetch_from_cache(city)),
    ]

    for provider_name, provider_func in providers:
        try:
            logger.info(f"Trying {provider_name} provider")
            result = provider_func()
            logger.info(f"Success with {provider_name} provider")
            return result
        except Exception as e:
            logger.warning(f"{provider_name} provider failed: {e}")
            continue

    return {
        "error": "all_providers_failed",
        "message": "Unable to fetch weather data",
        "recovery": "Please try again later"
    }
```

## Error Recovery Patterns

### Pattern: Detect, Analyze, Recover

```python
def process_order_with_recovery(order_id: str, action: str) -> dict:
    """Process order with error recovery.

    Error Recovery Workflow:
    1. Detect error from API response
    2. Analyze error type and context
    3. Attempt recovery based on error type
    4. If recovery fails, escalate

    Args:
        order_id: The order ID.
        action: Action to perform.

    Returns:
        Result or error with recovery information.
    """
    try:
        # Attempt operation
        result = api.process_order(order_id, action)
        return result

    except PaymentMethodNotFoundError as e:
        # Recovery: Fetch correct payment method
        logger.info("Payment method not found, fetching user details")
        user_details = api.get_user_details(order_id)
        payment_methods = user_details.get("payment_methods", [])

        if payment_methods:
            # Retry with correct payment method
            return api.process_order(
                order_id,
                action,
                payment_method_id=payment_methods[0]["id"]
            )
        else:
            return {
                "error": "no_payment_methods",
                "message": "No payment methods available",
                "recovery": "Please add a payment method"
            }

    except InvalidOrderStatusError as e:
        # Recovery: Check current status and suggest alternative
        order = api.get_order_details(order_id)
        current_status = order["status"]

        return {
            "error": "invalid_status",
            "message": f"Cannot {action} order with status {current_status}",
            "current_status": current_status,
            "recovery": f"Order is {current_status}. Try different action."
        }

    except ModificationLimitExceededError:
        # No recovery possible, inform user
        return {
            "error": "modification_limit",
            "message": "Modification limit exceeded for this order",
            "recovery": "Contact support for assistance"
        }
```

### Pattern: Circuit Breaker

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """Circuit breaker pattern for failing services."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable) -> Optional[any]:
        """Call function through circuit breaker."""
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

            raise e

# Usage
weather_api_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def get_weather_with_breaker(city: str) -> dict:
    """Get weather with circuit breaker."""
    try:
        return weather_api_breaker.call(
            lambda: fetch_weather_api(city)
        )
    except Exception as e:
        logger.error(f"Circuit breaker prevented call or call failed: {e}")
        return {
            "error": "service_unavailable",
            "message": "Weather service temporarily unavailable",
            "recovery": "Using cached data or try again later"
        }
```

### Pattern: Graceful Degradation

```python
def get_product_info_degraded(product_id: str) -> dict:
    """Get product info with graceful degradation.

    Degradation levels:
    1. Full data from primary API
    2. Basic data from cache
    3. Minimal data from database
    4. Error message
    """
    # Try full data
    try:
        return api.get_product_full(product_id)
    except Exception as e:
        logger.warning(f"Full product data failed: {e}")

    # Try cached data
    try:
        cached = cache.get(f"product:{product_id}")
        if cached:
            cached["_source"] = "cache"
            cached["_degraded"] = True
            return cached
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")

    # Try minimal data from database
    try:
        minimal = db.get_product_basic(product_id)
        minimal["_source"] = "database"
        minimal["_degraded"] = True
        return minimal
    except Exception as e:
        logger.error(f"All product data sources failed: {e}")

    # Return error
    return {
        "error": "product_unavailable",
        "message": f"Product {product_id} information temporarily unavailable"
    }
```

## Validation

Prevent errors through validation.

### Input Validation

```python
from typing import Optional
from pydantic import BaseModel, validator

class OrderRequest(BaseModel):
    """Validated order request."""
    user_id: str
    items: list[dict]
    payment_method_id: str

    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.startswith('user_'):
            raise ValueError('user_id must start with user_')
        return v

    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('items cannot be empty')
        for item in v:
            if 'product_id' not in item or 'quantity' not in item:
                raise ValueError('items must have product_id and quantity')
        return v

def create_order_validated(
    user_id: str,
    items: list[dict],
    payment_method_id: str
) -> dict:
    """Create order with validation."""
    try:
        # Validate input
        request = OrderRequest(
            user_id=user_id,
            items=items,
            payment_method_id=payment_method_id
        )

        # Process validated request
        return api.create_order(request.dict())

    except ValueError as e:
        return {
            "error": "validation_error",
            "message": str(e),
            "recovery": "Please check your input and try again"
        }
```

## Logging and Monitoring

Track errors for debugging and alerting.

### Structured Logging

```python
import logging
import json

class StructuredLogger:
    """Structured logger for production."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_error(
        self,
        error: Exception,
        context: dict,
        severity: str = "ERROR"
    ):
        """Log error with structured context."""
        log_entry = {
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

        self.logger.error(json.dumps(log_entry))

# Usage
logger = StructuredLogger("agent")

try:
    result = process_order(order_id)
except Exception as e:
    logger.log_error(
        error=e,
        context={
            "order_id": order_id,
            "user_id": user_id,
            "action": "process_order"
        }
    )
```

## Best Practices

### Error Handling

**Do:**
- Handle errors at appropriate level (tool, callback, application)
- Provide actionable error messages
- Log errors with context
- Implement retry logic for transient failures
- Use circuit breakers for failing services
- Validate inputs before processing

**Don't:**
- Swallow errors silently
- Return generic error messages
- Retry indefinitely
- Expose internal error details to users
- Ignore error patterns (monitor and fix root causes)

### Recovery Strategies

**Transient Errors** (network, timeout):
- Retry with exponential backoff
- Use circuit breakers
- Implement timeouts

**Permanent Errors** (not found, invalid input):
- Don't retry
- Provide clear error message
- Suggest corrective action

**Degraded Service**:
- Use fallback data sources
- Provide partial functionality
- Inform user of degradation

## Official Documentation

- [ADK Error Handling](https://github.com/google/adk-docs/blob/main/docs/error-handling/)
- [Callback Examples](https://context7.com/google/adk-python/llms.txt)
