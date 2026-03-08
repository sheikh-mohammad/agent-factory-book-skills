# Anti-Patterns and Common Mistakes

Common mistakes to avoid when using Claude Agent SDK.

## Configuration Anti-Patterns

### ❌ Assuming allowedTools Restricts bypassPermissions

```typescript
// This still allows ALL tools, not just Read
options: {
  allowedTools: ["Read"],
  permissionMode: "bypassPermissions"
}
```

**Why it's wrong**: `bypassPermissions` bypasses the permission system entirely. `allowedTools` is ignored.

**✅ Fix**: Use `disallowedTools` to explicitly block tools:
```typescript
options: {
  disallowedTools: ["Bash", "Write", "Edit"],
  permissionMode: "bypassPermissions"
}
```

### ❌ Not Setting Budget Limits

```typescript
// Can run indefinitely and cost unlimited money
query({ prompt: "Improve this codebase" })
```

**Why it's wrong**: No cost protection. Agent can spend hundreds of dollars.

**✅ Fix**: Always set budget limits:
```typescript
options: {
  maxBudgetUsd: 1.0
}
```

### ❌ Forgetting Streaming Input for MCP

```typescript
// Won't work - MCP requires streaming input
query({
  prompt: "Use weather tool",
  options: { mcpServers: { weather: weatherServer } }
})
```

**Why it's wrong**: MCP tools require async generator for prompt.

**✅ Fix**: Use streaming input:
```typescript
async function* generateMessages() {
  yield { role: "user", content: "Use weather tool" };
}

query({
  prompt: generateMessages(),
  options: { mcpServers: { weather: weatherServer } }
})
```

### ❌ Using Wrong Permission Mode

```typescript
// Dangerous in production
options: {
  permissionMode: "bypassPermissions"
}
// Running on developer's machine with access to everything
```

**Why it's wrong**: No safety checks. Agent can do anything.

**✅ Fix**: Use bypass only in isolated environments:
```bash
# Run in isolated container
docker run --read-only --network none agent-image
```

## Session Management Anti-Patterns

### ❌ Not Capturing Session IDs

```typescript
for await (const message of query({ prompt: "Task 1" })) {
  // Lost session ID, can't resume
}
```

**Why it's wrong**: Can't resume conversation later.

**✅ Fix**: Capture session ID:
```typescript
let sessionId: string;

for await (const message of query({ prompt: "Task 1" })) {
  if (message.type === "result") {
    sessionId = message.session_id;
  }
}
```

### ❌ Expecting Sessions to Persist Across Hosts

```typescript
// Container 1
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    await db.save({ sessionId: message.session_id });
  }
}

// Container 2 (different host)
const { sessionId } = await db.load();
for await (const message of query({
  prompt: "Continue",
  options: { resume: sessionId }  // Won't work - session file not on this host
})) {}
```

**Why it's wrong**: Sessions are local files. Don't sync across containers.

**✅ Fix**: Use hybrid pattern (ephemeral + history):
```typescript
const history = await db.loadHistory(userId);
query({
  prompt: `Previous context: ${history}\n\nNew task: ${task}`
})
```

### ❌ Not Using Fork for Experimentation

```typescript
// Overwrites original session
for await (const message of query({
  prompt: "Try different approach",
  options: { resume: originalSessionId }
})) {}
```

**Why it's wrong**: Loses original work if experiment fails.

**✅ Fix**: Use fork:
```typescript
for await (const message of query({
  prompt: "Try different approach",
  options: { resume: originalSessionId, forkSession: true }
})) {}
```

## Hook Anti-Patterns

### ❌ Using Matcher for File Paths

```typescript
// Matcher only matches tool NAME, not file paths
options: {
  canUseTool: {
    matcher: "*.env",  // This doesn't work
    hooks: [blockEnvFiles]
  }
}
```

**Why it's wrong**: Matcher matches tool names, not file paths.

**✅ Fix**: Check file path inside hook:
```typescript
options: {
  canUseTool: async (toolName, toolInput) => {
    if ((toolName === "Write" || toolName === "Edit") &&
        toolInput.file_path?.includes(".env")) {
      return { behavior: "block", message: "Cannot modify .env files" };
    }
    return { behavior: "allow" };
  }
}
```

### ❌ Not Deduplicating Parallel Tool Calls

