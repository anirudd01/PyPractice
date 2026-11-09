"""WebSocket page: chat in a room on pp_sockets/fastapi_ws.py.

Streamlit notes shown here:
- The open connection lives in a RoomClient object in session_state (one per browser tab).
- `@st.fragment(run_every="1s")` re-renders only the chat area every second to show
  messages the background thread received. No `while True` / `time.sleep` + rerun loops.
"""

import streamlit as st

from ws_client import RoomClient

ss = st.session_state
client: RoomClient | None = ss.get("ws_client")


def join() -> None:
    if ss.get("ws_client"):
        ss.ws_client.close()
    new = RoomClient(ss.ws_url, ss.ws_room, ss.ws_name, ss.ws_token)
    new.connect()
    ss.ws_client = new


def leave() -> None:
    if ss.get("ws_client"):
        ss.ws_client.close()
    ss.ws_client = None


st.title("WebSocket chat")
st.caption("Room chat against the FastAPI server (`cd pp_sockets && uvicorn fastapi_ws:app --port 8002`). Open two tabs to chat with yourself.")

with st.form("ws_join", border=True):
    with st.container(horizontal=True, vertical_alignment="bottom"):
        st.text_input("Server URL", value="ws://127.0.0.1:8002", key="ws_url")
        st.text_input("Room", value="general", key="ws_room")
        st.text_input("Your name", value="ani", max_chars=20, key="ws_name")
        st.text_input("Token", value="letmein", type="password", key="ws_token", help="The demo server accepts only 'letmein'.")
        st.form_submit_button("Join", icon=":material/login:", type="primary", key="ws_join_btn", on_click=join)

if client is not None:
    st.button("Leave", icon=":material/logout:", key="ws_leave", on_click=leave)


@st.fragment(run_every="1s" if client is not None and client.connected else None)
def chat_area() -> None:
    if client is None:
        st.info("Join a room to start chatting.")
        return
    if not client.connected:
        st.error(f"Connection {client.status}.", title="Not connected")

    members: list[str] = []
    with st.container(height=420, border=True, autoscroll=True):
        for msg in list(client.messages):
            if msg.get("type") == "message":
                mine = msg["from"] == client.name
                with st.chat_message("user" if mine else "assistant", avatar=":material/person:"):
                    # st.text, not st.markdown/st.caption, for anything a user typed:
                    # Markdown would render links/images someone else injected.
                    st.text(f"{msg['from']}: {msg['message']}")
            else:
                st.text(msg.get("message", ""))
                members = msg.get("members", members)
    st.text(f"#{client.room} · {client.status} · members: {', '.join(members) or '-'}")


chat_area()

if prompt := st.chat_input("Message the room", key="ws_input", disabled=client is None or not client.connected):
    client.send(prompt)  # the echo from the server shows up on the next refresh
