# Agent Basics

Core concepts for configuring and running OpenAI agents.

## Agent Configuration

An agent is a large language model (LLM) configured with instructions and tools.

### Required Properties

```python
from agents import Agent

agent = Agent(
    name="Assistant",  # Required: identifier for the agent
    instructions="You are a helpful assistant.",  # Agent's role and behavior
)
```

### Common Properties

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4o",  # Which LLM to use
    model_settings=ModelSettings(
        temperature=0.7,
        top_p=1.0,
        max_tokens=1000,
    ),
    tools=[],  # Function tools the agent can use
    handoffs=[],  # Other agents to delegate to
    mcp_servers=[],  # MCP servers providing tools
)
```

## Instructions (System Prompt)

The instructions define the agent's role, behavior, and capabilities.

### Best Practices

**Be specific and clear**:
```python
# ❌ Vague
instructions = "Be helpful."

# ✅ Specific
instructions = """You are a customer support agent for Acme Corp.
- Answer questions about products, orders, and returns
- Be polite and professional
- Escalate billing issues to the billing team
- Never share customer data"""
```

**Define boundaries**:
```python
instructions = """You are a data analyst assistant.
You CAN:
- Query databases using the search_data tool
- Generate visualizations
- Explain statistical concepts

You CANNOT:
- Modify or delete data
- Share raw customer information
- Make business decisions"""
```

**Include context**:
```python
instructions = """You are a technical support agent.
Company: TechCo
Products: Cloud hosting, CDN, DNS services
Support hours: 24/7
Escalation: Use escalate_to_engineer for infrastructure issues"""
```

## Model Selection

### Available Models

| Model | Best For | Cost | Speed |
|-------|----------|------|-------|
| `gpt-4o` | Complex reasoning, production quality | High | Medium |
| `gpt-4o-mini` | High-volume, simple tasks | Low | Fast |
| `gpt-4-turbo` | Legacy applications | Medium | Medium |

### Selection Guide

**Use `gpt-4o` when**:
- Complex multi-step reasoning required
- High accuracy is critical
- Handling nuanced or ambiguous queries
- Production customer-facing applications

**Use `gpt-4o-mini` when**:
- Simple, well-defined tasks
- High-volume operations (cost matters)
- Fast response time needed
- Triage or routing agents

### Model Settings

```python
from agents import ModelSettings

# Conservative (more focused, deterministic)
conservative = ModelSettings(
    temperature=0.3,
    top_p=0.9,
    max_tokens=500,
)

# Balanced (default)
balanced = ModelSettings(
    temperature=0.7,
    top_p=1.0,
    max_tokens=1000,
)

# Creative (more varied, exploratory)
creative = ModelSettings(
    temperature=0.9,
    top_p=1.0,
    max_tokens=2000,
)
```

**Temperature**: Controls randomness (0.0 = deterministic, 1.0 = creative)
**Top P**: Nucleus sampling threshold (0.9 = more focused, 1.0 = full range)
**Max Tokens**: Maximum response length (limits cost and latency)

## Running Agents

### Async Execution (Recommended)

```python
import asyncio
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant.",
    )

    result = await Runner.run(agent, "What's the weather like?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Sync Execution (Simple Scripts)

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
)

result = Runner.run_sync(agent, "What's the weather like?")
print(result.final_output)
```

### Run Options

```python
result = await Runner.run(
    agent,
    "Your query",
    max_turns=10,  # Limit agent iterations (default: 100)
    error_handlers={},  # Custom error handling
)
```

## Result Object

```python
result = await Runner.run(agent, "query")

# Access outputs
print(result.final_output)  # Final text response
print(result.last_agent.name)  # Which agent finished
print(result.history)  # Full conversation history

# Check status
if result.error:
    print(f"Error: {result.error}")
```

## Agent Cloning

Create variations of agents without modifying the original:

```python
base_agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4o",
    tools=[search_tool, calculate_tool],
)

# Clone with modifications
specialized_agent = base_agent.clone(
    name="Math Assistant",
    instructions="You only answer math questions.",
    tools=[calculate_tool],  # Subset of tools
)
```

## Common Patterns

### Simple Q&A Agent

```python
agent = Agent(
    name="FAQ Bot",
    instructions="Answer questions about our product using the knowledge base.",
    model="gpt-4o-mini",  # Cost-effective for simple queries
)
```

### Task Automation Agent

```python
agent = Agent(
    name="Automation Agent",
    instructions="Execute tasks using available tools. Confirm before destructive operations.",
    model="gpt-4o",
    tools=[file_tool, api_tool, database_tool],
)
```

### Analysis Agent

```python
agent = Agent(
    name="Data Analyst",
    instructions="Analyze data and provide insights. Always show your reasoning.",
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.3),  # More deterministic
    tools=[query_tool, visualize_tool],
)
```

## Best Practices

### Instructions
- Be specific about role and capabilities
- Define clear boundaries (what agent can/cannot do)
- Include relevant context (company, products, policies)
- Use examples for complex behaviors

### Model Selection
- Start with `gpt-4o-mini` for prototyping
- Upgrade to `gpt-4o` when quality matters
- Use temperature 0.3-0.5 for factual tasks
- Use temperature 0.7-0.9 for creative tasks

### Error Handling
- Always set `max_turns` to prevent infinite loops
- Add error handlers for production systems
- Log agent decisions for debugging
- Test with edge cases and malformed inputs

### Performance
- Keep instructions concise (tokens cost money)
- Set appropriate `max_tokens` limits
- Use `gpt-4o-mini` for high-volume operations
- Cache system prompts when possible

## Troubleshooting

### Agent doesn't use tools
- Check tool descriptions are clear
- Verify tools are in agent's `tools` list
- Review instructions mention when to use tools
- Test tools independently first

### Responses are too long/short
- Adjust `max_tokens` in model_settings
- Add length guidance in instructions
- Use temperature to control verbosity

### Agent is too creative/conservative
- Adjust `temperature` (lower = more focused)
- Adjust `top_p` (lower = more deterministic)
- Refine instructions to be more specific

### High costs
- Switch to `gpt-4o-mini` where possible
- Set lower `max_tokens` limits
- Reduce instruction length
- Cache repeated queries
