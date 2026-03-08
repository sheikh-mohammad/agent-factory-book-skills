# Workflows and Multi-Agent Orchestration

Guide to building complex workflows with subagents and orchestration patterns.

## The Agent Loop

Understanding how the agent loop works:

```
1. Claude receives: prompt + system prompt + tool definitions + history
2. Claude evaluates and responds: text and/or tool calls
3. SDK executes tools and feeds results back to Claude
4. Repeat until Claude produces text-only response (no tool calls)
5. Return final result
```

**Key insight**: The agent continues autonomously until it decides the task is complete.

## Single Agent Workflows

### Sequential Tasks

Agent naturally handles sequential tasks:

```typescript
for await (const message of query({
  prompt: `
    1. Read the auth.ts file
    2. Identify security vulnerabilities
    3. Fix the vulnerabilities
    4. Write tests for the fixes
  `,
  options: { allowedTools: ["Read", "Edit", "Write", "Bash"] }
})) {}
```

**The agent will**:
- Execute tasks in order
- Use context from previous steps
- Adapt if steps fail

### Conditional Logic

Agent handles conditional logic naturally:

```typescript
for await (const message of query({
  prompt: `
    Check if tests exist for auth.ts.
    If they exist, run them.
    If they don't exist, create them first, then run them.
  `,
  options: { allowedTools: ["Read", "Glob", "Write", "Bash"] }
})) {}
```

### Iterative Refinement

Agent can iterate until quality threshold met:

```typescript
for await (const message of query({
  prompt: `
    Optimize the database query in users.ts.
    Run the performance benchmark after each change.
    Continue optimizing until the query runs in under 100ms.
  `,
  options: {
    allowedTools: ["Read", "Edit", "Bash"],
    maxTurns: 50  // Prevent infinite loops
  }
})) {}
```

## Multi-Agent Orchestration

### Why Use Subagents?

**Benefits:**
1. **Context isolation**: Each subagent has fresh conversation (no context pollution)
2. **Parallelization**: Multiple subagents run concurrently
3. **Specialization**: Each subagent has specific instructions and tools
4. **Tool restrictions**: Limit what each subagent can do

### Defining Subagents

```typescript
for await (const message of query({
  prompt: "Review this codebase for issues",
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Agent"],
    agents: {
      "security-reviewer": {
        description: "Security expert for vulnerability analysis",
        prompt: "Analyze code for security vulnerabilities (SQL injection, XSS, auth issues)",
        tools: ["Read", "Grep"],
        model: "opus",
        systemPrompt: "You are a security expert with 10 years experience"
      },
      "performance-reviewer": {
        description: "Performance optimization expert",
        prompt: "Identify performance bottlenecks and suggest optimizations",
        tools: ["Read", "Bash"],
        model: "sonnet"
      },
      "code-quality-reviewer": {
        description: "Code quality and maintainability expert",
        prompt: "Review code quality, readability, and maintainability",
        tools: ["Read", "Grep"],
        model: "sonnet"
      }
    }
  }
})) {}
```

### Subagent Configuration Options

| Option | Description | Example |
|--------|-------------|---------|
| `description` | What the subagent does (shown to main agent) | "Security expert" |
| `prompt` | Task for the subagent | "Find vulnerabilities" |
| `tools` | Tools subagent can use | `["Read", "Grep"]` |
| `model` | Model for subagent | `"opus"`, `"sonnet"`, `"haiku"` |
| `systemPrompt` | Custom instructions | "You are an expert..." |

### How Main Agent Uses Subagents

The main agent decides when to invoke subagents:

```typescript
// Main agent sees subagent descriptions and can invoke them
for await (const message of query({
  prompt: "Review the authentication system",
  options: {
    agents: {
      "security-reviewer": {
        description: "Security expert - use for security analysis",
        prompt: "Check for auth vulnerabilities",
        tools: ["Read", "Grep"]
      }
    }
  }
})) {}

// Main agent might think:
// "I need security expertise, I'll use the security-reviewer subagent"
// Then invokes: Agent(description="security-reviewer", prompt="Review auth.ts")
```

## Orchestration Patterns

### Pattern 1: Parallel Review

Multiple experts review simultaneously:

```typescript
for await (const message of query({
  prompt: "Get comprehensive code review from all experts",
  options: {
    agents: {
      "security": {
        description: "Security review",
        prompt: "Find security issues",
        tools: ["Read", "Grep"]
      },
      "performance": {
        description: "Performance review",
        prompt: "Find performance issues",
        tools: ["Read", "Bash"]
      },
      "quality": {
        description: "Quality review",
        prompt: "Find code quality issues",
        tools: ["Read"]
      }
    }
  }
})) {}
```

**Main agent will**:
- Invoke all subagents in parallel
- Collect results from each
- Synthesize comprehensive report

