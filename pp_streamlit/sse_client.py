"""Tiny SSE client (no Streamlit code here, so it can be unit tested on its own).

Browsers have EventSource built in; in Python you read the text/event-stream
response line by line and group lines into events at each blank line.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import httpx


@dataclass
class SSEEvent:
    event: str = "message"  # "message" when the server sent no `event:` line
    data: str = ""
    id: str | None = None
    retry: int | None = None


def parse_sse(lines: Iterable[str]) -> Iterator[SSEEvent]:
    """Spec-style parser: `field: value` lines, `:` comments, blank line = dispatch."""
    event, data, event_id, retry = "message", [], None, None
    for line in lines:
        if line == "":
            if data:  # per the spec, an event without data is dropped
                yield SSEEvent(event, "\n".join(data), event_id, retry)
            event, data, retry = "message", [], None
            continue
        if line.startswith(":"):
            continue  # comment / heartbeat
        field, _, value = line.partition(":")
        value = value.removeprefix(" ")
        match field:
            case "event":
                event = value
            case "data":
                data.append(value)
            case "id":
                event_id = value  # the id "sticks" until the server sends a new one
            case "retry" if value.isdigit():
                retry = int(value)


def stream_events(base_url: str, last_event_id: str | None = None) -> Iterator[SSEEvent]:
    """Open GET /stream and yield events until the server closes the stream."""
    headers = {"Accept": "text/event-stream"}
    if last_event_id:
        headers["Last-Event-ID"] = last_event_id  # ask the server to resume
    # read=None: an SSE stream can be quiet for a long time; connect still times out.
    timeout = httpx.Timeout(5.0, read=None)
    with httpx.stream("GET", f"{base_url}/stream", headers=headers, timeout=timeout) as response:
        response.raise_for_status()
        yield from parse_sse(response.iter_lines())


def stop_stream(base_url: str, connection_id: str) -> dict:
    return httpx.post(f"{base_url}/stop-stream/{connection_id}", timeout=3).json()


def health(base_url: str) -> dict | None:
    try:
        return httpx.get(f"{base_url}/health", timeout=1).json()
    except (httpx.HTTPError, ValueError):  # ValueError: something else answered with non-JSON
        return None
