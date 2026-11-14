"""
mcp_agent.py - an agent whose tools come from an MCP server.

Same loop as agent.py, with two differences:
  1. Tools are DISCOVERED at runtime: we ask the server "what tools do you
     have?" instead of importing schemas from tools.py.
  2. Tools are EXECUTED by the server: we send "call get_weather(Paris)"
     over MCP and get the result back. This file never imports tools.py.

The MCP client is async, so this file uses asyncio and AsyncOpenAI.

Run:
    python mcp_agent.py
    python mcp_agent.py "What time is it in Bangalore and how much is 50 GBP in INR?"
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# How to start the server: "python mcp_server.py" as a child process.
SERVER = StdioServerParameters(command=sys.executable, args=[str(HERE / "mcp_server.py")])


def mcp_tool_to_openai(tool) -> dict:
    """MCP describes tools with a JSON schema too; just re-wrap it in OpenAI's format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,  # "inputSchema" in mcp 1.x
        },
    }


async def main(question: str) -> None:
    # 1. Start the server process and open an MCP session over its stdin/stdout.
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as session:
        await session.initialize()  # handshake: client and server agree on capabilities

        # 2. Discover tools (and peek at a resource, just to see one).
        listed = await session.list_tools()
        print("Tools from MCP server:", [t.name for t in listed.tools])
        cities = await session.read_resource("travel://cities")
        print("Resource travel://cities:", cities.contents[0].text, "\n")

        openai_tools = [mcp_tool_to_openai(t) for t in listed.tools]

        # 3. The usual agent loop.
        client = AsyncOpenAI()
        messages = [
            {"role": "system", "content": "You are a travel helper. Use the tools; never invent data."},
            {"role": "user", "content": question},
        ]
        for turn in range(1, 9):
            response = await client.chat.completions.create(model=MODEL, messages=messages, tools=openai_tools)
            reply = response.choices[0].message
            if not reply.tool_calls:
                print(f"\nAGENT: {reply.content}")
                return

            messages.append(reply)
            for call in reply.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError as exc:  # bad JSON from the model: report it, don't crash
                    text = f"Invalid JSON arguments: {exc}"
                else:
                    print(f"[mcp-agent] turn {turn}: {call.function.name}({args})")
                    # 4. The server runs the tool, not us. Tool errors come back as text too.
                    result = await session.call_tool(call.function.name, args)
                    text = "\n".join(c.text for c in result.content if c.type == "text")
                print(f"[mcp-agent]           -> {text}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": text})

        print("Stopped: too many turns.")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What's the weather in London and Tokyo? Which is better for an outdoor day?"
    print(f"USER: {q}\n")
    asyncio.run(main(q))
