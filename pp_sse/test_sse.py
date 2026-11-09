"""Tests for the SSE server. Run (from pp_sse/):  pytest -v"""

import json

import pytest
from fastapi.testclient import TestClient

import main


def parse_events(lines) -> list[dict]:
    """Minimal SSE parser: groups lines into events at each blank line."""
    events, current = [], {}
    for line in lines:
        if not line:
            if current:
                events.append(current)
            current = {}
            continue
        field, _, value = line.partition(": ")
        current[field] = current[field] + "\n" + value if field == "data" and field in current else value
    return events


@pytest.fixture
def client(tmp_path, monkeypatch):
    text = tmp_path / "book.txt"
    text.write_text("One. Two. Three.\n\nFour. Five.\n", encoding="utf-8")
    monkeypatch.setattr(main, "TEXT_FILE", text)
    monkeypatch.setattr(main, "DELAY_S", 0)
    monkeypatch.setattr(main, "PROGRESS_EVERY", 2)
    return TestClient(main.app)


def test_sse_event_format():
    assert main.sse_event("a\nb", event="x", event_id=7) == "event: x\nid: 7\ndata: a\ndata: b\n\n"


def test_full_stream(client):
    with client.stream("GET", "/stream") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = parse_events(r.iter_lines())

    assert events[0]["event"] == "connected" and events[0]["retry"] == "3000"
    sentences = [e["data"] for e in events if "event" not in e]
    assert sentences == ["One.", "Two.", "Three.", "Four.", "Five."]
    assert [json.loads(e["data"])["sent"] for e in events if e.get("event") == "progress"] == [2, 4]
    assert json.loads(events[-1]["data"]) == {"reason": "completed", "sent": 5}
    assert main.active_connections == {}


def test_resume_with_last_event_id(client):
    with client.stream("GET", "/stream", headers={"Last-Event-ID": "3"}) as r:
        events = parse_events(r.iter_lines())
    assert [e["id"] for e in events if "id" in e] == ["4", "5"]


def test_stop_stream(client, monkeypatch):
    monkeypatch.setattr(main, "DELAY_S", 0.05)
    with client.stream("GET", "/stream") as r:
        lines = r.iter_lines()
        first = parse_events(iter([next(lines), next(lines), next(lines), ""]))[0]
        connection_id = json.loads(first["data"])["connection_id"]
        assert client.post(f"/stop-stream/{connection_id}").json()["status"] == "streaming stopped"
        events = parse_events(lines)
    assert json.loads(events[-1]["data"])["reason"] == "stopped by client"
