# Troubleshooting Guide

Common issues and solutions for ChatKit applications.

---

## Installation Issues

### Issue: "uv: command not found"

**Cause**: uv package manager not installed

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal or source profile
source ~/.bashrc  # or ~/.zshrc
```

### Issue: "Module not found" errors

**Cause**: Dependencies not installed

**Solution**:
```bash
# Install Python dependencies
uv pip install -r requirements.txt

# Install Node dependencies
npm install
```

---

## Environment Variable Issues

### Issue: "AuthenticationError: Invalid API key"

**Cause**: OPENAI_API_KEY not set or invalid

**Solution**:
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Set key (replace with your actual key)
export OPENAI_API_KEY="sk-proj-your-key-here"

# Or add to .env file
echo "OPENAI_API_KEY=sk-proj-your-key-here" > .env
```

### Issue: "Vector store not found"

**Cause**: KNOWLEDGE_VECTOR_STORE_ID not set or invalid

**Solution**:
1. Go to https://platform.openai.com/storage/vector_stores
2. Verify vector store exists
3. Copy correct ID (starts with "vs_")
4. Set environment variable:
```bash
export KNOWLEDGE_VECTOR_STORE_ID="vs_your-id-here"
```

---

## Runtime Errors

### Issue: "CORS error" in browser console

**Cause**: Frontend origin not allowed

**Solution**:
```python
# In app/main.py, update CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5170",  # Add your frontend URL
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Connection refused" when calling backend

**Cause**: Backend not running or wrong port

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if not running
npm run backend

# Or check port in package.json
```

### Issue: "Rate limit exceeded"

**Cause**: Too many OpenAI API requests

**Solution**:
1. Implement rate limiting (see `references/security.md`)
2. Add exponential backoff (see `references/error-handling.md`)
3. Upgrade OpenAI plan if needed

---

## Vector Store Issues

### Issue: "No results from vector search"

**Cause**: Documents not indexed yet or poor query

**Solution**:
```python
# Check vector store status
def check_vector_store_status(vector_store_id: str):
    vs = client.beta.vector_stores.retrieve(vector_store_id)
    print(f"Status: {vs.status}")
    print(f"Files: {vs.file_counts.completed}/{vs.file_counts.total}")

# Wait for indexing to complete
# Try more specific queries
```

### Issue: "File upload failed"

**Cause**: Unsupported format or file too large

**Solution**:
- Check file format (PDF, DOCX, TXT, MD supported)
- Verify file size < 512 MB
- Try uploading via OpenAI platform UI

---

## Tool Execution Issues

### Issue: "Tool not found"

**Cause**: Tool not registered or name mismatch

**Solution**:
```python
# Verify tool is in TOOL_FUNCTIONS dict
TOOL_FUNCTIONS = {
    "get_weather": get_weather,  # Name must match exactly
    "send_email": send_email
}

# Check tool schema name matches
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",  # Must match TOOL_FUNCTIONS key
            # ...
        }
    }
]
```

### Issue: "Tool execution timeout"

**Cause**: Tool taking too long

**Solution**:
```python
# Add timeout protection
from contextlib import contextmanager
import signal

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Use in tool
def slow_tool():
    with timeout(30):
        # Tool logic
        pass
```

---

## Performance Issues

### Issue: "Slow response times"

**Cause**: Multiple factors

**Solution**:
1. **Enable streaming**:
```python
# Stream responses for better UX
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True
)
```

2. **Cache results**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query_hash: str):
    # Expensive operation
    pass
```

3. **Use connection pooling**:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10
)
```

### Issue: "High memory usage"

**Cause**: Large thread history or memory leaks

**Solution**:
1. Limit thread message history
2. Implement thread cleanup
3. Monitor with profiling tools

---

## Deployment Issues

### Issue: "Docker build fails"

**Cause**: Missing dependencies or wrong base image

**Solution**:
```dockerfile
# Use correct Python version
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv
```

### Issue: "Container crashes on startup"

**Cause**: Environment variables not set

**Solution**:
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    env_file:
      - .env
```

### Issue: "Health check failing"

**Cause**: Health endpoint not responding

**Solution**:
```python
# Add simple health check
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Test locally
curl http://localhost:8000/health
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Inspect Thread Messages

```python
def debug_thread(thread_id: str):
    """Debug thread messages."""
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    for msg in messages.data:
        print(f"Role: {msg.role}")
        print(f"Content: {msg.content[0].text.value}")
        print("---")
```

### Test OpenAI Connection

```python
def test_openai_connection():
    """Test OpenAI API connection."""
    try:
        models = client.models.list()
        print("✓ OpenAI connection successful")
        return True
    except Exception as e:
        print(f"✗ OpenAI connection failed: {str(e)}")
        return False
```

### Monitor API Usage

```python
def log_api_call(func):
    """Decorator to log API calls."""
    def wrapper(*args, **kwargs):
        logger.info(f"API call: {func.__name__}")
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"API call completed in {duration:.2f}s")
        return result
    return wrapper
```

---

## Common Error Messages

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Invalid API key" | Wrong or expired key | Check OPENAI_API_KEY |
| "Rate limit exceeded" | Too many requests | Implement backoff |
| "Model not found" | Invalid model name | Use "gpt-4" or "gpt-3.5-turbo" |
| "Thread not found" | Invalid thread ID | Create new thread |
| "Vector store not found" | Invalid vector store ID | Verify ID on platform |
| "Tool execution failed" | Tool error | Check tool implementation |
| "Connection timeout" | Network issue | Check internet, retry |
| "Insufficient quota" | API quota exceeded | Upgrade plan or wait |

---

## Getting Help

### Check Logs

```bash
# Backend logs
npm run backend 2>&1 | tee backend.log

# Docker logs
docker-compose logs -f backend
```

### Verify Configuration

```python
def verify_config():
    """Verify configuration."""
    checks = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "Backend running": check_backend_health(),
        "OpenAI connection": test_openai_connection()
    }

    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check}")

    return all(checks.values())
```

### Report Issues

When reporting issues, include:
1. Error message (full stack trace)
2. Environment (OS, Python version, Node version)
3. Configuration (sanitized, no API keys)
4. Steps to reproduce
5. Expected vs actual behavior

---

## Quick Fixes

### Reset Everything

```bash
# Stop all services
docker-compose down

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reinstall dependencies
rm -rf node_modules
npm install
uv pip install -r requirements.txt

# Restart
npm start
```

### Test Minimal Setup

```python
# test_minimal.py
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)
```

Run: `python test_minimal.py`

If this works, issue is in your application code, not OpenAI setup.
