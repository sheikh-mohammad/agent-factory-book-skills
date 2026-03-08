# Tools, Resources, and Prompts

Comprehensive guide to implementing MCP primitives: tools, resources, and prompts.

## Tools

Tools are executable functions that AI applications can invoke to perform actions with side effects.

### When to Use Tools

Use tools for:
- API calls to external services
- Database operations (queries, updates)
- File system operations (read, write, delete)
- Computations and data processing
- System commands
- Any action that changes state

### Tool Design Principles

1. **Single Responsibility** - Each tool should do one thing well
2. **Clear Naming** - Use descriptive names (e.g., `search_database` not `search`)
3. **Comprehensive Documentation** - Explain what, why, and how
4. **Input Validation** - Validate all parameters
5. **Error Handling** - Return meaningful error messages
6. **Idempotency** - When possible, make tools idempotent

### Python Tool Examples

**Basic Tool**:
```python
@mcp.tool()
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 3 * 4")
    """
    try:
        result = eval(expression)  # Use safe_eval in production
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

**Tool with Multiple Parameters**:
```python
@mcp.tool()
async def search_files(
    directory: str,
    pattern: str,
    recursive: bool = True,
    max_results: int = 100
) -> str:
    """Search for files matching a pattern.

    Args:
        directory: Directory to search in
        pattern: File pattern (e.g., "*.py", "test_*.txt")
        recursive: Search subdirectories (default: True)
        max_results: Maximum number of results (default: 100)
    """
    import glob
    from pathlib import Path

    path = Path(directory)
    if not path.exists():
        return f"Error: Directory not found: {directory}"

    pattern_str = f"**/{pattern}" if recursive else pattern
    files = list(path.glob(pattern_str))[:max_results]

    return "\n".join(str(f) for f in files)
```

**Tool with Structured Output**:
```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    total: int
    results: list[dict]
    query: str

@mcp.tool()
async def search_database(query: str, limit: int = 10) -> SearchResult:
    """Search database and return structured results.

    Args:
        query: Search query
        limit: Maximum results
    """
    results = await db.search(query, limit)

    return SearchResult(
        total=len(results),
        results=results,
        query=query
    )
```

**Tool with Progress Reporting**:
```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def process_large_file(
    filepath: str,
    ctx: Context
) -> str:
    """Process a large file with progress updates.

    Args:
        filepath: Path to file to process
    """
    file_size = os.path.getsize(filepath)
    processed = 0

    await ctx.report_progress(0.0, "Starting processing")

    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            # Process line
            await process_line(line)
            processed += len(line)

            # Report progress every 1000 lines
            if i % 1000 == 0:
                progress = processed / file_size
                await ctx.report_progress(progress, f"Processed {i} lines")

    await ctx.report_progress(1.0, "Complete")
    return f"Processed {file_size} bytes"
```

**Tool with External API Call**:
```python
import httpx

@mcp.tool()
async def fetch_weather(city: str, units: str = "metric") -> str:
    """Fetch current weather for a city.

    Args:
        city: City name
        units: Temperature units (metric, imperial, kelvin)
    """
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params={"q": city, "units": units, "appid": api_key},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            return f"""
Weather in {city}:
Temperature: {data['main']['temp']}°
Conditions: {data['weather'][0]['description']}
Humidity: {data['main']['humidity']}%
"""
        except httpx.HTTPStatusError as e:
            return f"API error: {e.response.status_code}"
        except Exception as e:
            return f"Error fetching weather: {str(e)}"
```

### TypeScript Tool Examples

**Basic Tool**:
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
        content: [{ type: "text", text: `Result: ${result}` }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true,
      };
    }
  }
);
```

