---
name: mcp-server
description: |
  Build Model Context Protocol (MCP) servers from hello world to production systems. Create servers that expose tools, resources, and prompts to AI applications like Claude Desktop, VS Code, and custom clients. Supports TypeScript and Python SDKs with stdio and HTTP transports.
  This skill should be used when users ask to create MCP servers, build context providers, implement MCP tools/resources/prompts, integrate with AI applications, or deploy MCP infrastructure.
version: "1.0.0"
---

# MCP Server Builder

Build production-ready Model Context Protocol servers that connect AI applications to external data and tools.

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing MCP servers, project structure, language preferences (TypeScript/Python) |
| **Conversation** | User's specific requirements: what tools/resources/prompts to expose, transport type, deployment target |
| **Skill References** | MCP SDK patterns from `references/` (official docs, implementation examples, best practices) |
| **User Guidelines** | Project conventions, security requirements, deployment constraints |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

## What This Skill Does

- Creates MCP servers exposing tools, resources, and prompts
- Implements both TypeScript and Python servers
- Configures stdio transport (local) and HTTP transport (remote)
- Sets up proper error handling, logging, and validation
- Provides production deployment patterns
- Integrates with Claude Desktop, VS Code, and custom clients

## What This Skill Does NOT Do

- Build MCP clients (use separate client implementation)
- Create AI models or LLM logic
- Handle non-MCP protocols
- Manage infrastructure provisioning (provides deployment guidance only)

## Official Resources

- **MCP Specification**: https://modelcontextprotocol.io (Protocol version: 2025-06-18)
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk (v1.2.0+)
- **TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk (v2 pre-alpha, v1.x for production)
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector

**For patterns not covered in references**: Use the `fetch-library-docs` skill to retrieve latest MCP documentation and examples.

---

## Required Clarifications

Ask user to specify (avoid asking all questions at once):

1. **Language** (Required): TypeScript or Python?
   - Default: Python (simpler with FastMCP)

2. **Server Purpose** (Required): What data/tools should the server expose?
   - Examples: Database access, file system, API integration, custom workflow

## Optional Clarifications

3. **Transport**: stdio (local) or HTTP (remote)?
   - Default: stdio (for Claude Desktop, VS Code)

4. **Primitives**: Which to implement?
   - Tools (actions with side effects)
   - Resources (read-only data)
   - Prompts (interaction templates)
   - Default: Tools

5. **Deployment Target**: Where will this run?
   - Claude Desktop, VS Code, Custom client, Cloud
   - Default: Claude Desktop

**Interaction Guidelines**:
- Start with language and purpose (questions 1-2)
- Ask additional questions based on user's needs
- If user doesn't specify optional parameters, proceed with defaults without re-asking
- Gather context from codebase and conversation before asking questions

---

## Implementation Workflow

### 1. Gather Requirements

Use clarifications above to understand user's needs.

### 2. Choose Implementation Pattern

| Pattern | When to Use | SDK |
|---------|-------------|-----|
| **FastMCP (Python)** | Quick development, simple servers, automatic schema generation | `mcp[cli]` |
| **McpServer (TypeScript)** | Complex servers, Node.js ecosystem, type safety | `@modelcontextprotocol/sdk` |
| **McpServer (Python)** | Advanced control, custom lifecycle management | `mcp` |

**Recommendation**: Start with FastMCP for Python or McpServer for TypeScript.

### 3. Initialize Project

**Python (FastMCP)**:
```bash
uv init my-mcp-server
cd my-mcp-server
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv add "mcp[cli]"
```

**TypeScript**:
```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod@3
npm install -D @types/node typescript
```

### 4. Implement Server Components

Follow this order:

1. **Server initialization** - Create server instance with name/version
2. **Implement primitives** - Add tools, resources, or prompts
3. **Add error handling** - Validate inputs, handle failures gracefully
4. **Configure transport** - Set up stdio or HTTP
5. **Add logging** - Use stderr for stdio, standard logging for HTTP

See `references/typescript-sdk.md` or `references/python-sdk.md` for detailed implementation.

### 5. Test Locally

**With MCP Inspector** (recommended):
```bash
npx @modelcontextprotocol/inspector <command> <args>
```

