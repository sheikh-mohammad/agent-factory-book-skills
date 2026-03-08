# Best Practices

Security, performance, error handling, and testing best practices for production MCP servers.

## Security Best Practices

### Input Validation

Always validate and sanitize inputs:

```python
from pydantic import BaseModel, validator, Field

class QueryParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)

    @validator('query')
    def validate_query(cls, v):
        # Prevent SQL injection
        if any(char in v for char in [';', '--', '/*', '*/']):
            raise ValueError("Invalid characters in query")
        return v

@mcp.tool()
async def search(params: QueryParams) -> str:
    # Safe to use params.query
    results = await db.search(params.query, params.limit)
    return results
```

### Path Traversal Prevention

```python
import os
from pathlib import Path

ALLOWED_DIR = Path("/app/documents")

@mcp.resource("file://documents/{filename}")
async def read_file(filename: str) -> str:
    # Prevent path traversal
    filepath = (ALLOWED_DIR / filename).resolve()

    if not filepath.is_relative_to(ALLOWED_DIR):
        raise ValueError("Access denied: path traversal attempt")

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    return filepath.read_text()
```

### SQL Injection Prevention

```python
# ❌ WRONG - vulnerable to SQL injection
@mcp.tool()
async def query_db(table: str, condition: str) -> str:
    query = f"SELECT * FROM {table} WHERE {condition}"
    return await db.execute(query)

# ✅ CORRECT - use parameterized queries
@mcp.tool()
async def query_db(table: str, column: str, value: str) -> str:
    # Whitelist allowed tables
    if table not in ['users', 'products', 'orders']:
        raise ValueError("Invalid table")

    # Use parameterized query
    query = f"SELECT * FROM {table} WHERE {column} = ?"
    return await db.execute(query, (value,))
```

### Command Injection Prevention

```python
import shlex

# ❌ WRONG - vulnerable to command injection
@mcp.tool()
async def run_command(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout.decode()

# ✅ CORRECT - use argument list, no shell
@mcp.tool()
async def run_command(cmd: str, args: list[str]) -> str:
    # Whitelist allowed commands
    if cmd not in ['ls', 'cat', 'grep']:
        raise ValueError("Command not allowed")

    # Use argument list
    result = subprocess.run([cmd] + args, capture_output=True)
    return result.stdout.decode()
```

### Secrets Management

```python
import os
from cryptography.fernet import Fernet

# ❌ WRONG - hardcoded secrets
API_KEY = "sk-1234567890abcdef"

# ✅ CORRECT - environment variables
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable required")

# ✅ CORRECT - encrypted secrets
def decrypt_secret(encrypted: str) -> str:
    key = os.getenv("ENCRYPTION_KEY").encode()
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()

DATABASE_PASSWORD = decrypt_secret(os.getenv("ENCRYPTED_DB_PASSWORD"))
```

### Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = datetime.now()
        cutoff = now - self.window

        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        self.requests[client_id].append(now)
        return True

limiter = RateLimiter(max_requests=100, window_seconds=60)

@mcp.tool()
async def rate_limited_tool(param: str, ctx: Context) -> str:
    client_id = ctx.session.client_id

    if not limiter.is_allowed(client_id):
        raise ValueError("Rate limit exceeded. Try again later.")

    return await perform_operation(param)
```

---

## Performance Best Practices

### Async Operations

```python
# ❌ WRONG - blocking operations
@mcp.tool()
def slow_tool(url: str) -> str:
    response = requests.get(url)  # Blocks event loop
    return response.text

