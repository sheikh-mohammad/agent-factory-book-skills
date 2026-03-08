# Multi-Agent Systems

Guide for building agent teams and Agent-to-Agent (A2A) coordination with Google ADK.

## Overview

Multi-agent systems enable complex problem-solving through agent collaboration:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Hierarchical** | Supervisor coordinates sub-agents | Task delegation, workflow orchestration |
| **Peer-to-peer** | Agents communicate directly | Collaborative problem-solving |
| **Sequential** | Agents process in pipeline | Data transformation, multi-step workflows |
| **Parallel** | Agents work concurrently | Independent tasks, result aggregation |

## Agent Teams

### Basic Agent Team

```python
from google.adk.agents import LlmAgent

# Define specialized agents
researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-flash",
    instruction="Research information using available tools.",
    description="Researches topics and gathers information",
    tools=[search_tool, web_fetch_tool],
)

writer = LlmAgent(
    name="writer",
    model="gemini-2.5-flash",
    instruction="Write content based on provided information.",
    description="Creates well-written content",
)

# Coordinator agent with sub-agents
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.5-flash",
    instruction="""You coordinate research and writing tasks.
    - Use the researcher agent to gather information
    - Use the writer agent to create content
    - Combine their outputs to provide comprehensive responses""",
    description="Coordinates research and writing",
    sub_agents=[researcher, writer],
)
```

### Weather Bot Example

Progressive multi-agent system from ADK tutorials:

```python
# Weather data agent
weather_data_agent = LlmAgent(
    name="weather_data",
    model="gemini-2.5-flash",
    instruction="Fetch weather data for locations.",
    tools=[get_weather_tool],
)

# Weather analysis agent
weather_analysis_agent = LlmAgent(
    name="weather_analysis",
    model="gemini-2.5-flash",
    instruction="Analyze weather data and provide insights.",
)

# Root weather bot
weather_bot = LlmAgent(
    name="weather_bot",
    model="gemini-2.5-flash",
    instruction="""You are a weather assistant.
    - Use weather_data agent to fetch current conditions
    - Use weather_analysis agent to provide insights
    - Combine information to help users""",
    sub_agents=[weather_data_agent, weather_analysis_agent],
)
```