**With Claude Desktop**:
- Configure in `claude_desktop_config.json`
- Restart Claude Desktop
- Test tools in conversation

See `references/testing.md` for comprehensive testing strategies.

### 6. Deploy

| Deployment | Transport | Use Case |
|------------|-----------|----------|
| **Claude Desktop** | stdio | Local development, personal use |
| **VS Code** | stdio | IDE integration |
| **Cloud (HTTP)** | Streamable HTTP | Remote access, multi-user, production |
| **Docker** | stdio or HTTP | Containerized deployment |

See `references/deployment.md` for deployment patterns.

---

## Core Primitives

### Tools

Executable functions that AI can invoke to perform actions.

**When to use**: Actions with side effects (API calls, file operations, database queries)

**Python (FastMCP)**:
```python
@mcp.tool()
async def search_database(query: str, limit: int = 10) -> str:
    """Search the database for records.

    Args:
        query: Search query string
        limit: Maximum number of results
    """
    # Implementation
    return results
```

**TypeScript**:
```typescript
server.tool("search_database", "Search the database", {
  query: z.string().describe("Search query"),
  limit: z.number().default(10)
}, async ({ query, limit }) => {
  // Implementation
  return { content: [{ type: "text", text: results }] };
});
```

### Resources

Data sources that provide contextual information (read-only).

**When to use**: Exposing file contents, database records, API responses

**Python (FastMCP)**:
```python
@mcp.resource("file://documents/{name}")
async def read_document(name: str) -> str:
    """Read a document by name."""
    # Implementation
    return content
```

**TypeScript**:
```typescript
server.resource({
  uri: "file://documents/{name}",
  name: "Document",
  description: "Read document contents"
}, async (uri) => {
  // Implementation
  return { contents: [{ uri, mimeType: "text/plain", text: content }] };
});
```

### Prompts

Reusable templates for structuring LLM interactions.

**When to use**: Common workflows, few-shot examples, system prompts

**Python (FastMCP)**:
```python
@mcp.prompt()
async def code_review_prompt(language: str) -> str:
    """Generate a code review prompt."""
    return f"Review this {language} code for best practices..."
```

See `references/tools-resources-prompts.md` for comprehensive primitive documentation.

---

## Critical Logging Rules

### STDIO Transport (Local Servers)

**NEVER write to stdout** - it corrupts JSON-RPC messages and breaks the server.

**Python**:
```python
# ❌ WRONG - breaks stdio
print("Processing request")

# ✅ CORRECT - writes to stderr
print("Processing request", file=sys.stderr)
logging.info("Processing request")  # Uses stderr by default
```

**TypeScript**:
```typescript
// ❌ WRONG - breaks stdio
console.log("Processing request");

// ✅ CORRECT - writes to stderr
console.error("Processing request");
```

### HTTP Transport (Remote Servers)

Standard logging is fine - stdout doesn't interfere with HTTP responses.

---

## Transport Configuration

### STDIO (Local)

**Use for**: Claude Desktop, VS Code, local development

**Python**: `mcp.run(transport="stdio")`
**TypeScript**: `const transport = new StdioServerTransport(); await server.connect(transport);`

**Client Configuration**: See `references/client-configuration.md` for Claude Desktop and VS Code setup.

### Streamable HTTP (Remote)

**Use for**: Cloud deployment, remote access, multi-user

**Python**: `mcp.run(transport="streamable-http", port=8000)`
**TypeScript**: Use `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node`

See `references/deployment.md` for production HTTP configuration with authentication.

---

## Error Handling

Always validate inputs and handle errors gracefully:

**Python**:
```python
@mcp.tool()
async def risky_operation(param: str) -> str:
    """Operation that might fail."""
    try:
        # Validate input
        if not param:
            raise ValueError("Parameter cannot be empty")

        # Perform operation
        result = await external_api_call(param)
        return result

    except ValueError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        return "Operation failed. Please try again."
```

**TypeScript**:
```typescript
server.tool("risky_operation", "Operation that might fail", {
  param: z.string().min(1)
}, async ({ param }) => {
  try {
    const result = await externalApiCall(param);
    return { content: [{ type: "text", text: result }] };
  } catch (error) {
    console.error("Operation failed:", error);
    return {
      content: [{ type: "text", text: "Operation failed" }],
      isError: true
    };
  }
});
```

