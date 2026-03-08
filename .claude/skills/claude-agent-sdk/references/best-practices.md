# Best Practices

Recommended patterns and approaches for Claude Agent SDK.

## Configuration Best Practices

### 1. Always Set Budget Limits

```typescript
// ✅ Good - Prevents runaway costs
options: {
  maxBudgetUsd: 1.0
}

// ❌ Bad - No cost protection
options: {}
```

### 2. Use Appropriate Permission Modes

```typescript
// Development - Interactive approval
options: {
  permissionMode: "default"
}

// Trusted workflows - Auto-approve edits
options: {
  permissionMode: "acceptEdits",
  allowedTools: ["Read", "Edit", "Grep"]
}

// CI/CD - Bypass with isolation
options: {
  permissionMode: "bypassPermissions",
  // MUST run in isolated container
}
```

### 3. Pre-approve Safe Tools

```typescript
// ✅ Good - Pre-approve read-only tools
options: {
  allowedTools: ["Read", "Grep", "Glob", "WebSearch"]
}

// ❌ Bad - Prompting for every tool slows down agent
options: {
  allowedTools: []
}
```

### 4. Block Dangerous Tools When Not Needed

```typescript
// ✅ Good - Block unnecessary dangerous tools
options: {
  allowedTools: ["Read", "Grep"],
  disallowedTools: ["Bash", "Write"]
}
```

### 5. Use Appropriate Effort Levels

```typescript
// Simple tasks - Low effort
options: {
  effort: "low",
  prompt: "List files in directory"
}

// Complex reasoning - High effort
options: {
  effort: "high",
  prompt: "Design system architecture"
}
```

## Tool Usage Best Practices

### 1. Return Errors as Text, Don't Throw

```typescript
// ✅ Good
async (args) => {
  try {
    const result = await fetch(args.url);
    return { content: [{ type: "text", text: await result.text() }] };
  } catch (error) {
    return { content: [{ type: "text", text: `Error: ${error.message}` }] };
  }
}

// ❌ Bad - Throws error
async (args) => {
  const result = await fetch(args.url);  // Throws on network error
  return { content: [{ type: "text", text: await result.text() }] };
}
```

### 2. Use Descriptive Tool Schemas

```typescript
// ✅ Good - Clear descriptions
{
  latitude: z.number().describe("Latitude coordinate (-90 to 90)"),
  longitude: z.number().describe("Longitude coordinate (-180 to 180)"),
  units: z.enum(["celsius", "fahrenheit"]).describe("Temperature units")
}

// ❌ Bad - No descriptions
{
  lat: z.number(),
  lon: z.number(),
  units: z.string()
}
```

### 3. Use Streaming Input for MCP

```typescript
// ✅ Good - Streaming input
async function* generateMessages() {
  yield { role: "user", content: "Use weather tool" };
}

query({
  prompt: generateMessages(),
  options: { mcpServers: { weather: weatherServer } }
})

// ❌ Bad - Static string (won't work with MCP)
query({
  prompt: "Use weather tool",
  options: { mcpServers: { weather: weatherServer } }
})
```

## Session Management Best Practices

### 1. Always Capture Session IDs

```typescript
// ✅ Good
let sessionId: string;

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    sessionId = message.session_id;
    await db.save({ userId, sessionId });
  }
}

// ❌ Bad - Lost session ID
for await (const message of query({ prompt: "Task" })) {
  // Can't resume later
}
```

### 2. Use Continue for Same Process

```typescript
// ✅ Good - Simple continuation
for await (const message of query({ prompt: "Task 1" })) {}
for await (const message of query({
  prompt: "Task 2",
  options: { continue: true }
})) {}

// ❌ Bad - Unnecessary session ID tracking
let sessionId;
for await (const message of query({ prompt: "Task 1" })) {
  if (message.type === "result") sessionId = message.session_id;
}
for await (const message of query({
  prompt: "Task 2",
  options: { resume: sessionId }
})) {}
```

### 3. Use Fork for Experimentation

