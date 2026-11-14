"""
Live tests for the AGENTS SDK version (agents_sdk/) against the real OpenAI model.

The SDK's RunResult records every step (new_items), so tests can ask
"which tools were called?" and "which agent gave the final answer?"
directly, instead of reading printed output.

One event loop for the whole file: the SDK reuses one OpenAI HTTP client, and
its connections belong to the event loop that opened them. Calling
Runner.run_sync() in one test and asyncio.run() in the next gives each a NEW
loop, and the second test hangs forever on the first loop's connection.
(Found the hard way.) So every test runs its coroutine through the same
asyncio.Runner, via the `run` fixture below. Same rule in real apps: pick one
loop and stay on it.
"""

import asyncio

import pytest
import sdk_mcp_agent
import sdk_orchestrator as orch
from agents import Runner
from conftest import mentions_number
from sdk_agent import tools_called, travel_agent

pytestmark = pytest.mark.llm


@pytest.fixture(scope="module")
def run():
    with asyncio.Runner() as runner:
        yield runner.run


TRIP = "One afternoon in Tokyo with 150 USD: what's the weather and how much is that in yen?"


def test_agent_calls_all_needed_tools_and_uses_their_numbers(run):
    result = run(
        Runner.run(
            travel_agent, "I'm in Paris with 200 USD. What's the weather, what should I visit, and how much in euros?"
        )
    )
    assert {"get_weather", "list_attractions", "convert_currency"} <= set(tools_called(result))
    assert mentions_number(result.final_output, "184"), result.final_output


def test_agent_only_calls_tools_it_needs(run):
    result = run(Runner.run(travel_agent, "Convert 100 USD to EUR."))
    assert tools_called(result) == ["convert_currency"]
    assert mentions_number(result.final_output, "92"), result.final_output


def test_mcp_agent_uses_server_tools(run):
    result = run(sdk_mcp_agent.ask("How much is 50 GBP in INR?"))
    assert "convert_currency" in tools_called(result)
    assert mentions_number(result.final_output, "5316.46"), result.final_output


def test_agents_as_tools_coordinator_delegates_and_keeps_tool_numbers(run):
    result = run(orch.agents_as_tools(TRIP))
    called = tools_called(result)  # the coordinator's tools are the specialists
    assert "ask_budget" in called and "ask_weather" in called, called
    assert result.last_agent.name == "coordinator"  # manager kept control
    assert mentions_number(result.final_output, "22650"), result.final_output


def test_parallel_fan_out_then_writer(run):
    result = run(orch.parallel(TRIP))
    assert result.last_agent.name == "writer"
    assert mentions_number(result.final_output, "22650"), result.final_output


@pytest.mark.parametrize(
    ("question", "expected_agent", "expected_tool"),
    [
        ("How much is 80 GBP in INR?", "budget", "convert_currency"),
        ("What's the weather like in London right now?", "weather", "get_weather"),
        ("Which attractions are there in Bangalore?", "sightseeing", "list_attractions"),
    ],
)
def test_handoff_routes_to_the_right_specialist(run, question, expected_agent, expected_tool):
    result = run(orch.handoff(question))
    assert result.last_agent.name == expected_agent  # control was transferred, specialist answered
    assert expected_tool in tools_called(result)
