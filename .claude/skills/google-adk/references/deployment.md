# Deployment

Complete guide for deploying Google ADK agents from local development to production.

## Deployment Options

| Option | Best For | Complexity | Scalability |
|--------|----------|------------|-------------|
| **Local CLI** | Development, testing | Low | Single machine |
| **FastAPI** | Self-hosted, custom infrastructure | Medium | Horizontal scaling |
| **Google Cloud Run** | Managed, serverless | Medium | Auto-scaling |
| **Custom Server** | Full control, existing infrastructure | High | Custom |

## Local Development

### CLI Commands

**Run agent directly:**
```bash
adk run agent.py
```

**Launch web UI:**
```bash
adk web ./agents
```

**API server:**
```bash
adk api_server ./agents
```

**With specific agent directory:**
```bash
adk web path/to/agents_dir
```

### Web UI Features

- Interactive chat interface
- Session management
- Tool call visualization
- Debug information
- Multi-agent support

### Environment Configuration

```bash
# .env file
GOOGLE_API_KEY=your_api_key
GOOGLE_GENAI_USE_VERTEXAI=0
```

## FastAPI Integration

Deploy agents as REST APIs using FastAPI.

### Basic FastAPI App

```python
from google.adk.cli.fast_api import get_fast_api_app

# Auto-generate FastAPI app from agents directory
app = get_fast_api_app(agent_dir="./agents")

# Run with uvicorn
# uvicorn main:app --host 0.0.0.0 --port 8000
```

### Custom FastAPI Integration

```python
from fastapi import FastAPI
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

app = FastAPI()

# Create agent
agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
)

# Create runner
runner = Runner(
    app_name="api_app",
    agent=agent,
    session_service=InMemorySessionService(),
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint."""
    events = []
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=request.session_id,
        new_message=types.UserContent(
            parts=[types.Part(text=request.message)]
        ),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    return ChatResponse(
                        response=part.text,
                        session_id=request.session_id,
                    )

    return ChatResponse(
        response="No response generated",
        session_id=request.session_id,
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

### Running FastAPI

**Development:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**With Gunicorn:**
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Google Cloud Run

Deploy to managed, serverless infrastructure.

### Using ADK CLI

```bash
adk deploy cloud_run \
  --project=your-project-id \
  --region=us-central1 \
  --service_name=my-agent \
  --with_ui \
  --a2a ./agent_dir
```

### Manual Cloud Run Deployment

**1. Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**2. Build and push image:**
```bash
# Build image
gcloud builds submit --tag gcr.io/your-project-id/agent-app

# Or with Docker
docker build -t gcr.io/your-project-id/agent-app .
docker push gcr.io/your-project-id/agent-app
```

**3. Deploy to Cloud Run:**
```bash
gcloud run deploy agent-service \
  --image gcr.io/your-project-id/agent-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=your-project-id
```

### Cloud Run Configuration

**Environment variables:**
```bash
gcloud run services update agent-service \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id \
  --set-env-vars GOOGLE_CLOUD_LOCATION=us-central1
```

**Secrets:**
```bash
# Create secret
echo -n "your_api_key" | gcloud secrets create api-key --data-file=-

# Mount secret
gcloud run services update agent-service \
  --set-secrets API_KEY=api-key:latest
```

**Resource limits:**
```bash
gcloud run services update agent-service \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10
```

## Production Runner Configuration

Use managed services for production deployments.

### Vertex AI Services

```python
from google.adk import Agent, Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiRagMemoryService

agent = Agent(
    name="production_assistant",
    model="gemini-2.5-flash",
    instruction="You are a production assistant.",
    tools=[...],
)

runner = Runner(
    app_name="production_app",
    agent=agent,
    session_service=VertexAiSessionService(
        project_id="your-project-id",
        location="us-central1",
    ),
    memory_service=VertexAiRagMemoryService(
        project_id="your-project-id",
        location="us-central1",
    ),
)
```

### PostgreSQL Sessions

For self-hosted deployments:

```python
from google.adk.sessions import PostgresSessionService

session_service = PostgresSessionService(
    connection_url=os.getenv("POSTGRES_URL"),
)

