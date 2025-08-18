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

### v1: Pure WebSocket (No FastAPI)
- 2-person private chat
- Basic connection handling
- Group chat functionality
- Simple chat room with broadcast messaging
- Message broadcasting to all clients

### v2: FastAPI WebSocket Integration
- Private messaging between users
- Enhanced chat room with FastAPI
- Room-based chat groups

### Socket Handling & Scaling
- Multiple client connections
- Connection pooling
- Connection scaling and load handling
- Error handling and recovery
- Performance optimization
- Load balancing strategies

## Technology Stack

- **Python**: Core implementation language
- **FastAPI/Flask-SocketIO**: Web framework with WebSocket support
- **websockets**: Python WebSocket library
- **JavaScript**: Client-side WebSocket API
- **HTML5**: WebSocket browser API

## Getting Started

```bash
# Install dependencies
pip install -r req.txt

# Run the WebSocket server
python main.py
```

## Example Usage

```javascript
// Client-side JavaScript
const socket = new WebSocket('ws://localhost:8000/ws');

socket.onopen = function(event) {
    console.log('Connected to WebSocket server');
    socket.send('Hello Server!');
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
