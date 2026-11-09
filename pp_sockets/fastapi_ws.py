"""WebSockets with FastAPI: room-based chat with a ConnectionManager.

Run (from pp_sockets/):  uvicorn fastapi_ws:app --port 8002 --reload
Open http://127.0.0.1:8002 in two tabs (built-in test page).

Cheat sheet:
- `@app.websocket("/path")` + `await websocket.accept()` to open the connection.
- `receive_text/receive_json` and `send_text/send_json` to talk.
- The client leaving raises `WebSocketDisconnect`; bad input can raise other errors.
  Clean up in `finally` so no exit path leaves a ghost member behind.
- Path/query params and Depends() work just like in HTTP routes.
- Reject before accepting with `await websocket.close(...)`: a real client sees the
  handshake fail with HTTP 403 (no close frame is ever sent, since the socket never
  opened). Starlette's TestClient reports it as close code 1008 instead.
- One process only: the manager lives in memory. With several workers/pods, fan out
  through Redis pub/sub (or similar) so every process sees every message.
"""

import json
from collections import defaultdict
from typing import Annotated

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse

app = FastAPI(title="FastAPI WebSocket rooms")

DEMO_TOKEN = "letmein"  # demo only: real apps validate a JWT/session here


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, dict[WebSocket, str]] = defaultdict(dict)  # room -> {socket: name}

    async def connect(self, room: str, name: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms[room][websocket] = name
        await self.broadcast(room, {"type": "system", "message": f"{name} joined #{room}", "members": self.members(room)})

    async def disconnect(self, room: str, websocket: WebSocket) -> None:
        name = self.rooms[room].pop(websocket, "someone")
        if not self.rooms[room]:
            del self.rooms[room]
            return
        await self.broadcast(room, {"type": "system", "message": f"{name} left #{room}", "members": self.members(room)})

    def members(self, room: str) -> list[str]:
        return sorted(self.rooms.get(room, {}).values())

    async def broadcast(self, room: str, data: dict) -> None:
        for ws in list(self.rooms.get(room, {})):
            try:
                await ws.send_json(data)
            except Exception:  # noqa: BLE001
                # A peer that already dropped (WebSocketDisconnect, RuntimeError...).
                # Swallow it so one dead peer can't break the SENDER's handler;
                # the peer's own handler cleans it up in its `finally`.
                pass


manager = ConnectionManager()


@app.websocket("/ws/{room}")
async def chat(
    websocket: WebSocket,
    room: str,
    name: Annotated[str, Query(min_length=1, max_length=20)],
    token: str = "",
):
    if token != DEMO_TOKEN:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(room, name, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("expected a JSON object")
            except ValueError:  # JSONDecodeError is a ValueError subclass
                await websocket.send_json({"type": "error", "message": 'Send JSON like {"message": "hi"}'})
                continue
            await manager.broadcast(room, {"type": "message", "from": name, "message": str(data.get("message", ""))})
    except WebSocketDisconnect:
        pass  # normal: the client left
    finally:
        await manager.disconnect(room, websocket)  # runs on every exit path


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>WS rooms</title></head>
<body style="font-family:sans-serif;max-width:640px;margin:24px auto">
<h3>FastAPI WebSocket rooms</h3>
<input id="name" placeholder="name"> <input id="room" value="general">
<button onclick="join()">Join</button>
<div id="log" style="border:1px solid #ccc;height:300px;overflow:auto;margin:8px 0;padding:6px"></div>
<input id="msg" placeholder="message" style="width:80%"> <button onclick="send()">Send</button>
<script>
let ws;
function log(t){const d=document.createElement('div');d.textContent=t;const l=document.getElementById('log');l.appendChild(d);l.scrollTop=l.scrollHeight;}
function join(){
  const n=encodeURIComponent(document.getElementById('name').value||'anon');
  const r=encodeURIComponent(document.getElementById('room').value||'general');
  ws=new WebSocket(`ws://${location.host}/ws/${r}?name=${n}&token=letmein`);
  ws.onmessage=e=>{const d=JSON.parse(e.data);log(d.type==='message'?`${d.from}: ${d.message}`:`* ${d.message} [${d.members}]`);};
  ws.onclose=e=>log(`* disconnected (code ${e.code})`);
}
function send(){const m=document.getElementById('msg');ws.send(JSON.stringify({message:m.value}));m.value='';}
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return PAGE
