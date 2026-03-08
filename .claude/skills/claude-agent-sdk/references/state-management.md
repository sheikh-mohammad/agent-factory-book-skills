# State Management

Guide to managing conversational state and sessions in Claude Agent SDK.

## What is a Session?

A session is the conversation history accumulated during agent work. Sessions persist to disk automatically in `.claude/sessions/`.

**Session includes:**
- All messages (user prompts, Claude responses, tool calls, tool results)
- Working directory context
- Configuration used

## Three Ways to Continue

### 1. Continue (Most Recent Session)

Resume the most recent session in the current working directory.

**TypeScript:**
```typescript
// First query
for await (const message of query({
  prompt: "Analyze the auth module"
})) {}

// Continue from most recent
for await (const message of query({
  prompt: "Now refactor it to use OAuth2",
  options: { continue: true }
})) {}
```

**Python:**
```python
# First query
async for message in query(prompt="Analyze the auth module"):
    pass

# Continue from most recent
async for message in query(
    prompt="Now refactor it to use OAuth2",
    options=ClaudeAgentOptions(continue_session=True)
):
    pass
```

**Use when**: Multi-turn conversation in same process.

### 2. Resume (Specific Session by ID)

Resume a specific session by its ID.

**TypeScript:**
```typescript
let sessionId: string;

// First query - capture session ID
for await (const message of query({
  prompt: "Analyze code"
})) {
  if (message.type === "result") {
    sessionId = message.session_id;
  }
}

// Resume later (different process, different time)
for await (const message of query({
  prompt: "Continue analysis",
  options: { resume: sessionId }
})) {}
```

**Python:**
```python
session_id = None

# First query - capture session ID
async for message in query(prompt="Analyze code"):
    if message.type == "result":
        session_id = message.session_id

# Resume later
async for message in query(
    prompt="Continue analysis",
    options=ClaudeAgentOptions(resume=session_id)
):
    pass
```

**Use when**: Multi-user apps, resuming after restart, long-running workflows.

### 3. Fork (Branch to Explore Alternatives)

Create a new branch from an existing session to explore alternatives without losing the original.

**TypeScript:**
```typescript
// Original session
for await (const message of query({
  prompt: "Implement authentication"
})) {
  if (message.type === "result") {
    sessionId = message.session_id;
  }
}

// Fork to try OAuth2
for await (const message of query({
  prompt: "Try OAuth2 instead",
  options: { resume: sessionId, forkSession: true }
})) {}

// Fork to try JWT
for await (const message of query({
  prompt: "Try JWT instead",
  options: { resume: sessionId, forkSession: true }
})) {}
```

**Python:**
```python
# Original session
async for message in query(prompt="Implement authentication"):
    if message.type == "result":
        session_id = message.session_id

# Fork to try OAuth2
async for message in query(
    prompt="Try OAuth2 instead",
    options=ClaudeAgentOptions(resume=session_id, fork_session=True)
):
    pass
```

**Use when**: Exploring different approaches, A/B testing implementations.

## Python: ClaudeSDKClient for Automatic Session Management

Python provides `ClaudeSDKClient` for automatic session continuation:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(ClaudeAgentOptions()) as client:
    # First task
    await client.query("Analyze the auth module")
    async for message in client.receive_response():
        if message.type == "text":
            print(message.text)

    # Automatically continues same session
    await client.query("Now refactor it")
    async for message in client.receive_response():
        if message.type == "text":
            print(message.text)

    # Still same session
    await client.query("Add tests")
    async for message in client.receive_response():
        if message.type == "text":
            print(message.text)
```

**Benefits:**
- No manual session ID tracking
- Automatic continuation between queries
- Clean context manager pattern

## Session Storage

Sessions are stored in `.claude/sessions/` by default.

**Session file structure:**
```
.claude/sessions/
├── session-abc123.json
├── session-def456.json
└── session-ghi789.json
```

**Each session file contains:**
- Full conversation history
- Tool calls and results
- Configuration used
- Timestamps

## Session Persistence Patterns

### Pattern 1: Ephemeral (No Persistence)

Don't save sessions - each query is independent.

```typescript
// No session options = ephemeral
for await (const message of query({
  prompt: "One-shot task"
})) {}
```

**Use for**: One-shot tasks, stateless operations.

### Pattern 2: Single Process Continuation

Use `continue: true` for multi-turn in same process.

```typescript
for await (const message of query({ prompt: "Task 1" })) {}
for await (const message of query({
  prompt: "Task 2",
  options: { continue: true }
})) {}
```

**Use for**: Interactive CLI tools, development workflows.

### Pattern 3: Multi-Process Resumption

Capture and store session IDs for resumption across processes.

```typescript
// Process 1: Start task
const sessionId = await startTask();
await db.save({ userId, sessionId });

// Process 2: Resume task
const { sessionId } = await db.load(userId);
for await (const message of query({
  prompt: "Continue",
  options: { resume: sessionId }
})) {}
```

**Use for**: Web apps, multi-user systems, background jobs.

### Pattern 4: Hybrid (Ephemeral + History)

Use ephemeral containers but hydrate with history.

```typescript
// Load previous conversation
const history = await db.loadHistory(userId);

// Start fresh container with history context
for await (const message of query({
  prompt: `Previous context: ${history}\n\nNew task: ${task}`
})) {}
```

**Use for**: Serverless functions, cost optimization.

## Session Management Best Practices

### 1. Always Capture Session IDs

```typescript
let sessionId: string;

for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    sessionId = message.session_id;
    // Store for later use
    await saveSessionId(sessionId);
  }
}
```

### 2. Handle Session Not Found

```typescript
try {
  for await (const message of query({
    prompt: "Continue",
    options: { resume: sessionId }
  })) {}
} catch (error) {
  if (error.message.includes("session not found")) {
    // Start new session
    for await (const message of query({ prompt: "Start fresh" })) {}
  }
}
```

### 3. Clean Up Old Sessions

```typescript
// Delete sessions older than 30 days
const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
const sessions = await fs.readdir(".claude/sessions");

for (const session of sessions) {
  const stats = await fs.stat(`.claude/sessions/${session}`);
  if (stats.mtimeMs < thirtyDaysAgo) {
    await fs.unlink(`.claude/sessions/${session}`);
  }
}
```

### 4. Use Fork for Experimentation

```typescript
// Don't lose original work when trying alternatives
for await (const message of query({
  prompt: "Try different approach",
  options: { resume: originalSessionId, forkSession: true }
})) {}
```

## Session Limitations

### Sessions are Local Files

Sessions don't automatically sync across:
- Different machines
- Different containers
- Different working directories

**Solution**: Store session files in shared storage (S3, database) for distributed systems.

### Session Size Grows

Long conversations accumulate large history.

**Solution**:
- Start fresh sessions periodically
- Use hybrid pattern (ephemeral + summary)
- Clean up old sessions

### Working Directory Matters

Sessions are tied to working directory.

**Solution**: Use `cwd` option to ensure consistent working directory:

```typescript
options: {
  cwd: "/path/to/project",
  resume: sessionId
}
```

## Complete Examples

See:
- `examples/typescript/session-management.ts`
- `examples/python/session_management.py`

For complete working examples of all session patterns.
