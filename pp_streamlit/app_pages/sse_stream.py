"""SSE page: consume pp_sse's /stream and show events as they arrive.

Streamlit notes shown here:
- The stream runs inside the script run. Clicking any button while it runs makes
  Streamlit stop the current run, which closes the generator and the HTTP
  connection, so the server sees a disconnect. The stop callback also calls the
  server's /stop-stream endpoint, which is how a browser client would do it.
- Everything that must survive reruns (lines, last event id) lives in session_state.
"""

import json

import streamlit as st

from sse_client import health, stop_stream, stream_events

MAX_SHOWN = 300  # keep the page light: show only the newest lines

ss = st.session_state
ss.setdefault("sse_lines", [])
ss.setdefault("sse_last_id", None)
ss.setdefault("sse_connection_id", None)
ss.setdefault("sse_status", "idle")


def on_stop() -> None:
    if ss.sse_connection_id:
        try:
            stop_stream(ss.sse_url, ss.sse_connection_id)
        except Exception:  # noqa: BLE001 - the stream may already be gone
            pass
    ss.sse_connection_id = None
    ss.sse_status = "stopped by you"


def on_clear() -> None:
    ss.sse_lines, ss.sse_last_id, ss.sse_status = [], None, "idle"


st.title("SSE stream")
st.caption("Streams a text file sentence by sentence from the pp_sse server (`python pp_sse/main.py`).")

with st.container(horizontal=True, vertical_alignment="bottom"):
    st.text_input("Server URL", value="http://127.0.0.1:8000", key="sse_url")
    resume = st.toggle("Resume from last event", key="sse_resume", help="Sends Last-Event-ID so the server skips what you already have.")
    start = st.button("Start", icon=":material/play_arrow:", type="primary", key="sse_start")
    st.button("Stop", icon=":material/stop:", key="sse_stop", on_click=on_stop)
    st.button("Clear", icon=":material/delete:", key="sse_clear", on_click=on_clear)

server = health(ss.sse_url)
if server is None:
    st.warning(f"Nothing is answering at {ss.sse_url}. Start it with `python pp_sse/main.py`.", title="Server offline")
else:
    st.caption(f":green[:material/circle:] Server online, source: {server.get('source')}")

with st.container(horizontal=True):
    status_metric = st.empty()
    count_metric = st.empty()
    last_id_metric = st.empty()


def show_metrics() -> None:
    status_metric.metric("Status", ss.sse_status, border=True)
    count_metric.metric("Sentences received", len(ss.sse_lines), border=True)
    last_id_metric.metric("Last event id", ss.sse_last_id or "-", border=True)


show_metrics()
output = st.container(height=420, border=True, autoscroll=True)
with output:
    for line in ss.sse_lines[-MAX_SHOWN:]:
        st.text(line)

if start and server is not None:
    if not resume:
        ss.sse_lines, ss.sse_last_id = [], None
    try:
        for ev in stream_events(ss.sse_url, ss.sse_last_id if resume else None):
            match ev.event:
                case "connected":
                    ss.sse_connection_id = json.loads(ev.data)["connection_id"]
                    ss.sse_status = "streaming"
                case "message":
                    ss.sse_last_id = ev.id
                    line = f"#{ev.id} {ev.data}"
                    ss.sse_lines.append(line)
                    with output:
                        st.text(line)
                case "progress":
                    pass  # metrics below already show the count
                case "end":
                    info = json.loads(ev.data)
                    ss.sse_status = f"finished: {info['reason']}"
                    ss.sse_connection_id = None
            show_metrics()
    except Exception as e:  # noqa: BLE001 - show network errors in the UI
        ss.sse_status = "error"
        st.error(str(e), title="Stream failed")
    show_metrics()
