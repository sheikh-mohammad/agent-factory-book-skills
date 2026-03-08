# Agent Configuration

Complete reference for configuring Claude Agent SDK agents.

## Core Options

### allowedTools

Pre-approve specific tools to skip permission prompts.

```typescript
// TypeScript
options: {
  allowedTools: ["Read", "Edit", "Bash", "Glob", "Grep"]
}
```

```python
# Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"]
)
```

**Use when**: You trust the agent with specific tools and want to avoid prompts.

### disallowedTools

Block specific tools entirely (agent cannot use them).

```typescript
options: {
  disallowedTools: ["Bash", "Write"]
}
```

**Use when**: You want to prevent dangerous operations.

### permissionMode

Control approval behavior for tool usage.

| Mode | Behavior | Use Case |
|------|----------|----------|
| `"default"` | Prompt for unapproved tools | Interactive development |
| `"acceptEdits"` | Auto-approve file edits | Trusted coding workflows |
| `"bypassPermissions"` | Auto-approve all tools | CI/CD, isolated environments |
| `"plan"` | Agent creates plan first | Complex tasks needing review |
| `"dontAsk"` (TS only) | Fail fast on blocked tools | Automated systems |

```typescript
// TypeScript
options: { permissionMode: "acceptEdits" }
```

```python
# Python
options=ClaudeAgentOptions(permission_mode="acceptEdits")
```

**⚠️ Security Note**: `bypassPermissions` is NOT a security boundary. Always use proper isolation (containers, VMs) for security.

### model

Specify which Claude model to use.

```typescript
options: {
  model: "claude-sonnet-4-6"  // or "opus", "haiku"
}
```

**Model Selection:**
- **Opus**: Most capable, best for complex reasoning
- **Sonnet**: Balanced performance and cost (default)
- **Haiku**: Fastest, cheapest, good for simple tasks

### effort

Control reasoning depth (extended thinking).

```typescript
options: {
  effort: "medium"  // "low", "medium", "high", "max"
}
```

**Effort Levels:**
- `"low"`: Minimal thinking, fast responses
- `"medium"`: Balanced (default)
- `"high"`: Deep reasoning for complex tasks
- `"max"`: Maximum thinking time

**Cost Impact**: Higher effort = more tokens = higher cost.

### max_turns

Limit number of tool-use rounds.

```typescript
options: {
  maxTurns: 50  // Default: 100
}
```

**Use when**: You want to prevent infinite loops or control execution time.

### max_budget_usd

Cap spending per query.

```typescript
options: {
  maxBudgetUsd: 1.0  // Stop after $1
}
```

**⚠️ Critical for Production**: Always set budget limits to prevent runaway costs.

### cwd

Set working directory for file operations.

```typescript
options: {
  cwd: "/path/to/project"
}
```

**Default**: Current working directory.

### systemPrompt

Add custom system instructions.

```typescript
options: {
  systemPrompt: "You are a security expert. Focus on finding vulnerabilities."
}
```

**Use when**: You need specialized behavior or domain expertise.

## Session Options

### continue

Resume most recent session.

```typescript
options: {
  continue: true
}
```

**Use when**: Multi-turn conversation in same process.

### resume

Resume specific session by ID.

```typescript
options: {
  resume: "session-id-here"
}
```

**Use when**: Multi-user apps, resuming after restart.

### forkSession

Branch from existing session to explore alternatives.

```typescript
options: {
  resume: "session-id",
  forkSession: true
}
```

**Use when**: You want to try different approaches without losing original.

## Subagent Configuration

### agents

Define specialized subagents.

```typescript
options: {
  agents: {
    "security-reviewer": {
      description: "Security expert for vulnerability analysis",
      prompt: "Analyze code for security issues",
      tools: ["Read", "Grep"],
      model: "opus",
      systemPrompt: "You are a security expert"
    },
    "performance-reviewer": {
      description: "Performance optimization expert",
      prompt: "Identify performance bottlenecks",
      tools: ["Read", "Bash"]
    }
  }
}
```

**Subagent Benefits:**
- Context isolation (fresh conversation per subagent)
- Parallelization (multiple subagents run concurrently)
- Specialized instructions (each has own system prompt)
- Tool restrictions (limit what each can do)

## MCP Configuration

### mcpServers

Register custom MCP servers for external tools.

```typescript
import { createSdkMcpServer, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const weatherServer = createSdkMcpServer({
  name: "weather",
  version: "1.0.0",
  tools: [
    tool("get_weather", "Get temperature", {
      latitude: z.number(),
      longitude: z.number()
    }, async (args) => {
      // Implementation
      return { content: [{ type: "text", text: "72°F" }] };
    })
  ]
});

options: {
  mcpServers: { weather: weatherServer },
  allowedTools: ["mcp__weather__get_weather"]
}
```

**⚠️ Important**: MCP requires streaming input (async generator for prompt).

## Hook Configuration

### canUseTool

Intercept tool calls before execution.

```typescript
options: {
  canUseTool: async (toolName, toolInput) => {
    if (toolName === "Bash" && toolInput.command.includes("rm -rf")) {
      return { behavior: "block", message: "Dangerous command blocked" };
    }
    return { behavior: "allow" };
  }
}
```

**Behaviors:**
- `"allow"`: Execute tool
- `"block"`: Prevent execution
- `"prompt"`: Ask user for approval

### beforeToolUse / afterToolUse

Monitor tool execution.

```typescript
options: {
  beforeToolUse: async (toolName, toolInput) => {
    console.log(`Calling ${toolName}`);
  },
  afterToolUse: async (toolName, toolInput, result) => {
    console.log(`${toolName} completed`);
  }
}
```

## Complete Configuration Example

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Review this codebase for security issues",
  options: {
    // Model and reasoning
    model: "claude-opus-4-6",
    effort: "high",

    // Tools and permissions
    allowedTools: ["Read", "Grep", "Glob"],
    disallowedTools: ["Bash", "Write"],
    permissionMode: "default",

    // Limits
    maxTurns: 50,
    maxBudgetUsd: 2.0,

    // Context
    cwd: "/path/to/project",
    systemPrompt: "You are a security expert",

    // Subagents
    agents: {
      "vuln-scanner": {
        description: "Vulnerability scanner",
        prompt: "Scan for common vulnerabilities",
        tools: ["Read", "Grep"]
      }
    },

    // Hooks
    canUseTool: async (tool, input) => {
      console.log(`Tool requested: ${tool}`);
      return { behavior: "allow" };
    }
  }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}
```

## Configuration Best Practices

1. **Always set budget limits** in production (`maxBudgetUsd`)
2. **Use allowedTools** to pre-approve safe tools
3. **Use disallowedTools** to block dangerous operations
4. **Set appropriate effort** (low for simple tasks, high for complex)
5. **Use subagents** for complex tasks to keep context lean
6. **Monitor costs** via `total_cost_usd` in result messages
7. **Use hooks** for custom validation and monitoring
