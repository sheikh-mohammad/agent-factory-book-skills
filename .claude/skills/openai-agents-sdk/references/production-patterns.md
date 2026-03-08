# Production Patterns

Best practices for deploying agents to production environments.

## Production Checklist

### Configuration Management

**Environment Variables**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validate required variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable required")
```

**Configuration Class**:
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    model: str = "gpt-4o"
    max_turns: int = 10
    timeout: float = 30.0
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

### Security

**Input Sanitization**:
```python
import re
from html import escape

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', user_input)

    # Escape HTML
    sanitized = escape(sanitized)

    # Limit length
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()
```

**Output Filtering**:
```python
def filter_sensitive_data(output: str) -> str:
    """Remove sensitive information from output."""
    # Remove credit card numbers
    output = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED]', output)

    # Remove SSN
    output = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED]', output)

    # Remove email addresses (optional)
    # output = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', output)

    return output
```

**Rate Limiting**:
```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Add new request
        self.requests[user_id].append(now)
        return True

rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)
```

### Monitoring

**Metrics Collection**:
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
agent_requests = Counter('agent_requests_total', 'Total agent requests', ['agent_name', 'status'])
agent_duration = Histogram('agent_duration_seconds', 'Agent execution time', ['agent_name'])
agent_tokens = Counter('agent_tokens_total', 'Total tokens used', ['agent_name', 'type'])
active_agents = Gauge('active_agents', 'Number of active agent executions')

async def run_with_metrics(agent, query: str):
    """Run agent with metrics collection."""
    start_time = time.time()
    active_agents.inc()

    try:
        result = await Runner.run(agent, query)

        # Record success
        agent_requests.labels(agent_name=agent.name, status='success').inc()

        # Record duration
        duration = time.time() - start_time
        agent_duration.labels(agent_name=agent.name).observe(duration)

        # Record tokens (if available)
        # agent_tokens.labels(agent_name=agent.name, type='input').inc(result.input_tokens)
        # agent_tokens.labels(agent_name=agent.name, type='output').inc(result.output_tokens)

        return result

    except Exception as e:
        agent_requests.labels(agent_name=agent.name, status='error').inc()
        raise
    finally:
        active_agents.dec()
```

**Structured Logging**:
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log(self, event: str, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))

logger = StructuredLogger('agent')

# Usage
logger.log('agent_start', agent_name='Assistant', query='Hello')
logger.log('tool_call', tool_name='search', params={'query': 'test'})
logger.log('agent_complete', duration=1.23, tokens=150)
```

### Error Handling

**Global Error Handler**:
```python
from agents import Agent, Runner, RunErrorHandlerInput, RunErrorHandlerResult

