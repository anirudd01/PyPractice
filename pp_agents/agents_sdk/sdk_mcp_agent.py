"""
sdk_mcp_agent.py - an Agents SDK agent using tools from an MCP server.

It connects to the SAME server as the from-scratch version (../mcp_server.py).
That is the point of MCP: one server, any client.

Compare with ../mcp_agent.py. There we:
  - opened the stdio connection and ClientSession ourselves,
  - listed the tools and converted each schema to OpenAI's format,
  - called session.call_tool() for every tool request in our own loop.
Here we pass the server to the Agent (mcp_servers=[...]); the SDK lists the
tools, shows them to the model and routes tool calls to the server.

Run (from pp_agents/agents_sdk):
    python sdk_mcp_agent.py
    python sdk_mcp_agent.py "What time is it in Bangalore and how much is 50 GBP in INR?"
"""

import asyncio
import sys
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from sdk_agent import MODEL, print_steps

SERVER_SCRIPT = Path(__file__).resolve().parent.parent / "mcp_server.py"


def travel_mcp_server() -> MCPServerStdio:
    """How to start the server: 'python ../mcp_server.py' as a child process, talking over stdio."""
    return MCPServerStdio(
        name="travel-helper",
        params={"command": sys.executable, "args": [str(SERVER_SCRIPT)]},
        cache_tools_list=True,  # the tool list won't change during a run, so list it once
    )


async def ask(question: str):
    # "async with" starts the server process and stops it again afterwards.
    async with travel_mcp_server() as server:
        agent = Agent(
            name="mcp_travel_helper",
            instructions="You are a travel helper. Use the tools; never invent data.",
            mcp_servers=[server],  # tools come from the server, not from our code
            model=MODEL,
        )
        return await Runner.run(agent, question, max_turns=8)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What's the weather in London and Tokyo? Which is better for an outdoor day?"
    print(f"USER: {q}\n")
    result = asyncio.run(ask(q))
    print_steps(result)
    print(f"\nAGENT: {result.final_output}")