```typescript
// ✅ Good - Preserve original
for await (const message of query({
  prompt: "Try alternative approach",
  options: { resume: originalSessionId, forkSession: true }
})) {}

// ❌ Bad - Overwrites original
for await (const message of query({
  prompt: "Try alternative approach",
  options: { resume: originalSessionId }
})) {}
```

## Multi-Agent Best Practices

### 1. Use Subagents for Complex Tasks

```typescript
// ✅ Good - Delegate to specialists
options: {
  agents: {
    "security-expert": {
      description: "Security vulnerability analysis",
      prompt: "Find security issues",
      tools: ["Read", "Grep"]
    }
  }
}

// ❌ Bad - Main agent does everything
options: {
  prompt: "Do security review, performance review, and code quality review"
}
```

### 2. Specialize Subagents

```typescript
// ✅ Good - Clear specialization
agents: {
  "backend-dev": {
    description: "Backend API development",
    prompt: "Implement backend logic",
    tools: ["Read", "Write", "Edit", "Bash"]
  },
  "frontend-dev": {
    description: "Frontend UI development",
    prompt: "Implement UI components",
    tools: ["Read", "Write", "Edit"]
  }
}

// ❌ Bad - Generic subagents
agents: {
  "helper-1": {
    description: "Helper agent",
    prompt: "Help with stuff",
    tools: ["Read", "Write", "Edit", "Bash"]
  }
}
```

### 3. Restrict Subagent Tools

```typescript
// ✅ Good - Minimal tools needed
agents: {
  "analyzer": {
    description: "Code analyzer",
    prompt: "Analyze code",
    tools: ["Read", "Grep"]  // Read-only
  }
}

// ❌ Bad - Unnecessary tools
agents: {
  "analyzer": {
    description: "Code analyzer",
    prompt: "Analyze code",
    tools: ["Read", "Write", "Edit", "Bash"]  // Too many
  }
}
```

## Security Best Practices

### 1. Always Use Isolation in Production

```bash
# ✅ Good - Isolated container
docker run \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --read-only \
  --user 1000:1000 \
  agent-image

# ❌ Bad - No isolation
node agent.js
```

### 2. Use Proxy Pattern for Credentials

```typescript
// ✅ Good - Proxy injects credentials
options: {
  baseURL: "http://proxy:8080"  // Proxy has credentials
}

// ❌ Bad - Credentials in container
options: {
  apiKey: process.env.ANTHROPIC_API_KEY  // Agent can read this
}
```

### 3. Mount Code Read-Only

```bash
# ✅ Good - Read-only mount
docker run -v /code:/workspace:ro agent-image

# ❌ Bad - Writable mount
docker run -v /code:/workspace agent-image
```

## Cost Optimization Best Practices

### 1. Set Budget Limits

```typescript
// ✅ Good - Prevents overspending
options: {
  maxBudgetUsd: 0.50
}
```

### 2. Use Appropriate Models

```typescript
// Simple tasks - Use Haiku
options: {
  model: "haiku",
  prompt: "List files"
}

// Complex reasoning - Use Opus
options: {
  model: "opus",
  prompt: "Design system architecture"
}

// Balanced - Use Sonnet (default)
options: {
  model: "sonnet",
  prompt: "Review code"
}
```

### 3. Use Lower Effort for Simple Tasks

```typescript
// ✅ Good - Low effort for simple tasks
options: {
  effort: "low",
  prompt: "Format this JSON"
}

// ❌ Bad - Wasting tokens on simple task
options: {
  effort: "max",
  prompt: "Format this JSON"
}
```

### 4. Limit Tools in Context

```typescript
// ✅ Good - Only needed tools
options: {
  allowedTools: ["Read", "Edit"]
}

// ❌ Bad - All tools (higher context cost)
options: {
  allowedTools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "WebSearch", "WebFetch"]
}
```

### 5. Track Costs

```typescript
// ✅ Good - Monitor costs
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    console.log(`Cost: $${message.total_cost_usd}`);
    await metrics.record("agent.cost", message.total_cost_usd);
  }
}
```

## Error Handling Best Practices

### 1. Check Result Subtype