# ✅ CORRECT - async operations
@mcp.tool()
async def fast_tool(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### Connection Pooling

```python
import httpx
from contextlib import asynccontextmanager

# Create persistent client
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100)
)

@asynccontextmanager
async def lifespan(app):
    # Startup
    yield
    # Shutdown
    await http_client.aclose()

mcp = FastMCP("my-server", lifespan=lifespan)

@mcp.tool()
async def fetch_data(url: str) -> str:
    # Reuse connection pool
    response = await http_client.get(url)
    return response.text
```

### Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

# In-memory cache with TTL
class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None

    def set(self, key: str, value):
        self.cache[key] = (value, datetime.now())

cache = TTLCache(ttl_seconds=300)

@mcp.tool()
async def cached_api_call(endpoint: str) -> str:
    # Check cache
    cached = cache.get(endpoint)
    if cached:
        return cached

    # Fetch and cache
    result = await fetch_from_api(endpoint)
    cache.set(endpoint, result)
    return result
```

### Batch Operations

```python
# ❌ WRONG - multiple individual queries
@mcp.tool()
async def get_users(user_ids: list[int]) -> str:
    users = []
    for user_id in user_ids:
        user = await db.get_user(user_id)  # N queries
        users.append(user)
    return json.dumps(users)

# ✅ CORRECT - single batch query
@mcp.tool()
async def get_users(user_ids: list[int]) -> str:
    users = await db.get_users_batch(user_ids)  # 1 query
    return json.dumps(users)
```

### Timeouts

```python
import asyncio

@mcp.tool()
async def operation_with_timeout(param: str) -> str:
    try:
        # Set timeout
        result = await asyncio.wait_for(
            slow_operation(param),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        return "Operation timed out after 30 seconds"
```

---

## Error Handling Best Practices

### Graceful Degradation

```python
@mcp.tool()
async def resilient_tool(primary_source: str, fallback_source: str) -> str:
    try:
        # Try primary source
        return await fetch_from_primary(primary_source)
    except Exception as e:
        logging.warning(f"Primary source failed: {e}")

        try:
            # Fallback to secondary source
            return await fetch_from_fallback(fallback_source)
        except Exception as e:
            logging.error(f"Fallback source failed: {e}")
            return "Unable to fetch data from any source"
```

### Retry Logic

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

@mcp.tool()
async def reliable_fetch(url: str) -> str:
    try:
        return await fetch_with_retry(url)
    except Exception as e:
        logging.error(f"Failed after retries: {e}")
        return f"Failed to fetch data: {str(e)}"
```

### Error Context

```python
class ToolError(Exception):
    def __init__(self, message: str, context: dict):
        super().__init__(message)
        self.context = context

@mcp.tool()
async def detailed_error_tool(param: str) -> str:
    try:
        result = await complex_operation(param)
        return result
    except ValueError as e:
        raise ToolError(
            "Invalid parameter",
            {
                "param": param,
                "error": str(e),
                "suggestion": "Check parameter format"
            }
        )
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        raise ToolError(
            "Operation failed",
            {
                "param": param,
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
```

### Circuit Breaker

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold: int, timeout_seconds: int):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failures = 0
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func):
        if self.state == "open":
            if datetime.now() - self.last_failure > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func()
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = datetime.now()

            if self.failures >= self.failure_threshold:
                self.state = "open"

            raise e

breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)

@mcp.tool()
async def protected_tool(param: str) -> str:
    return breaker.call(lambda: external_api_call(param))
```

---

## Testing Best Practices

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_tool_success():
    # Mock external dependencies
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.text = "test data"

        result = await my_tool("test_param")

        assert "test data" in result
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_tool_error_handling():
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = Exception("Network error")

        result = await my_tool("test_param")

        assert "error" in result.lower()
```

### Integration Testing

```python
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_server_integration():
    async with stdio_client("python", ["server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0

            # Call tool
            result = await session.call_tool("my_tool", {"param": "test"})
            assert result.content[0].text == "expected output"
```

### Load Testing

```python
import asyncio
import time

async def load_test():
    tasks = []
    start = time.time()

    # Simulate 100 concurrent requests
    for i in range(100):
        task = asyncio.create_task(call_tool("test_param"))
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = time.time() - start
    errors = sum(1 for r in results if isinstance(r, Exception))

    print(f"Duration: {duration:.2f}s")
    print(f"Requests/sec: {100/duration:.2f}")
    print(f"Errors: {errors}")

asyncio.run(load_test())
```

---

## Logging Best Practices

### Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_entry)
        )

