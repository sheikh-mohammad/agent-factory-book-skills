# Client Configuration

Guide to configuring MCP servers with different clients including Claude Desktop, VS Code, and custom clients.

## Claude Desktop

### Configuration File Location

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Basic Configuration

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"]
    }
  }
}
```

### Python Server (uv)

```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/server",
        "run",
        "server.py"
      ]
    }
  }
}
```

**Windows Path Example**:
```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\username\\projects\\my-server",
        "run",
        "server.py"
      ]
    }
  }
}
```

### Python Server (pip/venv)

```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

### TypeScript/Node Server

```json
{
  "mcpServers": {
    "my-node-server": {
      "command": "node",
      "args": ["/absolute/path/to/build/index.js"]
    }
  }
}
```

### With Environment Variables

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "API_KEY": "your-api-key",
        "DATABASE_URL": "postgresql://localhost/mydb",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Multiple Servers

```json
{
  "mcpServers": {
    "database-server": {
      "command": "python",
      "args": ["/path/to/database-server.py"],
      "env": {
        "DATABASE_URL": "postgresql://localhost/mydb"
      }
    },
    "filesystem-server": {
      "command": "node",
      "args": ["/path/to/filesystem-server/build/index.js"]
    },
    "api-server": {
      "command": "uv",
      "args": ["--directory", "/path/to/api-server", "run", "server.py"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

### Troubleshooting Claude Desktop

**Server not appearing**:
- Check JSON syntax (use a JSON validator)
- Verify absolute paths (no relative paths or ~)
- Restart Claude Desktop after config changes
- Check logs: `~/Library/Logs/Claude/` (macOS) or `%APPDATA%\Claude\logs\` (Windows)

**"Server disconnected" error**:
- Remove all `console.log()` / `print()` statements (use stderr)
- Check server starts successfully: run command manually
- Verify dependencies are installed
- Check for syntax errors in server code

**Tools not showing**:
- Verify server implements tools correctly
- Check tool schemas are valid
- Look for errors in Claude Desktop logs

---

## VS Code

### Configuration

Add to `.vscode/settings.json` or user settings:

```json
{
  "mcp.servers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### Workspace-Relative Paths

```json
{
  "mcp.servers": {
    "workspace-server": {
      "command": "python",
      "args": ["${workspaceFolder}/server.py"]
    }
  }
}
```

### Multiple Workspaces

```json
{
  "mcp.servers": {
    "project-a-server": {
      "command": "python",
      "args": ["${workspaceFolder:project-a}/server.py"]
    },
    "project-b-server": {
      "command": "node",
      "args": ["${workspaceFolder:project-b}/build/index.js"]
    }
  }
}
```

---

## Custom Clients

### Python Client

```python
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    # Connect to server via stdio
    async with stdio_client("python", ["server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Call a tool
            result = await session.call_tool("calculate", {
                "expression": "2 + 3"
            })
            print(f"Result: {result.content[0].text}")

            # List resources
            resources = await session.list_resources()
            print(f"Available resources: {[r.uri for r in resources.resources]}")

            # Read a resource
            if resources.resources:
                content = await session.read_resource(resources.resources[0].uri)
                print(f"Resource content: {content}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### TypeScript Client

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function main() {
  // Create transport
  const transport = new StdioClientTransport({
    command: 'python',
    args: ['server.py'],
  });

  // Create client
  const client = new Client({
    name: 'my-client',
    version: '1.0.0',
  });

  // Connect
  await client.connect(transport);

  // List tools
  const tools = await client.listTools();
  console.log('Available tools:', tools.tools.map(t => t.name));

  // Call tool
  const result = await client.callTool('calculate', {
    expression: '2 + 3',
  });
  console.log('Result:', result.content[0].text);

  // List resources
  const resources = await client.listResources();
  console.log('Available resources:', resources.resources.map(r => r.uri));

  // Close connection
  await client.close();
}

main().catch(console.error);
```

### HTTP Client (Python)

```python
import httpx
import json

async def call_mcp_http_server():
    """Call MCP server via HTTP."""
    url = "https://your-server.com/mcp"
    headers = {
        "Authorization": "Bearer your-token",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "my-client",
                    "version": "1.0.0"
                }
            }
        }

        response = await client.post(url, json=init_request, headers=headers)
        print("Initialize:", response.json())

        # List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        response = await client.post(url, json=list_tools_request, headers=headers)
        print("Tools:", response.json())

        # Call tool
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "calculate",
                "arguments": {
                    "expression": "2 + 3"
                }
            }
        }

        response = await client.post(url, json=call_tool_request, headers=headers)
        print("Result:", response.json())

if __name__ == "__main__":
    import asyncio
    asyncio.run(call_mcp_http_server())
```

---

## Environment Variables

### Loading from .env File

**Python**:
```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Access variables
API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

**TypeScript**:
```typescript
import dotenv from 'dotenv';

// Load .env file
dotenv.config();

// Access variables
const API_KEY = process.env.API_KEY;
const DATABASE_URL = process.env.DATABASE_URL;
```

### .env File Format

```bash
# API Keys
API_KEY=your-api-key-here
WEATHER_API_KEY=your-weather-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Server Configuration
PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# Feature Flags
ENABLE_CACHING=true
MAX_CONNECTIONS=100
```

### Security Best Practices

1. **Never commit .env files** - Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

2. **Use different .env files per environment**:
```
.env.development
.env.staging
.env.production
```

3. **Validate required variables**:
```python
import os

REQUIRED_VARS = ["API_KEY", "DATABASE_URL"]

for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")
```

---

## Remote Server Configuration

### HTTP Server with Authentication

**Client Configuration**:
```json
{
  "mcpServers": {
    "remote-server": {
      "url": "https://your-server.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    }
  }
}
```

### Server-Sent Events (SSE)

For servers that support SSE for notifications:

```json
{
  "mcpServers": {
    "sse-server": {
      "url": "https://your-server.com/mcp",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer your-token"
      }
    }
  }
}
```

---

## Configuration Templates

### Development Configuration

```json
{
  "mcpServers": {
    "dev-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "postgresql://localhost/dev_db"
      }
    }
  }
}
```

### Production Configuration

```json
{
  "mcpServers": {
    "prod-server": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_TOKEN}",
        "X-Environment": "production"
      },
      "timeout": 30000,
      "retries": 3
    }
  }
}
```

### Multi-Environment Setup

Use environment-specific config files:

**claude_desktop_config.development.json**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "ENVIRONMENT": "development"
      }
    }
  }
}
```