```typescript
let totalTokens = 0;

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "message") {
    // Counts same message multiple times in parallel calls
    totalTokens += message.message.usage.input_tokens;
  }
}
```

**Why it's wrong**: Parallel tool calls emit same message multiple times.

**✅ Fix**: Deduplicate by message ID:
```typescript
const seenIds = new Set();
let totalTokens = 0;

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "message" && !seenIds.has(message.message.id)) {
    seenIds.add(message.message.id);
    totalTokens += message.message.usage.input_tokens;
  }
}
```

## Tool Anti-Patterns

### ❌ Throwing Errors in Custom Tools

```typescript
tool("fetch", "Fetch data", schema, async (args) => {
  const response = await fetch(args.url);  // Throws on network error
  return { content: [{ type: "text", text: await response.text() }] };
})
```

**Why it's wrong**: Throws break agent loop. Agent can't recover.

**✅ Fix**: Catch errors and return as text:
```typescript
tool("fetch", "Fetch data", schema, async (args) => {
  try {
    const response = await fetch(args.url);
    return { content: [{ type: "text", text: await response.text() }] };
  } catch (error) {
    return { content: [{ type: "text", text: `Error: ${error.message}` }] };
  }
})
```

### ❌ Not Handling Tool Permission Denials

```typescript
// Agent wastes turns discovering tools are blocked
options: {
  allowedTools: [],
  permissionMode: "default"
}
```

**Why it's wrong**: Agent tries tools, gets denied, tries again, wastes turns.

**✅ Fix**: Use `dontAsk` mode (TypeScript) or `disallowedTools` (Python):
```typescript
options: {
  disallowedTools: ["Bash", "Write"],
  permissionMode: "dontAsk"  // Fail fast
}
```

### ❌ Poor Tool Descriptions

```typescript
// Vague description
tool("process", "Process data", schema, handler)
```

**Why it's wrong**: Agent doesn't know when to use tool.

**✅ Fix**: Clear, specific description:
```typescript
tool(
  "process_invoice",
  "Extract line items and totals from invoice PDF",
  schema,
  handler
)
```

## Security Anti-Patterns

### ❌ Mounting Sensitive Directories

```bash
# DANGEROUS
docker run -v ~/.aws:/root/.aws agent-image
docker run -v ~/.ssh:/root/.ssh agent-image
docker run -v .env:/app/.env agent-image
```

**Why it's wrong**: Agent can read credentials.

**✅ Fix**: Use proxy pattern for credentials:
```bash
# Agent uses proxy
docker run -e ANTHROPIC_BASE_URL=http://proxy:8080 agent-image
```

### ❌ Running as Root

```bash
# Runs as root by default
docker run agent-image
```

**Why it's wrong**: If agent escapes container, has root access.

**✅ Fix**: Run as non-root user:
```bash
docker run --user 1000:1000 agent-image
```

### ❌ Trusting allowedTools for Security

```typescript
// This is NOT a security boundary
options: {
  allowedTools: ["Read"],
  permissionMode: "bypassPermissions"
}
// Agent can still access filesystem, environment, etc.
```

**Why it's wrong**: `allowedTools` is convenience, not security.

**✅ Fix**: Use proper isolation:
```bash
docker run \
  --cap-drop ALL \
  --read-only \
  --network none \
  agent-image
```

### ❌ No Resource Limits

```typescript
// Can consume unlimited resources
query({ prompt: "Improve this codebase" })
```

**Why it's wrong**: Agent can exhaust memory, CPU, disk.

**✅ Fix**: Set resource limits:
```bash
docker run \
  --memory 2g \
  --cpus 1.0 \
  --pids-limit 100 \
  agent-image
```

## Workflow Anti-Patterns

### ❌ Not Using Subagents for Complex Tasks

```typescript
// Main agent does everything
query({
  prompt: "Do security review, performance review, and code quality review"
})
```

**Why it's wrong**: Context pollution. Main agent loses focus.

**✅ Fix**: Use specialized subagents:
```typescript
options: {
  agents: {
    "security": { description: "Security review", prompt: "Find vulnerabilities", tools: ["Read"] },
    "performance": { description: "Performance review", prompt: "Find bottlenecks", tools: ["Read", "Bash"] },
    "quality": { description: "Quality review", prompt: "Check code quality", tools: ["Read"] }
  }
}
```

