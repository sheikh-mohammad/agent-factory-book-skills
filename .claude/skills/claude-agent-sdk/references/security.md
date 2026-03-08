# Security Best Practices

Comprehensive security guide for deploying Claude Agent SDK in production.

## Security Model

**Critical Understanding**: The Agent SDK is NOT a security boundary. It's a development tool that executes code and commands. Security must come from proper isolation.

### Built-in Security Features

The SDK provides convenience features, not security guarantees:

1. **Permissions system** - Allow/block/prompt per tool (convenience, not security)
2. **Static analysis** - Basic bash command analysis (helpful, not comprehensive)
3. **Web search summarization** - Reduces prompt injection risk (helpful, not foolproof)
4. **Sandbox mode** - Optional bash sandboxing (limited protection)

**⚠️ Do NOT rely on these for security**. Use proper isolation instead.

## Security Principles

### 1. Isolation

Run agents in isolated environments with restricted capabilities.

**Isolation Technologies:**

| Technology | Isolation Strength | Performance Overhead | Complexity |
|------------|-------------------|---------------------|------------|
| Sandbox runtime | Good | Very low | Low |
| Docker containers | Setup dependent | Low | Medium |
| gVisor | Excellent | Medium/High | Medium |
| VMs (Firecracker) | Excellent | High | Medium/High |

### 2. Least Privilege

Only grant necessary tools and filesystem access.

**Tool Restrictions:**
```typescript
options: {
  allowedTools: ["Read", "Grep", "Glob"],  // Read-only
  disallowedTools: ["Bash", "Write", "Edit"]  // Block dangerous
}
```

**Filesystem Restrictions:**
```bash
# Mount code read-only
docker run -v /path/to/code:/workspace:ro agent-image

# Limit writable space
docker run --tmpfs /tmp:rw,noexec,nosuid,size=100m agent-image
```

### 3. Defense in Depth

Layer multiple security controls.

**Example layers:**
1. Container isolation (Docker)
2. Capability dropping (`--cap-drop ALL`)
3. Read-only filesystem (`--read-only`)
4. Network isolation (`--network none`)
5. Resource limits (`--memory 2g`)
6. Non-root user (`--user 1000:1000`)

## Docker Security Hardening

### Minimal Secure Container

```dockerfile
FROM node:20-slim

# Create non-root user
RUN useradd -m -u 1000 agent

# Install Claude Agent SDK
WORKDIR /app
COPY package*.json ./
RUN npm ci --production

# Copy application code
COPY --chown=agent:agent . .

# Switch to non-root user
USER agent

CMD ["node", "agent.js"]
```

### Secure Docker Run

```bash
docker run \
  # Drop all capabilities
  --cap-drop ALL \
  # Prevent privilege escalation
  --security-opt no-new-privileges \
  # Read-only root filesystem
  --read-only \
  # Writable tmp (no exec)
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  # No network access (if not needed)
  --network none \
  # Memory limit
  --memory 2g \
  # CPU limit
  --cpus 1.0 \
  # PID limit
  --pids-limit 100 \
  # Run as non-root
  --user 1000:1000 \
  # Mount code read-only
  -v /path/to/code:/workspace:ro \
  # Environment variables
  -e ANTHROPIC_API_KEY=sk-... \
  agent-image
```

### Docker Compose Example

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
```

## Credential Management

### ❌ Never Mount Credentials

```bash
# DANGEROUS - Don't do this
docker run -v ~/.aws:/root/.aws agent-image
docker run -v ~/.ssh:/root/.ssh agent-image
docker run -v .env:/app/.env agent-image
```

### ✅ Use Proxy Pattern

Run a proxy outside the agent boundary that injects credentials:

```
┌─────────────────────────────────────┐
│  Isolated Agent Container           │
│  - No credentials                   │
│  - Sends requests to proxy          │
│  - ANTHROPIC_BASE_URL=proxy:8080    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Credential Proxy (outside boundary)│
│  - Has API keys                     │
│  - Injects credentials              │
│  - Forwards to real API             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Anthropic API                      │
└─────────────────────────────────────┘
```

**Proxy Implementation:**

```typescript
// proxy.ts (runs outside agent container)
import express from 'express';
import { Anthropic } from '@anthropic-ai/sdk';

const app = express();
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

app.post('/v1/messages', async (req, res) => {
  // Inject credentials and forward
  const response = await client.messages.create(req.body);
  res.json(response);
});

app.listen(8080);
```

```bash
# Agent container uses proxy
docker run \
  -e ANTHROPIC_BASE_URL=http://proxy:8080 \
  --network agent-network \
  agent-image
```

### Environment Variable Injection

For simple cases, inject via environment:

```bash
docker run \
  -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
  agent-image
```

**⚠️ Caution**: Agent can read environment variables. Use proxy pattern for sensitive credentials.

## Filesystem Security

### Read-Only Mounts

```bash
# Code is read-only
docker run -v /path/to/code:/workspace:ro agent-image
```

### Exclude Sensitive Files

```bash
# Don't mount these
.env
.git-credentials
~/.aws/credentials
~/.ssh/
secrets/
*.key
*.pem
```

### Temporary Writable Space

```bash
# Agent can write to /tmp only
docker run \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  agent-image
```

## Network Security

### No Network Access

If agent doesn't need network:

```bash
docker run --network none agent-image
```

### Restricted Network

If agent needs network, restrict it:

```bash
# Create restricted network
docker network create --internal agent-network

