"""
Offline tests for the tools, in both versions.

Tools are plain Python, so test them like any other code. Also check that the
schemas (what the model reads) still match the functions (what runs): if they
drift apart, the model will call tools with arguments that don't exist.
"""

import inspect
import json
from datetime import UTC, datetime, timedelta

import sdk_tools

import tools

# ---------------------------------------------------------------- tool functions


def test_weather_known_city_is_case_insensitive():
    assert tools.get_weather("PaRiS") == {"city": "PaRiS", "temp_c": 14, "condition": "light rain"}


def test_weather_unknown_city_returns_error_not_exception():
    result = tools.get_weather("Atlantis")
    assert "error" in result and "paris" in result["error"]


def test_convert_currency():
    assert tools.convert_currency(100, "usd", "eur")["result"] == 92.0
    assert tools.convert_currency(200, "USD", "EUR")["result"] == 184.0
    assert tools.convert_currency(150, "USD", "JPY")["result"] == 22650.0


def test_convert_currency_round_trip_and_same_currency():
    eur = tools.convert_currency(100, "USD", "EUR")["result"]
    assert tools.convert_currency(eur, "EUR", "USD")["result"] == 100.0
    assert tools.convert_currency(42, "GBP", "GBP")["result"] == 42


def test_convert_currency_unsupported():
    assert "error" in tools.convert_currency(1, "USD", "BTC")


def test_local_time_uses_city_offset():
    result = tools.get_local_time("Tokyo")
    shown = datetime.strptime(result["local_time"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
    expected = datetime.now(UTC) + timedelta(hours=9)
    assert abs(shown - expected) < timedelta(minutes=2)


def test_attractions_are_marked_indoor_or_outdoor():
    for place in tools.list_attractions("london")["attractions"]:
        assert place.endswith(("(indoor)", "(outdoor)"))


# ---------------------------------------------------------------- run_tool dispatcher


def test_run_tool_parses_json_and_returns_json():
    out = tools.run_tool("convert_currency", '{"amount": 100, "from_currency": "USD", "to_currency": "EUR"}')
    assert json.loads(out)["result"] == 92.0


def test_run_tool_reports_problems_to_the_model_instead_of_raising():
    assert "Unknown tool" in tools.run_tool("book_flight", "{}")
    assert "JSONDecodeError" in tools.run_tool("get_weather", "not json")
    assert "TypeError" in tools.run_tool("get_weather", '{"town": "Paris"}')  # wrong argument name


# ---------------------------------------------------------------- schemas vs functions


def test_hand_written_schemas_match_function_signatures():
    for name, schema in tools.TOOL_SCHEMAS.items():
        params = schema["function"]["parameters"]
        func_args = set(inspect.signature(tools.TOOL_FUNCTIONS[name]).parameters)
        assert set(params["properties"]) == func_args, name
        assert set(params["required"]) <= func_args, name


def test_sdk_generated_schemas_match_the_hand_written_ones():
    """Both versions must describe the same tools to the model."""
    sdk = {t.name: t for t in sdk_tools.ALL_TOOLS}
    assert set(sdk) == set(tools.TOOL_SCHEMAS)
    for name, schema in tools.TOOL_SCHEMAS.items():
        hand = schema["function"]["parameters"]
        generated = sdk[name].params_json_schema
        assert set(generated["required"]) == set(hand["required"]), name
        # the SDK copied the "Args:" docstring lines into argument descriptions
        assert all("description" in p for p in generated["properties"].values()), name
