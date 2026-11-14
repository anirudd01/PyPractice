# AI Agents from Scratch (OpenAI + MCP)

Learn how agents work by reading small, plain files. No agent framework: just the
OpenAI SDK and the official `mcp` package, so you can see every step.

**Use case:** a tiny travel helper. The tools return fake, hard-coded data (weather,
local time, attractions, fixed currency rates), so only the LLM call needs the internet.

## Read in this order

| File | What it teaches |
| ---- | --------------- |
| `tools.py` | What a tool is: a Python function + a JSON schema + a name-to-function lookup. Run it alone to try the tools without an LLM. |
| `agent.py` | The agent loop: call the model, run the tools it asks for, feed results back, repeat until it answers. |
| `mcp_server.py` | The same tools served over MCP. `MCPServer` (called FastMCP in mcp 1.x) builds schemas from type hints and docstrings. Also shows a resource. |
| `mcp_agent.py` | An agent that discovers tools from the MCP server at runtime and lets the server run them. |
| `orchestrator.py` | One agent spawning focused sub-agents. LLM-driven delegation (default) and code-driven parallel fan-out (`--parallel`). |

## Setup

```bash
cd pp_agents
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r req.txt
```

Put your key in `pp_agents/.env` (git-ignored):

```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
```

## Run

```bash
python tools.py                     # no LLM, just the tools
python agent.py                     # default question
python agent.py "Is it a good day for Tokyo? What time is it there?"
python mcp_agent.py                 # starts mcp_server.py itself over stdio
python orchestrator.py              # LLM decides which sub-agents to spawn
python orchestrator.py --parallel   # code runs all sub-agents at once, a writer merges
```

Inspect the MCP server by hand (needs Node): `npx @modelcontextprotocol/inspector python mcp_server.py`

## Reminders

- The model never runs code. It returns a *request* to call a tool; your code runs it and sends the result back as a `tool` message with the matching `tool_call_id`.
- Tool descriptions are prompts. Vague descriptions give wrong tool choices.
- Return errors to the model as text instead of raising, so it can recover.
- Always cap the loop (`max_turns`).
- MCP separates *who defines and runs tools* (server) from *who uses them* (any client). Over stdio, never `print()` to stdout in the server.
- A sub-agent is the same loop with a narrower prompt, fewer tools and a fresh conversation. It can't see the parent's history, so delegated tasks must be self-contained.
- LLM-driven orchestration is flexible; code-driven is predictable and easy to parallelise.
- Sub-agents given a wide question "help" outside their job and guess numbers. Fix it in the prompts: a narrow job per specialist, shared rules (stay in your lane, only state tool facts), and a final writer that keeps tool numbers exactly and trusts the specialist who owns each topic.
