from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
import time
import os

app = FastAPI(title="SSE Text Streaming Server", debug=True)

# File path
TEXT_FILE = "the_intelligent_investor.txt"
DATA_FOLDER = "pp_sse/data/"
MAX_LINES = 1000

# Connection state management
from collections import defaultdict
import uuid

# Store active connections
active_connections = defaultdict(bool)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/stop-stream/{connection_id}")
async def stop_stream(connection_id: str):
    """Stop a specific streaming session"""
    if connection_id in active_connections:
        active_connections[connection_id] = False
        print(f"Streaming stopped for connection {connection_id}")
        return {"status": "streaming stopped", "connection_id": connection_id}
    return {"status": "connection not found", "connection_id": connection_id}


@app.get("/stream")
async def stream_text(request: Request):
    """SSE endpoint that streams text file content sentence by sentence"""
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = True
    
    print(f"New SSE connection started: {connection_id}")

    file_path = DATA_FOLDER + TEXT_FILE
    if not os.path.exists(file_path):
        return {"error": f"File {file_path} not found"}

    print("New SSE connection started")

    async def generate_sse():
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()[:MAX_LINES]  # Read first 200 lines
                print(f"Lines loaded: {len(lines)}")

            for line_num, line in enumerate(lines, 1):
                # Check if client disconnected or streaming stopped
                if await request.is_disconnected() or not active_connections[connection_id]:
                    print(
                        f"Client disconnected or streaming stopped at line {line_num} for connection {connection_id}"
                    )
                    break

                # Clean the line and split into sentences
                line = line.strip()
                if not line:
                    continue

                # Simple sentence splitting (split by periods)
                sentences = [s.strip() for s in line.split(".") if s.strip()]

                for sentence in sentences:
                    if await request.is_disconnected() or not active_connections[connection_id]:
                        print(
                            f"Client disconnected or streaming stopped while processing sentence for connection {connection_id}"
                        )
                        break

                    # Format as SSE event
                    yield f"data: {sentence}\n\n"

                    # Add delay between sentences (adjust as needed)
                    await asyncio.sleep(0.1)

            # Send completion event
            yield f"data: [END] Streaming completed. Processed {len(lines)} lines.\n\n"
            print("Streaming completed successfully")

        except Exception as e:
            print(f"Error during streaming: {str(e)}")
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
            print(f"SSE connection ended: {connection_id}")

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
