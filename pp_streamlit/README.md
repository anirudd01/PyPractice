# Streamlit test bench

A two-page Streamlit app for poking the realtime servers in this repo:

- **SSE stream**: start, stop and resume the text stream from `pp_sse`, with live status, sentence count and last event id.
- **WebSocket chat**: join a room on `pp_sockets/fastapi_ws.py` and chat; open two browser tabs to talk to yourself.

## Run

```bash
pip install -r pp_streamlit/req.txt

# terminal 1: SSE server on :8000
python pp_sse/main.py
# terminal 2: WebSocket rooms server on :8002
cd pp_sockets && uvicorn fastapi_ws:app --port 8002
# terminal 3: the UI on http://localhost:8501
streamlit run pp_streamlit/streamlit_app.py

# tests (start their own servers on spare ports)
cd pp_streamlit && pytest -v
```

## Files

| File | What it shows |
| --- | --- |
| `streamlit_app.py` | entry point: `st.navigation` + `st.Page` with icons and help text |
| `app_pages/sse_stream.py` | streaming inside a script run, `st.empty` placeholders for live metrics, `session_state` that survives reruns, button callbacks |
| `app_pages/ws_chat.py` | `st.form` to batch inputs, `@st.fragment(run_every="1s")` for live updates, `st.chat_message` / `st.chat_input` |
| `sse_client.py` | spec-style SSE parser and an `httpx` streaming client (no Streamlit code) |
| `ws_client.py` | WebSocket client on a background thread, so the connection outlives Streamlit reruns |
| `test_streamlit_app.py` | plain pytest for the parser, both clients against the real servers, `AppTest` for the pages |

## Streamlit reminders

- The **whole script reruns** on every interaction. Keep anything that must persist in `st.session_state`.
- Clicking a widget **while a run is in progress stops that run** and starts a new one. Here that closes the SSE stream, so the server sees a disconnect.
- Long-lived connections (WebSockets, streams you want to keep across reruns) belong in an object in `session_state`, read by a background thread. **Never call `st.*` from that thread.** Known demo limitation: closing the browser tab doesn't close that connection; it lives until the Streamlit server stops.
- For live updates use `@st.fragment(run_every=...)`, not `while True` + `time.sleep` + `st.rerun()`.
- `st.cache_data` caches serialisable results; `st.cache_resource` caches shared objects (DB clients, models) across all sessions.
- Test pages headlessly with `streamlit.testing.v1.AppTest`.
