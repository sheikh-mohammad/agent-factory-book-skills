# Testing MCP Servers

Comprehensive testing strategies for MCP servers including unit tests, integration tests, and testing with real clients.

## Testing Tools

### MCP Inspector

The official MCP Inspector is the recommended tool for testing servers during development.

**Installation**:
```bash
npx @modelcontextprotocol/inspector
```

**Usage**:
```bash
# Test Python server
npx @modelcontextprotocol/inspector python server.py

# Test TypeScript server
npx @modelcontextprotocol/inspector node build/index.js

# Test with arguments
npx @modelcontextprotocol/inspector uv --directory /path/to/server run server.py
```

**Features**:
- Interactive tool/resource/prompt testing
- Request/response inspection
- Error debugging
- Real-time server communication

### Claude Desktop

Test with Claude Desktop for real-world usage:

1. Configure server in `claude_desktop_config.json`
2. Restart Claude Desktop
3. Test tools in conversation
4. Check logs for errors

**Log Locations**:
- **macOS**: `~/Library/Logs/Claude/`
- **Windows**: `%APPDATA%\Claude\logs\`

---

## Unit Testing

### Python Unit Tests

**Setup**:
```bash
pip install pytest pytest-asyncio
```

**Test Structure**:
```python
# tests/test_tools.py
import pytest
from server import mcp

@pytest.mark.asyncio
async def test_calculate_tool():
    """Test calculate tool with valid input."""
    result = await mcp.call_tool("calculate", {"expression": "2 + 3"})
    assert "5" in result

@pytest.mark.asyncio
async def test_calculate_tool_error():
    """Test calculate tool with invalid input."""
    result = await mcp.call_tool("calculate", {"expression": "invalid"})
    assert "error" in result.lower()

@pytest.mark.asyncio
async def test_search_tool():
    """Test search tool."""
    result = await mcp.call_tool("search", {
        "query": "test",
        "limit": 5
    })
    assert result is not None
```

**Mocking External Dependencies**:
```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_api_call_success():
    """Test tool with mocked API call."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        result = await mcp.call_tool("fetch_data", {"url": "https://api.example.com"})

        assert "test" in result
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_api_call_failure():
    """Test tool with mocked API failure."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock failed response
        mock_get.side_effect = Exception("Network error")

        result = await mcp.call_tool("fetch_data", {"url": "https://api.example.com"})

        assert "error" in result.lower()
```

**Testing Resources**:
```python
@pytest.mark.asyncio
async def test_read_resource():
    """Test resource reading."""
    content = await mcp.read_resource("file://documents/test.txt")
    assert content is not None
    assert len(content) > 0

@pytest.mark.asyncio
async def test_resource_not_found():
    """Test resource not found error."""
    with pytest.raises(FileNotFoundError):
        await mcp.read_resource("file://documents/nonexistent.txt")
```

**Testing Prompts**:
```python
@pytest.mark.asyncio
async def test_code_review_prompt():
    """Test code review prompt generation."""
    prompt = await mcp.get_prompt("code_review", {"language": "python"})
    assert "python" in prompt.lower()
    assert "review" in prompt.lower()
```

### TypeScript Unit Tests

**Setup**:
```bash
npm install -D vitest @vitest/ui
```

**vitest.config.ts**:
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
  },
});
```

**Test Structure**:
```typescript
// tests/tools.test.ts
import { describe, it, expect, vi } from 'vitest';
import { server } from '../src/server';

describe('Calculate Tool', () => {
  it('should calculate expression correctly', async () => {
    const result = await server.callTool('calculate', {
      expression: '2 + 3',
    });

    expect(result.content[0].text).toContain('5');
  });

  it('should handle invalid expression', async () => {
    const result = await server.callTool('calculate', {
      expression: 'invalid',
    });

    expect(result.isError).toBe(true);
  });
});
```

**Mocking**:
```typescript
import { describe, it, expect, vi } from 'vitest';

describe('API Tool', () => {
  it('should fetch data successfully', async () => {
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'test' }),
    });

    const result = await server.callTool('fetch_data', {
      url: 'https://api.example.com',
    });

    expect(result.content[0].text).toContain('test');
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('should handle fetch error', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    const result = await server.callTool('fetch_data', {
      url: 'https://api.example.com',
    });

    expect(result.isError).toBe(true);
  });
});
```

---

## Integration Testing

### Python Integration Tests

Test complete server lifecycle with real MCP client:

```python
import pytest
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_server_lifecycle():
    """Test complete server initialization and tool execution."""
    async with stdio_client("python", ["server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            init_result = await session.initialize()
            assert init_result.serverInfo.name == "my-server"

            # List tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0
            assert any(t.name == "calculate" for t in tools.tools)

            # Call tool
            result = await session.call_tool("calculate", {
                "expression": "10 * 5"
            })
            assert "50" in result.content[0].text

            # List resources
            resources = await session.list_resources()
            assert len(resources.resources) >= 0

            # Read resource (if available)
            if resources.resources:
                resource = resources.resources[0]
                content = await session.read_resource(resource.uri)
                assert content is not None
```

