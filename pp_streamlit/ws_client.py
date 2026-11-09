"""WebSocket client for the FastAPI rooms server, run on a background thread.

Why a thread: Streamlit reruns the whole script on every interaction, but a
WebSocket must stay open between reruns. So the connection lives in this object
(kept in st.session_state), a daemon thread keeps reading into a list, and the
page just renders whatever has arrived. The thread must never call st.* itself.
"""

import json
import threading
from urllib.parse import quote, urlencode

from websockets import ConnectionClosed, InvalidStatus
from websockets.sync.client import ClientConnection, connect


class RoomClient:
    def __init__(self, base_url: str, room: str, name: str, token: str) -> None:
        query = urlencode({"name": name, "token": token})
        self.url = f"{base_url}/ws/{quote(room)}?{query}"
        self.room, self.name = room, name
        self.messages: list[dict] = []  # list.append is atomic under the GIL
        self.status = "disconnected"
        self._ws: ClientConnection | None = None

    def connect(self) -> None:
        """Start the connection thread and wait until it is open (or has failed)."""
        ready = threading.Event()
        threading.Thread(target=self._run, args=(ready,), name=f"ws-{self.name}", daemon=True).start()
        ready.wait(timeout=5)

    def _run(self, ready: threading.Event) -> None:
        # The whole connection lives inside `with`, so it is always closed cleanly.
        try:
            with connect(self.url, open_timeout=3) as ws:
                self._ws = ws
                self.status = "connected"
                ready.set()
                for raw in ws:  # ends when either side closes
                    self.messages.append(json.loads(raw))
        except InvalidStatus as e:  # server closed before accepting (e.g. bad token -> 403)
            self.status = f"rejected (HTTP {e.response.status_code})"
        except ConnectionClosed:
            pass
        except OSError as e:
            self.status = f"error: {e}"
        finally:
            if self.status == "connected":
                code = self._ws.close_code if self._ws else None
                self.status = f"closed (code {code})"
            ready.set()

    @property
    def connected(self) -> bool:
        return self.status == "connected"

    def send(self, text: str) -> None:
        if self._ws is not None and self.connected:
            self._ws.send(json.dumps({"message": text}))

    def close(self) -> None:
        if self._ws is not None:
            self.status = "disconnected"
            self._ws.close()
