"""Pure WebSocket chat server using the `websockets` library (no web framework).

Run (from pp_sockets/):  python main.py   then open test.html in two browser tabs.

Protocol (JSON messages):
    client -> server  {"type": "register", "name": "Ani"}              (must be first)
                      {"type": "private_message", "recipient_id": "...", "message": "hi"}
                      {"type": "broadcast", "message": "hello all"}
                      {"type": "list_clients"}
    server -> client  {"type": "system" | "clients_list" | "private_message" |
                       "private_sent" | "broadcast" | "error", ...}

Cheat sheet:
- `serve(handler, host, port)` calls `handler(websocket)` once per connection.
- `async for message in websocket:` reads until the client disconnects.
- `await websocket.send(text)` sends; `websockets.broadcast(conns, text)` fans out
  without awaiting each client (a slow client can't block the others).
- The handler returning closes the connection, so cleanup goes in `finally`.
"""

import asyncio
import json
import signal
import uuid

from websockets import ConnectionClosed, broadcast
from websockets.asyncio.server import ServerConnection, serve

HOST, PORT = "localhost", 8765


class ChatServer:
    def __init__(self) -> None:
        self.clients: dict[str, ServerConnection] = {}
        self.client_names: dict[str, str] = {}

    # ---------- connection lifecycle ----------
    async def register_client(self, websocket: ServerConnection, name: str) -> str:
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        self.client_names[client_id] = name
        print(f"Client {name} ({client_id}) connected")

        await self.send_to_client(
            client_id, {"type": "system", "message": f"Welcome {name}! Your ID: {client_id}", "client_id": client_id}
        )
        await self.send_clients_list(client_id)
        self.broadcast_json({"type": "system", "message": f"{name} has joined the chat"}, exclude=client_id)
        return client_id

    def unregister_client(self, client_id: str) -> None:
        name = self.client_names.pop(client_id, "Unknown")
        self.clients.pop(client_id, None)
        print(f"Client {name} ({client_id}) disconnected")
        self.broadcast_json({"type": "system", "message": f"{name} has left the chat"})

    # ---------- sending ----------
    async def send_to_client(self, client_id: str, data: dict) -> None:
        websocket = self.clients.get(client_id)
        if websocket is None:
            return
        try:
            await websocket.send(json.dumps(data))
        except ConnectionClosed:
            pass  # the handler's `finally` will unregister this client

    def broadcast_json(self, data: dict, exclude: str | None = None) -> None:
        targets = [ws for cid, ws in self.clients.items() if cid != exclude]
        broadcast(targets, json.dumps(data))

    async def send_clients_list(self, client_id: str) -> None:
        others = [{"id": cid, "name": name} for cid, name in self.client_names.items() if cid != client_id]
        await self.send_to_client(client_id, {"type": "clients_list", "clients": others})

    # ---------- message routing ----------
    async def handle_message(self, client_id: str, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await self.send_to_client(client_id, {"type": "error", "message": "Invalid JSON format"})
            return

        match data.get("type"):  # structural pattern matching (Python 3.10+)
            case "private_message":
                await self.handle_private_message(client_id, data.get("recipient_id"), data.get("message", ""))
            case "broadcast":
                sender = self.client_names[client_id]
                self.broadcast_json(
                    {"type": "broadcast", "sender_id": client_id, "sender_name": sender, "message": data.get("message", "")},
                    exclude=client_id,
                )
            case "list_clients":
                await self.send_clients_list(client_id)
            case "register":
                await self.send_to_client(client_id, {"type": "error", "message": "Already registered"})
            case other:
                await self.send_to_client(client_id, {"type": "error", "message": f"Unknown message type: {other}"})

    async def handle_private_message(self, sender_id: str, recipient_id: str | None, message: str) -> None:
        if recipient_id not in self.clients:
            await self.send_to_client(sender_id, {"type": "error", "message": "Recipient not found"})
            return
        await self.send_to_client(
            recipient_id,
            {
                "type": "private_message",
                "message": message,
                "sender_id": sender_id,
                "sender_name": self.client_names[sender_id],
            },
        )
        await self.send_to_client(
            sender_id,
            {
                "type": "private_sent",
                "message": f"Message sent to {self.client_names[recipient_id]}",
                "recipient_id": recipient_id,
            },
        )


chat_server = ChatServer()


async def websocket_handler(websocket: ServerConnection) -> None:
    """Called once per connection. Step 1: wait for registration. Step 2: route messages."""
    client_id = None
    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {}
            if data.get("type") == "register":
                client_id = await chat_server.register_client(websocket, data.get("name") or "Anonymous")
                break
            await websocket.send(
                json.dumps({"type": "error", "message": 'Register first: {"type": "register", "name": "YourName"}'})
            )

        if client_id:
            async for raw in websocket:  # continues on the same connection
                await chat_server.handle_message(client_id, raw)
    except ConnectionClosed:
        pass  # normal for clients that drop without a close frame
    finally:
        if client_id:
            chat_server.unregister_client(client_id)


async def main() -> None:
    stop = asyncio.get_running_loop().create_future()

    # Graceful shutdown on SIGTERM (Docker/Kubernetes). add_signal_handler is
    # Unix-only; on Windows Ctrl+C raises KeyboardInterrupt instead (handled below).
    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
        loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    except NotImplementedError:
        pass

    # Leaving the `async with` block closes all connections (close code 1001 "going away").
    async with serve(websocket_handler, HOST, PORT) as server:
        print(f"WebSocket chat server on ws://{HOST}:{PORT}  (Ctrl+C to stop)")
        await stop
        chat_server.broadcast_json({"type": "system", "message": "Server is shutting down"})
        server.close()
    print("Server shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