### ❌ Generic Subagent Descriptions

```typescript
agents: {
  "helper": {
    description: "Helper agent",
    prompt: "Help with stuff",
    tools: ["Read", "Write", "Edit", "Bash"]
  }
}
```

**Why it's wrong**: Main agent doesn't know when to use subagent.

**✅ Fix**: Specific descriptions:
```typescript
agents: {
  "database-expert": {
    description: "Database schema design and optimization specialist",
    prompt: "Design optimal database schema",
    tools: ["Read", "Write"]
  }
}
```

### ❌ Giving Subagents Unnecessary Tools

```typescript
agents: {
  "analyzer": {
    description: "Code analyzer",
    prompt: "Analyze code",
    tools: ["Read", "Write", "Edit", "Bash"]  // Too many
  }
}
```

**Why it's wrong**: Analyzer doesn't need write access. Security risk.

**✅ Fix**: Minimal tools:
```typescript
agents: {
  "analyzer": {
    description: "Code analyzer",
    prompt: "Analyze code",
    tools: ["Read", "Grep"]  // Read-only
  }
}
```

## Error Handling Anti-Patterns

### ❌ Not Checking Result Subtype

```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    console.log(message.result);  // May be undefined
  }
}
```

**Why it's wrong**: `result` is undefined if subtype is not "success".

**✅ Fix**: Check subtype:
```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    if (message.subtype === "success") {
      console.log(message.result);
    } else {
      console.error(`Error: ${message.subtype}`);
    }
  }
}
```

### ❌ No Retry Logic

```typescript
// Fails permanently on transient errors
for await (const message of query({ prompt: "Task" })) {}
```

**Why it's wrong**: Network blips cause permanent failures.

**✅ Fix**: Implement retry with backoff:
```typescript
async function runWithRetry(prompt: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      for await (const message of query({ prompt })) {
        if (message.type === "result" && message.subtype === "success") {
          return message.result;
        }
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * Math.pow(2, i));
    }
  }
}
```

### ❌ Ignoring Budget/Turn Limits

```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    // Ignores error_max_budget_usd and error_max_turns
    console.log(message.result);
  }
}
```

**Why it's wrong**: Doesn't handle limit errors. User doesn't know why it failed.

**✅ Fix**: Handle all error subtypes:
```typescript
if (message.subtype === "error_max_budget_usd") {
  console.log("Hit budget limit. Increase maxBudgetUsd or optimize task.");
} else if (message.subtype === "error_max_turns") {
  console.log("Hit turn limit. Increase maxTurns or simplify task.");
}
```

## Cost Anti-Patterns

### ❌ Using High Effort for Simple Tasks

```typescript
// Wastes tokens
options: {
  effort: "max",
  prompt: "List files in directory"
}
```

**Why it's wrong**: Pays for unnecessary thinking.

**✅ Fix**: Use appropriate effort:
```typescript
options: {
  effort: "low",
  prompt: "List files in directory"
}
```

### ❌ Not Tracking Costs

```typescript
// No cost visibility
for await (const message of query({ prompt: "Task" })) {}
```

**Why it's wrong**: Can't optimize or budget.

**✅ Fix**: Track and log costs:
```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    console.log(`Cost: $${message.total_cost_usd}`);
    await metrics.record("agent.cost", message.total_cost_usd);
  }
}
```

### ❌ Using Opus for Everything

```typescript
// Expensive
options: {
  model: "opus",
  prompt: "Format this JSON"
}
```

**Why it's wrong**: Opus is most expensive. Overkill for simple tasks.

**✅ Fix**: Use appropriate model:
```typescript
// Simple tasks - Haiku
options: { model: "haiku", prompt: "Format JSON" }

// Balanced - Sonnet
options: { model: "sonnet", prompt: "Review code" }

// Complex - Opus
options: { model: "opus", prompt: "Design architecture" }
```

## Summary

**Top 10 Mistakes to Avoid**:
1. Not setting budget limits
2. Trusting `allowedTools` for security
3. Throwing errors in custom tools
4. Not capturing session IDs
5. Running as root in containers
6. Not checking result subtype
7. Mounting sensitive directories
8. Not using subagents for complex tasks
9. Forgetting streaming input for MCP
10. Not tracking costs