**claude_desktop_config.production.json**:
```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://prod-server.com/mcp",
      "headers": {
        "Authorization": "Bearer ${PROD_TOKEN}"
      }
    }
  }
}
```

---

## Debugging Configuration Issues

### Check Configuration Syntax

```bash
# Validate JSON
python -m json.tool claude_desktop_config.json

# Or use jq
jq . claude_desktop_config.json
```

### Test Server Manually

```bash
# Test Python server
python server.py

# Test with uv
uv --directory /path/to/server run server.py

# Test Node server
node build/index.js
```

### Check Logs

**Claude Desktop Logs**:
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Windows
type %APPDATA%\Claude\logs\mcp*.log
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Server not found | Wrong command path | Use absolute path or full command |
| Permission denied | Script not executable | `chmod +x server.py` |
| Module not found | Wrong Python environment | Use full path to venv Python |
| JSON parse error | Invalid JSON syntax | Validate with JSON linter |
| Server crashes | Stdout corruption | Remove all console.log/print |

---

## Best Practices

1. **Use absolute paths** - Avoid relative paths and ~ expansion
2. **Validate configuration** - Check JSON syntax before restarting client
3. **Environment variables** - Use for secrets and environment-specific config
4. **Logging** - Always log to stderr for stdio servers
5. **Error handling** - Provide clear error messages in server
6. **Documentation** - Document required environment variables
7. **Testing** - Test configuration changes before deploying
