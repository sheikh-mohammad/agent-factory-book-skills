# Deployment Guide

Comprehensive guide to deploying Claude Agent SDK in production.

## Hosting Patterns

Choose the right pattern based on your use case:

### 1. Ephemeral Sessions

**Pattern**: New container per task, destroy when complete.

```
User Request → Spin up container → Run agent → Return result → Destroy container
```

**Use for**:
- Bug fixes
- Invoice processing
- Document translation
- One-shot tasks

**Benefits**:
- Clean state per task
- No session management
- Easy to scale
- Cost-efficient (pay per use)

**Drawbacks**:
- Cold start latency
- No conversation history
- Higher overhead per task

**Implementation**:
```typescript
// Lambda/Cloud Function
export async function handler(event) {
  const result = [];
  for await (const message of query({
    prompt: event.task,
    options: { allowedTools: ["Read", "Edit", "Bash"] }
  })) {
    if (message.type === "result") {
      result.push(message.result);
    }
  }
  return { statusCode: 200, body: JSON.stringify(result) };
}
```

### 2. Long-Running Sessions

**Pattern**: Persistent containers for ongoing work.

```
Container starts → Handles multiple requests → Maintains session → Runs indefinitely
```

**Use for**:
- Email agents
- Site builders
- High-frequency chatbots
- Interactive assistants

**Benefits**:
- No cold starts
- Session continuity
- Lower per-request overhead

**Drawbacks**:
- Higher baseline cost
- Session management complexity
- State persistence needed

**Implementation**:
```typescript
// Express server
import express from 'express';
import { query, ClaudeSDKClient } from '@anthropic-ai/claude-agent-sdk';

const app = express();
const sessions = new Map();

app.post('/chat', async (req, res) => {
  const { userId, message } = req.body;

  let client = sessions.get(userId);
  if (!client) {
    client = new ClaudeSDKClient({ allowedTools: ["Read", "WebSearch"] });
    sessions.set(userId, client);
  }

  await client.query(message);
  const result = [];
  for await (const msg of client.receive_response()) {
    if (msg.type === "text") result.push(msg.text);
  }

  res.json({ response: result.join('\n') });
});

app.listen(3000);
```

### 3. Hybrid Sessions

**Pattern**: Ephemeral containers hydrated with history.

```
User Request → Spin up container → Load history from DB → Run agent → Save history → Destroy
```

**Use for**:
- Project managers
- Research agents
- Support tickets
- Cost-optimized chatbots

**Benefits**:
- Session continuity without persistent containers
- Cost-efficient
- Scales to zero

**Drawbacks**:
- Cold start latency
- History storage needed
- More complex implementation

**Implementation**:
```typescript
export async function handler(event) {
  const { userId, message } = event;

  // Load history from database
  const history = await db.getHistory(userId);

  // Run agent with history context
  const result = [];
  for await (const msg of query({
    prompt: `Previous conversation:\n${history}\n\nUser: ${message}`,
    options: { allowedTools: ["Read", "WebSearch"] }
  })) {
    if (msg.type === "result") {
      result.push(msg.result);
      // Save updated history
      await db.saveHistory(userId, msg.session_id);
    }
  }

  return { statusCode: 200, body: JSON.stringify(result) };
}
```

### 4. Single Container, Multiple Agents

**Pattern**: Multiple agents in one container.

```
Container → Agent 1 (task A) + Agent 2 (task B) + Agent 3 (task C)
```

**Use for**:
- Simulations
- Agent-to-agent interactions
- Multi-agent systems
- Development/testing

**Benefits**:
- Agents can interact
- Shared resources
- Lower overhead

**Drawbacks**:
- Resource contention
- Harder to scale
- Blast radius (one agent affects others)

## Container Requirements

### Minimum Requirements

- **Runtime**: Python 3.10+ or Node.js 18+
- **Memory**: 1 GiB
- **Disk**: 5 GiB
- **CPU**: 1 core
- **Network**: Outbound HTTPS (api.anthropic.com)

### Recommended for Production

- **Memory**: 2-4 GiB
- **Disk**: 10 GiB
- **CPU**: 2 cores
- **Monitoring**: Prometheus/CloudWatch
- **Logging**: Structured JSON logs

## Docker Deployment

### Dockerfile (TypeScript)

```dockerfile
FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agent

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production

# Copy application code
COPY --chown=agent:agent . .

# Switch to non-root user
USER agent

# Expose port (if needed)
EXPOSE 3000

# Start application
CMD ["node", "dist/index.js"]
```

### Dockerfile (Python)

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agent

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=agent:agent . .

# Switch to non-root user
USER agent

# Expose port (if needed)
EXPOSE 8000

# Start application
CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  agent:
    build: .
    user: "1000:1000"
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
    mem_limit: 2g
    cpus: 1.0
    pids_limit: 100
    volumes:
      - ./code:/workspace:ro
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - NODE_ENV=production
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Cloud Platform Deployment

