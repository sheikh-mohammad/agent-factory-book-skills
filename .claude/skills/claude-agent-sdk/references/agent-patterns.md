# Agent Patterns Reference

Common patterns for building agents with Claude Agent SDK.

## Pattern Categories

### 1. Simple Query Pattern

**Use when**: One-shot task, no state needed.

**Characteristics**:
- Single query
- No session management
- Immediate result

**Example**:
```typescript
for await (const message of query({
  prompt: "Analyze this file",
  options: { allowedTools: ["Read"] }
})) {}
```

**Best for**:
- File analysis
- Code review
- Documentation generation
- One-time tasks

---

### 2. Session-Based Pattern

**Use when**: Multi-turn conversation needed.

**Characteristics**:
- Multiple queries
- Session continuation
- Context preservation

**Example**:
```typescript
// First query
for await (const message of query({ prompt: "Task 1" })) {}

// Continue
for await (const message of query({
  prompt: "Task 2",
  options: { continue: true }
})) {}
```

**Best for**:
- Interactive assistants
- Chatbots
- Iterative development
- Multi-step workflows

---

### 3. Subagent Orchestration Pattern

**Use when**: Complex task needs specialized expertise.

**Characteristics**:
- Main agent coordinates
- Subagents specialize
- Parallel execution possible

**Example**:
```typescript
options: {
  agents: {
    "expert-1": { description: "...", prompt: "...", tools: [...] },
    "expert-2": { description: "...", prompt: "...", tools: [...] }
  }
}
```

**Best for**:
- Code review (security, performance, quality)
- Multi-domain analysis
- Complex workflows
- Parallel processing

---

### 4. MCP Integration Pattern

**Use when**: Need external tools or APIs.

**Characteristics**:
- Custom tools via MCP
- External API integration
- Streaming input required

**Example**:
```typescript
const server = createSdkMcpServer({
  name: "tools",
  tools: [customTool]
});

async function* generateMessages() {
  yield { role: "user", content: "Use custom tool" };
}

query({
  prompt: generateMessages(),
  options: { mcpServers: { tools: server } }
})
```

**Best for**:
- Database queries
- External API calls
- Custom business logic
- Domain-specific tools

---

### 5. Production Service Pattern

**Use when**: Long-running, high-availability service.

**Characteristics**:
- HTTP server (Express/FastAPI)
- Error handling
- Monitoring
- Security hardening

**Example**:
```typescript
app.post('/agent', async (req, res) => {
  for await (const message of query({
    prompt: req.body.prompt,
    options: { maxBudgetUsd: 0.5 }
  })) {
    // Handle messages
  }
});
```

**Best for**:
- Customer support
- API services
- Production applications
- Multi-user systems

---

## Deployment Patterns

### Ephemeral Pattern

```
Request → Spin up container → Run agent → Return result → Destroy
```

**Use for**: Bug fixes, translations, one-shot tasks

**Pros**: Clean state, cost-efficient
**Cons**: Cold start latency

---

### Long-Running Pattern

```
Container starts → Handles requests → Maintains sessions → Runs indefinitely
```

**Use for**: Chatbots, assistants, high-frequency tasks

**Pros**: No cold starts, session continuity
**Cons**: Higher baseline cost

---

### Hybrid Pattern

```
Request → Spin up → Load history → Run → Save history → Destroy
```

**Use for**: Cost-optimized chatbots, project managers

**Pros**: Session continuity without persistent containers
**Cons**: Cold start + history loading latency

---

## Security Patterns

### Isolation Pattern

```
Agent runs in isolated container with:
- Dropped capabilities
- Read-only filesystem
- Network restrictions
- Resource limits
```

**Always use in production**

---

### Proxy Pattern

```
Agent → Proxy (injects credentials) → External API
```

**Use for**: Credential management, API key injection

---

### Tool Restriction Pattern

```typescript
options: {
  allowedTools: ["Read", "Grep"],  // Safe tools
  disallowedTools: ["Bash", "Write"]  // Dangerous tools
}
```

**Use for**: Limiting agent capabilities

---

## Error Handling Patterns

### Retry Pattern

```typescript
async function runWithRetry(prompt: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await runAgent(prompt);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * Math.pow(2, i));
    }
  }
}
```

---

### Graceful Degradation Pattern

```typescript
if (message.subtype === "error_max_budget_usd") {
  // Fall back to simpler approach
  return await runSimpleAgent(prompt);
}
```

---

### Circuit Breaker Pattern

```typescript
if (failureCount > threshold) {
  return cachedResponse;  // Stop calling agent
}
```

---

## Cost Optimization Patterns

### Budget Limit Pattern

```typescript
options: {
  maxBudgetUsd: 0.5  // Hard limit
}
```

---

### Model Selection Pattern

```typescript
// Simple tasks - Haiku
options: { model: "haiku" }

// Complex tasks - Opus
options: { model: "opus" }
```

---

### Effort Control Pattern

```typescript
// Simple tasks
options: { effort: "low" }

// Complex reasoning
options: { effort: "high" }
```

---

## Monitoring Patterns

### Cost Tracking Pattern

```typescript
for await (const message of query({ prompt })) {
  if (message.type === "result") {
    await metrics.record("cost", message.total_cost_usd);
  }
}
```

---

### Performance Tracking Pattern

```typescript
const startTime = Date.now();
// Run agent
const duration = Date.now() - startTime;
await metrics.record("duration", duration);
```

---

### Audit Logging Pattern

```typescript
options: {
  beforeToolUse: async (tool, input) => {
    await auditLog.write({ tool, input, timestamp: Date.now() });
  }
}
```

---

## Pattern Selection Guide

| Use Case | Pattern | Deployment |
|----------|---------|------------|
| One-shot task | Simple Query | Ephemeral |
| Chatbot | Session-Based | Long-Running or Hybrid |
| Code review | Subagent Orchestration | Ephemeral |
| External APIs | MCP Integration | Any |
| Production service | Production Service | Long-Running |
| Cost-sensitive | Budget Limit + Model Selection | Ephemeral |
| Security-critical | Isolation + Proxy | Isolated container |
