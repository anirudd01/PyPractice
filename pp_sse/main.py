"""Server-Sent Events (SSE) with FastAPI: stream a text file sentence by sentence.

Run (from anywhere):  python pp_sse/main.py        then open pp_sse/test.html
Put a .txt file at pp_sse/data/the_intelligent_investor.txt (git-ignored), or the
server streams a built-in sample text instead.

SSE wire format cheat sheet (each event ends with a blank line):
    event: progress          <- optional name; browser listens with addEventListener("progress")
    id: 42                   <- optional; browser resends it as the Last-Event-ID header on reconnect
    retry: 3000              <- optional; reconnect delay in ms
    data: first line         <- one "data:" per line of payload
    data: second line
    : keep-alive             <- a line starting with ":" is a comment (used as a heartbeat)

The browser's EventSource reconnects automatically when the stream drops, so the
server must tell it when it is really finished (here: an "end" event).
"""

import asyncio
import json
import uuid
from collections.abc import Iterator
from itertools import islice
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Paths relative to this file, so the server works from any working directory.
TEXT_FILE = Path(__file__).parent / "data" / "the_intelligent_investor.txt"
MAX_LINES = 1000
DELAY_S = 0.1
PROGRESS_EVERY = 25

SAMPLE_TEXT = """\
Server-Sent Events let a server push updates to the browser over plain HTTP. The connection stays open.
Each message is a small block of text that ends with a blank line. Events can have a name, an id and data.
If the connection drops, the browser reconnects by itself. It sends the last id it saw in the Last-Event-ID header.
The server can then resume from where the client left off. That is what this demo does.
SSE is one-way: server to client. For two-way messages, use WebSockets instead.
"""

app = FastAPI(title="SSE Text Streaming Server")

# CORS via middleware instead of hand-written headers (test.html is opened from file://).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# connection_id -> keep streaming?  (in memory: one process only; use Redis for many)
active_connections: dict[str, bool] = {}


def sse_event(data: str, event: str | None = None, event_id: int | None = None, retry_ms: int | None = None) -> str:
    """Format one SSE event. Multi-line data becomes several `data:` lines."""
    lines = []
    if event:
        lines.append(f"event: {event}")
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if retry_ms is not None:
        lines.append(f"retry: {retry_ms}")
    lines += [f"data: {line}" for line in (data.splitlines() or [""])]
    return "\n".join(lines) + "\n\n"


def iter_sentences() -> Iterator[str]:
    """Yield sentences from at most MAX_LINES lines.

    islice stops reading the file after MAX_LINES lines, so a huge file is never fully
    read; those lines are then held in memory (fine for 1000). For true streaming you
    would iterate the file inside the generator, ideally via a thread or aiofiles,
    because file reads block the event loop.
    """
    if TEXT_FILE.exists():
        with TEXT_FILE.open(encoding="utf-8") as f:
            lines = list(islice(f, MAX_LINES))
    else:
        lines = SAMPLE_TEXT.splitlines()
    for line in lines:
        for sentence in line.strip().split("."):
            if sentence.strip():
                yield sentence.strip() + "."


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "source": TEXT_FILE.name if TEXT_FILE.exists() else "built-in sample"}


@app.post("/stop-stream/{connection_id}")
async def stop_stream(connection_id: str) -> dict:
    if connection_id in active_connections:
        active_connections[connection_id] = False
        return {"status": "streaming stopped", "connection_id": connection_id}
    return {"status": "connection not found", "connection_id": connection_id}


@app.get("/stream")
async def stream_text(
    request: Request,
    # FastAPI maps `last_event_id` to the `Last-Event-ID` header the browser sends on reconnect.
    last_event_id: Annotated[int, Header()] = 0,
) -> StreamingResponse:
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = True

    async def event_stream():
        sent = 0
        reason = "completed"
        try:
            # 1) Tell the client its ID (needed for /stop-stream) and the retry delay.
            info = {"connection_id": connection_id, "resumed_after": last_event_id}
            yield sse_event(json.dumps(info), event="connected", retry_ms=3000)

            for sentence_id, sentence in enumerate(iter_sentences(), start=1):
                if sentence_id <= last_event_id:
                    continue  # already delivered before the reconnect
                if await request.is_disconnected():
                    reason = "client disconnected"
                    break
                if not active_connections.get(connection_id):
                    reason = "stopped by client"
                    break

                # 2) Unnamed events arrive in EventSource.onmessage.
                yield sse_event(sentence, event_id=sentence_id)
                sent += 1
                # 3) Named events go to addEventListener("progress", ...).
                if sent % PROGRESS_EVERY == 0:
                    yield sse_event(json.dumps({"sent": sent}), event="progress")
                await asyncio.sleep(DELAY_S)

            # 4) Explicit end so the browser closes instead of auto-reconnecting.
            if reason != "client disconnected":
                yield sse_event(json.dumps({"reason": reason, "sent": sent}), event="end")
        finally:
            active_connections.pop(connection_id, None)
            print(f"SSE connection {connection_id} ended: {reason}, {sent} sentences sent")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tell nginx not to buffer the stream
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
