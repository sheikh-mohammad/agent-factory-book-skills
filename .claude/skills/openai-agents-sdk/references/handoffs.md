# Handoffs

Multi-agent patterns for delegating tasks to specialized agents.

## Core Concept

Handoffs allow agents to recognize when a task is better suited for another agent and seamlessly transfer control. This enables complex multi-agent workflows where different agents specialize in different domains.

## Basic Handoff

```python
from agents import Agent, Runner
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Create specialized agents
billing_agent = Agent(
    name="Billing Agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nHandle billing questions.",
    handoff_description="Handles billing inquiries and payment issues",
)

technical_agent = Agent(
    name="Technical Support",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nProvide technical support.",
    handoff_description="Handles technical issues and troubleshooting",
)

# Create triage agent
triage_agent = Agent(
    name="Triage Agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nRoute to appropriate specialist.",
    handoffs=[billing_agent, technical_agent],
)

# Run
result = await Runner.run(triage_agent, "I have a billing question")
print(f"Handled by: {result.last_agent.name}")
```

**Key points**:
- Use `RECOMMENDED_PROMPT_PREFIX` in instructions for handoff-aware agents
- Set `handoff_description` to guide routing decisions
- Triage agent automatically gets handoff tools

## Handoff Description

The `handoff_description` helps the LLM decide when to delegate:

```python
# ❌ Vague
handoff_description="Handles billing"

# ✅ Specific
handoff_description="Handles billing inquiries, payment issues, invoice questions, and subscription changes"
```

**Best practices**:
- Be specific about what the agent handles
- Include keywords the LLM should recognize
- Mention edge cases or special scenarios
- Keep it concise (1-2 sentences)

## Custom Handoffs

Use the `handoff()` function for advanced control:

```python
from agents import Agent, handoff, RunContextWrapper
from pydantic import BaseModel

# Define input data structure
class EscalationData(BaseModel):
    reason: str
    priority: str

# Define callback
async def on_escalation(ctx: RunContextWrapper, data: EscalationData):
    """Called when escalation handoff is invoked."""
    print(f"Escalation: {data.reason} (Priority: {data.priority})")
    # Could trigger alerts, log to database, etc.

escalation_agent = Agent(
    name="Escalation Handler",
    instructions="Handle escalated issues with high priority.",
)

# Create custom handoff
triage_agent = Agent(
    name="Triage Agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\nRoute or escalate as needed.",
    handoffs=[
        billing_agent,  # Simple handoff
        handoff(
            agent=technical_agent,
            tool_name_override="transfer_to_tech",
            tool_description_override="Transfer to technical support for software/hardware issues",
        ),
        handoff(
            agent=escalation_agent,
            on_handoff=on_escalation,
            input_type=EscalationData,
        ),
    ],
)
```

### Handoff Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `agent` | Target agent | `billing_agent` |
| `tool_name_override` | Custom tool name | `"transfer_to_billing"` |
| `tool_description_override` | Custom description | `"Transfer billing questions"` |
| `on_handoff` | Callback function | `on_escalation` |
| `input_type` | Structured input | `EscalationData` |
| `input_filter` | Filter input data | `lambda x: filter_sensitive(x)` |
| `is_enabled` | Dynamic enable/disable | `lambda ctx: ctx.user.is_premium` |

## Common Patterns

### Triage Pattern

Central agent routes to specialists:

```python
# Specialists
sales_agent = Agent(name="Sales", instructions="Handle sales inquiries")
support_agent = Agent(name="Support", instructions="Handle support issues")
billing_agent = Agent(name="Billing", instructions="Handle billing questions")

# Triage
triage_agent = Agent(
    name="Triage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the first point of contact. Determine the nature of the request:
    - Sales questions → Sales agent
    - Technical issues → Support agent
    - Billing/payment → Billing agent
    """,
    handoffs=[sales_agent, support_agent, billing_agent],
)
```

### Escalation Pattern

Agents can escalate to higher authority:

```python
# Tier 1 support
tier1_agent = Agent(
    name="Tier 1 Support",
    instructions="Handle basic support questions. Escalate complex issues.",
)

# Tier 2 support
tier2_agent = Agent(
    name="Tier 2 Support",
    instructions="Handle complex technical issues.",
)

# Tier 1 can escalate to Tier 2
tier1_agent = Agent(
    name="Tier 1 Support",
    instructions="Handle basic support. Escalate if needed.",
    handoffs=[tier2_agent],
)
```

### Specialist Chain

Agents pass through multiple specialists:

```python
# Research → Analysis → Recommendation
research_agent = Agent(
    name="Researcher",
    instructions="Gather information and pass to analyst.",
)

analysis_agent = Agent(
    name="Analyst",
    instructions="Analyze data and pass to advisor.",
)

advisor_agent = Agent(
    name="Advisor",
    instructions="Provide final recommendations.",
)

# Chain them
research_agent.handoffs = [analysis_agent]
analysis_agent.handoffs = [advisor_agent]
```

### Parallel Specialists

Triage can route to multiple independent specialists:

