# Deployment Guide

Production deployment strategies for MCP servers across different environments.

## Deployment Options

| Option | Transport | Use Case | Complexity |
|--------|-----------|----------|------------|
| **Claude Desktop** | stdio | Local development, personal use | Low |
| **VS Code** | stdio | IDE integration | Low |
| **Docker (stdio)** | stdio | Containerized local servers | Medium |
| **Cloud HTTP** | HTTP | Remote access, multi-user | High |
| **Docker (HTTP)** | HTTP | Containerized remote servers | High |

---

## Claude Desktop Deployment

### Configuration

**macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Python Server**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/server",
        "run",
        "server.py"
      ]
    }
  }
}
```

**TypeScript Server**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/server/build/index.js"]
    }
  }
}
```

**With Environment Variables**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/path/to/server", "run", "server.py"],
      "env": {
        "API_KEY": "your-api-key",
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not appearing | Check absolute paths, restart Claude Desktop |
| "Server disconnected" | Remove all stdout logging (console.log/print) |
| Permission denied | Make script executable: `chmod +x server.py` |
| Command not found | Use full path to command: `/usr/local/bin/uv` |

---

## VS Code Deployment

### Configuration

Add to VS Code settings or `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    }
  }
}
```

---

## Docker Deployment (stdio)

### Dockerfile (Python)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY server.py .

# Install dependencies
RUN uv sync

# Run server
CMD ["uv", "run", "server.py"]
```

### Dockerfile (TypeScript)

```dockerfile
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY src/ ./src/

# Build
RUN npm run build

# Run server
CMD ["node", "build/index.js"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    stdin_open: true
    tty: true
    environment:
      - API_KEY=${API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./data:/app/data
```

### Running

```bash
docker-compose up -d
docker exec -it mcp-server_mcp-server_1 /bin/bash
```

---

## Cloud HTTP Deployment

### Python HTTP Server

```python
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("my-server")

# Register tools, resources, prompts...

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        cors_origins=["https://your-client.com"]
    )
```

### TypeScript HTTP Server

```typescript
import { createServer } from "node:http";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Register tools, resources, prompts...

const PORT = process.env.PORT || 3000;

createServer(async (req, res) => {
  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "https://your-client.com");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  // Authentication
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    res.writeHead(401);
    res.end(JSON.stringify({ error: "Unauthorized" }));
    return;
  }

  const token = authHeader.substring(7);
  if (!verifyToken(token)) {
    res.writeHead(403);
    res.end(JSON.stringify({ error: "Invalid token" }));
    return;
  }

  // Handle MCP request
  const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });

  await server.connect(transport);
  await transport.handleRequest(req, res);
}).listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
```

### Dockerfile (HTTP)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "server.py"]
```

### Docker Compose (HTTP)

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - API_KEY=${API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Cloud Platform Deployment

### AWS (Elastic Beanstalk)

**Procfile**:
```
web: python server.py
```

**Deploy**:
```bash
eb init -p python-3.11 my-mcp-server
eb create production
eb deploy
```

### Google Cloud Run

**Deploy**:
```bash
gcloud run deploy my-mcp-server \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Heroku

**Procfile**:
```
web: python server.py
```

**Deploy**:
```bash
heroku create my-mcp-server
git push heroku main
```

### Railway

**railway.json**:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python server.py",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

## Environment Variables

### Secure Configuration

**Never hardcode secrets**. Use environment variables:

```python
import os

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

### .env File (Development)

```bash
API_KEY=your-api-key
DATABASE_URL=postgresql://localhost/mydb
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

**Load with python-dotenv**:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Authentication & Security

### Bearer Token Authentication

```python
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization[7:]
    if token != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=403, detail="Invalid token")

    return token

@app.post("/mcp")
async def mcp_endpoint(token: str = Depends(verify_token)):
    # Handle MCP request
    pass
```

### API Key Authentication

```typescript
function verifyApiKey(req: IncomingMessage): boolean {
  const apiKey = req.headers["x-api-key"];
  return apiKey === process.env.API_KEY;
}

createServer(async (req, res) => {
  if (!verifyApiKey(req)) {
    res.writeHead(401);
    res.end(JSON.stringify({ error: "Invalid API key" }));
    return;
  }

  // Handle request
}).listen(3000);
```

### OAuth 2.0

For production systems, implement OAuth 2.0:

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
```

---

## Monitoring & Logging

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest

tool_calls = Counter('mcp_tool_calls_total', 'Total tool calls', ['tool_name'])
tool_duration = Histogram('mcp_tool_duration_seconds', 'Tool execution time', ['tool_name'])

@mcp.tool()
async def my_tool(param: str) -> str:
    tool_calls.labels(tool_name='my_tool').inc()

    with tool_duration.labels(tool_name='my_tool').time():
        # Execute tool
        return result

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Production Readiness Checklist

### Security
- [ ] Authentication implemented (Bearer token, API key, OAuth)
- [ ] HTTPS/TLS enabled
- [ ] Input validation on all tools
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Secrets in environment variables (not code)
- [ ] Security headers set

### Reliability
- [ ] Error handling on all operations
- [ ] Timeouts on external calls
- [ ] Retry logic for transient failures
- [ ] Health check endpoint
- [ ] Graceful shutdown handling
- [ ] Connection pooling for databases/APIs

### Observability
- [ ] Structured logging implemented
- [ ] Metrics collection (Prometheus/CloudWatch)
- [ ] Distributed tracing (optional)
- [ ] Error tracking (Sentry/Rollbar)
- [ ] Performance monitoring

### Performance
- [ ] Async operations used throughout
- [ ] Database queries optimized
- [ ] Caching implemented where appropriate
- [ ] Resource limits configured
- [ ] Load testing completed

### Operations
- [ ] Automated deployment pipeline
- [ ] Environment-specific configurations
- [ ] Backup and recovery procedures
- [ ] Monitoring and alerting configured
- [ ] Documentation complete
- [ ] Runbook for common issues

---

## Scaling Strategies

### Horizontal Scaling

Deploy multiple instances behind a load balancer:

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-server:
    build: .
    deploy:
      replicas: 3
    environment:
      - PORT=8000

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - mcp-server
```

**nginx.conf**:
```nginx
upstream mcp_servers {
    server mcp-server:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://mcp_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Caching

Implement caching for expensive operations:

```python
from functools import lru_cache
import redis

# In-memory cache
@lru_cache(maxsize=1000)
def expensive_operation(param: str) -> str:
    # Expensive computation
    return result

# Redis cache
redis_client = redis.Redis(host='localhost', port=6379)

@mcp.tool()
async def cached_tool(param: str) -> str:
    # Check cache
    cached = redis_client.get(f"tool:{param}")
    if cached:
        return cached.decode()

    # Compute and cache
    result = await expensive_operation(param)
    redis_client.setex(f"tool:{param}", 3600, result)
    return result
```

---

## Backup & Recovery

### Database Backups

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://my-backups/
```

### State Management

For stateful servers, persist state to external storage:

```python
import json

class StateManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.state = self.load()

    def load(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.state, f)

    def set(self, key: str, value: any):
        self.state[key] = value
        self.save()
```
