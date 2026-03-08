# TypeScript Implementation Guide

Complete guide to implementing Claude Agent SDK in TypeScript.

## Installation

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## Basic Setup

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

// Set API key
process.env.ANTHROPIC_API_KEY = 'your-api-key';

// Simple query
for await (const message of query({
  prompt: 'What files are in this directory?',
  options: { allowedTools: ['Bash', 'Glob'] }
})) {
  if (message.type === 'result') {
    console.log(message.result);
  }
}
```

## Message Types

```typescript
import { query, TextMessage, ToolUseMessage, ResultMessage } from '@anthropic-ai/claude-agent-sdk';

for await (const message of query({ prompt: 'Task' })) {
  switch (message.type) {
    case 'text':
      const textMsg = message as TextMessage;
      console.log('Claude says:', textMsg.text);
      break;

    case 'tool_use':
      const toolMsg = message as ToolUseMessage;
      console.log(`Calling ${toolMsg.name} with`, toolMsg.input);
      break;

    case 'result':
      const resultMsg = message as ResultMessage;
      if (resultMsg.subtype === 'success') {
        console.log('Result:', resultMsg.result);
      } else {
        console.error('Error:', resultMsg.subtype);
      }
      break;
  }
}
```

## Configuration Options

```typescript
import { query, ClaudeAgentOptions } from '@anthropic-ai/claude-agent-sdk';

const options: ClaudeAgentOptions = {
  // Model selection
  model: 'claude-sonnet-4-6',  // or 'opus', 'haiku'
  effort: 'medium',  // 'low', 'medium', 'high', 'max'

  // Tools
  allowedTools: ['Read', 'Edit', 'Grep'],
  disallowedTools: ['Bash'],

  // Permissions
  permissionMode: 'acceptEdits',  // 'default', 'acceptEdits', 'bypassPermissions', 'plan', 'dontAsk'

  // Limits
  maxTurns: 50,
  maxBudgetUsd: 1.0,

  // Context
  cwd: '/path/to/project',
  systemPrompt: 'You are a security expert',

  // Session
  continue: true,
  resume: 'session-id',
  forkSession: false
};

for await (const message of query({ prompt: 'Task', options })) {
  // Process messages
}
```

## Creating Custom MCP Tools

```typescript
import { tool, createSdkMcpServer } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

// Define tool with Zod schema
const weatherTool = tool(
  'get_weather',
  'Get current temperature for a location',
  {
    latitude: z.number().describe('Latitude coordinate'),
    longitude: z.number().describe('Longitude coordinate')
  },
  async (args) => {
    try {
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m`
      );
      const data = await response.json();

      return {
        content: [{
          type: 'text',
          text: `Temperature: ${data.current.temperature_2m}°F`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Failed to fetch weather: ${error.message}`
        }]
      };
    }
  }
);

// Create MCP server
const weatherServer = createSdkMcpServer({
  name: 'weather',
  version: '1.0.0',
  tools: [weatherTool]
});

// Use in agent (requires streaming input)
async function* generateMessages() {
  yield { role: 'user', content: 'What is the weather in San Francisco?' };
}

for await (const message of query({
  prompt: generateMessages(),
  options: {
    mcpServers: { weather: weatherServer },
    allowedTools: ['mcp__weather__get_weather']
  }
})) {
  if (message.type === 'result') {
    console.log(message.result);
  }
}
```

## Session Management

### Continue Most Recent Session

```typescript
// First query
for await (const message of query({
  prompt: 'Analyze the auth module'
})) {}

// Continue from most recent
for await (const message of query({
  prompt: 'Now refactor it',
  options: { continue: true }
})) {}
```

### Resume Specific Session

```typescript
let sessionId: string;

// First query - capture session ID
for await (const message of query({
  prompt: 'Analyze code'
})) {
  if (message.type === 'result') {
    sessionId = message.session_id;
  }
}

