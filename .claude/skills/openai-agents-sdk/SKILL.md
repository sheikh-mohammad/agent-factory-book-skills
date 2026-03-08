---
name: openai-agents-sdk
description: |
  Build AI agents with OpenAI Agents SDK from hello world to production systems.
  Covers agent configuration, custom tools, handoffs, streaming, MCP integration, error handling, and deployment.
  This skill should be used when building conversational agents, automation workflows, multi-agent systems, or integrating AI capabilities into applications using OpenAI's official Python SDK.
---

# OpenAI Agents SDK

Build production-grade AI agents using OpenAI's official Python SDK.

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing structure, patterns, conventions, dependencies |
| **Conversation** | User's specific requirements, constraints, industry domain |
| **Skill References** | SDK patterns from `references/` (API docs, best practices, examples) |
| **User Guidelines** | Project-specific conventions, team standards, security policies |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (SDK expertise is in this skill).

---

## Quick Start Decision Tree

```
What are you building?
├─ First agent / Learning → Use: Hello World Template
├─ Single-purpose agent → Use: Basic Agent Pattern
├─ Agent with custom tools → Use: Function Tools Pattern
├─ Multi-agent system → Use: Handoffs Pattern
├─ Streaming responses → Use: Streaming Pattern
├─ External tool integration → Use: MCP Integration
└─ Production deployment → Use: Production Checklist
```

---

## Core Workflows

### 1. Create Basic Agent

**When**: Building your first agent or simple single-purpose agent.

```python
from agents import Agent, Runner

# 1. Define agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4o",  # or gpt-4o-mini for cost efficiency
)

# 2. Run agent
result = await Runner.run(agent, "Your query here")
print(result.final_output)
```

**Key decisions**:
- Model: `gpt-4o` (quality) vs `gpt-4o-mini` (speed/cost)
- Instructions: Clear, specific role definition
- Sync vs async: Use `Runner.run_sync()` for simple scripts

See: `references/agent-basics.md`

### 2. Add Custom Tools

**When**: Agent needs to perform actions or access external data.

```python
from agents import Agent, Runner, function_tool

# 1. Define tool with decorator
@function_tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the database for matching records.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.
    """
    # Your implementation
    return f"Found {limit} results for '{query}'"

# 2. Add to agent
agent = Agent(
    name="Assistant",
    instructions="Use search_database to find information.",
    tools=[search_database],
)
```

**Key decisions**:
- Sync vs async tools: Use `async def` for I/O operations
- Error handling: Add `failure_error_function` for graceful failures
- Timeouts: Set `timeout` parameter for long-running operations
- Context access: Add `ctx: RunContextWrapper` first param for agent context

See: `references/function-tools.md`

### 3. Implement Multi-Agent Handoffs

**When**: Building specialized agents that delegate to each other.

```python
from agents import Agent, Runner, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# 1. Create specialized agents
billing_agent = Agent(
    name="Billing Agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nHandle billing questions.",
    handoff_description="Handles billing inquiries and payments",
)

technical_agent = Agent(
    name="Technical Support",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nProvide technical support.",
)

# 2. Create triage agent with handoffs
triage_agent = Agent(
    name="Triage Agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nRoute to appropriate specialist.",
    handoffs=[billing_agent, technical_agent],
)

# 3. Run
result = await Runner.run(triage_agent, "I have a billing question")
print(f"Handled by: {result.last_agent.name}")
```

**Key decisions**:
- Handoff descriptions: Clear, specific routing criteria
- Custom handoffs: Use `handoff()` function for callbacks, input filtering
- Escalation patterns: Add escalation agent for complex cases

See: `references/handoffs.md`

### 4. Stream Responses

**When**: Need real-time feedback for long-running operations.

```python
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

agent = Agent(name="Assistant", instructions="Be helpful.")

# Stream token-by-token
result = Runner.run_streamed(agent, "Tell me a story")
async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

# Access final result after stream completes
print(f"\n\nFinal: {result.final_output}")
```