runner = Runner(
    app_name="self_hosted_app",
    agent=agent,
    session_service=session_service,
)
```

**PostgreSQL setup:**
```bash
# .env
POSTGRES_URL=postgresql+asyncpg://user:password@host:5432/adk_sessions
```

## Docker Deployment

### Production Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_GENAI_USE_VERTEXAI=1
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GOOGLE_CLOUD_LOCATION=us-central1
      - POSTGRES_URL=postgresql+asyncpg://postgres:postgres@db:5432/adk
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=adk
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adk-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: adk-agent
  template:
    metadata:
      labels:
        app: adk-agent
    spec:
      containers:
      - name: agent
        image: gcr.io/your-project-id/agent-app:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_GENAI_USE_VERTEXAI
          value: "1"
        - name: GOOGLE_CLOUD_PROJECT
          value: "your-project-id"
        - name: GOOGLE_CLOUD_LOCATION
          value: "us-central1"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: adk-agent-service
spec:
  selector:
    app: adk-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

**Deploy to Kubernetes:**
```bash
kubectl apply -f deployment.yaml
```

## Monitoring and Observability

### Logging

```python
import logging
from google.cloud import logging as cloud_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For Cloud Run/GKE, use Cloud Logging
if os.getenv("GOOGLE_CLOUD_PROJECT"):
    client = cloud_logging.Client()
    client.setup_logging()

# Log agent interactions
async def log_interactions(
    ctx: CallbackContext,
    response: LlmResponse,
) -> Optional[LlmResponse]:
    """Log agent responses."""
    logger.info(f"Agent response: {response.content}")
    return None

agent = Agent(
    name="monitored_agent",
    model="gemini-2.5-flash",
    after_model_callback=[log_interactions],
)
```

### Metrics

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
request_count = Counter('agent_requests_total', 'Total agent requests')
request_duration = Histogram('agent_request_duration_seconds', 'Request duration')

@app.post("/chat")
async def chat(request: ChatRequest):
    request_count.inc()
    with request_duration.time():
        # Process request
        response = await process_chat(request)
    return response

# Start metrics server
start_http_server(9090)
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    checks = {
        "status": "ok",
        "agent": "initialized",
        "database": await check_database(),
        "model": await check_model_access(),
    }

    if all(v == "ok" or v == "initialized" for v in checks.values()):
        return checks
    else:
        return JSONResponse(status_code=503, content=checks)

async def check_database():
    """Check database connectivity."""
    try:
        await session_service.list_sessions("health_check", "test_user")
        return "ok"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return "error"

async def check_model_access():
    """Check model API access."""
    try:
        # Simple test query
        await runner.run_debug("test", quiet=True)
        return "ok"
    except Exception as e:
        logger.error(f"Model check failed: {e}")
        return "error"
```

## Production Checklist

Before deploying to production:

- [ ] Environment variables externalized (not hardcoded)
- [ ] Secrets stored in Secret Manager (not .env files)
- [ ] Managed services configured (Vertex AI sessions/memory)
- [ ] Authentication implemented for all external APIs
- [ ] Error handling and recovery strategies in place
- [ ] Logging configured (structured logging for Cloud Logging)
- [ ] Metrics and monitoring set up
- [ ] Health check endpoints implemented
- [ ] Resource limits configured (memory, CPU, timeout)
- [ ] Auto-scaling configured
- [ ] Rate limiting implemented
- [ ] Database connection pooling configured
- [ ] Backup and disaster recovery plan
- [ ] CI/CD pipeline set up
- [ ] Load testing completed
- [ ] Security review completed
- [ ] Documentation for operations team

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}

    - name: Build and push image
      run: |
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/agent-app

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy agent-service \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/agent-app \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

## Scaling Considerations

### Horizontal Scaling

- Use stateless agents (session state in external storage)
- Implement connection pooling for databases
- Use managed services (Vertex AI) for auto-scaling
- Configure load balancing

### Vertical Scaling

- Increase memory/CPU for Cloud Run instances
- Use `gemini-2.5-flash` for better throughput
- Implement caching for repeated queries
- Optimize tool execution

### Cost Optimization

- Use `gemini-2.5-flash` instead of `gemini-2.5-pro` when possible
- Implement request caching
- Set appropriate min/max instances
- Use preemptible instances for non-critical workloads
- Monitor and optimize token usage

## Troubleshooting

### Common Deployment Issues

**Issue: "Module not found"**
- Ensure all dependencies in requirements.txt
- Check Python version compatibility
- Verify virtual environment is activated

**Issue: "Connection timeout"**
- Increase Cloud Run timeout (default 300s)
- Check network connectivity
- Verify firewall rules

**Issue: "Out of memory"**
- Increase memory allocation
- Implement streaming for large responses
- Optimize session state size

**Issue: "Cold start latency"**
- Set min-instances > 0
- Implement health check warming
- Optimize import statements

## Official Documentation

- [ADK Deployment Guide](https://github.com/google/adk-docs/blob/main/docs/deployment/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
