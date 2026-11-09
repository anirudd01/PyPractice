"""Tests for both servers. Run (from pp_sockets/):  pytest -v"""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

import main
from fastapi_ws import app


# ---------- FastAPI version ----------
def test_fastapi_room_broadcast():
    client = TestClient(app)
    with client.websocket_connect("/ws/py?name=ann&token=letmein") as ann:
        assert ann.receive_json()["members"] == ["ann"]
        with client.websocket_connect("/ws/py?name=bob&token=letmein") as bob:
            assert bob.receive_json()["members"] == ["ann", "bob"]
            assert ann.receive_json()["message"] == "bob joined #py"

            bob.send_json({"message": "hi"})
            expected = {"type": "message", "from": "bob", "message": "hi"}
            assert ann.receive_json() == expected
            assert bob.receive_json() == expected
        assert ann.receive_json()["message"] == "bob left #py"


def test_fastapi_bad_json_gets_error_and_no_ghost_member():
    import fastapi_ws

    client = TestClient(app)
    with client.websocket_connect("/ws/bad?name=ann&token=letmein") as ann:
        ann.receive_json()  # join notice
        ann.send_text("not json")
        assert ann.receive_json()["type"] == "error"
        ann.send_text("[1, 2]")
        assert ann.receive_json()["type"] == "error"
        ann.send_json({"message": "still here"})
        assert ann.receive_json()["message"] == "still here"
    assert "bad" not in fastapi_ws.manager.rooms  # cleaned up on exit


def test_fastapi_rejects_bad_token():
    with pytest.raises(WebSocketDisconnect) as exc:
        with TestClient(app).websocket_connect("/ws/py?name=eve&token=wrong") as ws:
            ws.receive_json()
    assert exc.value.code == 1008


# ---------- pure websockets version ----------
async def _recv(ws) -> dict:
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=2))


async def _private_chat_flow() -> None:
    main.chat_server = main.ChatServer()
    async with serve(main.websocket_handler, "localhost", 0) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://localhost:{port}"
        async with connect(url) as ann, connect(url) as bob:
            await ann.send(json.dumps({"type": "hello"}))
            assert (await _recv(ann))["type"] == "error"  # must register first

            await ann.send(json.dumps({"type": "register", "name": "Ann"}))
            ann_id = (await _recv(ann))["client_id"]
            assert (await _recv(ann))["clients"] == []

            await bob.send(json.dumps({"type": "register", "name": "Bob"}))
            bob_id = (await _recv(bob))["client_id"]
            assert (await _recv(bob))["clients"] == [{"id": ann_id, "name": "Ann"}]
            assert (await _recv(ann))["message"] == "Bob has joined the chat"

            await bob.send(json.dumps({"type": "register", "name": "Bob2"}))
            assert (await _recv(bob))["message"] == "Already registered"

            await bob.send(json.dumps({"type": "private_message", "recipient_id": ann_id, "message": "hey"}))
            msg = await _recv(ann)
            assert (msg["type"], msg["sender_id"], msg["message"]) == ("private_message", bob_id, "hey")
            assert (await _recv(bob))["type"] == "private_sent"

    # Exiting `serve` waits for every handler's `finally`, so both clients are gone.
    assert main.chat_server.clients == {}


def test_websockets_private_chat():
    asyncio.run(_private_chat_flow())
