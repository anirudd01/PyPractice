"""
agent.py - a single agent, built by hand with the OpenAI SDK.

An "agent" is just an LLM in a loop:

    1. Send the conversation + the list of tools to the model.
    2. If the model answers with plain text -> done, that's the answer.
    3. If the model asks for tool calls -> run them, append the results
       to the conversation, and go back to step 1.

That's it. Frameworks (OpenAI Agents SDK, LangGraph, ...) wrap this loop,
but this is what they do underneath.

Run:
    python agent.py
    python agent.py "Is it a good day to visit Tokyo? What time is it there?"
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_SCHEMAS, run_tool

# Load OPENAI_API_KEY / OPENAI_MODEL from the .env file next to this script.
load_dotenv(Path(__file__).parent / ".env")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def run_agent(
    user_message: str,
    system_prompt: str,
    tools: list[dict],
    name: str = "agent",
    max_turns: int = 8,
    tool_runner=run_tool,
) -> str:
    """
    The agent loop. Reused by orchestrator.py, so sub-agents are just
    this same function with a different prompt and a smaller tool list.
    tool_runner(name, arguments_json) -> str executes a tool call; the
    orchestrator passes its own so it can handle "ask a specialist".
    """
    client = OpenAI()  # reads OPENAI_API_KEY from the environment

    # The conversation ("messages") is the agent's only memory.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # max_turns is a safety net: a confused model could otherwise loop forever.
    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools or None,  # the model sees the schemas, never the code
        )
        reply = response.choices[0].message

        # Case 1: no tool calls -> the model has its final answer.
        if not reply.tool_calls:
            print(f"[{name}] turn {turn}: final answer")
            return reply.content

        # Case 2: the model wants tools. First, record its request in the
        # conversation (the API requires the assistant message before the results).
        messages.append(reply)

        # It can ask for several tools at once (e.g. weather for 2 cities).
        for call in reply.tool_calls:
            print(f"[{name}] turn {turn}: calling {call.function.name}({call.function.arguments})")
            result = tool_runner(call.function.name, call.function.arguments)
            print(f"[{name}]           -> {result}")

            # Each result is linked to its request by tool_call_id.
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return "Stopped: reached max_turns without a final answer."


SYSTEM_PROMPT = """You are a friendly travel helper.
Use the tools to look up weather, local time, attractions and currency.
Never invent data: if a tool returns an error, say so.
Keep answers short and practical."""


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or (
        "I'm in Paris with 200 USD. What's the weather, what should I visit given the weather, "
        "and how much is my money in euros?"
    )
    print(f"USER: {question}\n")
    answer = run_agent(question, SYSTEM_PROMPT, tools=list(TOOL_SCHEMAS.values()))
    print(f"\nAGENT: {answer}")
