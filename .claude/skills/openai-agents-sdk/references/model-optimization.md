# Model Optimization

Strategies for optimizing model selection, costs, and performance.

## Model Selection Strategy

### Decision Matrix

| Scenario | Recommended Model | Reasoning |
|----------|------------------|-----------|
| Simple Q&A, FAQ | `gpt-4o-mini` | Fast, cost-effective, sufficient quality |
| Triage/routing | `gpt-4o-mini` | Simple classification task |
| Complex reasoning | `gpt-4o` | Better at multi-step logic |
| Creative content | `gpt-4o` | Higher quality, more nuanced |
| Code generation | `gpt-4o` | Better at complex code patterns |
| Data analysis | `gpt-4o` | Better at analytical reasoning |
| High-volume operations | `gpt-4o-mini` | Cost optimization critical |

### Dynamic Model Selection

```python
def select_model_dynamically(query: str, context: dict) -> str:
    """Select model based on query characteristics."""

    # Check query complexity
    word_count = len(query.split())
    has_code = '```' in query or 'code' in query.lower()
    has_analysis = any(word in query.lower() for word in ['analyze', 'compare', 'evaluate'])

    # Simple queries
    if word_count < 50 and not has_code and not has_analysis:
        return "gpt-4o-mini"

    # Code or analysis tasks
    if has_code or has_analysis:
        return "gpt-4o"

    # Check user tier (if available)
    if context.get('user_tier') == 'premium':
        return "gpt-4o"

    # Default to mini for cost efficiency
    return "gpt-4o-mini"
```

## Cost Optimization

### Token Management

**Reduce Instruction Length**:
```python
# ❌ Verbose (wastes tokens)
instructions = """
You are a helpful assistant that helps users with their questions.
You should always be polite and professional in your responses.
You should provide accurate information based on the context provided.
You should ask clarifying questions when needed.
"""

# ✅ Concise (saves tokens)
instructions = "You are a helpful assistant. Be polite, accurate, and ask clarifying questions when needed."
```

**Limit Response Length**:
```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Assistant",
    instructions="Be concise. Limit responses to 2-3 sentences unless more detail is requested.",
    model_settings=ModelSettings(
        max_tokens=500,  # Limit output length
    ),
)
```

**Truncate History**:
```python
def truncate_history(history: list, max_messages: int = 10) -> list:
    """Keep only recent messages to reduce context size."""
    if len(history) <= max_messages:
        return history

    # Keep system message + recent messages
    return [history[0]] + history[-max_messages:]
```

### Caching Strategy

**Response Caching**:
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_response(agent_name: str, query: str) -> str:
    """Cache responses for identical queries."""
    # This is a simple in-memory cache
    # For production, use Redis or similar
    pass

async def run_with_cache(agent, query: str):
    """Run agent with caching."""
    cache_key = f"{agent.name}:{query}"

    # Check cache
    cached = get_cached_response(agent.name, query)
    if cached:
        return cached

    # Run agent
    result = await Runner.run(agent, query)

    # Cache result
    get_cached_response.cache_info()  # Monitor cache hits

    return result.final_output
```

**Prompt Caching** (if supported):
```python
# Cache system prompts that don't change
agent = Agent(
    name="Assistant",
    instructions="""[Long system prompt that rarely changes]
    This prompt will be cached by the API to reduce costs.""",
    model="gpt-4o",
)
```

### Batch Processing

Process multiple queries efficiently:

```python
async def batch_process(agent, queries: list[str], batch_size: int = 10):
    """Process queries in batches."""
    results = []

    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]

        # Process batch concurrently
        tasks = [Runner.run(agent, query) for query in batch]
        batch_results = await asyncio.gather(*tasks)

        results.extend(batch_results)

    return results
```

## Performance Optimization

### Concurrent Execution

```python
import asyncio

async def run_multiple_agents(queries: list[tuple[Agent, str]]):
    """Run multiple agents concurrently."""
    tasks = [Runner.run(agent, query) for agent, query in queries]
    results = await asyncio.gather(*tasks)
    return results
```

### Connection Pooling

```python
import httpx

# Reuse HTTP client for tool calls
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)

@function_tool
async def api_call(endpoint: str) -> str:
    """API call with connection pooling."""
    response = await http_client.get(f"{API_BASE}/{endpoint}")
    return response.json()
```

### Lazy Loading

```python
# Don't load all tools upfront
def get_tools_for_query(query: str) -> list:
    """Load only relevant tools based on query."""
    tools = []

    if 'database' in query.lower():
        tools.append(query_database)

    if 'file' in query.lower():
        tools.append(read_file)

    if 'api' in query.lower():
        tools.append(call_api)

    return tools

agent = Agent(
    name="Assistant",
    instructions="Use available tools to help users.",
    tools=get_tools_for_query(user_query),
)
```

## Quality Optimization

### Temperature Tuning

```python
from agents import ModelSettings

# Factual tasks (low temperature)
factual_agent = Agent(
    name="Factual Assistant",
    model_settings=ModelSettings(temperature=0.3),
    instructions="Provide accurate, factual information.",
)

# Creative tasks (higher temperature)
creative_agent = Agent(
    name="Creative Assistant",
    model_settings=ModelSettings(temperature=0.8),
    instructions="Generate creative content and ideas.",
)

# Balanced (default)
balanced_agent = Agent(
    name="Balanced Assistant",
    model_settings=ModelSettings(temperature=0.7),
)
```

### Few-Shot Examples

Include examples in instructions for better quality:

