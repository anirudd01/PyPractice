"""
sdk_orchestrator.py - multi-agent patterns with the OpenAI Agents SDK.

Compare with ../orchestrator.py. Same specialists, same prompt rules, but:

  A) Agents as tools (default)
     ../orchestrator.py: we wrote an ask_specialist tool schema, a tool
     runner, and spawn_subagent() that ran a fresh loop.
     Here: specialist.as_tool(...) turns an Agent into a tool. When the
     coordinator calls it, the SDK runs that agent on a fresh conversation
     and returns its final answer as the tool result.

  B) Parallel fan-out / fan-in (--parallel)
     ../orchestrator.py: threads + the synchronous loop.
     Here: the SDK is async, so asyncio.gather runs the specialists at once.

  C) Handoffs (--handoff)  -- new, the from-scratch version doesn't have it
     A triage agent doesn't call a specialist and wait for a report; it
     HANDS OVER the conversation. The specialist then answers the user
     directly and the run ends with it. Good for routing ("which desk
     should handle this?"), not for combining several answers.
     Rule of thumb: as_tool = manager keeps control; handoff = transfer control.

Run (from pp_agents/agents_sdk):
    python sdk_orchestrator.py
    python sdk_orchestrator.py --parallel
    python sdk_orchestrator.py --handoff
    python sdk_orchestrator.py --handoff "How much is 80 GBP in INR?"
"""

import asyncio
import sys

from agents import Agent, Runner
from sdk_agent import MODEL, print_steps
from sdk_tools import convert_currency, get_local_time, get_weather, list_attractions

# ---------------------------------------------------------------------------
# The specialists: narrow job + only the tools that job needs.
# Same lesson as ../orchestrator.py: wide jobs make sub-agents guess numbers.
# ---------------------------------------------------------------------------
SUBAGENT_RULES = """Rules:
- Do ONLY your job. Other specialists handle everything else; ignore those parts of the task.
- State only facts returned by your tools. Never estimate or invent prices, costs,
  exchange rates, places or opening times.
- Give exact numbers as the tools returned them.
- No advice or suggestions beyond your job. Reply in 1-3 short sentences."""


def specialist(name: str, job: str, tools: list) -> Agent:
    return Agent(
        name=name,
        handoff_description=f"Specialist who can {job}.",  # what a triage agent reads when routing
        instructions=f"You are the {name} specialist. Your job: {job}.\n\n{SUBAGENT_RULES}",
        tools=tools,
        model=MODEL,
    )


weather_agent = specialist(
    "weather",
    "report the current weather and local time, and say if it suits indoor or outdoor activities",
    [get_weather, get_local_time],
)
sightseeing_agent = specialist(
    "sightseeing", "list the city's attractions and mark each one indoor or outdoor", [list_attractions]
)
budget_agent = specialist("budget", "convert the money amount into the requested currency", [convert_currency])
SPECIALISTS = [weather_agent, sightseeing_agent, budget_agent]


# ---------------------------------------------------------------------------
# A) Agents as tools: the coordinator keeps control and combines the reports
# ---------------------------------------------------------------------------
coordinator = Agent(
    name="coordinator",
    instructions=(
        "You are a trip-planning coordinator with no data tools of your own.\n"
        "1. Split the request into parts. Call each specialist tool with ONE narrow, self-contained "
        'task that matches its job (e.g. "Convert 150 USD to JPY", not "plan a budget"). '
        "The specialists cannot see this conversation, so include the city, amounts and currencies.\n"
        "2. Combine their reports into one short, practical plan.\n"
        "Use only facts the specialists reported and keep their numbers exactly as given. "
        "Do not add prices, cost breakdowns, places or times nobody reported."
    ),
    tools=[
        a.as_tool(tool_name=f"ask_{a.name}", tool_description=a.handoff_description, max_turns=5) for a in SPECIALISTS
    ],
    model=MODEL,
)


async def agents_as_tools(request: str):
    return await Runner.run(coordinator, request, max_turns=8)


# ---------------------------------------------------------------------------
# B) Parallel fan-out, then a writer agent fans in
# ---------------------------------------------------------------------------
writer = Agent(
    name="writer",
    instructions=(
        "You write short, practical trip plans from specialist reports.\n"
        "- Use ONLY facts in the reports. Do not add places, prices, cost breakdowns or times.\n"
        "- Copy numbers exactly as reported.\n"
        "- If reports disagree, trust the specialist that owns the topic "
        "(budget for money, weather for weather and time, sightseeing for places)."
    ),
    model=MODEL,
)


async def parallel(request: str):
    # Every specialist sees the full request; its job in the instructions makes it pick its part.
    task = f"Do only your job for this user request, ignore the rest:\n{request}"
    results = await asyncio.gather(*(Runner.run(a, task, max_turns=5) for a in SPECIALISTS))
    for a, r in zip(SPECIALISTS, results, strict=True):
        print(f"  << {a.name} reported: {r.final_output}")

    reports = "\n\n".join(f"## {a.name} report\n{r.final_output}" for a, r in zip(SPECIALISTS, results, strict=True))
    return await Runner.run(writer, f"User request: {request}\n\nSpecialist reports:\n{reports}")


# ---------------------------------------------------------------------------
# C) Handoffs: triage routes the conversation to ONE specialist, who answers
# ---------------------------------------------------------------------------
triage = Agent(
    name="triage",
    instructions=(
        "You are the front desk. Do not answer questions yourself. "
        "Hand the conversation off to the one specialist best suited to the user's question."
    ),
    handoffs=SPECIALISTS,  # the SDK turns each into a transfer_to_<name> tool
    model=MODEL,
)


async def handoff(request: str):
    return await Runner.run(triage, request, max_turns=8)


DEFAULT_TRIP = (
    "I have one afternoon in Tokyo and 150 USD. What should I do given the weather, and how much is my budget in yen?"
)
DEFAULT_HANDOFF = "What's the weather like in London right now?"


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "parallel" if "--parallel" in args else "handoff" if "--handoff" in args else "as_tools"
    request = " ".join(a for a in args if not a.startswith("--")) or (
        DEFAULT_HANDOFF if mode == "handoff" else DEFAULT_TRIP
    )
    print(f"USER: {request}  (mode: {mode})\n")
    run = {"as_tools": agents_as_tools, "parallel": parallel, "handoff": handoff}[mode]
    result = asyncio.run(run(request))
    print_steps(result)
    print(f"\nFINAL ({result.last_agent.name}):\n{result.final_output}")
