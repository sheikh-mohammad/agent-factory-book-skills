# MCP Integration

Integrate Model Context Protocol (MCP) servers to expose external tools to agents.

## What is MCP?

Model Context Protocol (MCP) is a standard for connecting AI agents to external tools and data sources. MCP servers expose tools that agents can discover and use dynamically.

## MCP Server Types

| Type | Use Case | Example |
|------|----------|---------|
| **Stdio** | Local subprocess | Filesystem, Git, local scripts |
| **HTTP** | Remote service | APIs, cloud services, microservices |
| **Hosted** | OpenAI-managed | Pre-configured integrations |

## Stdio MCP Servers

Run MCP servers as local subprocesses.

### Basic Stdio Server

```python
from pathlib import Path
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="Filesystem Server",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
    },
) as server:
    agent = Agent(
        name="File Assistant",
        instructions="Use filesystem tools to help users.",
        mcp_servers=[server],
    )

    result = await Runner.run(agent, "List all files")
    print(result.final_output)
```

**Key points**:
- Use `async with` for automatic cleanup
- Server spawns subprocess and manages pipes
- Tools automatically available to agent
- Server closes when context exits

### Common Stdio Servers

**Filesystem Server**:
```python
MCPServerStdio(
    name="Filesystem",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(data_dir)]
    },
)
```

**Git Server**:
```python
MCPServerStdio(
    name="Git",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-git", str(repo_dir)]
    },
)
```

**Custom Python Server**:
```python
MCPServerStdio(
    name="Custom Server",
    params={
        "command": "python",
        "args": ["./my_mcp_server.py"]
    },
)
```

## HTTP MCP Servers

Connect to remote MCP servers via HTTP.

### Basic HTTP Server

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="API Server",
    params={
        "url": "http://localhost:8000/mcp",
        "headers": {"Authorization": "Bearer token"},
        "timeout": 30,
    },
    cache_tools_list=True,
) as server:
    agent = Agent(
        name="API Assistant",
        instructions="Use API tools to help users.",
        mcp_servers=[server],
    )

    result = await Runner.run(agent, "Use the available tools")
    print(result.final_output)
```

**Parameters**:
- `url`: MCP server endpoint
- `headers`: Authentication headers
- `timeout`: Request timeout in seconds
- `cache_tools_list`: Cache tool discovery (improves performance)

### Multiple HTTP Servers

```python
servers = [
    MCPServerStreamableHttp(
        name="Calendar",
        params={"url": "http://localhost:8000/mcp"}
    ),
    MCPServerStreamableHttp(
        name="Email",
        params={"url": "http://localhost:8001/mcp"}
    ),
]

async with MCPServerManager(servers) as manager:
    agent = Agent(
        name="Assistant",
        instructions="Use calendar and email tools.",
        mcp_servers=manager.active_servers,
    )
```

## MCP Server Manager

Manage multiple MCP servers with parallel connection and failure handling.

### Basic Manager

```python
from agents.mcp import MCPServerManager, MCPServerStdio, MCPServerStreamableHttp

servers = [
    MCPServerStdio(name="Filesystem", params={...}),
    MCPServerStreamableHttp(name="API", params={...}),
    MCPServerStdio(name="Git", params={...}),
]

async with MCPServerManager(servers) as manager:
    # Only successfully connected servers
    agent = Agent(
        name="Assistant",
        mcp_servers=manager.active_servers,
    )

    # Check which servers connected
    print(f"Active: {[s.name for s in manager.active_servers]}")
    print(f"Failed: {[s.name for s in manager.failed_servers]}")
```

**Features**:
- Parallel connection to all servers
- Continues if some servers fail
- Tracks active and failed servers
- Configurable connection timeout

### Strict Mode

Fail if any server fails to connect:

```python
async with MCPServerManager(servers, strict=True) as manager:
    # Raises exception if any server fails
    agent = Agent(name="Assistant", mcp_servers=manager.active_servers)
```

### Connection Timeout

```python
async with MCPServerManager(
    servers,
    connection_timeout=10.0,  # 10 second timeout per server
) as manager:
    agent = Agent(name="Assistant", mcp_servers=manager.active_servers)
```

## Hosted MCP Tools

Use OpenAI-hosted MCP servers (no local setup required).

```python
from agents import Agent, Runner, HostedMCPTool

agent = Agent(
    name="Git Assistant",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "gitmcp",
                "server_url": "https://gitmcp.io/openai/codex",
                "require_approval": "never"
            }
        )
    ],
)

result = await Runner.run(agent, "What languages are used in this repository?")
print(result.final_output)
```

**Configuration**:
- `server_label`: Identifier for the hosted server
- `server_url`: Hosted server URL
- `require_approval`: `"never"`, `"always"`, or `"auto"`

## Tool Discovery

MCP servers expose tools dynamically. Agents discover available tools at runtime.

### List Available Tools

```python
async with MCPServerStdio(name="Filesystem", params={...}) as server:
    # Tools are automatically discovered
    agent = Agent(name="Assistant", mcp_servers=[server])

    # Access tool information
    for tool in agent.tools:
        if isinstance(tool, FunctionTool):
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
```

### Selective Tool Usage

Agents automatically choose which tools to use based on instructions:

```python
agent = Agent(
    name="Assistant",
    instructions="""You have access to filesystem tools.
    Only use read operations. Never delete or modify files.""",
    mcp_servers=[filesystem_server],
)
```

## Common Patterns

### Filesystem Operations

```python
from pathlib import Path
from agents.mcp import MCPServerStdio