---

## Quick Start Templates

Use templates from `assets/templates/`:

- `python-fastmcp-basic.py` - Simple FastMCP server with tools
- `python-fastmcp-full.py` - Full-featured server with tools, resources, prompts
- `typescript-basic.ts` - Simple TypeScript server
- `typescript-http.ts` - HTTP server with authentication

---

## Reference Files

| File | Content | Search Keywords |
|------|---------|-----------------|
| `references/python-sdk.md` | Complete Python SDK documentation (FastMCP, McpServer) | "FastMCP", "tool", "resource", "prompt", "Context" |
| `references/typescript-sdk.md` | Complete TypeScript SDK documentation | "McpServer", "tool", "resource", "prompt", "HTTP" |
| `references/tools-resources-prompts.md` | Detailed primitive implementation patterns | "Tools", "Resources", "Prompts", "validation" |
| `references/deployment.md` | Production deployment strategies (Docker, cloud, monitoring) | "Docker", "AWS", "HTTP", "authentication", "monitoring" |
| `references/best-practices.md` | Security, performance, error handling, testing | "Security", "Performance", "Testing", "SQL injection", "caching" |
| `references/testing.md` | Testing strategies with MCP Inspector and clients | "MCP Inspector", "pytest", "integration", "load testing" |
| `references/client-configuration.md` | Configuring Claude Desktop, VS Code, custom clients | "Claude Desktop", "VS Code", "config", "environment" |

**For large files (>500 lines)**: Use grep to find specific topics. Example: `grep -n "Security" references/best-practices.md`

**For unlisted patterns or latest updates**: Use `fetch-library-docs` skill with library "modelcontextprotocol" to retrieve current documentation.

---

## Common Patterns

### Pattern 1: Database Query Server

Expose database as tools and resources:
- **Tools**: Execute queries, insert/update records
- **Resources**: Expose schema, table contents
- **Transport**: stdio for local, HTTP for remote

### Pattern 2: File System Server

Provide file access to AI:
- **Tools**: Read, write, search files
- **Resources**: File contents by URI pattern
- **Security**: Validate paths, restrict access

### Pattern 3: API Integration Server

Connect AI to external APIs:
- **Tools**: API operations (search, create, update)
- **Resources**: Cached API responses
- **Error Handling**: Rate limiting, retry logic

### Pattern 4: Multi-Tool Workflow Server

Complex operations requiring multiple steps:
- **Tools**: Individual operations
- **Prompts**: Workflow templates
- **Context**: Use sampling/elicitation for user input

See `references/best-practices.md` for detailed pattern implementations.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Server not appearing in Claude Desktop | Config error, wrong path | Check `claude_desktop_config.json`, use absolute paths |
| "Server disconnected" error | Stdout corruption | Remove all `console.log()` / `print()` statements |
| Tools not executing | Schema validation error | Check input schema matches tool signature |
| Slow performance | Blocking operations | Use async/await, avoid synchronous I/O |
| Authentication failures | Missing headers | Configure bearer tokens, API keys properly |

See `references/best-practices.md` for comprehensive troubleshooting.

---

## Output Checklist

Before delivering the server, verify:

- [ ] Server initializes without errors
- [ ] Tools/resources/prompts registered correctly
- [ ] Input validation implemented on all tools
- [ ] Error handling in place for all operations
- [ ] Logging configured correctly (stderr for stdio, standard for HTTP)
- [ ] Transport configured (stdio or HTTP)
- [ ] Client configuration provided (claude_desktop_config.json or equivalent)
- [ ] Testing instructions included
- [ ] Security considerations addressed (authentication, input sanitization)
- [ ] Documentation complete (tool descriptions, usage examples)

---

## Next Steps After Implementation

1. **Test thoroughly** - Use MCP Inspector and real clients
2. **Add monitoring** - Log errors, track usage, measure performance
3. **Document tools** - Clear descriptions help AI use tools correctly
4. **Secure deployment** - Add authentication, validate inputs, restrict access
5. **Iterate based on usage** - Monitor how AI uses tools, refine as needed

See `references/deployment.md` for production readiness checklist.
