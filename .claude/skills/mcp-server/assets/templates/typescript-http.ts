#!/usr/bin/env node
/**
 * HTTP MCP Server using TypeScript SDK
 * Demonstrates HTTP transport with authentication, tools, resources, and prompts.
 */

import { createServer, IncomingMessage, ServerResponse } from "node:http";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { z } from "zod";
import { randomUUID } from "node:crypto";

// Configuration
const PORT = parseInt(process.env.PORT || "3000");
const API_KEY = process.env.API_KEY || "demo-api-key";

// Create server instance
const server = new McpServer({
  name: "http-server",
  version: "1.0.0",
});

// ============================================================================
// TOOLS - Executable functions with side effects
// ============================================================================

server.tool(
  "search_database",
  "Search the database for records",
  {
    query: z.string().min(1).describe("Search query"),
    limit: z.number().min(1).max(100).default(10).describe("Maximum results"),
  },
  async ({ query, limit }) => {
    try {
      // Example: Query database
      const results = await mockDatabaseSearch(query, limit);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Database error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

server.tool(
  "send_notification",
  "Send a notification to users",
  {
    message: z.string().min(1).describe("Notification message"),
    recipients: z.array(z.string()).describe("List of recipient IDs"),
    priority: z.enum(["low", "normal", "high"]).default("normal"),
  },
  async ({ message, recipients, priority }) => {
    try {
      // Example: Send notifications
      console.log(`Sending ${priority} priority notification to ${recipients.length} recipients`);

      return {
        content: [
          {
            type: "text",
            text: `Notification sent to ${recipients.length} recipients`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Failed to send notification: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// ============================================================================
// RESOURCES - Read-only data sources
// ============================================================================

server.resource(
  {
    uri: "config://settings",
    name: "Server Settings",
    description: "Server configuration and settings",
    mimeType: "application/json",
  },
  async (uri) => {
    const settings = {
      server_name: "http-server",
      version: "1.0.0",
      environment: process.env.NODE_ENV || "development",
      port: PORT,
    };

    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(settings, null, 2),
        },
      ],
    };
  }
);

server.resource(
  {
    uri: "data://records/{id}",
    name: "Database Record",
    description: "Fetch a database record by ID",
    mimeType: "application/json",
  },
  async (uri) => {
    const match = uri.match(/data:\/\/records\/(.+)/);
    if (!match) {
      throw new Error("Invalid URI format");
    }

    const id = match[1];
    const record = await mockFetchRecord(id);

    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(record, null, 2),
        },
      ],
    };
  }
);

// ============================================================================
// PROMPTS - Reusable interaction templates
// ============================================================================

server.prompt(
  "sql_query_helper",
  "Generate SQL queries from natural language",
  {
    task: z.string().describe("What you want to query"),
    database_type: z.enum(["postgresql", "mysql", "sqlite"]).default("postgresql"),
  },
  async ({ task, database_type }) => {
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Generate a ${database_type} SQL query for: ${task}

Consider:
- Proper indexing and performance
- SQL injection prevention (use parameterized queries)
- Best practices for ${database_type}

Provide the query with explanation.`,
          },
        },
      ],
    };
  }
);

// ============================================================================
// AUTHENTICATION & HTTP SERVER
// ============================================================================

function verifyAuthentication(req: IncomingMessage): boolean {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return false;
  }

  const token = authHeader.substring(7);
  return token === API_KEY;
}

function setCORSHeaders(res: ServerResponse) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

// Create HTTP server
const httpServer = createServer(async (req, res) => {
  // Set CORS headers
  setCORSHeaders(res);

  // Handle preflight
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  // Only accept POST requests
  if (req.method !== "POST") {
    res.writeHead(405, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Method not allowed" }));
    return;
  }

  // Verify authentication
  if (!verifyAuthentication(req)) {
    res.writeHead(401, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Unauthorized" }));
    return;
  }

  // Handle MCP request
  try {
    const transport = new NodeStreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
    });

    await server.connect(transport);
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error("Request handling error:", error);
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Internal server error" }));
  }
});

// ============================================================================
// MOCK FUNCTIONS (Replace with real implementations)
// ============================================================================

async function mockDatabaseSearch(query: string, limit: number) {
  // Mock implementation
  return {
    total: 42,
    results: [
      { id: 1, title: "Result 1", content: `Matches query: ${query}` },
      { id: 2, title: "Result 2", content: `Another match for: ${query}` },
    ].slice(0, limit),
  };
}

async function mockFetchRecord(id: string) {
  // Mock implementation
  return {
    id,
    title: `Record ${id}`,
    created_at: new Date().toISOString(),
    data: { example: "data" },
  };
}

// ============================================================================
// MAIN
// ============================================================================

httpServer.listen(PORT, () => {
  console.log(`HTTP MCP server listening on port ${PORT}`);
  console.log(`Authentication: Bearer token required`);
  console.log(`API Key: ${API_KEY === "demo-api-key" ? "DEMO (set API_KEY env var)" : "configured"}`);
});

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("\nShutting down server...");
  httpServer.close(() => {
    console.log("Server closed");
    process.exit(0);
  });
});
