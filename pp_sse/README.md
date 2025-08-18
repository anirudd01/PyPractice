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

### Core Features ✅
- ✅ Python app that streams large text file data (sentence by sentence)
- ✅ Configurable streaming speed (0.1s delay between sentences)
- ✅ Text file input handling with UTF-8 encoding
- ✅ File size limiting (MAX_LINES = 1000)
- ✅ Health check endpoint (`/health`)

### Connection Management ✅
- ✅ Client connection establishment with unique IDs
- ✅ Connection state tracking using `active_connections`
- ✅ Multiple client handling with connection isolation
- ✅ Connection cleanup on completion/disconnect
- ✅ Manual stream stopping endpoint (`/stop-stream/{connection_id}`)

### Client Interface ✅
- ✅ HTML test interface with EventSource API
- ✅ Start/Stop/Clear controls
- ✅ Real-time message display with auto-scroll
- ✅ Connection status indicators
- ✅ Error handling for client disconnections

### Error Handling ✅
- ✅ File not found error handling
- ✅ Client disconnection detection
- ✅ Exception handling during streaming
- ✅ Graceful connection cleanup

## Pending Action Items

### Advanced Features
- 🔄 **Connection Pooling**: Redis/Memcached for connection state management
- 🔄 **Streaming Optimization**: Async generators for large file handling
- 🔄 **Chunk Configuration**: Word/character-level streaming options
- 🔄 **Event Types**: Custom event types (progress, error, status)
- 🔄 **Rate Limiting**: Token bucket algorithm for request throttling

### Enhanced Client Features
- 🔄 **Auto Reconnect**: Exponential backoff retry mechanism
- 🔄 **Error Recovery**: Circuit breaker pattern for fault tolerance
- 🔄 **Progress Tracking**: Real-time streaming statistics (bytes/s, lines/s)
- 🔄 **Stream Control**: Pause/resume with state preservation
- 🔄 **Multi-file Support**: Concurrent streaming from multiple sources

### Monitoring and Analytics
- 🔄 **Metrics Collection**: Prometheus/Grafana for connection monitoring
- 🔄 **Structured Logging**: JSON logging with correlation IDs

### Production Features
- 🔄 **Load Balancing**: Nginx/HAProxy with sticky sessions
- 🔄 **Security**: CORS, CSP headers, rate limiting

## Technology Stack

- **Python**: Core implementation language
- **FastAPI**: Web framework for SSE endpoints
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
const eventSource = new EventSource('/stream');

eventSource.onmessage = function(event) {
    console.log('Received:', event.data);
};

eventSource.onerror = function(error) {
    console.error('SSE Error:', error);
};
```

## Current Implementation Details

- **Server**: FastAPI-based SSE server running on port 8000
- **Text Source**: Streams from `data/the_intelligent_investor.txt`
- **Streaming**: Sentence-by-sentence with 0.1s delays
- **Max Lines**: 1000 lines per session
- **Connection Management**: UUID-based connection tracking
- **Test Interface**: HTML file with EventSource implementation

## Resources

- [MDN Web Docs - Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [W3C SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [FastAPI SSE Implementation](https://fastapi.tiangolo.com/advanced/custom-response/)
