"""
Live tests for the FROM-SCRATCH version (agent.py, mcp_agent.py, orchestrator.py)
against the real OpenAI model.

Our hand-written loop returns only the final text, so to see which tools ran
we read what it printed (pytest's capsys captures stdout). Compare with
test_live_sdk.py, where the SDK's RunResult lists every step for us.
"""

import asyncio

import pytest
from conftest import mentions_number

import agent
import mcp_agent
import orchestrator

pytestmark = pytest.mark.llm


def test_agent_calls_all_needed_tools_and_uses_their_numbers(capsys):
    answer = agent.run_agent(
        "I'm in Paris with 200 USD. What's the weather, what should I visit, and how much is that in euros?",
        agent.SYSTEM_PROMPT,
        tools=list(agent.TOOL_SCHEMAS.values()),
    )
    log = capsys.readouterr().out
    for tool in ("get_weather", "list_attractions", "convert_currency"):
        assert f"calling {tool}" in log
    assert mentions_number(answer, "184"), answer  # 200 USD -> 184 EUR from the tool


def test_agent_only_calls_tools_it_needs(capsys):
    answer = agent.run_agent("Convert 100 USD to EUR.", agent.SYSTEM_PROMPT, tools=list(agent.TOOL_SCHEMAS.values()))
    log = capsys.readouterr().out
    assert "calling convert_currency" in log
    assert "calling get_weather" not in log
    assert mentions_number(answer, "92"), answer


def test_mcp_agent_uses_server_tools(capsys):
    asyncio.run(mcp_agent.main("How much is 50 GBP in INR?"))
    log = capsys.readouterr().out
    assert "convert_currency" in log
    final = log.split("AGENT:")[-1]
    assert mentions_number(final, "5316.46"), final


def test_orchestrator_llm_driven_delegates_and_keeps_tool_numbers(capsys):
    plan = orchestrator.llm_driven("One afternoon in Tokyo with 150 USD: weather and yen?")
    log = capsys.readouterr().out
    assert "spawning sub-agent 'budget'" in log
    assert "spawning sub-agent 'weather'" in log
    assert mentions_number(plan, "22650"), plan  # exact tool number, not a guess like 22,000


def test_orchestrator_parallel_runs_every_specialist(capsys):
    plan = orchestrator.code_driven("One afternoon in Tokyo with 150 USD: weather and yen?")
    log = capsys.readouterr().out
    for name in orchestrator.SPECIALISTS:
        assert f"spawning sub-agent '{name}'" in log
    assert "calling convert_currency" in log
    assert mentions_number(plan, "22650"), plan