def global_error_handler(data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    """Handle all agent errors."""
    logger.log('agent_error', error=str(data.error), agent=data.agent.name)

    # Send to error tracking
    sentry_sdk.capture_exception(data.error)

    return RunErrorHandlerResult(
        final_output="I encountered an error. Our team has been notified.",
        include_in_history=False,
    )

# Apply to all agents
error_handlers = {
    "max_turns": global_error_handler,
    "tool_error": global_error_handler,
}
```

**Circuit Breaker**:
```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure = None
        self.state = "closed"

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if datetime.now() - self.last_failure > timedelta(seconds=self.timeout):
                self.state = "half_open"
            else:
                raise Exception("Service unavailable (circuit breaker open)")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = datetime.now()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise

breaker = CircuitBreaker()
```

### Caching

**Response Caching**:
```python
import hashlib
import json
from typing import Optional
import redis

class ResponseCache:
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl

    def _make_key(self, agent_name: str, query: str) -> str:
        """Generate cache key."""
        content = f"{agent_name}:{query}"
        return f"agent:{hashlib.sha256(content.encode()).hexdigest()}"

    def get(self, agent_name: str, query: str) -> Optional[str]:
        """Get cached response."""
        key = self._make_key(agent_name, query)
        cached = self.redis.get(key)
        return cached.decode() if cached else None

    def set(self, agent_name: str, query: str, response: str):
        """Cache response."""
        key = self._make_key(agent_name, query)
        self.redis.setex(key, self.ttl, response)

cache = ResponseCache(REDIS_URL)

async def run_with_cache(agent, query: str):
    """Run agent with caching."""
    # Check cache
    cached = cache.get(agent.name, query)
    if cached:
        logger.log('cache_hit', agent=agent.name)
        return cached

    # Run agent
    result = await Runner.run(agent, query)

    # Cache result
    cache.set(agent.name, query, result.final_output)

    return result
```

### Cost Optimization

**Token Tracking**:
```python
class TokenTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def track(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def estimate_cost(self, model: str) -> float:
        """Estimate cost based on model pricing."""
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        }

        if model not in pricing:
            return 0.0

        input_cost = (self.total_input_tokens / 1000) * pricing[model]["input"]
        output_cost = (self.total_output_tokens / 1000) * pricing[model]["output"]

        return input_cost + output_cost

tracker = TokenTracker()
```

**Model Selection Strategy**:
```python
def select_model(query: str, complexity_threshold: int = 100) -> str:
    """Select model based on query complexity."""
    # Simple heuristic: use mini for short queries
    if len(query.split()) < complexity_threshold:
        return "gpt-4o-mini"
    return "gpt-4o"

# Use in agent creation
model = select_model(user_query)
agent = Agent(name="Assistant", model=model, instructions="Be helpful.")
```

## Deployment Patterns

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["python", "main.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  agent:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    ports:
      - "8000:8000"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from agents import Agent, Runner

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    agent_name: str = "Assistant"

class QueryResponse(BaseModel):
    response: str
    agent_name: str
    duration: float

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Query an agent."""
    # Rate limiting
    if not rate_limiter.is_allowed(request.agent_name):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Sanitize input
    query = sanitize_input(request.query)

    # Create agent
    agent = Agent(
        name=request.agent_name,
        instructions="Be helpful and concise.",
        model=select_model(query),
    )

    # Run with metrics
    start_time = time.time()
    result = await run_with_metrics(agent, query)
    duration = time.time() - start_time

    # Filter output
    response = filter_sensitive_data(result.final_output)

    return QueryResponse(
        response=response,
        agent_name=agent.name,
        duration=duration,
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

### Kubernetes Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-service
  template:
    metadata:
      labels:
        app: agent-service
    spec:
      containers:
      - name: agent
        image: agent-service:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Serverless Deployment (AWS Lambda)

```python
import json
from agents import Agent, Runner

def lambda_handler(event, context):
    """AWS Lambda handler."""
    try:
        # Parse request
        body = json.loads(event['body'])
        query = body['query']

        # Create agent
        agent = Agent(
            name="Assistant",
            instructions="Be helpful and concise.",
            model="gpt-4o-mini",  # Use mini for cost efficiency
        )

        # Run agent (sync for Lambda)
        result = Runner.run_sync(agent, query)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': result.final_output
            })
        }

    except Exception as e:
        logger.error(f"Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

## Testing in Production

### Canary Deployment

```python
import random

def should_use_new_version(user_id: str, rollout_percentage: int = 10) -> bool:
    """Determine if user should get new version."""
    # Consistent hashing for same user
    hash_value = hash(user_id) % 100
    return hash_value < rollout_percentage

async def run_with_canary(agent_v1, agent_v2, query: str, user_id: str):
    """Run with canary deployment."""
    if should_use_new_version(user_id, rollout_percentage=10):
        logger.log('canary_request', user_id=user_id, version='v2')
        return await Runner.run(agent_v2, query)
    else:
        return await Runner.run(agent_v1, query)
```

### A/B Testing

```python
class ABTest:
    def __init__(self, test_name: str, variants: dict):
        self.test_name = test_name
        self.variants = variants

    def get_variant(self, user_id: str) -> str:
        """Get variant for user."""
        hash_value = hash(f"{self.test_name}:{user_id}") % 100

        cumulative = 0
        for variant, percentage in self.variants.items():
            cumulative += percentage
            if hash_value < cumulative:
                return variant

        return list(self.variants.keys())[0]

# Define test
ab_test = ABTest(
    test_name="model_comparison",
    variants={"gpt-4o": 50, "gpt-4o-mini": 50}
)

# Use in production
variant = ab_test.get_variant(user_id)
agent = Agent(name="Assistant", model=variant, instructions="Be helpful.")
```

## Best Practices

### Configuration
- Use environment variables for secrets
- Validate configuration on startup
- Use configuration classes (Pydantic)
- Separate config per environment

### Security
- Sanitize all user inputs
- Filter sensitive data from outputs
- Implement rate limiting
- Use HTTPS for all communications
- Rotate API keys regularly

### Monitoring
- Log all agent interactions
- Track metrics (requests, duration, errors)
- Set up alerts for anomalies
- Monitor token usage and costs

### Error Handling
- Implement global error handlers
- Use circuit breakers for external services
- Provide graceful degradation
- Log errors with full context

### Performance
- Cache frequent queries
- Use appropriate models (mini vs full)
- Implement connection pooling
- Monitor and optimize slow operations

### Cost Management
- Track token usage
- Use gpt-4o-mini where possible
- Implement caching
- Set max_tokens limits
- Monitor and alert on cost spikes

## Troubleshooting

### High latency
- Check model selection (use mini for simple queries)
- Implement caching
- Optimize tool execution
- Review network connectivity

### High costs
- Audit token usage
- Switch to gpt-4o-mini where appropriate
- Implement aggressive caching
- Set max_tokens limits
- Review and optimize prompts

### Errors in production
- Check logs for patterns
- Review error rates in metrics
- Verify configuration
- Test error handlers
- Check external service status

### Memory issues
- Monitor memory usage
- Implement connection pooling
- Clear caches periodically
- Review agent history management
- Scale horizontally if needed