**Key decisions**:
- Event types: `raw_response_event` (tokens) vs `run_item_stream_event` (structured)
- UI updates: Stream for immediate display, use final_output for storage
- Error handling: Wrap stream iteration in try/except

See: `references/streaming.md`

### 5. Integrate MCP Servers

**When**: Need to connect external tools via Model Context Protocol.

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# Local MCP server via stdio
async with MCPServerStdio(
    name="Filesystem Server",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
    },
) as server:
    agent = Agent(
        name="File Assistant",
        instructions="Use filesystem tools to help users.",
        mcp_servers=[server],
    )

    result = await Runner.run(agent, "List all files")
    print(result.final_output)
```

**Key decisions**:
- Server type: `MCPServerStdio` (local) vs `MCPServerStreamableHttp` (remote)
- Multiple servers: Use `MCPServerManager` for parallel connections
- Hosted MCP: Use `HostedMCPTool` for OpenAI-hosted servers

See: `references/mcp-integration.md`

---

## Production Checklist

Before deploying to production:

### Configuration
- [ ] Environment variables for API keys (never hardcode)
- [ ] Model selection optimized for cost/quality tradeoff
- [ ] Timeout settings for all tools and operations
- [ ] Max turns limit to prevent infinite loops

### Error Handling
- [ ] Error handlers for max_turns, tool failures, API errors
- [ ] Custom error messages for user-facing failures
- [ ] Logging for debugging and monitoring
- [ ] Graceful degradation when tools fail

### Security
- [ ] Input validation for user queries
- [ ] Output sanitization for sensitive data
- [ ] Tool approval settings (`require_approval` for risky operations)
- [ ] Rate limiting and abuse prevention

### Monitoring
- [ ] Track token usage and costs
- [ ] Log agent decisions and handoffs
- [ ] Monitor tool execution times
- [ ] Alert on error rates

### Testing
- [ ] Unit tests for custom tools
- [ ] Integration tests for agent workflows
- [ ] Load testing for concurrent requests
- [ ] Cost estimation for expected usage

See: `references/production-patterns.md`

---

## Common Patterns by Industry

Quick reference for domain-specific implementations:

| Industry | Agent Type | Key Tools | Pattern |
|----------|-----------|-----------|---------|
| Customer Support | Triage + Specialists | Search, Ticketing, Escalation | Handoffs |
| Data Analysis | Single Agent | Query, Visualize, Export | Function Tools |
| Manufacturing | Multi-Agent | IoT, Inventory, Scheduling | Handoffs + MCP |
| Sales | Pipeline Manager | CRM, Research, Email | Function Tools + MCP |
| Finance | Analyst | Query, Calculate, Report | Function Tools |
| Healthcare | Documentation | EHR, Coding, Compliance | MCP + Validation |
| Legal | Document Review | Search, Extract, Flag | Function Tools + Streaming |
| HR | Recruiting | ATS, Schedule, Screen | Handoffs + MCP |

See: `references/industry-patterns.md` for detailed implementations.

---

## Error Handling Patterns

### Handle Max Turns

```python
from agents import Agent, Runner, RunErrorHandlerInput, RunErrorHandlerResult

def on_max_turns(_data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="Couldn't complete. Please narrow the request.",
        include_in_history=False,
    )

result = await Runner.run(
    agent,
    "Complex query",
    max_turns=5,
    error_handlers={"max_turns": on_max_turns},
)
```

### Handle Tool Failures

```python
from agents import function_tool, RunContextWrapper

def custom_error_handler(ctx: RunContextWrapper, error: Exception) -> str:
    return f"Service temporarily unavailable: {type(error).__name__}"

@function_tool(failure_error_function=custom_error_handler)
def call_external_api(endpoint: str) -> str:
    """Call external API with error handling."""
    # Implementation
    pass
