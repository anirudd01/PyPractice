"""
sdk_agent.py - a single agent with the OpenAI Agents SDK.

Compare with ../agent.py. There we wrote the loop ourselves:
    call model -> run requested tools -> append results -> repeat.
Here the whole loop is one line: Runner.run_sync(agent, question).

What the SDK gives you:
  - Agent      : the configuration (name, instructions, tools, model).
  - Runner     : the loop. It calls the model, runs tools, feeds results
                 back, and stops at a final answer or after max_turns.
  - RunResult  : the answer (final_output) PLUS every step that happened
                 (new_items), so you can see/test which tools were called.

Two things that differ from the from-scratch version:
  - The SDK uses OpenAI's newer Responses API by default; ../agent.py uses
    Chat Completions. Same idea, different endpoint.
  - Tracing: by default every run is uploaded as a trace to your OpenAI
    account (platform.openai.com > Traces), a nice visual of each step.
    Set OPENAI_AGENTS_DISABLE_TRACING=1 in .env to switch it off.

Run (from pp_agents/agents_sdk):
    python sdk_agent.py
    python sdk_agent.py "Is it a good day for Tokyo? What time is it there?"
"""

import os
import sys
from pathlib import Path

from agents import Agent, HandoffOutputItem, Runner, ToolCallItem, ToolCallOutputItem
from dotenv import load_dotenv
from sdk_tools import ALL_TOOLS

# Same .env as the from-scratch version: pp_agents/.env
# (The SDK reads OPENAI_API_KEY and OPENAI_AGENTS_DISABLE_TRACING on first use, not on import.)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

travel_agent = Agent(
    name="travel_helper",
    instructions=(
        "You are a friendly travel helper. Use the tools to look up weather, local time, "
        "attractions and currency. Never invent data: if a tool returns an error, say so. "
        "Keep answers short and practical."
    ),
    tools=ALL_TOOLS,
    model=MODEL,
)


def print_steps(result) -> None:
    """Walk the run's items: this is what our hand-written loop printed as it went."""
    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            print(f"[{item.agent.name}] calls {item.raw_item.name}({item.raw_item.arguments})")
        elif isinstance(item, ToolCallOutputItem):
            print(f"[{item.agent.name}]   -> {item.output}")
        elif isinstance(item, HandoffOutputItem):
            print(f"[handoff] {item.source_agent.name} -> {item.target_agent.name}")


def tools_called(result) -> list[str]:
    """Names of the tools the model called during a run (handy in tests)."""
    return [item.raw_item.name for item in result.new_items if isinstance(item, ToolCallItem)]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or (
        "I'm in Paris with 200 USD. What's the weather, what should I visit given the weather, "
        "and how much is my money in euros?"
    )
    print(f"USER: {question}\n")
    result = Runner.run_sync(travel_agent, question, max_turns=8)
    print_steps(result)
    print(f"\nAGENT: {result.final_output}")
