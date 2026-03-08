# Testing Guide

Comprehensive guide to testing Claude Agent SDK applications.

## Testing Approaches

### 1. Unit Testing Custom Tools

Test MCP tools in isolation.

**TypeScript:**
```typescript
import { tool } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

// Define tool
const weatherTool = tool(
  'get_weather',
  'Get temperature',
  { latitude: z.number(), longitude: z.number() },
  async (args) => {
    const response = await fetch(`https://api.example.com/weather?lat=${args.latitude}&lon=${args.longitude}`);
    const data = await response.json();
    return { content: [{ type: 'text', text: `${data.temp}°F` }] };
  }
);

// Test tool
describe('weatherTool', () => {
  it('returns temperature', async () => {
    const result = await weatherTool.handler({ latitude: 37.7, longitude: -122.4 });
    expect(result.content[0].text).toContain('°F');
  });

  it('handles errors gracefully', async () => {
    // Mock fetch to throw error
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    const result = await weatherTool.handler({ latitude: 0, longitude: 0 });
    expect(result.content[0].text).toContain('error');
  });
});
```

**Python:**
```python
import pytest
from claude_agent_sdk import tool
from pydantic import BaseModel

class WeatherArgs(BaseModel):
    latitude: float
    longitude: float

async def get_weather(args: WeatherArgs):
    # Implementation
    return {"content": [{"type": "text", "text": "72°F"}]}

weather_tool = tool(
    name="get_weather",
    description="Get temperature",
    parameters=WeatherArgs,
    handler=get_weather
)

@pytest.mark.asyncio
async def test_weather_tool():
    result = await weather_tool.handler(WeatherArgs(latitude=37.7, longitude=-122.4))
    assert "°F" in result["content"][0]["text"]
```

### 2. Integration Testing Agent Behavior

Test complete agent workflows.

**TypeScript:**
```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

describe('Code Review Agent', () => {
  it('finds and fixes bugs', async () => {
    const messages = [];

    for await (const message of query({
      prompt: 'Fix the bug in utils.ts',
      options: {
        allowedTools: ['Read', 'Edit'],
        cwd: '/test/fixtures'
      }
    })) {
      messages.push(message);
    }

    const result = messages.find(m => m.type === 'result');
    expect(result.subtype).toBe('success');
    expect(result.result).toContain('fixed');
  });

  it('respects budget limits', async () => {
    const messages = [];

    for await (const message of query({
      prompt: 'Analyze entire codebase',
      options: {
        maxBudgetUsd: 0.01,  // Very low limit
        allowedTools: ['Read', 'Grep']
      }
    })) {
      messages.push(message);
    }

    const result = messages.find(m => m.type === 'result');
    expect(result.subtype).toBe('error_max_budget_usd');
  });
});
```

**Python:**
```python
import pytest
from claude_agent_sdk import query, ClaudeAgentOptions

@pytest.mark.asyncio
async def test_code_review_agent():
    messages = []

    async for message in query(
        prompt="Fix the bug in utils.py",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit"],
            cwd="/test/fixtures"
        )
    ):
        messages.append(message)

    result = next(m for m in messages if m.type == "result")
    assert result.subtype == "success"
    assert "fixed" in result.result
```

### 3. Testing with Mocked Tools

Mock tool execution for deterministic tests.

**TypeScript:**
```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

describe('Agent with mocked tools', () => {
  it('uses Read tool correctly', async () => {
    const readCalls = [];

    for await (const message of query({
      prompt: 'Read config.json',
      options: {
        allowedTools: ['Read'],
        beforeToolUse: async (toolName, toolInput) => {
          if (toolName === 'Read') {
            readCalls.push(toolInput.file_path);
          }
        }
      }
    })) {}

    expect(readCalls).toContain('config.json');
  });
});
```

### 4. Testing Permission Flows

Test tool permission handling.

**TypeScript:**
```typescript
describe('Permission handling', () => {
  it('prompts for unapproved tools', async () => {
    const canUseTool = jest.fn().mockResolvedValue({ behavior: 'allow' });

    for await (const message of query({
      prompt: 'Delete file',
      options: {
        canUseTool,
        allowedTools: []  // No pre-approved tools
      }
    })) {}

    expect(canUseTool).toHaveBeenCalledWith('Bash', expect.any(Object));
  });

  it('blocks dangerous commands', async () => {
    const canUseTool = jest.fn().mockImplementation((tool, input) => {
      if (tool === 'Bash' && input.command.includes('rm -rf')) {
        return { behavior: 'block', message: 'Dangerous command' };
      }
      return { behavior: 'allow' };
    });

    for await (const message of query({
      prompt: 'Delete all files',
      options: { canUseTool }
    })) {}

    expect(canUseTool).toHaveBeenCalled();
  });
});
```

### 5. Testing Error Handling

Test error scenarios.

**TypeScript:**
```typescript
describe('Error handling', () => {
  it('handles max turns error', async () => {
    const messages = [];

    for await (const message of query({
      prompt: 'Infinite loop task',
      options: { maxTurns: 5 }
    })) {
      messages.push(message);
    }

    const result = messages.find(m => m.type === 'result');
    expect(result.subtype).toBe('error_max_turns');
  });

  it('handles API errors gracefully', async () => {
    // Test with invalid API key
    process.env.ANTHROPIC_API_KEY = 'invalid';

    try {
      for await (const message of query({ prompt: 'Task' })) {}
      fail('Should have thrown error');
    } catch (error) {
      expect(error.message).toContain('authentication');
    }
  });
});
```

## Testing Patterns

### Pattern 1: Fixture-Based Testing

Use test fixtures for consistent testing.

```typescript
// test/fixtures/buggy-code.ts
export const buggyCode = `
function add(a, b) {
  return a - b;  // Bug: should be +
}
`;

