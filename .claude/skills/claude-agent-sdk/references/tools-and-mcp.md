# Tools and MCP Integration

Complete guide to built-in tools and custom MCP tools in Claude Agent SDK.

## Built-in Tools

The Agent SDK provides these tools out of the box:

### File Operations

**Read** - Read file contents
```typescript
// Agent can use: Read file_path="/path/to/file.txt"
```

**Write** - Create or overwrite files
```typescript
// Agent can use: Write file_path="/path/to/file.txt" content="..."
```

**Edit** - Make targeted edits to existing files
```typescript
// Agent can use: Edit file_path="/path/to/file.txt" old_string="..." new_string="..."
```

### Search Tools

**Glob** - Find files by pattern
```typescript
// Agent can use: Glob pattern="**/*.ts"
```

**Grep** - Search file contents
```typescript
// Agent can use: Grep pattern="function.*login" path="src/"
```

### Execution

**Bash** - Run shell commands
```typescript
// Agent can use: Bash command="npm test"
```

**⚠️ Security**: Bash is powerful but dangerous. Use `allowedTools`/`disallowedTools` carefully.

### Web Access

**WebSearch** - Search the web
```typescript
// Agent can use: WebSearch query="latest React patterns"
```

**WebFetch** - Fetch and process web pages
```typescript
// Agent can use: WebFetch url="https://example.com" prompt="Extract pricing"
```

### Orchestration

**Agent** - Spawn subagents for specialized tasks
```typescript
// Agent can use: Agent description="Security review" prompt="Check for vulnerabilities"
```

**Skill** - Load and execute skills
```typescript
// Agent can use: Skill skill="commit" args="-m 'Fix bug'"
```

**AskUserQuestion** - Ask user for input during execution
```typescript
// Agent can use: AskUserQuestion questions=[...]
```

## Custom Tools via MCP

Model Context Protocol (MCP) lets you create custom tools that agents can use.

### TypeScript: Creating MCP Tools

```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Define tool with Zod schema
const weatherTool = tool(
  "get_weather",
  "Get current temperature for a location",
  {
    latitude: z.number().describe("Latitude coordinate"),
    longitude: z.number().describe("Longitude coordinate")
  },
  async (args) => {
    try {
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m`
      );
      const data = await response.json();

      return {
        content: [{
          type: "text",
          text: `Temperature: ${data.current.temperature_2m}°F`
        }]
      };
    } catch (error) {
      // Always return error as text, don't throw
      return {
        content: [{
          type: "text",
          text: `Failed to fetch weather: ${error.message}`
        }]
      };
    }
  }
);

// Create MCP server
const weatherServer = createSdkMcpServer({
  name: "weather",
  version: "1.0.0",
  tools: [weatherTool]
});

// Use in agent
async function* generateMessages() {
  yield { role: "user", content: "What's the weather in San Francisco?" };
}

