"""Tests for the Streamlit test bench. Run (from pp_streamlit/):  pytest -v

- Pure logic (SSE parsing) with plain pytest.
- Clients against the REAL pp_sse and pp_sockets apps, served by uvicorn in a thread.
- Pages with streamlit.testing.v1.AppTest (headless, in-process, no browser).
"""

import importlib.util
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from streamlit.testing.v1 import AppTest

from sse_client import parse_sse, stream_events
from ws_client import RoomClient

REPO = Path(__file__).resolve().parent.parent


def load_module(name: str, path: Path):
    """Both server folders name their file main.py, so load each by path under its own name."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def serve():
    servers = []

    def _serve(app) -> int:
        port = free_port()
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        threading.Thread(target=server.run, daemon=True).start()
        while not server.started:
            time.sleep(0.05)
        servers.append(server)
        return port

    yield _serve
    for server in servers:
        server.should_exit = True


# ---------- pure logic ----------
def test_parse_sse_handles_names_ids_multiline_and_comments():
    raw = ["event: connected", "retry: 3000", "data: {}", "", ": keep-alive", "", "id: 7", "data: a", "data: b", ""]
    events = list(parse_sse(raw))
    assert [(e.event, e.data, e.id, e.retry) for e in events] == [
        ("connected", "{}", None, 3000),
        ("message", "a\nb", "7", None),
    ]


# ---------- clients against the real servers ----------
def test_sse_client_full_stream_and_resume(serve, monkeypatch):
    sse = load_module("pp_sse_main", REPO / "pp_sse" / "main.py")
    monkeypatch.setattr(sse, "DELAY_S", 0)
    monkeypatch.setattr(sse, "TEXT_FILE", Path("missing.txt"))  # use the built-in sample text
    url = f"http://127.0.0.1:{serve(sse.app)}"

    events = list(stream_events(url))
    sentences = [e for e in events if e.event == "message"]
    assert events[0].event == "connected" and events[-1].event == "end"
    assert len(sentences) == 10

    resumed = [e for e in stream_events(url, last_event_id="8") if e.event == "message"]
    assert [e.id for e in resumed] == ["9", "10"]


def test_room_client_chat_and_rejection(serve):
    ws = load_module("pp_fastapi_ws", REPO / "pp_sockets" / "fastapi_ws.py")
    url = f"ws://127.0.0.1:{serve(ws.app)}"

    ann, bob = RoomClient(url, "py", "ann", "letmein"), RoomClient(url, "py", "bob", "letmein")
    ann.connect()
    bob.connect()
    bob.send("hi")
    deadline = time.time() + 3
    while not any(m.get("type") == "message" for m in ann.messages) and time.time() < deadline:
        time.sleep(0.05)
    assert {"type": "message", "from": "bob", "message": "hi"} in ann.messages
    ann.close()
    bob.close()

    eve = RoomClient(url, "py", "eve", "wrong")
    eve.connect()
    assert eve.status == "rejected (HTTP 403)"


# ---------- pages (servers offline) ----------
def test_pages_render_without_servers():
    at = AppTest.from_file("streamlit_app.py", default_timeout=10)
    at.session_state["sse_url"] = "http://127.0.0.1:9"  # nothing listens there
    at.run()
    assert not at.exception
    assert at.warning[0].value.startswith("Nothing is answering")

    at.switch_page("app_pages/ws_chat.py").run()
    assert not at.exception
    assert at.info[0].value == "Join a room to start chatting."
    assert at.chat_input[0].disabled
