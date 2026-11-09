# WebSocket Practice

This folder contains experiments and implementations of WebSocket connections for real-time bidirectional communication between client and server.

## What are WebSockets?

WebSockets provide a persistent connection between a client and server, allowing real-time bidirectional data exchange. Unlike HTTP requests, WebSocket connections stay open and can send data in both directions.

## Key Features of WebSockets

- **Bidirectional**: Full-duplex communication
- **Persistent Connection**: Single connection for multiple messages
- **Real-time**: Low latency data exchange
- **Protocol Upgrade**: Upgrades from HTTP to WebSocket protocol
- **Event-driven**: Message-based communication

## Implementation Roadmap

### v1: Pure WebSocket (No FastAPI) — `main.py` + `test.html` ✅
- ✅ 2-person private chat
- ✅ Registration handshake, join/leave notifications
- ✅ Broadcast message type (`{"type": "broadcast", ...}`, not yet in `test.html`)
- ✅ Graceful shutdown (SIGTERM on Linux, Ctrl+C on Windows)

### v2: FastAPI WebSocket Integration — `fastapi_ws.py` ✅
- ✅ Room-based chat groups with a `ConnectionManager`
- ✅ Token check before accepting (real clients see the handshake fail with HTTP 403)
- ✅ Built-in test page at `/`
- 🔄 Private messaging between users

### Socket Handling & Scaling (to do)
- Multiple client connections
- Connection pooling
- Connection scaling and load handling
- Error handling and recovery
- Performance optimization
- Load balancing strategies

## Technology Stack

- **Python**: Core implementation language
- **FastAPI**: Web framework with WebSocket support
- **websockets**: Python WebSocket library
- **JavaScript**: Client-side WebSocket API
- **HTML5**: WebSocket browser API

## Getting Started

```bash
# from pp_sockets/
pip install -r req.txt

# v1: pure websockets server on ws://localhost:8765, then open test.html in two tabs
python main.py

# v2: FastAPI rooms, then open http://127.0.0.1:8002 in two tabs
uvicorn fastapi_ws:app --port 8002 --reload

# tests for both
pytest -v
```

## Example Usage

```javascript
// Client-side JavaScript (v1 server)
const socket = new WebSocket('ws://localhost:8765');

socket.onopen = function(event) {
    console.log('Connected to WebSocket server');
    socket.send(JSON.stringify({ type: 'register', name: 'Ani' }));
};

socket.onmessage = function(event) {
    console.log('Received:', event.data);
};

socket.onclose = function(event) {
    console.log('WebSocket connection closed');
};

socket.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

## WebSocket vs SSE vs HTTP Polling

| Feature | WebSocket | SSE | HTTP Polling |
|---------|-----------|-----|--------------|
| Direction | Bidirectional | Unidirectional | Unidirectional |
| Connection | Persistent | Persistent | Multiple requests |
| Protocol | ws:// or wss:// | HTTP | HTTP |
| Browser Support | Excellent | Good | Universal |
| Use Case | Chat, gaming, collaboration | Notifications, feeds | Simple updates |

## Resources

- [MDN Web Docs - WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [RFC 6455 - WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [FastAPI WebSocket Support](https://fastapi.tiangolo.com/advanced/websockets/)
- [websockets Python Library](https://websockets.readthedocs.io/)