**Testing with Database**:
```python
import pytest
import asyncpg

@pytest.fixture
async def db():
    """Create test database."""
    conn = await asyncpg.connect("postgresql://localhost/test_db")
    await conn.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL, name TEXT)")
    yield conn
    await conn.execute("DROP TABLE users")
    await conn.close()

@pytest.mark.asyncio
async def test_database_tool(db):
    """Test tool with real database."""
    async with stdio_client("python", ["server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Insert data
            result = await session.call_tool("insert_user", {
                "name": "Test User"
            })
            assert "success" in result.content[0].text.lower()

            # Query data
            result = await session.call_tool("get_users", {})
            assert "Test User" in result.content[0].text
```

### TypeScript Integration Tests

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

describe('Server Integration', () => {
  let client: Client;
  let transport: StdioClientTransport;

  beforeAll(async () => {
    transport = new StdioClientTransport({
      command: 'node',
      args: ['build/index.js'],
    });

    client = new Client({
      name: 'test-client',
      version: '1.0.0',
    });

    await client.connect(transport);
  });

  afterAll(async () => {
    await client.close();
  });

  it('should initialize server', async () => {
    const info = await client.getServerInfo();
    expect(info.name).toBe('my-server');
  });

  it('should list and call tools', async () => {
    const tools = await client.listTools();
    expect(tools.tools.length).toBeGreaterThan(0);

    const result = await client.callTool('calculate', {
      expression: '2 + 3',
    });

    expect(result.content[0].text).toContain('5');
  });
});
```

---

## End-to-End Testing

### Testing with Claude Desktop

**Manual Testing Checklist**:

1. **Configuration**
   - [ ] Server appears in Claude Desktop
   - [ ] No connection errors in logs
   - [ ] Tools are discoverable

2. **Tool Execution**
   - [ ] Tools execute successfully
   - [ ] Parameters are validated
   - [ ] Errors are handled gracefully
   - [ ] Results are formatted correctly

3. **Resources**
   - [ ] Resources are listed
   - [ ] Resource content loads
   - [ ] URIs are resolved correctly

4. **Prompts**
   - [ ] Prompts are available
   - [ ] Parameters work correctly
   - [ ] Generated prompts are useful

5. **Performance**
   - [ ] Tools respond quickly (<5s)
   - [ ] No memory leaks
   - [ ] Server remains stable

**Automated E2E Tests**:
```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_claude_desktop_integration():
    """Test server with Claude Desktop (requires running instance)."""
    async with async_playwright() as p:
        # This is a conceptual example
        # Actual implementation depends on Claude Desktop's automation capabilities
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to Claude Desktop
        await page.goto("claude://")

        # Test tool usage
        await page.fill('textarea', 'Use the calculate tool to compute 2 + 3')
        await page.press('textarea', 'Enter')

        # Wait for response
        await page.wait_for_selector('.tool-result')
        result = await page.text_content('.tool-result')

        assert '5' in result

        await browser.close()
```

---

## Load Testing

### Python Load Tests

```python
import asyncio
import time
from statistics import mean, median

async def load_test_tool(num_requests: int = 100):
    """Load test a tool with concurrent requests."""
    async def call_tool():
        start = time.time()
        try:
            result = await mcp.call_tool("calculate", {"expression": "2 + 3"})
            duration = time.time() - start
            return {"success": True, "duration": duration}
        except Exception as e:
            duration = time.time() - start
            return {"success": False, "duration": duration, "error": str(e)}

    # Execute concurrent requests
    tasks = [call_tool() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)

    # Analyze results
    successes = sum(1 for r in results if r["success"])
    failures = num_requests - successes
    durations = [r["duration"] for r in results]

    print(f"Total requests: {num_requests}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Mean duration: {mean(durations):.3f}s")
    print(f"Median duration: {median(durations):.3f}s")
    print(f"Min duration: {min(durations):.3f}s")
    print(f"Max duration: {max(durations):.3f}s")

# Run load test
asyncio.run(load_test_tool(100))
```

### Using Locust

```python
# locustfile.py
from locust import User, task, between
import asyncio

class MCPUser(User):
    wait_time = between(1, 3)

    @task
    def call_calculate_tool(self):
        start_time = time.time()
        try:
            asyncio.run(mcp.call_tool("calculate", {"expression": "2 + 3"}))
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="MCP",
                name="calculate",
                response_time=total_time,
                response_length=0,
                exception=None,
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="MCP",
                name="calculate",
                response_time=total_time,
                response_length=0,
                exception=e,
            )
```

**Run**:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

---

## Test Coverage

### Python Coverage

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest --cov=server --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### TypeScript Coverage

```bash
# Install coverage
npm install -D @vitest/coverage-v8

# Run tests with coverage
npx vitest --coverage

# View report
open coverage/index.html
```

---

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test MCP Server

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: pytest --cov=server --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

---

## Debugging Tests

### Python Debugging

```python
import pytest
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
async def test_with_debugging():
    """Test with debug output."""
    import pdb; pdb.set_trace()  # Breakpoint

    result = await mcp.call_tool("calculate", {"expression": "2 + 3"})
    print(f"Result: {result}")  # Debug output

    assert "5" in result
```

### TypeScript Debugging

```typescript
import { describe, it } from 'vitest';

describe('Debug Test', () => {
  it('should debug tool execution', async () => {
    debugger; // Breakpoint

    const result = await server.callTool('calculate', {
      expression: '2 + 3',
    });

    console.log('Result:', result); // Debug output
  });
});
```

**Run with debugger**:
```bash
node --inspect-brk node_modules/.bin/vitest
```
