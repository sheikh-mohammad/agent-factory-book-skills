#!/usr/bin/env node
/**
 * Basic MCP Server using TypeScript SDK
 * A minimal example with one tool demonstrating core concepts.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create server instance
const server = new McpServer({
  name: "basic-server",
  version: "1.0.0",
});

// Register a simple tool
server.tool(
  "calculate",
  "Evaluate a mathematical expression",
  {
    expression: z.string().describe("Math expression to evaluate (e.g., '2 + 3 * 4')"),
  },
  async ({ expression }) => {
    try {
      // Note: eval() is used for simplicity. Use a safe math parser in production.
      const result = eval(expression);

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

// Connect and run server
async function main() {
  // Use stdio transport for local clients (Claude Desktop, VS Code)
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr (CRITICAL for stdio transport - never use console.log)
  console.error("Basic MCP server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