```typescript
// ✅ Good - Handle all subtypes
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    switch (message.subtype) {
      case "success":
        console.log(message.result);
        break;
      case "error_max_turns":
        console.log("Hit turn limit, resuming with higher limit");
        break;
      case "error_max_budget_usd":
        console.log("Hit budget limit");
        break;
      default:
        console.error(`Error: ${message.subtype}`);
    }
  }
}

// ❌ Bad - Assumes success
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    console.log(message.result);  // May be undefined
  }
}
```

### 2. Set Reasonable Limits

```typescript
// ✅ Good - Reasonable limits
options: {
  maxTurns: 50,
  maxBudgetUsd: 1.0
}

// ❌ Bad - No limits (can run forever)
options: {}
```

### 3. Implement Retry Logic

```typescript
// ✅ Good - Retry on transient errors
async function runAgentWithRetry(prompt: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      for await (const message of query({ prompt })) {
        if (message.type === "result") {
          if (message.subtype === "success") {
            return message.result;
          }
        }
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * Math.pow(2, i));  // Exponential backoff
    }
  }
}
```

## Monitoring Best Practices

### 1. Log All Tool Calls

```typescript
options: {
  beforeToolUse: async (toolName, toolInput) => {
    await logger.info("Tool called", { tool: toolName, input: toolInput });
  }
}
```

### 2. Track Performance Metrics

```typescript
const startTime = Date.now();

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    await metrics.record({
      duration: Date.now() - startTime,
      turns: message.turn_count,
      cost: message.total_cost_usd
    });
  }
}
```

### 3. Alert on Anomalies

```typescript
if (message.total_cost_usd > 5.0) {
  await alert.send("High cost detected", { cost: message.total_cost_usd });
}

if (message.turn_count > 100) {
  await alert.send("High turn count", { turns: message.turn_count });
}
```

## Testing Best Practices

### 1. Unit Test Custom Tools

```typescript
// ✅ Good - Test tools in isolation
test("weather tool returns temperature", async () => {
  const result = await weatherTool.handler({ latitude: 37.7, longitude: -122.4 });
  expect(result.content[0].text).toContain("°F");
});
```

### 2. Integration Test Agent Behavior

```typescript
// ✅ Good - Test complete workflows
test("agent fixes bugs", async () => {
  for await (const message of query({
    prompt: "Fix bug in utils.ts",
    options: { allowedTools: ["Read", "Edit"] }
  })) {
    if (message.type === "result") {
      expect(message.subtype).toBe("success");
    }
  }
});
```

### 3. Test Error Scenarios

```typescript
// ✅ Good - Test limits
test("respects budget limit", async () => {
  for await (const message of query({
    prompt: "Complex task",
    options: { maxBudgetUsd: 0.01 }
  })) {
    if (message.type === "result") {
      expect(message.subtype).toBe("error_max_budget_usd");
    }
  }
});
```

## Deployment Best Practices

### 1. Use Appropriate Hosting Pattern

- **Ephemeral**: One-shot tasks (bug fixes, translations)
- **Long-running**: High-frequency chatbots, assistants
- **Hybrid**: Cost-optimized chatbots with history

### 2. Implement Health Checks

```typescript
app.get("/health", (req, res) => {
  res.json({ status: "healthy", timestamp: Date.now() });
});
```

### 3. Configure Auto-scaling

```yaml
# Scale based on CPU/memory
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

### 4. Use Structured Logging

```typescript
logger.info("Agent started", {
  userId,
  task: prompt,
  timestamp: Date.now()
});
```

## Summary

**Key Takeaways**:
1. Always set budget limits in production
2. Use appropriate permission modes for context
3. Pre-approve safe tools, block dangerous ones
4. Return errors as text in custom tools
5. Always capture session IDs for resumption
6. Use subagents for complex tasks
7. Run in isolated containers in production
8. Track costs and performance metrics
9. Test error scenarios and limits
10. Choose appropriate hosting pattern

## Official Documentation

For the latest best practices and updates, refer to:
- **Agent SDK Best Practices**: https://platform.claude.com/docs/en/agent-sdk/overview
- **Security Guidelines**: https://platform.claude.com/docs/en/agent-sdk/hosting
