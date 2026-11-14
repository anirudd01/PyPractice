"""
orchestrator.py - one agent that spawns and coordinates sub-agents.

A sub-agent is NOT special: it is run_agent() from agent.py with
  - its own system prompt (a narrow job),
  - a smaller tool list (only what that job needs),
  - a FRESH conversation (it doesn't see the orchestrator's history).

Why bother? Small focused agents follow instructions better, keep the main
conversation short, and can run in parallel.

Two common ways to orchestrate, both shown here:

  A) LLM-driven ("agents as tools", the default)
     The orchestrator gets one tool, ask_specialist(specialist, task).
     The MODEL decides which specialists to call, with what task, and when
     it has enough to answer. Flexible, but less predictable.

  B) Code-driven ("fan-out / fan-in", run with --parallel)
     YOUR code decides: run all specialists at the same time in threads,
     then hand their reports to a writer agent. Predictable and faster,
     but the plan is fixed.

Run:
    python orchestrator.py
    python orchestrator.py --parallel
    python orchestrator.py "Plan an afternoon in London on 80 GBP, I'm paying in INR"
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from agent import run_agent
from tools import schemas_for

# ---------------------------------------------------------------------------
# The specialists
#   job   : one line saying what this specialist owns (and nothing else)
#   tools : the only tools it may use
#
# Lesson learned from running this: give a sub-agent a wide question and it
# "helps" by answering parts that aren't its job, often with guessed numbers
# (a weather agent guessing the exchange rate). The fixes are all prompt-level:
#   1. a narrow job per specialist,
#   2. shared rules: stay in your lane, only state facts your tools returned,
#   3. a final writer that trusts tool numbers over anything else.
# ---------------------------------------------------------------------------
SPECIALISTS = {
    "weather": {
        "job": "report the current weather and local time, and say if it suits indoor or outdoor activities",
        "tools": ["get_weather", "get_local_time"],
    },
    "sightseeing": {
        "job": "list the city's attractions and mark each one indoor or outdoor",
        "tools": ["list_attractions"],
    },
    "budget": {
        "job": "convert the money amount into the requested currency",
        "tools": ["convert_currency"],
    },
}

# Rules every sub-agent gets, on top of its job.
SUBAGENT_RULES = """Rules:
- Do ONLY your job. Other specialists handle everything else; ignore those parts of the task.
- State only facts returned by your tools. Never estimate or invent prices, costs,
  exchange rates, places or opening times.
- Give exact numbers as the tools returned them.
- No advice or suggestions beyond your job. Reply in 1-3 short sentences."""


def spawn_subagent(specialist: str, task: str) -> str:
    """Create a sub-agent for one task and return its answer."""
    if specialist not in SPECIALISTS:
        return f"Unknown specialist '{specialist}'. Choose from {list(SPECIALISTS)}."
    spec = SPECIALISTS[specialist]
    prompt = f"You are the {specialist} specialist. Your job: {spec['job']}.\n\n{SUBAGENT_RULES}"
    print(f"\n  >> spawning sub-agent '{specialist}' with task: {task}")
    answer = run_agent(task, prompt, tools=schemas_for(spec["tools"]), name=f"  sub:{specialist}")
    print(f"  << '{specialist}' reported: {answer}\n")
    return answer


# ---------------------------------------------------------------------------
# A) LLM-driven orchestration
# ---------------------------------------------------------------------------
ASK_SPECIALIST_TOOL = {
    "type": "function",
    "function": {
        "name": "ask_specialist",
        "description": "Delegate a focused task to a specialist sub-agent and get its report back.",
        "parameters": {
            "type": "object",
            "properties": {
                "specialist": {"type": "string", "enum": list(SPECIALISTS)},
                "task": {
                    "type": "string",
                    "description": "A complete, self-contained instruction. The specialist cannot "
                    "see this conversation, so include the city, amounts, currencies, etc.",
                },
            },
            "required": ["specialist", "task"],
        },
    },
}

ORCHESTRATOR_PROMPT = f"""You are a trip-planning coordinator. You have no data tools yourself.

Specialists you can call with ask_specialist:
{chr(10).join(f"- {name}: {spec['job']}" for name, spec in SPECIALISTS.items())}

Steps:
1. Split the request into parts. Send each specialist ONE narrow task that matches
   its job exactly (e.g. "Convert 150 USD to JPY", not "plan a budget").
2. Combine their reports into one short, practical plan.

Rules for the plan:
- Use only facts the specialists reported. Keep their numbers exactly as given.
- Do not add prices, cost breakdowns, places or times nobody reported.
- If something the user asked for can't be answered by any specialist, say so."""


def orchestrator_tool_runner(name: str, arguments_json: str) -> str:
    """The orchestrator's only tool: spawning a sub-agent."""
    if name != "ask_specialist":
        return f"Unknown tool '{name}'"
    try:
        args = json.loads(arguments_json)
        return spawn_subagent(args["specialist"], args["task"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:  # bad arguments: tell the model, don't crash
        return f"Bad ask_specialist arguments ({type(exc).__name__}: {exc}). Send 'specialist' and 'task'."


def llm_driven(request: str) -> str:
    return run_agent(
        request,
        ORCHESTRATOR_PROMPT,
        tools=[ASK_SPECIALIST_TOOL],
        name="orchestrator",
        tool_runner=orchestrator_tool_runner,
    )


# ---------------------------------------------------------------------------
# B) Code-driven orchestration: fan out in parallel, then fan in to a writer
# ---------------------------------------------------------------------------
WRITER_PROMPT = """You write short, practical trip plans from specialist reports.
- Use ONLY facts in the reports. Do not add places, prices, cost breakdowns or times.
- Copy numbers exactly as reported.
- If reports disagree, trust the specialist that owns the topic
  (budget for money, weather for weather and time, sightseeing for places)."""


def code_driven(request: str) -> str:
    # Fan-out: every specialist sees the full request (no LLM split it for us),
    # but the task restates its job so it picks out only its own part.
    # Threads are fine here: sub-agents spend their time waiting on the network.
    with ThreadPoolExecutor() as pool:
        futures = {
            name: pool.submit(
                spawn_subagent,
                name,
                f"Your job: {spec['job']}. Do only that for this user request, ignore the rest:\n{request}",
            )
            for name, spec in SPECIALISTS.items()
        }
        reports = {name: f.result() for name, f in futures.items()}

    # Fan-in: a writer agent (no tools) merges the reports.
    merged = "\n\n".join(f"## {name} report\n{text}" for name, text in reports.items())
    return run_agent(
        f"User request: {request}\n\nSpecialist reports:\n{merged}", WRITER_PROMPT, tools=[], name="writer"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    parallel = "--parallel" in args
    request = " ".join(a for a in args if a != "--parallel") or (
        "I have one afternoon in Tokyo and 150 USD. What should I do given the weather, "
        "and how much is my budget in yen?"
    )
    print(f"USER: {request}  (mode: {'code-driven parallel' if parallel else 'LLM-driven'})")
    plan = code_driven(request) if parallel else llm_driven(request)
    print(f"\nFINAL PLAN:\n{plan}")