```

See: `references/error-handling.md`

---

## Model Selection Guide

| Model | Use When | Cost | Speed | Quality |
|-------|----------|------|-------|---------|
| `gpt-4o` | Production, complex reasoning | $$$ | Medium | Highest |
| `gpt-4o-mini` | High-volume, simple tasks | $ | Fast | Good |
| `gpt-4-turbo` | Legacy, specific requirements | $$ | Medium | High |

**Cost optimization**:
- Use `gpt-4o-mini` for triage/routing agents
- Use `gpt-4o` for specialized/complex agents
- Set `max_tokens` to limit response length
- Cache system prompts when possible

See: `references/model-optimization.md`

---

## Quick Reference

### Agent Configuration

```python
agent = Agent(
    name="Agent Name",                    # Required: identifier
    instructions="System prompt",         # Agent's role and behavior
    model="gpt-4o",                       # Model selection
    model_settings=ModelSettings(         # Optional tuning
        temperature=0.7,
        max_tokens=1000,
    ),
    tools=[tool1, tool2],                 # Custom function tools
    handoffs=[agent1, agent2],            # Other agents to delegate to
    mcp_servers=[server1],                # MCP tool providers
)
```

### Runner Methods

```python
# Async execution
result = await Runner.run(agent, "query")

# Sync execution (for scripts)
result = Runner.run_sync(agent, "query")

# Streaming
result = Runner.run_streamed(agent, "query")
async for event in result.stream_events():
    # Process events
    pass

# With options
result = await Runner.run(
    agent,
    "query",
    max_turns=10,                         # Limit iterations
    error_handlers={"max_turns": handler}, # Error handling
)
```

### Function Tool Decorator

```python
@function_tool(
    name_override="custom_name",          # Override function name
    timeout=5.0,                          # Execution timeout
    failure_error_function=error_handler, # Custom error handling
)
async def my_tool(
    ctx: RunContextWrapper,               # Optional: agent context
    param1: str,                          # Required parameter
    param2: int = 10,                     # Optional with default
) -> str:
    """Tool description for LLM.

    Args:
        param1: Description of param1.
        param2: Description of param2.
    """
    # Implementation
    return "result"
```

---

## Getting Started

### Installation

```bash
pip install openai-agents-sdk
```

### Hello World

Use template: `assets/templates/hello-world.py`

### Next Steps

1. Start with basic agent (`references/agent-basics.md`)
2. Add custom tools (`references/function-tools.md`)
3. Implement handoffs if needed (`references/handoffs.md`)
4. Add streaming for UX (`references/streaming.md`)
5. Review production checklist (`references/production-patterns.md`)

---

## References

| File | Content |
|------|---------|
| `references/agent-basics.md` | Agent configuration, model settings, instructions |
| `references/function-tools.md` | Custom tool creation, parameters, error handling |
| `references/handoffs.md` | Multi-agent patterns, routing, escalation |
| `references/streaming.md` | Real-time responses, event types, UI integration |
| `references/mcp-integration.md` | MCP servers, stdio, HTTP, hosted tools |
| `references/error-handling.md` | Error handlers, retries, graceful degradation |
| `references/production-patterns.md` | Deployment, monitoring, security, optimization |
| `references/industry-patterns.md` | Domain-specific implementations and examples |
| `references/model-optimization.md` | Cost reduction, performance tuning, caching |
| `references/api-reference.md` | Complete SDK API documentation |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.py` | Initialize new agent project |
| `scripts/validate.py` | Validate agent configuration |
| `scripts/test-tools.py` | Test custom tools in isolation |
| `scripts/estimate-cost.py` | Estimate API costs for workload |

---

## What This Skill Does NOT Do

- Deploy infrastructure (use deployment tools)
- Manage API keys (use environment variables)
- Monitor production systems (use observability tools)
- Train or fine-tune models (use OpenAI fine-tuning API)
