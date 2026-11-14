"""
mcp_server.py - expose the travel tools as an MCP server.

MCP (Model Context Protocol) is a standard way to SHARE tools. Instead of
copying tool schemas into every app (like agent.py does), one server
publishes them, and any MCP client (Claude Code, VS Code, Cursor, or our own
mcp_agent.py) can discover and call them.

Compare with tools.py:
  - There we hand-wrote JSON schemas.
  - Here MCPServer BUILDS the schema from the type hints and the docstring.
  (In mcp 1.x this class was called FastMCP; most tutorials online still use
  that name: `from mcp.server.fastmcp import FastMCP`. Same idea.)

An MCP server can offer three kinds of things:
  - tools     : functions the model can call       (@mcp.tool)
  - resources : read-only data, addressed by a URI (@mcp.resource)
  - prompts   : reusable prompt templates          (@mcp.prompt)

Transport: "stdio". The client starts this script as a child process and they
talk JSON-RPC over stdin/stdout. So: never print() to stdout in here, it
would corrupt the protocol. You normally don't run this file yourself;
mcp_agent.py starts it. To poke at it by hand:
    npx @modelcontextprotocol/inspector python mcp_server.py
"""

from mcp.server.mcpserver import MCPServer

import tools  # reuse the same plain functions; MCP is just another way to serve them

mcp = MCPServer("travel-helper")


@mcp.tool()
def get_weather(city: str) -> dict:
    """Get the current weather (temperature in C and condition) for a city."""
    return tools.get_weather(city)


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount of money between currencies (USD, EUR, GBP, JPY, INR)."""
    return tools.convert_currency(amount, from_currency, to_currency)


@mcp.tool()
def get_local_time(city: str) -> dict:
    """Get the current local date and time in a city."""
    return tools.get_local_time(city)


@mcp.tool()
def list_attractions(city: str) -> dict:
    """List popular attractions in a city, each marked as indoor or outdoor."""
    return tools.list_attractions(city)


@mcp.resource("travel://cities")
def supported_cities() -> str:
    """A resource: read-only data the client can fetch (not called by the model)."""
    return ", ".join(tools.WEATHER)


if __name__ == "__main__":
    mcp.run(transport="stdio")
