# AI Agents: From Scratch and with the OpenAI Agents SDK

Learn how agents work by building the same thing twice:

1. **From scratch** (this folder): just the OpenAI SDK and the official `mcp` package, so you see every step of the loop.
2. **With the OpenAI Agents SDK** (`agents_sdk/`): the same agents, tools and patterns, with the framework doing the loop.

Read a from-scratch file, then its SDK twin, and you can see exactly what the framework hides.

**Use case:** a tiny travel helper. The tools return fake, hard-coded data (weather,
local time, attractions, fixed currency rates), so only the LLM call needs the internet.
Both versions share the same data (`tools.py`) and the same MCP server (`mcp_server.py`).

## Read in this order

| Topic | From scratch | Agents SDK | What changes |
| ----- | ------------ | ---------- | ------------ |
| Tools | `tools.py` | `agents_sdk/sdk_tools.py` | Hand-written JSON schemas + dispatcher vs `@function_tool` building them from type hints and docstrings |
| One agent | `agent.py` | `agents_sdk/sdk_agent.py` | Our own loop vs `Runner.run`; `RunResult` records every step |
| MCP | `mcp_agent.py` (+ `mcp_server.py`) | `agents_sdk/sdk_mcp_agent.py` | We list, convert and call MCP tools vs `Agent(mcp_servers=[...])`. Same server for both |
| Multi-agent | `orchestrator.py` | `agents_sdk/sdk_orchestrator.py` | Hand-made "ask specialist" tool vs `agent.as_tool()`; threads vs `asyncio.gather`; plus SDK **handoffs** |
| Tests | `tests/` | `tests/` | Real tests for both versions, see below |

## Setup

```bash
cd pp_agents
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r req.txt
```

Put your key in `pp_agents/.env` (git-ignored, used by both versions):

```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
# OPENAI_AGENTS_DISABLE_TRACING=1   # SDK only: stop uploading run traces to your OpenAI account
```

## Run

From scratch (from `pp_agents/`):

```bash
python tools.py                     # no LLM, just the tools
python agent.py                     # default question
python agent.py "Is it a good day for Tokyo? What time is it there?"
python mcp_agent.py                 # starts mcp_server.py itself over stdio
python orchestrator.py              # LLM decides which sub-agents to spawn
python orchestrator.py --parallel   # code runs all sub-agents at once, a writer merges
```

Agents SDK (from `pp_agents/agents_sdk/`):

```bash
python sdk_tools.py                     # print the schemas the SDK generated
python sdk_agent.py
python sdk_mcp_agent.py                 # same ../mcp_server.py
python sdk_orchestrator.py              # agents as tools: coordinator keeps control
python sdk_orchestrator.py --parallel   # asyncio.gather fan-out, then a writer
python sdk_orchestrator.py --handoff    # triage hands the conversation to one specialist
```

The SDK uploads each run as a trace to your OpenAI account (platform.openai.com, Traces):
a visual timeline of every model call, tool call and handoff. Useful for learning.

Inspect the MCP server by hand (needs Node): `npx @modelcontextprotocol/inspector python mcp_server.py`

## Tests

No mocks: every test runs real code.

```bash
pytest -m "not llm"   # offline: real tools + real MCP server process (free, ~10 s)
pytest -m llm         # live: real OpenAI model for both versions (needs the key, ~1 min, costs cents)
pytest                # everything
```

- `test_tools.py`: the tool functions, the dispatcher's error handling, and that both versions describe the same tools to the model.
- `test_mcp_server.py`: starts `mcp_server.py` and talks MCP to it like any client would.
- `test_live_from_scratch.py` / `test_live_sdk.py`: real agent runs. Answers vary in wording, so tests never compare text. They check what must be true: **which tools were called**, **which agent answered** (handoffs), and that **the exact tool number appears** in the answer (200 USD must be 184 EUR, not "about 180").

## Reminders

- The model never runs code. It returns a *request* to call a tool; your code (or the SDK) runs it and sends the result back.
- Tool descriptions are prompts. Vague descriptions give wrong tool choices.
- Return errors to the model as text instead of raising, so it can recover. The SDK does this for you.
- Always cap the loop (`max_turns`).
- MCP separates *who defines and runs tools* (server) from *who uses them* (any client). Over stdio, never `print()` to stdout in the server.
- A sub-agent is the same loop with a narrower prompt, fewer tools and a fresh conversation. It can't see the parent's history, so delegated tasks must be self-contained.
- LLM-driven orchestration is flexible; code-driven is predictable and easy to parallelise.
- Agent as tool = the manager keeps control and combines answers. Handoff = control moves to the specialist, who answers the user.
- Sub-agents given a wide question "help" outside their job and guess numbers. Fix it in the prompts: a narrow job per specialist, shared rules (stay in your lane, only state tool facts), and a final writer that keeps tool numbers exactly.
- Async: stay on one event loop. The SDK reuses its HTTP client, and connections opened on one loop hang when used from another (mixing `Runner.run_sync` and `asyncio.run` in one process).
