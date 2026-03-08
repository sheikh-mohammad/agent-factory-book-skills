# TypeScript SDK Reference

Complete guide to building MCP servers with TypeScript using the official MCP SDK.

## Installation

```bash
npm install @modelcontextprotocol/sdk zod@3
npm install -D @types/node typescript

# For HTTP transport (Node.js)
npm install @modelcontextprotocol/node

# For HTTP transport (Express)
npm install @modelcontextprotocol/express

# For HTTP transport (Hono)
npm install @modelcontextprotocol/hono
```

**Requirements**: Node.js 16 or higher

---

## Basic Server Setup

### Project Configuration

**package.json**:
```json
{
  "type": "module",
  "bin": {
    "my-server": "./build/index.js"
  },
  "scripts": {
    "build": "tsc && chmod 755 build/index.js"
  }
}
```

**tsconfig.json**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

### Server Initialization

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create server instance
const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Connect via stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## Implementing Tools

Tools are registered using `server.tool()` with Zod schemas for validation.

### Basic Tool

```typescript
server.tool(
  "calculate",
  "Evaluate a mathematical expression",
  {
    expression: z.string().describe("Math expression to evaluate"),
  },
  async ({ expression }) => {
    try {
      const result = eval(expression); // Use safe-eval in production
      return {
        content: [
          {
            type: "text",
            text: `Result: ${result}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
);
```

### Tool with Multiple Parameters

```typescript
server.tool(
  "search_database",
  "Search the database for records",
  {
    query: z.string().describe("Search query"),
    limit: z.number().default(10).describe("Maximum results"),
    offset: z.number().default(0).describe("Results offset"),
  },
  async ({ query, limit, offset }) => {
    // Perform search
    const results = await database.search(query, limit, offset);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(results, null, 2),
        },
      ],
    };
  }
);
```

### Tool with Complex Schema

```typescript
const UserSchema = z.object({
  name: z.string(),
  email: z.string().email(),
  age: z.number().min(0).max(150),
  roles: z.array(z.enum(["admin", "user", "guest"])),
});

