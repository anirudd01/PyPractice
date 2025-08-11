# Server-Sent Events (SSE) Practice

This folder contains experiments and implementations of Server-Sent Events (SSE) for real-time data streaming from server to client.

## What is SSE?

Server-Sent Events (SSE) is a web standard that allows a web page to get updates from a server. It's a one-way communication channel where the server can push data to the client in real-time.

## Key Features of SSE

- **Unidirectional**: Server to client only
- **Automatic Reconnection**: Built-in reconnection mechanism
- **Event-based**: Supports different event types
- **Text-based**: Data is sent as text/event-stream
- **HTTP-based**: Uses standard HTTP protocol

## Implementation Roadmap

### Core Features
- Python app that streams large text file data (word/sentence at a time)
- Configurable streaming speed and chunk size
- Text file input handling

### Connection Management
- Client connection establishment
- Connection re-establishment on disconnect
- Multiple client handling
- Connection state tracking

### Advanced Features
- Client authentication
- Error handling and recovery
- Performance optimization
- Connection pooling

## Technology Stack

- **Python**: Core implementation language
- **FastAPI/Flask**: Web framework for SSE endpoints
- **JavaScript**: Client-side event handling
- **HTML5**: EventSource API for client connections

## Getting Started

```bash
# Install dependencies
pip install -r req.txt

# Run the SSE server
python main.py
```

## Example Usage

```javascript
// Client-side JavaScript
const eventSource = new EventSource('/events');

eventSource.onmessage = function(event) {
    console.log('Received:', event.data);
};

eventSource.onerror = function(error) {
    console.error('SSE Error:', error);
};
```

## Resources

- [MDN Web Docs - Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [W3C SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [FastAPI SSE Implementation](https://fastapi.tiangolo.com/advanced/custom-response/)