// test/agent.test.ts
import { query } from '@anthropic-ai/claude-agent-sdk';
import { buggyCode } from './fixtures/buggy-code';
import fs from 'fs/promises';

beforeEach(async () => {
  await fs.writeFile('/tmp/test.ts', buggyCode);
});

test('fixes bug', async () => {
  for await (const message of query({
    prompt: 'Fix the bug in /tmp/test.ts',
    options: { allowedTools: ['Read', 'Edit'] }
  })) {
    if (message.type === 'result') {
      const fixed = await fs.readFile('/tmp/test.ts', 'utf-8');
      expect(fixed).toContain('a + b');
    }
  }
});
```

### Pattern 2: Snapshot Testing

Test agent output consistency.

```typescript
test('generates consistent output', async () => {
  const messages = [];

  for await (const message of query({
    prompt: 'Describe the architecture',
    options: { allowedTools: ['Read'], cwd: '/test/fixtures' }
  })) {
    if (message.type === 'text') {
      messages.push(message.text);
    }
  }

  expect(messages.join('\n')).toMatchSnapshot();
});
```

### Pattern 3: Cost Testing

Verify budget limits work.

```typescript
test('respects budget limits', async () => {
  const budget = 0.10;

  for await (const message of query({
    prompt: 'Complex task',
    options: { maxBudgetUsd: budget }
  })) {
    if (message.type === 'result') {
      expect(message.total_cost_usd).toBeLessThanOrEqual(budget);
    }
  }
});
```

### Pattern 4: Timeout Testing

Test time limits.

```typescript
test('completes within time limit', async () => {
  const startTime = Date.now();

  for await (const message of query({
    prompt: 'Quick task',
    options: { maxTurns: 10 }
  })) {
    if (message.type === 'result') {
      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(60000);  // 60 seconds
    }
  }
});
```

## Test Utilities

### Helper: Collect Messages

```typescript
async function collectMessages(prompt: string, options = {}) {
  const messages = [];
  for await (const message of query({ prompt, options })) {
    messages.push(message);
  }
  return messages;
}

// Usage
test('agent behavior', async () => {
  const messages = await collectMessages('Task', { allowedTools: ['Read'] });
  const result = messages.find(m => m.type === 'result');
  expect(result.subtype).toBe('success');
});
```

### Helper: Extract Result

```typescript
async function getResult(prompt: string, options = {}) {
  for await (const message of query({ prompt, options })) {
    if (message.type === 'result') {
      return message;
    }
  }
  throw new Error('No result received');
}

// Usage
test('successful completion', async () => {
  const result = await getResult('Task');
  expect(result.subtype).toBe('success');
});
```

### Helper: Mock Tool Execution

```typescript
function createMockTool(responses: Record<string, any>) {
  return async (toolName: string, toolInput: any) => {
    if (responses[toolName]) {
      return responses[toolName](toolInput);
    }
    return { behavior: 'allow' };
  };
}

// Usage
test('with mocked tools', async () => {
  const canUseTool = createMockTool({
    Read: (input) => ({
      behavior: 'allow',
      result: { content: [{ type: 'text', text: 'mocked content' }] }
    })
  });

  for await (const message of query({
    prompt: 'Read file',
    options: { canUseTool }
  })) {}
});
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '20'

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: npm test

    - name: Check budget
      run: |
        if [ $(cat test-results.json | jq '.totalCost') -gt 1.0 ]; then
          echo "Test cost exceeded $1"
          exit 1
        fi
```

### GitLab CI

```yaml
test:
  image: node:20
  script:
    - npm ci
    - npm test
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
  only:
    - merge_requests
    - main
```

## Testing Best Practices

1. **Test custom tools in isolation** - Unit test tool handlers before integration
2. **Use fixtures** - Consistent test data for reproducible results
3. **Test error scenarios** - Max turns, budget limits, API errors
4. **Mock external dependencies** - Don't rely on external APIs in tests
5. **Test permission flows** - Verify tool approval/blocking works
6. **Monitor test costs** - Set budget limits in tests
7. **Use CI/CD** - Automate testing on every commit
8. **Test security** - Verify isolation and permission enforcement

## Testing Checklist

Before deploying:

- [ ] Custom tools unit tested
- [ ] Agent behavior integration tested
- [ ] Error scenarios tested (max turns, budget, API errors)
- [ ] Permission flows tested
- [ ] Security isolation tested
- [ ] Cost limits verified
- [ ] Performance benchmarked
- [ ] CI/CD pipeline configured
