# PyPractice

A personal learning repository for experimenting with new technologies, tools, and frameworks. This repo contains working prototypes and simple applications to learn and master various Python-based technologies and concepts.

## Overview

This repository serves as a sandbox for:
- Learning new technologies and frameworks
- Building working prototypes
- Experimenting with different architectural patterns
- Refreshing knowledge on core concepts
- Testing integration between different tools

## Project Structure

### API & Web Development
- **`pp_fastapi/`** - FastAPI reference app: versioned `APIRouter`s (`/api/v1`, `/api/v2`), all three middleware styles plus built-ins, dependencies and auth header, Pydantic v2 models, exception handlers, lifespan, background tasks, tests
- **`pp_sse/`** - Server-Sent Events: named events, event IDs, resume with `Last-Event-ID`, stop endpoint, HTML client, tests
- **`pp_sockets/`** - WebSockets: pure `websockets` private chat server and a FastAPI room-based chat, HTML clients, tests
- **`pp_streamlit/`** - Streamlit test bench: SSE stream page and WebSocket chat page (navigation, fragments, session state, AppTest)

### Communication & Networking
- **`pp_grpc/`** - gRPC: all four RPC styles (unary, server/client/bidirectional streaming), interceptor, status codes, deadlines, REST gateway, tests
- **`pp_memcached/`** - Memcached with pymemcache: core commands, counters, TTL, CAS, cache-aside pattern; Docker Compose with an admin UI and a Dockerised integration-test runner

### AI Agents
- **`pp_agents/`** - Agents from scratch with OpenAI: tools and the agent loop, an MCP server and MCP-client agent, and an orchestrator that spawns sub-agents (LLM-driven and parallel fan-out)

### Infrastructure
- **`pp_k8s/graceful_shutdown/`** - FastAPI + preStop + request draining on kind, with and without preStop (Docker, kind, kubectl)

### Core Python Concepts
- **`py_async/`** - asyncio series 01–08 (event loop to production patterns), producer/consumer, pub/sub, generators
- **`py_dsa/`** - Data Structures and Algorithms practice

## Getting Started

Requires **Python 3.11+**.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt  # everything; or a folder's own req.txt

pytest pp_fastapi                # FastAPI tests run from the repo root
cd pp_grpc && pytest             # the other folders run their tests from inside the folder
docker compose -f pp_memcached/docker-compose.yaml run --rm tester   # memcached tests in Docker
```

Each folder has its own `README.md` with run instructions and a short list of interview reminders.

## Technologies Explored

- **FastAPI** - Modern web framework for building APIs
- **gRPC** - High-performance RPC framework
- **Protocol Buffers** - Data serialization format
- **Memcached** - Distributed memory caching system
- **Docker** - Containerization
- **WebSockets** - Real-time bidirectional communication
- **Server-Sent Events** - Real-time unidirectional data streaming
- **Streamlit** - Interactive web UI for testing and demonstration
- **Kubernetes** - Graceful shutdown, probes, preStop hooks (kind)
- **OpenAI / MCP** - Tool-calling agents, Model Context Protocol, multi-agent orchestration
- **AsyncIO** - Asynchronous programming in Python
- **Data Structures** - Core algorithms and data structure implementations
