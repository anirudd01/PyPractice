"""Realtime test bench: Streamlit UI for the SSE and WebSocket practice servers.

Run (from the repo root):
    streamlit run pp_streamlit/streamlit_app.py

Needs the servers it talks to (see pp_streamlit/README.md):
    python pp_sse/main.py                                          # SSE on :8000
    cd pp_sockets && uvicorn fastapi_ws:app --port 8002            # WebSocket rooms on :8002
"""

import streamlit as st

st.set_page_config(page_title="Realtime test bench", page_icon=":material/bolt:", layout="wide")

page = st.navigation(
    [
        st.Page(
            "app_pages/sse_stream.py",
            title="SSE stream",
            icon=":material/stream:",
            help="Start, stop and resume the server-sent events text stream from pp_sse and watch events arrive.",
        ),
        st.Page(
            "app_pages/ws_chat.py",
            title="WebSocket chat",
            icon=":material/forum:",
            help="Join a room on the FastAPI WebSocket server from pp_sockets and chat. Open two browser tabs to talk to yourself.",
        ),
    ]
)
page.run()