for await (const message of query({
  prompt: generateMessages(), // MCP requires streaming input
  options: {
    mcpServers: { weather: weatherServer },
    allowedTools: ["mcp__weather__get_weather"]
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Python: Creating MCP Tools

```python
from claude_agent_sdk import query, ClaudeAgentOptions, create_sdk_mcp_server, tool
from pydantic import BaseModel, Field
import httpx

# Define tool schema with Pydantic
class WeatherArgs(BaseModel):
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")

# Define tool handler
async def get_weather(args: WeatherArgs):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": args.latitude,
                    "longitude": args.longitude,
                    "current": "temperature_2m"
                }
            )
            data = response.json()

            return {
                "content": [{
                    "type": "text",
                    "text": f"Temperature: {data['current']['temperature_2m']}°F"
                }]
            }
    except Exception as e:
        # Always return error as text, don't raise
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to fetch weather: {str(e)}"
            }]
        }

# Create tool
weather_tool = tool(
    name="get_weather",
    description="Get current temperature for a location",
    parameters=WeatherArgs,
    handler=get_weather
)

# Create MCP server
weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[weather_tool]
)

# Use in agent
async def generate_messages():
    yield {"role": "user", "content": "What's the weather in San Francisco?"}

async def main():
    async for message in query(
        prompt=generate_messages(),  # MCP requires streaming input
        options=ClaudeAgentOptions(
            mcp_servers={"weather": weather_server},
            allowed_tools=["mcp__weather__get_weather"]
        )
    ):
        if hasattr(message, "result"):
            print(message.result)
```

## MCP Tool Naming Convention

MCP tools follow this pattern:
```
mcp__<server-name>__<tool-name>
```

Examples:
- `mcp__weather__get_weather`
- `mcp__database__query_users`
- `mcp__slack__send_message`

## Tool Best Practices

### 1. Error Handling

**❌ Don't throw errors:**
```typescript
async (args) => {
  const response = await fetch(url); // Throws on network error
  return { content: [{ type: "text", text: await response.text() }] };
}
```

**✅ Return errors as text:**
```typescript
async (args) => {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return { content: [{ type: "text", text: `HTTP ${response.status}` }] };
    }
    return { content: [{ type: "text", text: await response.text() }] };
  } catch (error) {
    return { content: [{ type: "text", text: `Error: ${error.message}` }] };
  }
}
```

### 2. Schema Design

**Use descriptive field names and descriptions:**
```typescript
{
  latitude: z.number().describe("Latitude coordinate (-90 to 90)"),
  longitude: z.number().describe("Longitude coordinate (-180 to 180)"),
  units: z.enum(["celsius", "fahrenheit"]).describe("Temperature units")
}
```

### 3. Response Format

**Return structured text that Claude can parse:**
```typescript
return {
  content: [{
    type: "text",
    text: JSON.stringify({ temperature: 72, conditions: "sunny" }, null, 2)
  }]
};
```

### 4. Streaming Input Requirement

**⚠️ Critical**: MCP tools require streaming input (async generator for prompt).

**❌ Won't work:**
```typescript
query({
  prompt: "Use weather tool",
  options: { mcpServers: { weather: weatherServer } }
})
```

**✅ Correct:**
```typescript
async function* generateMessages() {
  yield { role: "user", content: "Use weather tool" };
}

query({
  prompt: generateMessages(),
  options: { mcpServers: { weather: weatherServer } }
})
```

## Tool Configuration

### Pre-approve Tools

```typescript
options: {
  allowedTools: [
    "Read", "Grep", "Glob",  // Built-in
    "mcp__weather__get_weather"  // Custom MCP
  ]
}
```

### Block Tools

```typescript
options: {
  disallowedTools: ["Bash", "Write"]
}
```

### Tool Hooks

Intercept tool calls before execution:

```typescript
options: {
  canUseTool: async (toolName, toolInput) => {
    // Block dangerous bash commands
    if (toolName === "Bash" && toolInput.command.includes("rm -rf")) {
      return { behavior: "block", message: "Dangerous command blocked" };
    }

    // Log file writes
    if (toolName === "Write") {
      console.log(`Writing to ${toolInput.file_path}`);
    }

    return { behavior: "allow" };
  }
}
```

## Complete MCP Example

See `examples/typescript/mcp-weather-agent.ts` and `examples/python/mcp_weather_agent.py` for complete working examples.

## External MCP Servers

You can also connect to external MCP servers (not created with SDK):

```typescript
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const externalServer = new StdioClientTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
});

options: {
  mcpServers: { filesystem: externalServer }
}
```

See MCP documentation for more on external servers.

## Official Documentation

For the latest information on tools and MCP integration:
- **Agent SDK Tools**: https://platform.claude.com/docs/en/agent-sdk/overview
- **MCP Documentation**: https://modelcontextprotocol.io/

For patterns not covered here, use fetch-library-docs to get the latest official documentation.