```python
# Domain specialists
legal_agent = Agent(name="Legal", instructions="Review legal aspects")
financial_agent = Agent(name="Finance", instructions="Review financial aspects")
technical_agent = Agent(name="Technical", instructions="Review technical aspects")

# Coordinator
coordinator = Agent(
    name="Coordinator",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Route to appropriate specialist based on question type.
    Multiple specialists may be needed for complex questions.
    """,
    handoffs=[legal_agent, financial_agent, technical_agent],
)
```

## Handoff Callbacks

Execute custom logic when handoffs occur:

```python
from agents import handoff, RunContextWrapper

async def log_handoff(ctx: RunContextWrapper, data: dict):
    """Log handoff for analytics."""
    print(f"Handoff from {ctx.agent.name} at {datetime.now()}")
    # Log to database, send metrics, etc.

async def fetch_context(ctx: RunContextWrapper, data: dict):
    """Fetch additional context for target agent."""
    user_id = data.get("user_id")
    # Fetch user history, preferences, etc.
    return {"user_history": fetch_user_history(user_id)}

specialist = Agent(name="Specialist", instructions="Handle specialized tasks")

triage = Agent(
    name="Triage",
    handoffs=[
        handoff(
            agent=specialist,
            on_handoff=log_handoff,
        ),
    ],
)
```

## Input Filtering

Control what data is passed to the next agent:

```python
from agents import handoff

def filter_sensitive_data(input_data: dict) -> dict:
    """Remove sensitive information before handoff."""
    filtered = input_data.copy()
    filtered.pop("credit_card", None)
    filtered.pop("ssn", None)
    return filtered

secure_agent = Agent(name="Secure Agent", instructions="Handle sensitive data")

triage = Agent(
    name="Triage",
    handoffs=[
        handoff(
            agent=secure_agent,
            input_filter=filter_sensitive_data,
        ),
    ],
)
```

## Dynamic Handoffs

Enable/disable handoffs based on context:

```python
from agents import handoff, RunContextWrapper

def can_escalate(ctx: RunContextWrapper) -> bool:
    """Check if user can escalate."""
    # Check user permissions, time of day, etc.
    return ctx.user.is_premium and is_business_hours()

premium_agent = Agent(name="Premium Support", instructions="VIP support")

standard_agent = Agent(
    name="Standard Support",
    instructions="Standard support",
    handoffs=[
        handoff(
            agent=premium_agent,
            is_enabled=can_escalate,
        ),
    ],
)
```

## Handoff History

Track which agents handled the conversation:

```python
result = await Runner.run(triage_agent, "I need help")

# Check final agent
print(f"Final agent: {result.last_agent.name}")

# Check history for all agents involved
for item in result.history:
    if hasattr(item, 'agent'):
        print(f"Agent: {item.agent.name}")
```

## Best Practices

### Instructions
- Always use `RECOMMENDED_PROMPT_PREFIX` for handoff-aware agents
- Clearly define each agent's domain
- Specify when to handoff vs handle directly
- Include examples of edge cases

### Handoff Descriptions
- Be specific about capabilities
- Include relevant keywords
- Mention what NOT to handoff
- Keep concise (1-2 sentences)

### Agent Design
- Keep agents focused on single domain
- Avoid overlapping responsibilities
- Design clear handoff criteria
- Test handoff decisions

### Error Handling
- Handle cases where no agent matches
- Provide fallback for unclear requests
- Log handoff failures
- Allow users to override routing

### Performance
- Minimize handoff chains (prefer direct routing)
- Use `gpt-4o-mini` for triage agents
- Use `gpt-4o` for specialist agents
- Cache common routing decisions

## Testing Handoffs

### Unit Testing

```python
import pytest
from agents import Agent, Runner

@pytest.mark.asyncio
async def test_billing_handoff():
    triage = create_triage_agent()
    result = await Runner.run(triage, "I have a billing question")
    assert result.last_agent.name == "Billing Agent"

@pytest.mark.asyncio
async def test_technical_handoff():
    triage = create_triage_agent()
    result = await Runner.run(triage, "My app is crashing")
    assert result.last_agent.name == "Technical Support"
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_escalation_flow():
    tier1 = create_tier1_agent()
    result = await Runner.run(tier1, "Complex database issue")

    # Verify escalation occurred
    assert result.last_agent.name == "Tier 2 Support"

    # Verify callback was triggered
    assert escalation_logged()
```

## Troubleshooting

### Handoffs not occurring
- Check `RECOMMENDED_PROMPT_PREFIX` is in instructions
- Verify `handoff_description` is clear and specific
- Review triage agent instructions
- Test with explicit handoff requests

### Wrong agent selected
- Improve handoff descriptions
- Add more specific routing criteria in instructions
- Use `tool_description_override` for clarity
- Test with edge cases

### Handoff loops
- Set `max_turns` to prevent infinite loops
- Design clear termination conditions
- Avoid circular handoff chains
- Log handoff history for debugging

### Performance issues
- Reduce handoff chain length
- Use `gpt-4o-mini` for routing
- Cache routing decisions
- Consider direct routing vs triage
