"""
Shared test setup. Nothing here is mocked: every test runs real code.

Two kinds of tests:
  - Offline (no marker): real tool code and a real MCP server process.
    Free, fast, deterministic. Run them all the time.
  - Live (@pytest.mark.llm): call the real OpenAI model with your key.
    They cost a little and the wording of answers varies, so they never
    assert on exact text. They assert on things that MUST be true:
      * which tools the model actually called,
      * that the answer contains the exact number the tool returned
        (e.g. 200 USD -> 184 EUR). If the model invents a number, this fails.
    Skipped automatically when OPENAI_API_KEY is not set.

Run from pp_agents/:
    pytest                 # everything
    pytest -m "not llm"    # offline only
    pytest -m llm -v       # live model only
"""

import os
import re
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

PP_AGENTS = Path(__file__).resolve().parent.parent
# Both versions importable: from-scratch modules (tools, agent, ...) and SDK modules (sdk_*).
# Module names don't clash, so both folders can be on the path together.
sys.path.insert(0, str(PP_AGENTS))
sys.path.insert(0, str(PP_AGENTS / "agents_sdk"))

load_dotenv(PP_AGENTS / ".env")


def pytest_collection_modifyitems(config, items):
    if os.getenv("OPENAI_API_KEY"):
        return
    skip = pytest.mark.skip(reason="OPENAI_API_KEY not set in pp_agents/.env")
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(skip)


def mentions_number(text: str, number: str) -> bool:
    """True if `number` (e.g. "22650" or "5316.46") appears in text, ignoring thousands commas."""
    cleaned = (text or "").replace(",", "")
    return re.search(rf"(?<![\d.]){re.escape(number)}(?:\.0+)?(?!\d)", cleaned) is not None
