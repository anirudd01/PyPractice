"""
sdk_tools.py - the same travel tools, declared the OpenAI Agents SDK way.

Compare with ../tools.py (the from-scratch version):
  - There we wrote a JSON schema by hand for every tool, kept a
    name -> function dict, and wrote run_tool() to parse arguments and catch errors.
  - Here @function_tool does all three. It reads:
      * the function name           -> tool name
      * the type hints              -> JSON schema of the arguments
      * the docstring (+ "Args:")   -> descriptions the model reads
    and when the model calls the tool, the SDK parses the JSON, calls the
    function and sends the result back. If the function raises, the SDK
    sends the error text to the model instead of crashing (same idea as our
    run_tool, but built in).

The tool bodies just call the plain functions in ../tools.py so both
versions use exactly the same fake data.
"""

import sys
from pathlib import Path

from agents import function_tool

# Make ../tools.py importable (it lives in the parent folder).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools


@function_tool
def get_weather(city: str) -> dict:
    """Get the current weather (temperature in C and condition) for a city.

    Args:
        city: City name, e.g. Paris.
    """
    return tools.get_weather(city)


@function_tool
def get_local_time(city: str) -> dict:
    """Get the current local date and time in a city.

    Args:
        city: City name, e.g. Tokyo.
    """
    return tools.get_local_time(city)


@function_tool
def list_attractions(city: str) -> dict:
    """List popular attractions in a city, each marked as indoor or outdoor.

    Args:
        city: City name, e.g. London.
    """
    return tools.list_attractions(city)


@function_tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount of money from one currency to another (USD, EUR, GBP, JPY, INR).

    Args:
        amount: Amount to convert.
        from_currency: 3-letter code, e.g. USD.
        to_currency: 3-letter code, e.g. EUR.
    """
    return tools.convert_currency(amount, from_currency, to_currency)


ALL_TOOLS = [get_weather, get_local_time, list_attractions, convert_currency]


if __name__ == "__main__":
    # See what the SDK generated from the type hints and docstrings:  python sdk_tools.py
    import json

    for t in ALL_TOOLS:
        print(f"{t.name}: {t.description}")
        print(json.dumps(t.params_json_schema, indent=2), "\n")
