---
name: claude-agent-sdk
description: |
  Build reliable AI agents with Claude Agent SDK (Anthropic's agent framework) from hello world to production systems.
  Covers agent creation, tools integration (built-in and custom MCP), multi-agent coordination, state management, error handling, security, testing, and deployment (local, Docker, cloud).
  This skill should be used when building autonomous agents, task automation, multi-agent systems, or deploying AI agents to production using Anthropic's official Agent SDK with Claude models.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

# Claude Agent SDK

Build production-ready AI agents with Anthropic's Claude Agent SDK.

## What This Skill Does

- Guides agent implementation from hello world to production
- Provides patterns for autonomous coding, automation, research, and multi-agent systems
- Covers TypeScript and Python implementations equally
- Includes security, testing, and deployment best practices
- Embeds official documentation patterns and anti-patterns

## What This Skill Does NOT Do

- Replace official Claude Agent SDK documentation (always check latest docs)
- Handle non-Anthropic agent frameworks (OpenAI Agents SDK, LangChain, etc.)
- Provide domain-specific business logic (you implement your use case)
- Manage production infrastructure (you handle hosting/monitoring)

## Official Documentation

For the latest information, always refer to official Anthropic documentation:

- **Agent SDK Overview**: https://platform.claude.com/docs/en/agent-sdk/overview
- **API Reference**: https://platform.claude.com/docs/en/agent-sdk/api-reference
- **Migration Guide**: https://platform.claude.com/docs/en/agent-sdk/migration-guide
- **Hosting Guide**: https://platform.claude.com/docs/en/agent-sdk/hosting

For patterns not covered in this skill, use the fetch-library-docs skill to get the latest official documentation.

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing structure, dependencies, patterns to integrate with |
| **Conversation** | User's specific requirements, use case, constraints |
| **Skill References** | Agent patterns from `references/` (configuration, tools, deployment) |
| **User Guidelines** | Project-specific conventions, security requirements |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Implementation Workflow

### 1. Clarify Requirements

Ask about the user's specific agent needs.

#### Required Clarifications

Always ask these questions:

1. **Agent Purpose**: What task will the agent perform? What's the expected input/output?
2. **Language Preference**: TypeScript or Python? Existing project or new?

#### Optional Clarifications

Ask these if relevant to the user's context:

3. **Tools Needed** (if not obvious from purpose):
   - File operations (Read, Write, Edit)?
   - Code execution (Bash)?
   - Web access (WebSearch, WebFetch)?
   - Custom tools via MCP?

4. **Deployment Context** (if deploying to production):
   - Local development, Docker, or cloud?
   - Security requirements (isolation, credentials)?

5. **Budget Constraints** (if cost-sensitive):
   - Any spending limits?
   - Expected usage volume?

6. **Execution Pattern** (if unclear from purpose):
   - Will it run once or continuously?
   - Single-turn or multi-turn conversation?

**Note**: Avoid asking too many questions in a single message. Start with required clarifications, then ask optional ones based on user's responses.

### 2. Choose Agent Pattern

Based on requirements, select pattern from `references/agent-patterns.md`:

| Pattern | Use When | Example |
|---------|----------|---------|
| **Simple Query** | One-shot task, no state | "Analyze this file" |
| **Session-Based** | Multi-turn conversation | Chatbot, assistant |
| **Subagent Orchestration** | Complex task with subtasks | Code review with specialized agents |
| **MCP Integration** | Need external tools/APIs | Weather data, database queries |
| **Production Service** | Long-running, high-availability | Customer support agent |

### 3. Implement Agent

Follow language-specific implementation from `references/`:

**TypeScript:**
- `references/typescript-guide.md` - Setup, query patterns, MCP
- `references/examples/typescript/` - Code examples

**Python:**
- `references/python-guide.md` - Setup, query patterns, MCP
- `references/examples/python/` - Code examples

**Core Implementation Steps:**
1. Install SDK and set API key
2. Configure agent options (tools, permissions, model)
3. Implement query with proper error handling
4. Add session management if needed
5. Create custom MCP tools if needed

### 4. Configure Security

Apply security patterns from `references/security.md`:

- Set `allowedTools` to pre-approve safe tools
- Use `disallowedTools` to block dangerous operations
- Set `max_budget_usd` to prevent runaway costs
- Run in isolated container for production
- Use proxy pattern for credential injection

### 5. Test Agent

Follow testing patterns from `references/testing.md`:

- Unit test custom MCP tools
- Integration test agent behavior
- Test error handling (max_turns, budget limits)
- Test permission flows
- Validate security isolation

### 6. Deploy

Follow deployment pattern from `references/deployment.md`:

**Local Development:**
- Run directly with Node.js/Python
- Use `.env` for API keys

**Docker:**
- Use provided Dockerfile templates
- Apply security hardening (read-only, user isolation)

**Cloud/Production:**
- Choose hosting pattern (ephemeral, long-running, hybrid)
- Set up monitoring and cost tracking
- Implement credential proxy
- Configure resource limits

---

## Quick Start Examples

### TypeScript: Simple Query

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "What files are in this directory?",
  options: { allowedTools: ["Bash", "Glob"] }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Python: Simple Query

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="What files are in this directory?",
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"]),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

See `references/examples/` for complete examples including:
- Session management
- Custom MCP tools
- Multi-agent orchestration
- Production deployment

---

## Key Concepts

### Agent vs Client SDK

| Feature | Client SDK | Agent SDK |
|---------|-----------|-----------|
| Tool execution | You implement | Autonomous |
| Agent loop | You implement | Built-in |
| Session management | Manual | Automatic |
| Use case | Full control | Rapid development |

### Built-in Tools

- **File**: Read, Write, Edit, Glob, Grep
- **Execution**: Bash
- **Web**: WebSearch, WebFetch
- **Orchestration**: Agent (subagents), Skill, AskUserQuestion

### Custom Tools (MCP)

Create custom tools using Model Context Protocol:
- Define tool schema with Zod (TypeScript) or Pydantic (Python)
- Implement tool handler function
- Register with MCP server
- Use in agent with `mcpServers` option

See `references/tools-and-mcp.md` for complete guide.

### Session Management

Three ways to continue conversations:

1. **Continue**: Resume most recent session
2. **Resume**: Resume specific session by ID
3. **Fork**: Branch to explore alternatives

See `references/state-management.md` for patterns.

---

## Common Patterns

### Multi-Agent Orchestration

```typescript
for await (const message of query({
  prompt: "Review this codebase",
  options: {
    agents: {
      "security-reviewer": {
        description: "Security expert",
        prompt: "Check for vulnerabilities",
        tools: ["Read", "Grep"]
      },
      "performance-reviewer": {
        description: "Performance expert",
        prompt: "Identify bottlenecks",
        tools: ["Read", "Bash"]
      }
    }
  }
})) {}
```

### Error Handling

```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    switch (message.subtype) {
      case "success":
        console.log(message.result);
        break;
      case "error_max_turns":
        // Resume with higher limit
        break;
      case "error_max_budget_usd":
        // Handle budget exceeded
        break;
    }
  }
}
```

### Cost Tracking

```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "result") {
    console.log(`Cost: $${message.total_cost_usd}`);
  }
}
```

---

## Implementation Checklist

Before delivering agent implementation:

### Configuration
- [ ] API key configured (environment variable)
- [ ] Appropriate model selected (sonnet/opus/haiku)
- [ ] Tools configured (allowedTools/disallowedTools)
- [ ] Permission mode set appropriately
- [ ] Budget limit set (max_budget_usd)

### Error Handling
- [ ] Result subtype checked before reading result
- [ ] Max turns error handled
- [ ] Budget exceeded error handled
- [ ] Custom tool errors caught and returned as text

### Security (Production)
- [ ] Running in isolated container
- [ ] Filesystem mounted read-only where possible
- [ ] Credentials injected via proxy (not mounted)
- [ ] Resource limits set (memory, CPU)
- [ ] Dangerous tools blocked or restricted

### Testing
- [ ] Custom tools unit tested
- [ ] Agent behavior integration tested
- [ ] Error scenarios tested
- [ ] Permission flows tested

### Deployment
- [ ] Hosting pattern chosen (ephemeral/long-running/hybrid)
- [ ] Container security hardened
- [ ] Monitoring and cost tracking implemented
- [ ] Session persistence configured if needed

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/getting-started.md` | Installation, hello world, first agent |
| `references/agent-configuration.md` | All configuration options and patterns |
| `references/tools-and-mcp.md` | Built-in tools, custom MCP tools |
| `references/workflows.md` | Multi-step, subagents, orchestration |
| `references/state-management.md` | Sessions, continue/resume/fork |
| `references/security.md` | Isolation, permissions, credentials |
| `references/deployment.md` | Docker, cloud, production patterns |
| `references/testing.md` | Unit tests, integration tests, mocking |
| `references/best-practices.md` | Recommended patterns and approaches |
| `references/anti-patterns.md` | Common mistakes to avoid |
| `references/typescript-guide.md` | TypeScript-specific implementation |
| `references/python-guide.md` | Python-specific implementation |
| `references/examples/` | Complete code examples |

---

## Troubleshooting

### Agent not using tools
- Check `allowedTools` includes needed tools
- Verify permission mode allows tool execution
- Check if tools are blocked by `disallowedTools`

### MCP tools not working
- Ensure using streaming input (async generator for prompt)
- Verify tool name format: `mcp__<server>__<tool>`
- Check MCP server is properly registered

### Session not resuming
- Verify session ID captured from result message
- Check session files exist in `.claude/sessions/`
- Ensure same working directory

### High costs
- Set `max_budget_usd` limit
- Use lower `effort` for simple tasks
- Reduce number of tools in context
- Monitor via `total_cost_usd` in result

### Security concerns
- Never mount credential directories
- Use proxy pattern for API keys
- Run in isolated container with minimal capabilities
- Set filesystem to read-only where possible

See `references/anti-patterns.md` for complete troubleshooting guide.