See: [Weather Bot Tutorial](https://github.com/google/adk-docs/blob/main/docs/tutorials/agent-team.md)

## Hierarchical Teams

Supervisor agent delegates to specialized sub-agents.

### Customer Service Example

```python
# Order management agent
order_agent = LlmAgent(
    name="order_manager",
    model="gemini-2.5-flash",
    instruction="""Handle order operations:
    - Check order status
    - Modify orders
    - Process returns
    Use available tools to access order system.""",
    tools=[get_order, modify_order, process_return],
)

# Payment agent
payment_agent = LlmAgent(
    name="payment_manager",
    model="gemini-2.5-flash",
    instruction="""Handle payment operations:
    - Process refunds
    - Update payment methods
    - Check payment status""",
    tools=[process_refund, update_payment_method],
)

# Human handoff agent
human_agent = LlmAgent(
    name="human_handoff",
    model="gemini-2.5-flash",
    instruction="Transfer complex issues to human agents.",
    tools=[transfer_to_human],
)

# Supervisor agent
customer_service_bot = LlmAgent(
    name="customer_service",
    model="gemini-2.5-pro",  # More capable model for coordination
    instruction="""You are a customer service supervisor.

    Analyze customer requests and delegate to appropriate agents:
    - order_manager: For order-related questions
    - payment_manager: For payment and refund issues
    - human_handoff: For complex issues or explicit requests

    Coordinate responses and ensure customer satisfaction.""",
    sub_agents=[order_agent, payment_agent, human_agent],
)
```

### Task Delegation Pattern

```python
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.5-pro",
    instruction="""Analyze tasks and delegate appropriately:

    1. Understand the user's request
    2. Determine which sub-agent(s) can help
    3. Delegate to appropriate agent(s)
    4. Synthesize results into coherent response

    Available agents:
    - data_analyst: For data analysis and insights
    - report_writer: For creating reports
    - visualizer: For creating charts and graphs""",
    sub_agents=[data_analyst, report_writer, visualizer],
)
```

## Agent-to-Agent (A2A) Communication

Agents can communicate and coordinate with each other.

### A2A Authentication Flow

Remote agent requests OAuth from root agent:

```python
# Remote agent that needs OAuth
bigquery_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    instruction="""You help users query BigQuery.

    When you need OAuth credentials:
    1. Surface authentication request to root agent
    2. Wait for credentials
    3. Use credentials to access BigQuery""",
    tools=[bigquery_tools],
)

# Root agent handles OAuth flow
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""You coordinate with sub-agents.

    When sub-agent needs OAuth:
    1. Guide user through OAuth flow
    2. Obtain authorization
    3. Return credentials to sub-agent""",
    sub_agents=[bigquery_agent],
)
```

See: [A2A OAuth Sample](https://github.com/google/adk-python/blob/main/contributing/samples/a2a_auth/README.md)

### A2A Message Passing

Agents can pass messages and context:

```python
# Agent 1: Data collector
collector = LlmAgent(
    name="collector",
    model="gemini-2.5-flash",
    instruction="""Collect data from various sources.
    Pass collected data to processor agent.""",
    tools=[fetch_data_tool],
)

# Agent 2: Data processor
processor = LlmAgent(
    name="processor",
    model="gemini-2.5-flash",
    instruction="""Process data received from collector.
    Pass processed data to reporter agent.""",
    tools=[process_data_tool],
)

# Agent 3: Report generator
reporter = LlmAgent(
    name="reporter",
    model="gemini-2.5-flash",
    instruction="""Generate reports from processed data.""",
    tools=[generate_report_tool],
)

# Coordinator
pipeline = LlmAgent(
    name="pipeline",
    model="gemini-2.5-pro",
    instruction="""Coordinate data pipeline:
    1. collector gathers data
    2. processor transforms data
    3. reporter generates final report""",
    sub_agents=[collector, processor, reporter],
)
```

## Parallel Execution

Multiple agents work concurrently.

### Parallel Research Example

```python
# Specialized research agents
tech_researcher = LlmAgent(
    name="tech_researcher",
    model="gemini-2.5-flash",
    instruction="Research technical topics.",
    tools=[search_tech_docs],
)

market_researcher = LlmAgent(
    name="market_researcher",
    model="gemini-2.5-flash",
    instruction="Research market trends.",
    tools=[search_market_data],
)

competitor_researcher = LlmAgent(
    name="competitor_researcher",
    model="gemini-2.5-flash",
    instruction="Research competitors.",
    tools=[search_competitor_info],
)

# Coordinator runs agents in parallel
research_coordinator = LlmAgent(
    name="research_coordinator",
    model="gemini-2.5-pro",
    instruction="""Coordinate parallel research:

    1. Assign research topics to specialized agents
    2. Agents work concurrently
    3. Aggregate and synthesize results
    4. Provide comprehensive analysis""",
    sub_agents=[tech_researcher, market_researcher, competitor_researcher],
)
```

## Shared Context and State

Agents can share context through session state.

### Shared State Example

```python
def share_context(key: str, value: str, tool_context: ToolContext) -> str:
    """Share context with other agents."""
    shared = tool_context.state.get("shared_context", {})
    shared[key] = value
    tool_context.state["shared_context"] = shared
    return f"Shared: {key} = {value}"

def read_shared_context(key: str, tool_context: ToolContext) -> str:
    """Read shared context from other agents."""
    shared = tool_context.state.get("shared_context", {})
    value = shared.get(key)
    return f"Read: {key} = {value}" if value else f"No shared context for {key}"

# Agents with shared context tools
agent1 = LlmAgent(
    name="agent1",
    model="gemini-2.5-flash",
    instruction="Share findings with other agents.",
    tools=[share_context, read_shared_context],
)

agent2 = LlmAgent(
    name="agent2",
    model="gemini-2.5-flash",
    instruction="Use shared context from other agents.",
    tools=[share_context, read_shared_context],
)
```

## Workflow Orchestration

Coordinate complex workflows across agents.

### Sequential Workflow

```python
coordinator = LlmAgent(
    name="workflow_coordinator",
    model="gemini-2.5-pro",
    instruction="""Orchestrate sequential workflow:

    Step 1: data_collector gathers raw data
    Step 2: data_validator checks data quality
    Step 3: data_processor transforms data
    Step 4: data_storer saves to database

    Only proceed to next step if previous step succeeds.
    Handle errors at each step.""",
    sub_agents=[
        data_collector,
        data_validator,
        data_processor,
        data_storer,
    ],
)
```

### Conditional Workflow

```python
coordinator = LlmAgent(
    name="conditional_coordinator",
    model="gemini-2.5-pro",
    instruction="""Orchestrate conditional workflow:

    1. analyzer assesses the request
    2. Based on analysis:
       - If simple: use quick_processor
       - If complex: use deep_processor
       - If unclear: use clarifier
    3. validator checks results
    4. If validation fails, retry with different processor""",
    sub_agents=[
        analyzer,
        quick_processor,
        deep_processor,
        clarifier,
        validator,
    ],
)
```

## Error Handling in Multi-Agent Systems

### Agent Failure Recovery

```python
coordinator = LlmAgent(
    name="resilient_coordinator",
    model="gemini-2.5-pro",
    instruction="""Coordinate with error recovery:

    1. Try primary_agent first
    2. If primary_agent fails:
       - Try backup_agent
    3. If both fail:
       - Use fallback_agent with limited functionality
    4. If all fail:
       - Escalate to human_agent

    Always inform user of any issues.""",
    sub_agents=[
        primary_agent,
        backup_agent,
        fallback_agent,
        human_agent,
    ],
)
```

### Timeout Handling

```python
coordinator = LlmAgent(
    name="timeout_coordinator",
    model="gemini-2.5-pro",
    instruction="""Coordinate with timeout awareness:

    1. Set reasonable timeouts for each agent
    2. If agent times out:
       - Try faster alternative agent
       - Or break task into smaller pieces
    3. Keep user informed of progress""",
    sub_agents=[slow_but_thorough_agent, fast_but_basic_agent],
)
```

## Best Practices

### Agent Design

**Do:**
- Give each agent a clear, specific role
- Use descriptive names and descriptions
- Define clear delegation criteria in coordinator
- Implement error handling and fallbacks
- Keep agent instructions focused

**Don't:**
- Create too many agents (3-5 is usually enough)
- Give agents overlapping responsibilities
- Make coordinator instructions too complex
- Forget to handle agent failures

### Coordination Patterns

**Hierarchical** - Best for:
- Clear task delegation
- Specialized capabilities
- Supervisor-worker patterns

**Peer-to-peer** - Best for:
- Collaborative problem-solving
- Agents with equal authority
- Flexible workflows

**Sequential** - Best for:
- Pipeline processing
- Step-by-step workflows
- Data transformation

**Parallel** - Best for:
- Independent tasks
- Time-sensitive operations
- Result aggregation

### Performance Optimization

```python
# Use faster model for simple agents
simple_agent = LlmAgent(
    name="simple_agent",
    model="gemini-2.5-flash",  # Fast
    instruction="Handle simple tasks quickly.",
)

# Use more capable model for coordinator
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.5-pro",  # More capable
    instruction="Coordinate complex workflows.",
    sub_agents=[simple_agent],
)
```

### Testing Multi-Agent Systems

```python
# Test individual agents first
await runner.run_debug("Test researcher agent", verbose=True)

# Then test coordination
await runner.run_debug("Test full workflow", verbose=True)

# Check agent interactions
# Look for proper delegation in verbose output
```

## Common Patterns

### Pattern: Specialist Team

Multiple specialists coordinated by generalist:

```python
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.5-pro",
    instruction="Route requests to appropriate specialist.",
    sub_agents=[
        legal_specialist,
        technical_specialist,
        financial_specialist,
    ],
)
```

### Pattern: Pipeline

Sequential processing through stages:

```python
pipeline = LlmAgent(
    name="pipeline",
    model="gemini-2.5-pro",
    instruction="Process through stages: collect → validate → transform → store",
    sub_agents=[collector, validator, transformer, storer],
)
```

### Pattern: Consensus

Multiple agents provide input, coordinator synthesizes:

```python
consensus = LlmAgent(
    name="consensus",
    model="gemini-2.5-pro",
    instruction="Get opinions from all agents and synthesize consensus.",
    sub_agents=[agent1, agent2, agent3],
)
```

### Pattern: Fallback Chain

Try agents in order until one succeeds:

```python
fallback = LlmAgent(
    name="fallback",
    model="gemini-2.5-pro",
    instruction="Try agents in order: primary → secondary → tertiary",
    sub_agents=[primary, secondary, tertiary],
)
```

## Official Documentation

- [Agent Team Tutorial](https://github.com/google/adk-docs/blob/main/docs/tutorials/agent-team.md)
- [A2A Authentication](https://github.com/google/adk-python/blob/main/contributing/samples/a2a_auth/README.md)
- [ADK Tutorials](https://github.com/google/adk-docs/blob/main/docs/tutorials/index.md)
