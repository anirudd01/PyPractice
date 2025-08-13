# Streamlit UI Testing

Streamlit-based UI for testing and demonstrating SSE and WebSocket implementations.

## Purpose

- Interactive testing interface for SSE text streaming
- Real-time chat interface for WebSocket connections
- Visual feedback and connection status monitoring
- Easy demonstration of real-time features

## Implementation Roadmap

### SSE Testing Interface
- File upload for text streaming
- Streaming speed controls
- Connection status display
- Real-time text display
- Multiple client simulation

### WebSocket Chat Interface
- Chat room interface
- User name/ID input
- Message history display
- Connection status indicators
- Room/group selection

### Common Features
- Connection management controls
- Error handling display
- Performance metrics
- Debug information panel

## Technology Stack

- **Streamlit**: Web UI framework
- **Python**: Core implementation
- **WebSocket Client**: For WebSocket testing
- **EventSource**: For SSE testing

## Getting Started

```bash
# Install dependencies
pip install -r req.txt

# Run Streamlit app
streamlit run main.py
```

## Usage

1. Start SSE/WebSocket servers in respective folders
2. Launch Streamlit UI
3. Configure connection settings
4. Test real-time features interactively