# Run agent in restricted network
docker run --network agent-network agent-image
```

### Egress Filtering

Use firewall rules to limit outbound connections:

```bash
# Allow only Anthropic API
iptables -A OUTPUT -d api.anthropic.com -j ACCEPT
iptables -A OUTPUT -j DROP
```

## Tool Security

### Restrict Dangerous Tools

```typescript
options: {
  disallowedTools: [
    "Bash",  // Can execute arbitrary commands
    "Write",  // Can overwrite files
    "Edit"   // Can modify files
  ]
}
```

### Hook-Based Validation

Validate tool calls before execution:

```typescript
options: {
  canUseTool: async (toolName, toolInput) => {
    // Block dangerous bash commands
    if (toolName === "Bash") {
      const dangerous = ["rm -rf", "dd if=", ":(){ :|:& };:", "mkfs"];
      if (dangerous.some(cmd => toolInput.command.includes(cmd))) {
        return { behavior: "block", message: "Dangerous command blocked" };
      }
    }

    // Block writes to sensitive paths
    if (toolName === "Write" || toolName === "Edit") {
      const sensitive = [".env", "credentials", ".ssh", ".aws"];
      if (sensitive.some(path => toolInput.file_path.includes(path))) {
        return { behavior: "block", message: "Sensitive file blocked" };
      }
    }

    return { behavior: "allow" };
  }
}
```

## Resource Limits

### Memory Limits

```bash
docker run --memory 2g --memory-swap 2g agent-image
```

### CPU Limits

```bash
docker run --cpus 1.0 agent-image
```

### Process Limits

```bash
docker run --pids-limit 100 agent-image
```

### Disk Limits

```bash
docker run --tmpfs /tmp:size=100m agent-image
```

### Time Limits

```typescript
options: {
  maxTurns: 50,  // Limit agent iterations
  maxBudgetUsd: 1.0  // Limit spending
}
```

## Monitoring and Auditing

### Log All Tool Calls

```typescript
options: {
  beforeToolUse: async (toolName, toolInput) => {
    await auditLog.write({
      timestamp: Date.now(),
      tool: toolName,
      input: toolInput,
      user: userId
    });
  }
}
```

### Monitor Resource Usage

```typescript
// Track costs
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    await metrics.record({
      cost: message.total_cost_usd,
      turns: message.turn_count,
      duration: message.duration_ms
    });
  }
}
```

### Alert on Anomalies

```typescript
if (message.total_cost_usd > 5.0) {
  await alert.send("High cost detected");
}

if (message.turn_count > 100) {
  await alert.send("High turn count detected");
}
```

## Security Checklist

Before deploying to production:

### Isolation
- [ ] Running in isolated container/VM
- [ ] Capabilities dropped (`--cap-drop ALL`)
- [ ] No new privileges (`--security-opt no-new-privileges`)
- [ ] Read-only filesystem where possible
- [ ] Network isolated or restricted

### Credentials
- [ ] No credential files mounted
- [ ] Using proxy pattern for sensitive APIs
- [ ] Environment variables minimized
- [ ] Secrets rotated regularly

### Filesystem
- [ ] Code mounted read-only
- [ ] Sensitive files excluded
- [ ] Temporary space limited
- [ ] No write access to host

### Tools
- [ ] Dangerous tools blocked
- [ ] Tool validation hooks implemented
- [ ] Bash commands validated
- [ ] File paths validated

### Resources
- [ ] Memory limits set
- [ ] CPU limits set
- [ ] Process limits set
- [ ] Budget limits set (`maxBudgetUsd`)
- [ ] Turn limits set (`maxTurns`)

### Monitoring
- [ ] Tool calls logged
- [ ] Costs tracked
- [ ] Anomaly alerts configured
- [ ] Audit trail maintained

## Official Documentation

For the latest security guidance and best practices:
- **Hosting Security**: https://platform.claude.com/docs/en/agent-sdk/hosting
- **Agent SDK Overview**: https://platform.claude.com/docs/en/agent-sdk/overview

## Security Anti-Patterns

### ❌ Trusting `allowedTools` for Security

```typescript
// This is NOT a security boundary
options: {
  allowedTools: ["Read"],
  permissionMode: "bypassPermissions"
}
// Agent can still access filesystem, environment, etc.
```

### ❌ Running as Root

```bash
# DANGEROUS
docker run agent-image  # Runs as root by default
```

### ❌ Mounting Sensitive Directories

```bash
# DANGEROUS
docker run -v ~/.aws:/root/.aws agent-image
docker run -v ~/.ssh:/root/.ssh agent-image
```

### ❌ No Resource Limits

```typescript
// Can run forever and cost unlimited money
query({ prompt: "Improve this codebase" })
```

### ❌ Assuming Sandbox is Secure

```typescript
// Sandbox mode is NOT a security boundary
options: { sandboxMode: true }
// Still need proper isolation
```

## Further Reading

- Docker Security Best Practices: https://docs.docker.com/engine/security/
- gVisor: https://gvisor.dev/
- Firecracker: https://firecracker-microvm.github.io/