### AWS Lambda

```typescript
// handler.ts
import { query } from '@anthropic-ai/claude-agent-sdk';

export const handler = async (event) => {
  const result = [];

  for await (const message of query({
    prompt: event.task,
    options: {
      allowedTools: ["Read", "WebSearch"],
      maxBudgetUsd: 0.5
    }
  })) {
    if (message.type === "result") {
      result.push(message.result);
    }
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ result })
  };
};
```

**Configuration**:
- Runtime: Node.js 20.x
- Memory: 2048 MB
- Timeout: 15 minutes (max)
- Environment: `ANTHROPIC_API_KEY`

### Google Cloud Run

```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: claude-agent
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project/claude-agent:latest
        resources:
          limits:
            memory: 2Gi
            cpu: 2
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: anthropic-key
              key: api-key
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name claude-agent \
  --image myregistry.azurecr.io/claude-agent:latest \
  --cpu 2 \
  --memory 2 \
  --environment-variables ANTHROPIC_API_KEY=$API_KEY \
  --secure-environment-variables ANTHROPIC_API_KEY=$API_KEY
```

## Sandbox Providers

Specialized providers for running untrusted code:

### Modal Sandbox

```python
import modal

app = modal.App("claude-agent")

@app.function(
    image=modal.Image.debian_slim().pip_install("claude-agent-sdk"),
    secrets=[modal.Secret.from_name("anthropic-api-key")],
    memory=2048,
    timeout=900
)
async def run_agent(task: str):
    from claude_agent_sdk import query, ClaudeAgentOptions

    result = []
    async for message in query(
        prompt=task,
        options=ClaudeAgentOptions(allowed_tools=["Read", "Bash"])
    ):
        if hasattr(message, "result"):
            result.append(message.result)

    return result
```

### E2B

```typescript
import { Sandbox } from '@e2b/sdk';
import { query } from '@anthropic-ai/claude-agent-sdk';

const sandbox = await Sandbox.create();

for await (const message of query({
  prompt: "Analyze this code",
  options: {
    allowedTools: ["Read", "Bash"],
    cwd: sandbox.workdir
  }
})) {
  // Process messages
}

await sandbox.close();
```

## Monitoring and Observability

### Cost Tracking

```typescript
let totalCost = 0;

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    totalCost += message.total_cost_usd;

    // Log to monitoring system
    await metrics.record({
      metric: "agent.cost",
      value: message.total_cost_usd,
      tags: { task: "code-review" }
    });
  }
}
```

### Performance Tracking

```typescript
const startTime = Date.now();

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    const duration = Date.now() - startTime;

    await metrics.record({
      metric: "agent.duration",
      value: duration,
      tags: { task: "code-review" }
    });
  }
}
```

### Error Tracking

```typescript
try {
  for await (const message of query({ prompt: "Task" })) {
    if (message.type === "result" && message.subtype !== "success") {
      await errorTracker.capture({
        error: message.subtype,
        context: { prompt: "Task" }
      });
    }
  }
} catch (error) {
  await errorTracker.capture(error);
}
```

## Scaling Strategies

### Horizontal Scaling

Run multiple agent containers:

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-agent
spec:
  replicas: 5  # Scale to 5 instances
  selector:
    matchLabels:
      app: claude-agent
  template:
    metadata:
      labels:
        app: claude-agent
    spec:
      containers:
      - name: agent
        image: claude-agent:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Auto-scaling

Scale based on queue depth or CPU:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: claude-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: claude-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Official Documentation

For the latest deployment patterns and hosting guidance:
- **Hosting Guide**: https://platform.claude.com/docs/en/agent-sdk/hosting
- **Production Best Practices**: https://platform.claude.com/docs/en/agent-sdk/overview

## Deployment Checklist

Before deploying to production:

### Security
- [ ] Running in isolated container
- [ ] Security hardening applied (see security.md)
- [ ] Credentials managed via proxy or secrets
- [ ] Resource limits set
- [ ] Network restricted

### Configuration
- [ ] Budget limits set (`maxBudgetUsd`)
- [ ] Turn limits set (`maxTurns`)
- [ ] Appropriate tools allowed/disallowed
- [ ] Model selected appropriately
- [ ] Working directory configured

### Monitoring
- [ ] Cost tracking implemented
- [ ] Performance metrics collected
- [ ] Error tracking configured
- [ ] Logging structured and centralized
- [ ] Alerts configured

### Reliability
- [ ] Error handling implemented
- [ ] Retry logic for transient failures
- [ ] Graceful degradation
- [ ] Health checks configured
- [ ] Backup/recovery plan

### Testing
- [ ] Load tested
- [ ] Security tested
- [ ] Cost tested (budget limits work)
- [ ] Error scenarios tested
- [ ] Integration tested
