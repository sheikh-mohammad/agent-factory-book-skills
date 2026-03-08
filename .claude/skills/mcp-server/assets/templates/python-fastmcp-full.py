#!/usr/bin/env python3
"""
Full-Featured MCP Server using FastMCP
Demonstrates tools, resources, prompts, context access, and lifecycle management.
"""

import sys
import os
import json
from pathlib import Path
from typing import Any
from contextlib import asynccontextmanager

import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ServerSession, LifespanContext


# Lifecycle management for startup/shutdown
@asynccontextmanager
async def lifespan(app):
    """Manage server lifecycle."""
    # Startup: Initialize resources
    print("Server starting...", file=sys.stderr)
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    app.state.data_dir = Path("data")
    app.state.data_dir.mkdir(exist_ok=True)

    yield

    # Shutdown: Cleanup resources
    print("Server shutting down...", file=sys.stderr)
    await app.state.http_client.aclose()


# Initialize server with lifecycle
mcp = FastMCP("full-featured-server", lifespan=lifespan)


# ============================================================================
# TOOLS - Executable functions with side effects
# ============================================================================

@mcp.tool()
async def search_web(query: str, limit: int = 5) -> str:
    """Search the web for information.

    Args:
        query: Search query string
        limit: Maximum number of results (default: 5, max: 10)
    """
    # Validate input
    if not query or len(query) < 2:
        return "Error: Query must be at least 2 characters"

    if limit < 1 or limit > 10:
        return "Error: Limit must be between 1 and 10"

    try:
        # Example: Call a search API
        api_key = os.getenv("SEARCH_API_KEY", "demo-key")
        url = f"https://api.example.com/search?q={query}&limit={limit}&key={api_key}"

        client = mcp.state.http_client
        response = await client.get(url)
        response.raise_for_status()

        results = response.json()
        return json.dumps(results, indent=2)

    except httpx.HTTPStatusError as e:
        return f"API error: {e.response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def save_note(title: str, content: str) -> str:
    """Save a note to the data directory.

    Args:
        title: Note title (used as filename)
        content: Note content
    """
    try:
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        filename = f"{safe_title}.txt"
        filepath = mcp.state.data_dir / filename

        # Save note
        filepath.write_text(content)

        return f"Note saved: {filename}"

    except Exception as e:
        return f"Error saving note: {str(e)}"


@mcp.tool()
async def process_with_progress(
    items: list[str],
    ctx: Context[ServerSession, LifespanContext]
) -> str:
    """Process items with progress reporting.

    Args:
        items: List of items to process
    """
    total = len(items)
    await ctx.report_progress(0.0, "Starting processing")

    results = []
    for i, item in enumerate(items):
        # Process item
        ctx.info(f"Processing item {i+1}/{total}: {item}")
        processed = item.upper()  # Example processing
        results.append(processed)

        # Report progress
        progress = (i + 1) / total
        await ctx.report_progress(progress, f"Processed {i+1}/{total} items")

    await ctx.report_progress(1.0, "Complete")
    return f"Processed {total} items: {', '.join(results)}"


# ============================================================================
# RESOURCES - Read-only data sources
# ============================================================================

@mcp.resource("note://{filename}")
async def read_note(filename: str) -> str:
    """Read a note from the data directory.

    Args:
        filename: Name of the note file
    """
    filepath = mcp.state.data_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Note not found: {filename}")

    # Validate path (prevent directory traversal)
    if not filepath.resolve().is_relative_to(mcp.state.data_dir.resolve()):
        raise ValueError("Access denied: invalid path")

    return filepath.read_text()


@mcp.resource("config://settings")
async def get_settings() -> str:
    """Get server configuration settings."""
    settings = {
        "server_name": "full-featured-server",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "data_directory": str(mcp.state.data_dir),
    }
    return json.dumps(settings, indent=2)


# ============================================================================
# PROMPTS - Reusable interaction templates
# ============================================================================

@mcp.prompt()
async def code_review(language: str, focus: str = "best practices") -> str:
    """Generate a code review prompt.

    Args:
        language: Programming language
        focus: What to focus on in the review
    """
    return f"""Review this {language} code focusing on {focus}.

Provide specific, actionable feedback on:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Best practices for {language}

Format your review with:
- Clear issue descriptions
- Severity levels (critical, major, minor)
- Specific code examples
- Suggested fixes"""


@mcp.prompt()
async def data_analysis(dataset_description: str, goal: str) -> str:
    """Generate a data analysis prompt.

    Args:
        dataset_description: Description of the dataset
        goal: Analysis goal
    """
    return f"""Analyze the following dataset: {dataset_description}

Goal: {goal}

Please provide:
1. Initial data exploration approach
2. Key metrics to calculate
3. Visualizations to create
4. Statistical tests to perform
5. Insights to look for

Consider data quality, outliers, and potential biases."""


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the server."""
    # Check for required environment variables
    if not os.getenv("SEARCH_API_KEY"):
        print("Warning: SEARCH_API_KEY not set, using demo key", file=sys.stderr)

    # Run with stdio transport (for Claude Desktop, VS Code)
    mcp.run(transport="stdio")

    # For HTTP transport (remote access), use:
    # port = int(os.getenv("PORT", 8000))
    # mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Configure logging to stderr (CRITICAL for stdio transport)
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

    main()