**Tool with Complex Schema**:
```typescript
const SearchParamsSchema = z.object({
  query: z.string().min(1).max(1000),
  filters: z.object({
    category: z.enum(["all", "docs", "code", "data"]).optional(),
    dateFrom: z.string().datetime().optional(),
    dateTo: z.string().datetime().optional(),
  }).optional(),
  limit: z.number().min(1).max(100).default(10),
  offset: z.number().min(0).default(0),
});

server.tool(
  "advanced_search",
  "Search with advanced filters",
  SearchParamsSchema.shape,
  async ({ query, filters, limit, offset }) => {
    const results = await database.search({
      query,
      filters,
      limit,
      offset,
    });

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

---

## Resources

Resources expose data sources that provide contextual information to AI applications. They are read-only and identified by URIs.

### When to Use Resources

Use resources for:
- File contents
- Database records
- API responses
- Configuration data
- Documentation
- Any read-only data

### Resource Design Principles

1. **URI Patterns** - Use clear, hierarchical URI patterns
2. **Read-Only** - Resources should not have side effects
3. **Caching** - Consider caching expensive resources
4. **MIME Types** - Specify appropriate MIME types
5. **Error Handling** - Handle missing resources gracefully

### Python Resource Examples

**Basic Resource**:
```python
@mcp.resource("file://documents/{filename}")
async def read_document(filename: str) -> str:
    """Read a document by filename.

    Args:
        filename: Name of the document file
    """
    filepath = Path("documents") / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Document not found: {filename}")

    return filepath.read_text()
```

**Resource with Path Validation**:
```python
from pathlib import Path

ALLOWED_DIR = Path("/app/data")

@mcp.resource("data://{path}")
async def read_data_file(path: str) -> str:
    """Read a data file with path validation.

    Args:
        path: Relative path to data file
    """
    # Resolve and validate path
    filepath = (ALLOWED_DIR / path).resolve()

    if not filepath.is_relative_to(ALLOWED_DIR):
        raise ValueError("Access denied: path outside allowed directory")

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return filepath.read_text()
```

**Dynamic Resource Listing**:
```python
@mcp.resource("database://tables/{table}/schema")
async def get_table_schema(table: str) -> str:
    """Get database table schema.

    Args:
        table: Table name
    """
    # Validate table name
    if table not in await db.list_tables():
        raise ValueError(f"Table not found: {table}")

    schema = await db.get_schema(table)
    return json.dumps(schema, indent=2)
```

**Resource with Multiple Content Types**:
```python
from mcp.types import TextContent, ImageContent

@mcp.resource("api://reports/{report_id}")
async def get_report(report_id: str) -> list[TextContent | ImageContent]:
    """Get a report with text and images.

    Args:
        report_id: Report identifier
    """
    report = await fetch_report(report_id)

    contents = [
        TextContent(
            type="text",
            text=report["summary"]
        )
    ]

    # Add chart image if available
    if report.get("chart_url"):
        chart_data = await fetch_image(report["chart_url"])
        contents.append(
            ImageContent(
                type="image",
                data=chart_data,
                mimeType="image/png"
            )
        )

    return contents
