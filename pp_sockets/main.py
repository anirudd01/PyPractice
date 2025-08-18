import asyncio
import json
import signal
import uuid
from typing import Dict, Set

from websockets import ServerProtocol, serve


class ChatServer:
    def __init__(self):
        self.clients: Dict[str, ServerProtocol] = {}
        self.client_names: Dict[str, str] = {}
        self.private_chats: Dict[str, Set[str]] = {}

    async def register_client(self, websocket: ServerProtocol, name: str):
        """Register a new client with a unique ID"""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        self.client_names[client_id] = name
        print(f"Client {name} ({client_id}) connected")

        # Send welcome message
        await websocket.send(
            json.dumps(
                {
                    "type": "system",
                    "message": f"Welcome {name}! Your ID: {client_id}",
                    "client_id": client_id,
                }
            )
        )

        # Send list of available clients
        available_clients = [
            {"id": cid, "name": cname}
            for cid, cname in self.client_names.items()
            if cid != client_id
        ]
        await websocket.send(
            json.dumps({"type": "clients_list", "clients": available_clients})
        )

        return client_id

    async def unregister_client(self, client_id: str):
        """Unregister a client when they disconnect"""
        if client_id in self.clients:
            name = self.client_names.get(client_id, "Unknown")
            del self.clients[client_id]
            del self.client_names[client_id]
            print(f"Client {name} ({client_id}) disconnected")

            # Notify other clients
            await self.broadcast_system_message(f"{name} has left the chat")

    async def handle_private_message(
        self, sender_id: str, recipient_id: str, message: str
    ):
        """Handle private message between two clients"""
        if recipient_id not in self.clients:
            await self.send_to_client(
                sender_id, {"type": "error", "message": "Recipient not found"}
            )
            return

        sender_name = self.client_names.get(sender_id, "Unknown")
        recipient_name = self.client_names.get(recipient_id, "Unknown")

        # Send to recipient
        await self.send_to_client(
            recipient_id,
            {
                "type": "private_message",
                "message": message,
                "sender_id": sender_id,
                "sender_name": sender_name,
            },
        )

        # Send confirmation to sender
        await self.send_to_client(
            sender_id,
            {
                "type": "private_sent",
                "message": f"Message sent to {recipient_name}",
                "recipient_id": recipient_id,
            },
        )

    async def send_to_client(self, client_id: str, data: dict):
        """Send data to a specific client"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(json.dumps(data))
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")

    async def broadcast_system_message(self, message: str):
        """Broadcast system message to all clients"""
        data = {"type": "system", "message": message}
        for client_id in list(self.clients.keys()):
            await self.send_to_client(client_id, data)

    async def handle_message(self, websocket: ServerProtocol, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            client_id = None

            # Find client ID for this websocket
            for cid, ws in self.clients.items():
                if ws == websocket:
                    client_id = cid
                    break

            if not client_id:
                return

            msg_type = data.get("type", "message")

            if msg_type == "register":
                # Client registration
                name = data.get("name", f"User_{client_id[:8]}")
                await self.register_client(websocket, name)

            elif msg_type == "private_message":
                # Private message
                recipient_id = data.get("recipient_id")
                message_text = data.get("message", "")
                if recipient_id:
                    await self.handle_private_message(
                        client_id, recipient_id, message_text
                    )

            elif msg_type == "list_clients":
                # Send list of available clients
                available_clients = [
                    {"id": cid, "name": cname}
                    for cid, cname in self.client_names.items()
                    if cid != client_id
                ]
                await self.send_to_client(
                    client_id, {"type": "clients_list", "clients": available_clients}
                )

        except json.JSONDecodeError:
            await websocket.send(
                json.dumps({"type": "error", "message": "Invalid JSON format"})
            )
        except Exception as e:
            print(f"Error handling message: {e}")
            await websocket.send(
                json.dumps({"type": "error", "message": "Internal server error"})
            )

    async def cleanup(self):
        """Clean up all connections gracefully"""
        print("\nShutting down server...")
        if self.clients:
            print(f"Disconnecting {len(self.clients)} clients...")
            # Send shutdown message to all clients
            for client_id in list(self.clients.keys()):
                try:
                    await self.send_to_client(
                        client_id,
                        {"type": "system", "message": "Server is shutting down"},
                    )
                except Exception as e:
                    print(f"Error sending shutdown message to client {client_id}: {e}")
            # Clear all clients
            self.clients.clear()
            self.client_names.clear()
        print("Server shutdown complete.")


# Global chat server instance
chat_server = ChatServer()


async def websocket_handler(websocket: ServerProtocol):
    """Main WebSocket connection handler"""
    client_id = None

    try:
        # Wait for client registration
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "register":
                    name = data.get("name", "Anonymous")
                    client_id = await chat_server.register_client(websocket, name)
                    break
            except json.JSONDecodeError:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "error",
                            "message": 'Please register first with: {"type": "register", "name": "YourName"}',
                        }
                    )
                )

        # Handle messages after registration
        if client_id:
            async for message in websocket:
                await chat_server.handle_message(websocket, message)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if client_id:
            await chat_server.unregister_client(client_id)


async def shutdown(signal, loop):
    """Handle shutdown gracefully"""
    print(f"\nReceived exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    # Cancel all tasks
    for task in tasks:
        task.cancel()

    # Wait for all tasks to be cancelled
    await asyncio.gather(*tasks, return_exceptions=True)

    # Cleanup chat server
    await chat_server.cleanup()

    # Stop the loop
    loop.stop()


async def main():
    """Start the WebSocket server"""
    print("Starting WebSocket Chat Server on ws://localhost:8765")
    print("Waiting for connections... (Press Ctrl+C to stop)")

    # Get the event loop
    loop = asyncio.get_running_loop()

    # Set up signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )

    try:
        async with serve(websocket_handler, "localhost", 8765):
            # Keep the server running
            await asyncio.Future()  # run forever
    except asyncio.CancelledError:
        print("Server cancelled")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        await chat_server.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
