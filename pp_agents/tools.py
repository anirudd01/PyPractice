"""
tools.py - the central toolbox shared by every file in this folder.

Use case: a tiny TRAVEL HELPER. The data is fake and hard-coded so everything
runs offline; only the agent (the LLM) needs the internet.

A "tool" for an LLM is just three things:
  1. A normal Python function that does the work.
  2. A JSON schema that DESCRIBES the function to the model
     (name, what it does, which arguments it takes).
  3. A way to look the function up by name when the model asks to call it.

The model never runs your code. It only replies "please call get_weather with
{"city": "Paris"}". YOUR code runs the function and sends the result back.
"""

import json
from datetime import UTC, datetime, timedelta

# ---------------------------------------------------------------------------
# 1. Fake data
# ---------------------------------------------------------------------------
WEATHER = {
    "paris": {"temp_c": 14, "condition": "light rain"},
    "tokyo": {"temp_c": 19, "condition": "sunny"},
    "london": {"temp_c": 11, "condition": "cloudy"},
    "bangalore": {"temp_c": 27, "condition": "partly cloudy"},
    "new york": {"temp_c": 9, "condition": "windy"},
}

# How many units of each currency you get for 1 USD.
RATES_PER_USD = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 151.0, "INR": 84.0}

# Fixed offsets keep it simple; real code would use zoneinfo (these ignore daylight saving).
UTC_OFFSET_HOURS = {"paris": 1, "tokyo": 9, "london": 0, "bangalore": 5.5, "new york": -5}

ATTRACTIONS = {
    "paris": ["Louvre (indoor)", "Eiffel Tower (outdoor)", "Musee d'Orsay (indoor)"],
    "tokyo": ["Senso-ji Temple (outdoor)", "teamLab Planets (indoor)", "Shibuya Crossing (outdoor)"],
    "london": ["British Museum (indoor)", "Tower of London (outdoor)", "Tate Modern (indoor)"],
    "bangalore": ["Lalbagh Garden (outdoor)", "Bangalore Palace (indoor)", "Cubbon Park (outdoor)"],
    "new york": ["MoMA (indoor)", "Central Park (outdoor)", "Natural History Museum (indoor)"],
}


# ---------------------------------------------------------------------------
# 2. The tool functions (plain Python, nothing AI-specific)
#    Return simple dicts; errors are returned as data too, so the model
#    can read them and recover (e.g. ask the user for a different city).
# ---------------------------------------------------------------------------
def get_weather(city: str) -> dict:
    """Current weather for a city."""
    data = WEATHER.get(city.lower())
    if data is None:
        return {"error": f"No weather data for '{city}'. Known cities: {list(WEATHER)}"}
    return {"city": city, **data}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert money between currencies using fixed rates."""
    src, dst = from_currency.upper(), to_currency.upper()
    if src not in RATES_PER_USD or dst not in RATES_PER_USD:
        return {"error": f"Unsupported currency. Supported: {list(RATES_PER_USD)}"}
    usd = amount / RATES_PER_USD[src]
    return {"amount": amount, "from": src, "to": dst, "result": round(usd * RATES_PER_USD[dst], 2)}


def get_local_time(city: str) -> dict:
    """Current local time in a city."""
    offset = UTC_OFFSET_HOURS.get(city.lower())
    if offset is None:
        return {"error": f"Unknown city '{city}'. Known cities: {list(UTC_OFFSET_HOURS)}"}
    now = datetime.now(UTC) + timedelta(hours=offset)
    return {"city": city, "local_time": now.strftime("%Y-%m-%d %H:%M")}


def list_attractions(city: str) -> dict:
    """Top attractions in a city, each marked indoor or outdoor."""
    places = ATTRACTIONS.get(city.lower())
    if places is None:
        return {"error": f"No attractions for '{city}'. Known cities: {list(ATTRACTIONS)}"}
    return {"city": city, "attractions": places}


# ---------------------------------------------------------------------------
# 3. Schemas: how the model learns what each tool does.
#    This is the OpenAI Chat Completions "tools" format.
#    The description matters a lot: it is the only thing the model reads.
# ---------------------------------------------------------------------------
def _city_tool(name: str, description: str) -> dict:
    """Small helper: all city tools take a single 'city' string."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name, e.g. Paris"}},
                "required": ["city"],
            },
        },
    }


TOOL_SCHEMAS = {
    "get_weather": _city_tool("get_weather", "Get the current weather (temperature in C and condition) for a city."),
    "get_local_time": _city_tool("get_local_time", "Get the current local date and time in a city."),
    "list_attractions": _city_tool(
        "list_attractions", "List popular attractions in a city, each marked as indoor or outdoor."
    ),
    "convert_currency": {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert an amount of money from one currency to another (USD, EUR, GBP, JPY, INR).",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount to convert"},
                    "from_currency": {"type": "string", "description": "3-letter code, e.g. USD"},
                    "to_currency": {"type": "string", "description": "3-letter code, e.g. EUR"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
}

# Name -> function. This is how we find the code to run when the model asks.
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "convert_currency": convert_currency,
    "get_local_time": get_local_time,
    "list_attractions": list_attractions,
}


def schemas_for(names: list[str]) -> list[dict]:
    """Pick a subset of tools. Sub-agents only get the tools they need."""
    return [TOOL_SCHEMAS[n] for n in names]


def run_tool(name: str, arguments_json: str) -> str:
    """
    Execute a tool the model asked for.
    The model sends arguments as a JSON STRING, so we parse it first,
    and we send the result back as a string too.
    """
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return json.dumps({"error": f"Unknown tool '{name}'"})
    try:
        args = json.loads(arguments_json or "{}")
        return json.dumps(func(**args))
    except Exception as exc:  # noqa: BLE001 - bad JSON or wrong arguments: tell the model, don't crash
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    # Try the tools without any LLM:  python tools.py
    print(run_tool("get_weather", '{"city": "Paris"}'))
    print(run_tool("convert_currency", '{"amount": 100, "from_currency": "USD", "to_currency": "EUR"}'))
    print(run_tool("get_local_time", '{"city": "Tokyo"}'))
    print(run_tool("list_attractions", '{"city": "London"}'))
    print(run_tool("get_weather", '{"city": "Atlantis"}'))  # error path