server.tool(
  "create_user",
  "Create a new user account",
  {
    user: UserSchema.describe("User information"),
  },
  async ({ user }) => {
    // Validate and create user
    const newUser = await database.createUser(user);

    return {
      content: [
        {
          type: "text",
          text: `User created: ${newUser.id}`,
        },
      ],
    };
  }
);
```

### Tool with Progress Reporting

```typescript
server.tool(
  "process_large_file",
  "Process a large file with progress updates",
  {
    filepath: z.string().describe("Path to file"),
  },
  async ({ filepath }, { progressToken }) => {
    const fileSize = await getFileSize(filepath);
    let processed = 0;

    // Report progress
    if (progressToken) {
      await server.notification({
        method: "notifications/progress",
        params: {
          progressToken,
          progress: 0,
          total: fileSize,
        },
      });
    }

    // Process file in chunks
    for await (const chunk of readFileChunks(filepath)) {
      await processChunk(chunk);
      processed += chunk.length;

      if (progressToken) {
        await server.notification({
          method: "notifications/progress",
          params: {
            progressToken,
            progress: processed,
            total: fileSize,
          },
        });
      }
    }

    return {
      content: [
        {
          type: "text",
          text: `Processed ${processed} bytes`,
        },
      ],
    };
  }
);
```

---

## Implementing Resources

Resources expose data via URI patterns.

### Basic Resource

```typescript
server.resource(
  {
    uri: "file://documents/{name}",
    name: "Document",
    description: "Read document contents",
    mimeType: "text/plain",
  },
  async (uri) => {
    // Extract name from URI
    const match = uri.match(/file:\/\/documents\/(.+)/);
    if (!match) {
      throw new Error("Invalid URI");
    }

    const name = match[1];
    const content = await fs.readFile(`documents/${name}`, "utf-8");

    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: content,
        },
      ],
    };
  }
);
```

### Resource with Multiple Content Types

```typescript
server.resource(
  {
    uri: "api://data/{id}",
    name: "API Data",
    description: "Fetch data from API",
  },
  async (uri) => {
    const match = uri.match(/api:\/\/data\/(.+)/);
    const id = match?.[1];

    const data = await fetchFromAPI(id);

    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(data, null, 2),
        },
        {
          uri: `${uri}/summary`,
          mimeType: "text/plain",
          text: `Summary: ${data.title}`,
        },
      ],
    };
  }
);
```

### Dynamic Resource Listing

```typescript
server.setRequestHandler("resources/list", async () => {
  // Dynamically list available resources
  const files = await fs.readdir("documents");

  return {
    resources: files.map((file) => ({
      uri: `file://documents/${file}`,
      name: file,
      description: `Document: ${file}`,
      mimeType: "text/plain",
    })),
  };
});
```

---

## Implementing Prompts

Prompts are reusable templates for LLM interactions.

### Basic Prompt

```typescript
server.prompt(
  "code_review",
  "Generate a code review prompt",
  {
    language: z.string().describe("Programming language"),
    focus: z.string().default("best practices").describe("Review focus"),
  },
  async ({ language, focus }) => {
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Review this ${language} code focusing on ${focus}.

Provide specific, actionable feedback on:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Security concerns`,
          },
        },
      ],
    };
  }
);
```

### Prompt with Context

```typescript
server.prompt(
  "debug_assistant",
  "Help debug an error",
  {
    error: z.string().describe("Error message"),
    context: z.string().optional().describe("Additional context"),
  },
  async ({ error, context }) => {
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `I'm encountering this error: ${error}

${context ? `Context: ${context}` : ""}

Please help me:
1. Understand what's causing this error
2. Suggest potential solutions
3. Provide code examples if applicable`,
          },
        },
      ],
    };
  }
);
```

---

## HTTP Transport

### Node.js HTTP Server

```typescript
import { createServer } from "node:http";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";

const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Register tools, resources, prompts...

// Create HTTP server
createServer(async (req, res) => {
  const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });

  await server.connect(transport);
  await transport.handleRequest(req, res);
}).listen(3000, () => {
  console.error("Server listening on port 3000");
});
```

### Express Integration

```typescript
import express from "express";
import { ExpressStreamableHTTPServerTransport } from "@modelcontextprotocol/express";

const app = express();
const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Register tools, resources, prompts...

app.post("/mcp", async (req, res) => {
  const transport = new ExpressStreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });

  await server.connect(transport);
  await transport.handleRequest(req, res);
});

app.listen(3000, () => {
  console.error("Server listening on port 3000");
});
```

### Authentication

```typescript
import { createServer } from "node:http";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";

createServer(async (req, res) => {
  // Verify authentication
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    res.writeHead(401, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Unauthorized" }));
    return;
  }

  const token = authHeader.substring(7);
  if (!verifyToken(token)) {
    res.writeHead(403, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Invalid token" }));
    return;
  }

  // Handle MCP request
  const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });

  await server.connect(transport);
  await transport.handleRequest(req, res);
}).listen(3000);
```

---

## Error Handling

### Tool Error Handling

```typescript
server.tool(
  "risky_operation",
  "Operation that might fail",
  {
    param: z.string().min(1),
  },
  async ({ param }) => {
    try {
      // Validate
      if (!isValid(param)) {
        throw new Error("Invalid parameter");
      }

      // Perform operation
      const result = await externalApiCall(param);

      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    } catch (error) {
      console.error("Operation failed:", error);

      return {
        content: [
          {
            type: "text",
            text: `Operation failed: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
);
```

### Global Error Handler

```typescript
process.on("uncaughtException", (error) => {
  console.error("Uncaught exception:", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled rejection at:", promise, "reason:", reason);
  process.exit(1);
});
```

---

## Logging

### STDIO Transport (Critical)

**NEVER use `console.log()`** - it corrupts JSON-RPC messages.

```typescript
// ❌ WRONG - breaks stdio
console.log("Processing request");

// ✅ CORRECT - writes to stderr
console.error("Processing request");

// ✅ CORRECT - use logging library
import winston from "winston";

const logger = winston.createLogger({
  transports: [new winston.transports.Console({ stream: process.stderr })],
});

logger.info("Processing request");
```

### HTTP Transport

Standard logging is fine:

```typescript
console.log("HTTP server started on port 3000");
```

---

## Complete Example: Weather Server

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const NWS_API_BASE = "https://api.weather.gov";
const USER_AGENT = "weather-app/1.0";

// Create server
const server = new McpServer({
  name: "weather",
  version: "1.0.0",
});

// Helper function
async function makeNWSRequest<T>(url: string): Promise<T | null> {
  const headers = {
    "User-Agent": USER_AGENT,
    Accept: "application/geo+json",
  };

  try {
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return (await response.json()) as T;
  } catch (error) {
    console.error("NWS API error:", error);
    return null;
  }
}

// Register tools
server.tool(
  "get_forecast",
  "Get weather forecast for a location",
  {
    latitude: z.number().describe("Latitude"),
    longitude: z.number().describe("Longitude"),
  },
  async ({ latitude, longitude }) => {
    // Get forecast grid endpoint
    const pointsUrl = `${NWS_API_BASE}/points/${latitude},${longitude}`;
    const pointsData = await makeNWSRequest<any>(pointsUrl);

    if (!pointsData) {
      return {
        content: [
          {
            type: "text",
            text: "Unable to fetch forecast data.",
          },
        ],
        isError: true,
      };
    }

    // Get forecast
    const forecastUrl = pointsData.properties.forecast;
    const forecastData = await makeNWSRequest<any>(forecastUrl);

    if (!forecastData) {
      return {
        content: [
          {
            type: "text",
            text: "Unable to fetch detailed forecast.",
          },
        ],
        isError: true,
      };
    }

    // Format periods
    const periods = forecastData.properties.periods.slice(0, 5);
    const forecasts = periods.map(
      (period: any) => `
${period.name}:
Temperature: ${period.temperature}°${period.temperatureUnit}
Wind: ${period.windSpeed} ${period.windDirection}
Forecast: ${period.detailedForecast}
`
    );

    return {
      content: [
        {
          type: "text",
          text: forecasts.join("\n---\n"),
        },
      ],
    };
  }
);

// Connect and run
const transport = new StdioServerTransport();
await server.connect(transport);

console.error("Weather MCP server running on stdio");
```

---

## Testing

### Unit Testing

```typescript
import { describe, it, expect } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

describe("Weather Server", () => {
  it("should register tools correctly", async () => {
    const server = new McpServer({
      name: "weather",
      version: "1.0.0",
    });

    // Register tools...

    const tools = await server.listTools();
    expect(tools.tools).toHaveLength(1);
    expect(tools.tools[0].name).toBe("get_forecast");
  });
});
```

### Integration Testing

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

describe("Server Integration", () => {
  it("should handle tool calls", async () => {
    const transport = new StdioClientTransport({
      command: "node",
      args: ["build/index.js"],
    });

    const client = new Client({
      name: "test-client",
      version: "1.0.0",
    });

    await client.connect(transport);

    const result = await client.callTool("get_forecast", {
      latitude: 37.7749,
      longitude: -122.4194,
    });

    expect(result.content[0].text).toContain("Temperature");
  });
});
```

---

## Performance Tips

1. **Connection pooling** - Reuse HTTP clients
2. **Caching** - Cache expensive operations
3. **Async operations** - Use async/await properly
4. **Timeouts** - Set timeouts on external calls
5. **Resource cleanup** - Close connections on shutdown

```typescript
// Connection pooling
const httpClient = new HttpClient();

server.tool("fetch_data", "Fetch data", { url: z.string() }, async ({ url }) => {
  const response = await httpClient.get(url, { timeout: 10000 });
  return { content: [{ type: "text", text: response.data }] };
});

// Cleanup on shutdown
process.on("SIGINT", async () => {
  await httpClient.close();
  process.exit(0);
});
```