data_dir = Path("./data")

async with MCPServerStdio(
    name="Filesystem",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(data_dir)]
    },
) as server:
    agent = Agent(
        name="File Manager",
        instructions="Help users manage files in the data directory.",
        mcp_servers=[server],
    )

    result = await Runner.run(agent, "List all CSV files")
```

### Git Operations

```python
repo_dir = Path("./repo")

async with MCPServerStdio(
    name="Git",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-git", str(repo_dir)]
    },
) as server:
    agent = Agent(
        name="Git Assistant",
        instructions="Help with git operations. Be careful with destructive commands.",
        mcp_servers=[server],
    )

    result = await Runner.run(agent, "Show recent commits")
```

### API Integration

```python
async with MCPServerStreamableHttp(
    name="CRM",
    params={
        "url": "https://api.example.com/mcp",
        "headers": {"Authorization": f"Bearer {API_KEY}"},
    },
) as server:
    agent = Agent(
        name="CRM Assistant",
        instructions="Help users manage CRM data.",
        mcp_servers=[server],
    )

    result = await Runner.run(agent, "Find all leads from last week")
```

### Multi-Server Integration

```python
servers = [
    MCPServerStdio(name="Filesystem", params={...}),
    MCPServerStdio(name="Git", params={...}),
    MCPServerStreamableHttp(name="API", params={...}),
]

async with MCPServerManager(servers) as manager:
    agent = Agent(
        name="DevOps Assistant",
        instructions="""You have access to filesystem, git, and API tools.
        Help users with development and deployment tasks.""",
        mcp_servers=manager.active_servers,
    )

    result = await Runner.run(
        agent,
        "Check git status, read config file, and update deployment via API"
    )
```

## Error Handling

### Server Connection Failures

```python
try:
    async with MCPServerStdio(name="Server", params={...}) as server:
        agent = Agent(name="Assistant", mcp_servers=[server])
except Exception as e:
    print(f"Failed to connect to MCP server: {e}")
    # Fallback to agent without MCP tools
    agent = Agent(name="Assistant")
```

### Graceful Degradation

```python
servers = [
    MCPServerStdio(name="Primary", params={...}),
    MCPServerStdio(name="Backup", params={...}),
]

async with MCPServerManager(servers, strict=False) as manager:
    if not manager.active_servers:
        print("No MCP servers available, using fallback")
        agent = Agent(name="Assistant", tools=[fallback_tool])
    else:
        agent = Agent(name="Assistant", mcp_servers=manager.active_servers)
```

### Tool Execution Errors

MCP tool errors are handled like regular function tool errors:

```python
agent = Agent(
    name="Assistant",
    instructions="""Use MCP tools carefully.
    If a tool fails, explain the error to the user and suggest alternatives.""",
    mcp_servers=[server],
)
```

## Security Considerations

### Filesystem Access

Limit filesystem access to specific directories:

```python
# ✅ Good: Restricted to data directory
MCPServerStdio(
    name="Filesystem",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
    },
)

# ❌ Bad: Full filesystem access
MCPServerStdio(
    name="Filesystem",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"]
    },
)
```

### API Authentication

Use environment variables for credentials:

```python
import os

MCPServerStreamableHttp(
    name="API",
    params={
        "url": os.getenv("MCP_API_URL"),
        "headers": {"Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"},
    },
)
```

### Tool Approval

Require approval for sensitive operations:

```python
HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "admin",
        "server_url": "https://admin.example.com/mcp",
        "require_approval": "always"  # User must approve each tool call
    }
)
```

## Best Practices

### Server Lifecycle
- Always use `async with` for automatic cleanup
- Handle connection failures gracefully
- Use MCPServerManager for multiple servers
- Set appropriate connection timeouts

### Tool Discovery
- Let agents discover tools dynamically
- Use clear instructions to guide tool usage
- Don't hardcode tool names in instructions
- Test with different MCP servers

### Performance
- Use `cache_tools_list=True` for HTTP servers
- Connect servers in parallel with MCPServerManager
- Set reasonable timeouts
- Monitor tool execution times

### Security
- Limit filesystem access to specific directories
- Use environment variables for credentials
- Require approval for destructive operations
- Validate tool inputs and outputs

### Error Handling
- Use MCPServerManager with `strict=False` for resilience
- Provide fallback tools when MCP servers fail
- Log connection and tool execution errors
- Test with servers offline

## Testing

### Unit Testing

```python
import pytest
from agents.mcp import MCPServerStdio

@pytest.mark.asyncio
async def test_mcp_server_connection():
    async with MCPServerStdio(
        name="Test",
        params={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "./test_data"]}
    ) as server:
        assert server is not None
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_agent_with_mcp():
    async with MCPServerStdio(name="Filesystem", params={...}) as server:
        agent = Agent(
            name="Test Agent",
            instructions="List files.",
            mcp_servers=[server],
        )

        result = await Runner.run(agent, "List all files")
        assert result.final_output is not None
```

## Troubleshooting

### Server won't connect
- Check command and args are correct
- Verify server binary is installed
- Check network connectivity (HTTP servers)
- Review server logs for errors

### Tools not available
- Verify server connected successfully
- Check agent has `mcp_servers` configured
- Review server tool discovery logs
- Test server independently

### Tool execution fails
- Check tool parameters are valid
- Verify permissions (filesystem, API)
- Review error messages from server
- Test tool with minimal inputs

### Performance issues
- Enable tool list caching
- Use MCPServerManager for parallel connections
- Set appropriate timeouts
- Monitor server response times