logger = StructuredLogger("mcp-server")

@mcp.tool()
async def logged_tool(param: str) -> str:
    logger.log("info", "Tool called", tool="logged_tool", param=param)

    try:
        result = await operation(param)
        logger.log("info", "Tool succeeded", tool="logged_tool", result_length=len(result))
        return result
    except Exception as e:
        logger.log("error", "Tool failed", tool="logged_tool", error=str(e))
        raise
```

### Log Levels

```python
import logging

# Configure log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))

@mcp.tool()
async def tool_with_logging(param: str) -> str:
    logging.debug(f"Tool called with param: {param}")  # Verbose details
    logging.info("Processing request")  # Normal operations
    logging.warning("Deprecated parameter used")  # Warnings
    logging.error("Operation failed")  # Errors
    logging.critical("System failure")  # Critical issues
```

---

## Documentation Best Practices

### Tool Documentation

```python
@mcp.tool()
async def well_documented_tool(
    query: str,
    limit: int = 10,
    include_metadata: bool = False
) -> str:
    """Search the database for records.

    This tool performs a full-text search across all indexed fields
    and returns matching records sorted by relevance.

    Args:
        query: Search query string. Supports boolean operators (AND, OR, NOT)
               and phrase matching with quotes. Example: "python AND (web OR api)"
        limit: Maximum number of results to return. Must be between 1 and 100.
               Default is 10.
        include_metadata: Whether to include metadata (timestamps, authors) in
                         results. Default is False.

    Returns:
        JSON string containing search results with the following structure:
        {
            "total": <number of total matches>,
            "results": [
                {
                    "id": <record id>,
                    "title": <record title>,
                    "content": <record content>,
                    "metadata": {...}  // if include_metadata is True
                }
            ]
        }

    Raises:
        ValueError: If query is empty or limit is out of range
        DatabaseError: If database connection fails

    Example:
        >>> await well_documented_tool("python web", limit=5)
        '{"total": 42, "results": [...]}'
    """
    # Implementation
    pass
```

### README Documentation

Create comprehensive README for your server:

```markdown
# My MCP Server

Brief description of what the server does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Configuration

Required environment variables:
- `API_KEY`: Your API key
- `DATABASE_URL`: Database connection string

## Usage

### With Claude Desktop

Add to `claude_desktop_config.json`:
\`\`\`json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
\`\`\`

## Available Tools

### search_database
Search the database for records.

**Parameters:**
- `query` (string): Search query
- `limit` (number, optional): Max results (default: 10)

**Example:**
\`\`\`
Search for "python web frameworks" with limit 5
\`\`\`

## Development

\`\`\`bash
# Run tests
pytest

# Run server
python server.py
\`\`\`

## License

MIT
```

---

## Monitoring Best Practices

### Health Checks

```python
from datetime import datetime

@app.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }

    # Database check
    try:
        await db.execute("SELECT 1")
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["checks"]["database"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"

    # External API check
    try:
        await http_client.get("https://api.example.com/health", timeout=5)
        checks["checks"]["external_api"] = "healthy"
    except Exception as e:
        checks["checks"]["external_api"] = f"unhealthy: {str(e)}"

    return checks
```

### Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
tool_calls_total = Counter(
    'mcp_tool_calls_total',
    'Total number of tool calls',
    ['tool_name', 'status']
)

tool_duration_seconds = Histogram(
    'mcp_tool_duration_seconds',
    'Tool execution duration',
    ['tool_name']
)

active_sessions = Gauge(
    'mcp_active_sessions',
    'Number of active sessions'
)

@mcp.tool()
async def monitored_tool(param: str) -> str:
    tool_calls_total.labels(tool_name='monitored_tool', status='started').inc()

    with tool_duration_seconds.labels(tool_name='monitored_tool').time():
        try:
            result = await operation(param)
            tool_calls_total.labels(tool_name='monitored_tool', status='success').inc()
            return result
        except Exception as e:
            tool_calls_total.labels(tool_name='monitored_tool', status='error').inc()
            raise
```