```

### TypeScript Resource Examples

**Basic Resource**:
```typescript
server.resource(
  {
    uri: "file://documents/{name}",
    name: "Document",
    description: "Read document contents",
    mimeType: "text/plain",
  },
  async (uri) => {
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

**Resource with Caching**:
```typescript
const cache = new Map<string, { data: string; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

server.resource(
  {
    uri: "api://data/{id}",
    name: "API Data",
    description: "Fetch data from external API",
  },
  async (uri) => {
    const match = uri.match(/api:\/\/data\/(.+)/);
    const id = match?.[1];

    // Check cache
    const cached = cache.get(id);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: cached.data,
          },
        ],
      };
    }

    // Fetch and cache
    const data = await fetchFromAPI(id);
    cache.set(id, { data: JSON.stringify(data), timestamp: Date.now() });

    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }
);
```

---

## Prompts

Prompts are reusable templates that help structure interactions with language models.

### When to Use Prompts

Use prompts for:
- Common workflows
- Few-shot examples
- System prompts
- Task templates
- Interaction patterns

### Prompt Design Principles

1. **Clear Instructions** - Be explicit about what to do
2. **Context** - Provide necessary background
3. **Examples** - Include examples when helpful
4. **Parameters** - Make prompts customizable
5. **Structure** - Use consistent formatting

### Python Prompt Examples

**Basic Prompt**:
```python
@mcp.prompt()
async def code_review(language: str) -> str:
    """Generate a code review prompt.

    Args:
        language: Programming language
    """
    return f"""Review this {language} code for:

1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Best practices

Provide specific, actionable feedback with examples."""
```

**Prompt with Few-Shot Examples**:
```python
@mcp.prompt()
async def sql_query_generator(task: str) -> str:
    """Generate SQL query from natural language.

    Args:
        task: Description of what to query
    """
    return f"""Generate a SQL query for the following task: {task}

Examples:

Task: Get all users who signed up in the last 7 days
Query: SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days';

Task: Count orders by status
Query: SELECT status, COUNT(*) as count FROM orders GROUP BY status;

Task: Find top 10 products by revenue
Query: SELECT product_id, SUM(price * quantity) as revenue
       FROM order_items
       GROUP BY product_id
       ORDER BY revenue DESC
       LIMIT 10;

Now generate a query for: {task}"""
```

**Prompt with Context**:
```python
@mcp.prompt()
async def debug_assistant(
    error: str,
    code: str,
    language: str
) -> str:
    """Help debug an error.

    Args:
        error: Error message
        code: Code that produced the error
        language: Programming language
    """
    return f"""I'm encountering this error in {language}:

Error:
```
{error}
```

Code:
```{language}
{code}
```

Please help me:
1. Understand what's causing this error
2. Identify the root cause
3. Suggest a fix with code example
4. Explain how to prevent similar errors"""
```

### TypeScript Prompt Examples

**Basic Prompt**:
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

**Prompt with System Message**:
```typescript
server.prompt(
  "technical_writer",
  "Technical writing assistant",
  {
    topic: z.string().describe("Topic to write about"),
    audience: z.enum(["beginner", "intermediate", "advanced"]),
  },
  async ({ topic, audience }) => {
    return {
      messages: [
        {
          role: "system",
          content: {
            type: "text",
            text: `You are a technical writer creating documentation for ${audience} developers.
Use clear, concise language with appropriate technical depth.
Include code examples and practical use cases.`,
          },
        },
        {
          role: "user",
          content: {
            type: "text",
            text: `Write documentation about: ${topic}`,
          },
        },
      ],
    };
  }
);
```

---

## Combining Primitives

Effective MCP servers often combine tools, resources, and prompts to create comprehensive solutions.

### Example: Database Server

```python
from mcp.server.fastmcp import FastMCP
import asyncpg

mcp = FastMCP("database-server")

# Resource: Database schema
@mcp.resource("database://schema")
async def get_schema() -> str:
    """Get complete database schema."""
    schema = await db.get_full_schema()
    return json.dumps(schema, indent=2)

# Resource: Table data
@mcp.resource("database://tables/{table}")
async def get_table_data(table: str) -> str:
    """Get data from a specific table."""
    data = await db.query(f"SELECT * FROM {table} LIMIT 100")
    return json.dumps(data, indent=2)

# Tool: Execute query
@mcp.tool()
async def execute_query(sql: str) -> str:
    """Execute a SQL query.

    Args:
        sql: SQL query to execute
    """
    try:
        results = await db.query(sql)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Query error: {str(e)}"

# Prompt: Query helper
@mcp.prompt()
async def query_helper(task: str) -> str:
    """Generate SQL query from natural language.

    Args:
        task: What you want to query
    """
    schema = await db.get_schema()

    return f"""Generate a SQL query for: {task}

Available tables and columns:
{json.dumps(schema, indent=2)}

Generate an efficient, safe SQL query."""
```

This creates a complete database integration where:
- **Resources** expose schema and table data
- **Tools** allow query execution
- **Prompts** help generate queries

The AI can use resources to understand the database structure, prompts to generate queries, and tools to execute them.