### Pattern 2: Sequential Pipeline

Output of one subagent feeds into next:

```typescript
for await (const message of query({
  prompt: `
    1. Use analyzer to identify issues
    2. Use fixer to fix the issues found
    3. Use tester to verify fixes work
  `,
  options: {
    agents: {
      "analyzer": {
        description: "Analyzes code for issues",
        prompt: "Find all bugs and issues",
        tools: ["Read", "Grep"]
      },
      "fixer": {
        description: "Fixes code issues",
        prompt: "Fix the issues provided",
        tools: ["Read", "Edit"]
      },
      "tester": {
        description: "Tests code changes",
        prompt: "Run tests and verify fixes",
        tools: ["Bash"]
      }
    }
  }
})) {}
```

### Pattern 3: Hierarchical Delegation

Main agent delegates to specialists who may delegate further:

```typescript
for await (const message of query({
  prompt: "Build a complete authentication system",
  options: {
    agents: {
      "backend-dev": {
        description: "Backend developer",
        prompt: "Implement backend auth logic",
        tools: ["Read", "Write", "Edit", "Bash"],
        agents: {
          "database-expert": {
            description: "Database specialist",
            prompt: "Design and implement database schema",
            tools: ["Read", "Write", "Bash"]
          }
        }
      },
      "frontend-dev": {
        description: "Frontend developer",
        prompt: "Implement frontend auth UI",
        tools: ["Read", "Write", "Edit"]
      }
    }
  }
})) {}
```

### Pattern 4: Consensus Building

Multiple agents vote or reach consensus:

```typescript
for await (const message of query({
  prompt: `
    Ask all reviewers to evaluate the code.
    If 2 or more approve, proceed with deployment.
    If 2 or more reject, list issues to fix.
  `,
  options: {
    agents: {
      "reviewer-1": { description: "Senior reviewer", prompt: "Review code", tools: ["Read"] },
      "reviewer-2": { description: "Senior reviewer", prompt: "Review code", tools: ["Read"] },
      "reviewer-3": { description: "Senior reviewer", prompt: "Review code", tools: ["Read"] }
    }
  }
})) {}
```

## Advanced Patterns

### Dynamic Subagent Creation

Main agent can request subagents based on runtime conditions:

```typescript
for await (const message of query({
  prompt: `
    Analyze the codebase to determine what languages are used.
    For each language found, use a specialized reviewer:
    - TypeScript: use typescript-expert
    - Python: use python-expert
    - Go: use go-expert
  `,
  options: {
    agents: {
      "typescript-expert": { description: "TS expert", prompt: "Review TS code", tools: ["Read"] },
      "python-expert": { description: "Python expert", prompt: "Review Python code", tools: ["Read"] },
      "go-expert": { description: "Go expert", prompt: "Review Go code", tools: ["Read"] }
    }
  }
})) {}
```

### Subagent with Different Model

Use Opus for complex reasoning, Sonnet for routine tasks:

```typescript
agents: {
  "architect": {
    description: "System architect for complex design decisions",
    prompt: "Design the system architecture",
    tools: ["Read", "Write"],
    model: "opus",  // Use most capable model
    effort: "high"
  },
  "implementer": {
    description: "Implements code based on design",
    prompt: "Implement the designed system",
    tools: ["Read", "Write", "Edit"],
    model: "sonnet",  // Use balanced model
    effort: "medium"
  }
}
```

### Subagent with Restricted Tools

Limit subagent capabilities for safety:

```typescript
agents: {
  "analyzer": {
    description: "Read-only code analyzer",
    prompt: "Analyze code structure",
    tools: ["Read", "Grep", "Glob"],  // No write/edit/bash
    disallowedTools: ["Write", "Edit", "Bash"]
  }
}
```

## Workflow Best Practices

1. **Use subagents for complex tasks** - Keeps main context lean
2. **Specialize subagents** - Give each a clear, focused role
3. **Restrict tools appropriately** - Only give tools needed for the task
4. **Use appropriate models** - Opus for complex, Haiku for simple
5. **Set clear prompts** - Tell subagent exactly what to do
6. **Monitor costs** - Multiple agents = higher costs
7. **Set max_turns** - Prevent infinite loops in iterative workflows

## Monitoring Workflow Progress

Track which subagents are invoked:

```typescript
for await (const message of query({ prompt: "Task", options: { agents: {...} } })) {
  if (message.type === "tool_use" && message.name === "Agent") {
    console.log(`Invoking subagent: ${message.input.description}`);
  }
  if (message.type === "result") {
    console.log(`Total cost: $${message.total_cost_usd}`);
  }
}
```

## Complete Examples

See:
- `examples/typescript/multi-agent-review.ts`
- `examples/python/multi_agent_review.py`

For complete working examples of multi-agent orchestration.