// Resume later
for await (const message of query({
  prompt: 'Continue analysis',
  options: { resume: sessionId }
})) {}
```

### Fork Session

```typescript
// Fork to try alternative
for await (const message of query({
  prompt: 'Try OAuth2 instead',
  options: { resume: sessionId, forkSession: true }
})) {}
```

## Multi-Agent Orchestration

```typescript
for await (const message of query({
  prompt: 'Review this codebase',
  options: {
    allowedTools: ['Read', 'Grep', 'Agent'],
    agents: {
      'security-reviewer': {
        description: 'Security expert for vulnerability analysis',
        prompt: 'Analyze code for security vulnerabilities',
        tools: ['Read', 'Grep'],
        model: 'opus',
        systemPrompt: 'You are a security expert'
      },
      'performance-reviewer': {
        description: 'Performance optimization expert',
        prompt: 'Identify performance bottlenecks',
        tools: ['Read', 'Bash'],
        model: 'sonnet'
      }
    }
  }
})) {
  if (message.type === 'result') {
    console.log(message.result);
  }
}
```

## Hooks

### canUseTool Hook

```typescript
for await (const message of query({
  prompt: 'Task',
  options: {
    canUseTool: async (toolName, toolInput) => {
      // Block dangerous commands
      if (toolName === 'Bash' && toolInput.command.includes('rm -rf')) {
        return { behavior: 'block', message: 'Dangerous command blocked' };
      }

      // Log file writes
      if (toolName === 'Write') {
        console.log(`Writing to ${toolInput.file_path}`);
      }

      return { behavior: 'allow' };
    }
  }
})) {}
```

### beforeToolUse / afterToolUse Hooks

```typescript
for await (const message of query({
  prompt: 'Task',
  options: {
    beforeToolUse: async (toolName, toolInput) => {
      console.log(`Calling ${toolName}`);
    },
    afterToolUse: async (toolName, toolInput, result) => {
      console.log(`${toolName} completed`);
    }
  }
})) {}
```

## Error Handling

```typescript
for await (const message of query({ prompt: 'Task' })) {
  if (message.type === 'result') {
    switch (message.subtype) {
      case 'success':
        console.log('Success:', message.result);
        break;

      case 'error_max_turns':
        console.log('Hit turn limit');
        // Resume with higher limit
        break;

      case 'error_max_budget_usd':
        console.log('Hit budget limit');
        break;

      case 'error_during_execution':
        console.error('Execution error');
        break;

      default:
        console.error('Unknown error:', message.subtype);
    }
  }
}
```

## Express Server Example

```typescript
import express from 'express';
import { query } from '@anthropic-ai/claude-agent-sdk';

const app = express();
app.use(express.json());

app.post('/agent', async (req, res) => {
  const { prompt } = req.body;
  const result = [];

  try {
    for await (const message of query({
      prompt,
      options: {
        allowedTools: ['Read', 'WebSearch'],
        maxBudgetUsd: 0.5
      }
    })) {
      if (message.type === 'text') {
        result.push(message.text);
      } else if (message.type === 'result') {
        if (message.subtype === 'success') {
          res.json({ result: result.join('\n'), cost: message.total_cost_usd });
        } else {
          res.status(500).json({ error: message.subtype });
        }
      }
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Agent server running on port 3000');
});
```

## Testing

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

describe('Agent', () => {
  it('completes task successfully', async () => {
    const messages = [];

    for await (const message of query({
      prompt: 'List files in current directory',
      options: { allowedTools: ['Bash', 'Glob'] }
    })) {
      messages.push(message);
    }

    const result = messages.find(m => m.type === 'result');
    expect(result.subtype).toBe('success');
  });

  it('respects budget limits', async () => {
    for await (const message of query({
      prompt: 'Complex task',
      options: { maxBudgetUsd: 0.01 }
    })) {
      if (message.type === 'result') {
        expect(message.subtype).toBe('error_max_budget_usd');
      }
    }
  });
});
```

## TypeScript Types

```typescript
import {
  query,
  ClaudeAgentOptions,
  TextMessage,
  ToolUseMessage,
  ResultMessage,
  MessageStreamEvent
} from '@anthropic-ai/claude-agent-sdk';

// Message types
type Message = TextMessage | ToolUseMessage | ResultMessage;

// Result subtypes
type ResultSubtype =
  | 'success'
  | 'error_max_turns'
  | 'error_max_budget_usd'
  | 'error_during_execution'
  | 'error_max_structured_output_retries';

// Permission behaviors
type PermissionBehavior = 'allow' | 'block' | 'prompt';

// Permission modes
type PermissionMode = 'default' | 'acceptEdits' | 'bypassPermissions' | 'plan' | 'dontAsk';
```

## Best Practices

1. **Always set budget limits**: `maxBudgetUsd: 1.0`
2. **Use TypeScript types**: Import types for better IDE support
3. **Handle all result subtypes**: Check `message.subtype` before reading `message.result`
4. **Use streaming input for MCP**: Async generator required
5. **Capture session IDs**: Store `message.session_id` for resumption
6. **Use appropriate models**: Haiku for simple, Opus for complex
7. **Pre-approve safe tools**: `allowedTools: ['Read', 'Grep']`
8. **Return errors as text in tools**: Don't throw in tool handlers

## Official Documentation

For the latest TypeScript patterns and API reference:
- **Agent SDK API Reference**: https://platform.claude.com/docs/en/agent-sdk/api-reference
- **TypeScript Examples**: https://platform.claude.com/docs/en/agent-sdk/overview

For patterns not covered here, use fetch-library-docs to get the latest official documentation.