```python
agent = Agent(
    name="Classifier",
    instructions="""Classify customer inquiries into categories.

Examples:
- "My payment failed" → billing
- "App is crashing" → technical
- "How do I use feature X?" → support

Classify the following inquiry:""",
)
```

### Chain of Thought

Encourage reasoning for complex tasks:

```python
agent = Agent(
    name="Analyst",
    instructions="""When analyzing data:
1. State what you observe
2. Explain your reasoning
3. Draw conclusions
4. Provide recommendations

Always show your work.""",
)
```

## Monitoring and Optimization

### Token Tracking

```python
class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.by_agent = {}

    def track(self, agent_name: str, input_tokens: int, output_tokens: int):
        self.total_input += input_tokens
        self.total_output += output_tokens

        if agent_name not in self.by_agent:
            self.by_agent[agent_name] = {'input': 0, 'output': 0}

        self.by_agent[agent_name]['input'] += input_tokens
        self.by_agent[agent_name]['output'] += output_tokens

    def get_cost(self, model: str) -> float:
        """Calculate total cost."""
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        }

        if model not in pricing:
            return 0.0

        input_cost = (self.total_input / 1000) * pricing[model]["input"]
        output_cost = (self.total_output / 1000) * pricing[model]["output"]

        return input_cost + output_cost

    def get_report(self) -> dict:
        """Generate usage report."""
        return {
            'total_input_tokens': self.total_input,
            'total_output_tokens': self.total_output,
            'by_agent': self.by_agent,
        }

tracker = TokenTracker()
```

### Performance Metrics

```python
import time
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    duration: float
    tokens_input: int
    tokens_output: int
    tool_calls: int
    cache_hit: bool

async def run_with_metrics(agent, query: str) -> tuple[any, PerformanceMetrics]:
    """Run agent and collect performance metrics."""
    start_time = time.time()

    result = await Runner.run(agent, query)

    duration = time.time() - start_time

    metrics = PerformanceMetrics(
        duration=duration,
        tokens_input=0,  # Extract from result if available
        tokens_output=0,
        tool_calls=0,  # Count from history
        cache_hit=False,
    )

    return result, metrics
```

### A/B Testing

```python
class ModelABTest:
    def __init__(self):
        self.results = {'gpt-4o': [], 'gpt-4o-mini': []}

    def run_test(self, agent_name: str, query: str, user_id: str):
        """Run A/B test between models."""
        # Assign user to variant
        variant = 'gpt-4o' if hash(user_id) % 2 == 0 else 'gpt-4o-mini'

        agent = Agent(name=agent_name, model=variant, instructions="Be helpful.")

        start = time.time()
        result = Runner.run_sync(agent, query)
        duration = time.time() - start

        self.results[variant].append({
            'duration': duration,
            'query': query,
            'user_id': user_id,
        })

        return result

    def analyze(self):
        """Analyze A/B test results."""
        for model, results in self.results.items():
            avg_duration = sum(r['duration'] for r in results) / len(results)
            print(f"{model}: avg duration = {avg_duration:.2f}s")
```

## Cost Estimation

### Pre-Execution Estimation

```python
def estimate_cost(query: str, model: str, expected_response_tokens: int = 500) -> float:
    """Estimate cost before execution."""
    pricing = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    }

    if model not in pricing:
        return 0.0

    # Rough token estimation (4 chars per token)
    input_tokens = len(query) / 4

    input_cost = (input_tokens / 1000) * pricing[model]["input"]
    output_cost = (expected_response_tokens / 1000) * pricing[model]["output"]

    return input_cost + output_cost
```

### Budget Limits

```python
class BudgetManager:
    def __init__(self, daily_limit: float):
        self.daily_limit = daily_limit
        self.current_spend = 0.0
        self.last_reset = datetime.now().date()

    def check_budget(self, estimated_cost: float) -> bool:
        """Check if request is within budget."""
        # Reset daily counter
        if datetime.now().date() > self.last_reset:
            self.current_spend = 0.0
            self.last_reset = datetime.now().date()

        return (self.current_spend + estimated_cost) <= self.daily_limit

    def record_spend(self, actual_cost: float):
        """Record actual spend."""
        self.current_spend += actual_cost

budget = BudgetManager(daily_limit=100.0)  # $100/day
```

## Best Practices

### Model Selection
- Start with `gpt-4o-mini` for prototyping
- Use `gpt-4o` only when quality justifies cost
- Implement dynamic selection based on query complexity
- A/B test to validate model choices

### Cost Management
- Set `max_tokens` limits
- Implement response caching
- Truncate conversation history
- Use concise instructions
- Monitor and alert on spending

### Performance
- Use async for I/O operations
- Implement connection pooling
- Process queries in batches
- Cache frequent queries
- Load tools lazily

### Quality
- Tune temperature for task type
- Include few-shot examples
- Encourage chain of thought
- Test with diverse inputs
- Monitor output quality

## Troubleshooting

### High costs
- Audit token usage by agent
- Check for unnecessary verbosity
- Implement caching
- Switch to `gpt-4o-mini` where possible
- Set stricter `max_tokens` limits

### Slow performance
- Profile agent execution
- Optimize tool implementations
- Use concurrent execution
- Implement caching
- Check network latency

### Poor quality
- Upgrade to `gpt-4o` for complex tasks
- Add few-shot examples
- Tune temperature
- Improve instructions
- Test with edge cases

### Inconsistent results
- Lower temperature for consistency
- Add more specific instructions
- Use structured outputs
- Implement validation
- Test thoroughly
