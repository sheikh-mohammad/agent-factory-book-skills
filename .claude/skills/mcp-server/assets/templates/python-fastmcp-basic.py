#!/usr/bin/env python3
"""
Basic MCP Server using FastMCP
A minimal example with one tool demonstrating core concepts.
"""

import sys
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("basic-server")


@mcp.tool()
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
    """
    try:
        # Note: eval() is used for simplicity. Use a safe math parser in production.
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    """Run the server."""
    # Use stdio transport for local clients (Claude Desktop, VS Code)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    # Configure logging to stderr (CRITICAL for stdio transport)
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

    main()
