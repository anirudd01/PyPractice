"""
Offline tests for the MCP server: start the real mcp_server.py as a child
process and talk to it over stdio, exactly like an MCP client (Claude Code,
mcp_agent.py, sdk_mcp_agent.py) would. No LLM involved.
"""

import asyncio
import json
import sys
from contextlib import asynccontextmanager

import pytest
from conftest import PP_AGENTS
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import tools

SERVER = StdioServerParameters(command=sys.executable, args=[str(PP_AGENTS / "mcp_server.py")])


@asynccontextmanager
async def mcp_session():
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session


def run(coro):
    return asyncio.run(coro)


def test_server_lists_the_same_tools_as_tools_py():
    async def go():
        async with mcp_session() as s:
            return (await s.list_tools()).tools

    listed = run(go())
    assert {t.name for t in listed} == set(tools.TOOL_FUNCTIONS)
    by_name = {t.name: t for t in listed}
    assert by_name["convert_currency"].input_schema["required"] == ["amount", "from_currency", "to_currency"]
    assert "indoor or outdoor" in by_name["list_attractions"].description


def test_call_tool_runs_on_the_server():
    async def go():
        async with mcp_session() as s:
            return await s.call_tool("convert_currency", {"amount": 100, "from_currency": "USD", "to_currency": "EUR"})

    result = run(go())
    assert not result.is_error
    assert json.loads(result.content[0].text)["result"] == 92.0


def test_tool_level_error_comes_back_as_data():
    """Unknown city: the tool itself returns an error dict; the call succeeds."""

    async def go():
        async with mcp_session() as s:
            return await s.call_tool("get_weather", {"city": "Atlantis"})

    result = run(go())
    assert not result.is_error
    assert "No weather data" in json.loads(result.content[0].text)["error"]


@pytest.mark.parametrize("args", [{}, {"town": "Paris"}])
def test_bad_arguments_are_rejected_by_the_server(args):
    """Schema validation happens on the server: the result is flagged is_error, nothing crashes."""

    async def go():
        async with mcp_session() as s:
            return await s.call_tool("get_weather", args)

    result = run(go())
    assert result.is_error
    assert "city" in result.content[0].text


def test_resource_lists_supported_cities():
    async def go():
        async with mcp_session() as s:
            return await s.read_resource("travel://cities")

    text = run(go()).contents[0].text
    assert text.split(", ") == list(tools.WEATHER)
