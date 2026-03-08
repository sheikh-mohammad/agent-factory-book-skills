# Claude Agent SDK Examples

Complete working examples for TypeScript and Python implementations.

## TypeScript Examples

### Prerequisites

```bash
npm install
```

### Examples

1. **simple-query.ts** - Basic agent usage
   ```bash
   npx tsx simple-query.ts
   ```

2. **mcp-weather-agent.ts** - Custom MCP tools
   ```bash
   npx tsx mcp-weather-agent.ts
   ```

3. **session-management.ts** - Continue, resume, and fork patterns
   ```bash
   npx tsx session-management.ts
   ```

4. **multi-agent-review.ts** - Multi-agent orchestration
   ```bash
   npx tsx multi-agent-review.ts
   ```

5. **production-server.ts** - Production Express server
   ```bash
   npx tsx production-server.ts
   # Then: curl -X POST http://localhost:3000/agent -H "Content-Type: application/json" -d '{"prompt":"Hello","userId":"user1"}'
   ```

## Python Examples

### Prerequisites

```bash
pip install -r requirements.txt
```

### Examples

1. **simple_query.py** - Basic agent usage
   ```bash
   python simple_query.py
   ```

2. **mcp_weather_agent.py** - Custom MCP tools
   ```bash
   python mcp_weather_agent.py
   ```

3. **session_management.py** - Continue, resume, and fork patterns
   ```bash
   python session_management.py
   ```

4. **multi_agent_review.py** - Multi-agent orchestration
   ```bash
   python multi_agent_review.py
   ```

5. **production_server.py** - Production FastAPI server
   ```bash
   python production_server.py
   # Then: curl -X POST http://localhost:8000/agent -H "Content-Type: application/json" -d '{"prompt":"Hello","user_id":"user1"}'
   ```

## Environment Setup

Set your API key:

```bash
export ANTHROPIC_API_KEY=your-api-key
```

## Example Descriptions

### Simple Query
Demonstrates basic agent usage with built-in tools (Read, Bash, Glob). Good starting point for understanding the agent loop.

### MCP Weather Agent
Shows how to create custom MCP tools with external API integration. Demonstrates proper error handling in tools.

### Session Management
Illustrates three session patterns:
- **Continue**: Resume most recent session
- **Resume**: Resume specific session by ID
- **Fork**: Branch to explore alternatives

### Multi-Agent Review
Demonstrates orchestrating multiple specialized subagents for comprehensive code review (security, performance, quality).

### Production Server
Production-ready HTTP server with:
- Error handling
- Cost tracking
- Security (tool restrictions)
- Monitoring endpoints
- Graceful shutdown

## Notes

- All examples include proper error handling
- Budget limits are set to prevent runaway costs
- Examples use safe tools by default
- Production examples include monitoring and metrics
