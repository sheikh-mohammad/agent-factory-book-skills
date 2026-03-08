# Getting Started with Claude Agent SDK

## What is Claude Agent SDK?

The Claude Agent SDK embeds Claude Code's autonomous agent capabilities into your applications. Unlike the Client SDK where you implement tool execution yourself, the Agent SDK handles tool execution autonomously - you provide the prompt and configuration, Claude does the rest.

**Key Difference:**
- **Client SDK**: You send prompts and implement tool execution
- **Agent SDK**: Claude handles tool execution autonomously with built-in agent loop

## Installation

### TypeScript

```bash
npm install @anthropic-ai/claude-agent-sdk
```

### Python

```bash
pip install claude-agent-sdk
```

## Authentication

Set your API key as an environment variable:

```bash
export ANTHROPIC_API_KEY=your-api-key
```

**Alternative Providers:**
- Amazon Bedrock: `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- Google Vertex AI: `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_REGION`
- Microsoft Azure: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`

## Hello World

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "What files are in this directory?",
  options: { allowedTools: ["Bash", "Glob"] }
})) {
  if ("result" in message) {
    console.log(message.result);
  }
}
```

### Python

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

## How It Works

1. **You provide**: Prompt + configuration (tools, permissions, model)
2. **SDK handles**: Tool execution, agent loop, context management
3. **Agent loop**: Claude evaluates → calls tools → SDK executes → feeds results back → repeat until complete
4. **You receive**: Stream of messages including final result

## Message Types

### TypeScript

```typescript
for await (const message of query({ prompt: "Task" })) {
  if (message.type === "text") {
    // Claude's text response
    console.log(message.text);
  } else if (message.type === "tool_use") {
    // Tool being called (informational)
    console.log(`Calling ${message.name}`);
  } else if (message.type === "result") {
    // Final result
    if (message.subtype === "success") {
      console.log(message.result);
    }
  }
}
```

### Python

```python
async for message in query(prompt="Task"):
    if message.type == "text":
        print(message.text)
    elif message.type == "tool_use":
        print(f"Calling {message.name}")
    elif message.type == "result":
        if message.subtype == "success":
            print(message.result)
```

## Next Steps

- **Configuration**: See `agent-configuration.md` for all options
- **Tools**: See `tools-and-mcp.md` for built-in and custom tools
- **Sessions**: See `state-management.md` for multi-turn conversations
- **Examples**: See `examples/` for complete implementations

## Official Documentation

For the latest information and updates:

- **Agent SDK Overview**: https://platform.claude.com/docs/en/agent-sdk/overview
- **API Reference**: https://platform.claude.com/docs/en/agent-sdk/api-reference
- **Migration Guide**: https://platform.claude.com/docs/en/agent-sdk/migration-guide
- **Hosting Guide**: https://platform.claude.com/docs/en/agent-sdk/hosting

Always check official documentation for the most current patterns and best practices.
