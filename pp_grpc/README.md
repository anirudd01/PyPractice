# gRPC Practice

A customer service that shows all four gRPC call styles, a server interceptor,
error codes, deadlines, metadata, and a FastAPI REST gateway in front of it.
Storage is in memory so nothing else needs to be running.

## Run (all commands inside `pp_grpc/`)

```bash
pip install -r req.txt

python server.py                       # terminal 1: gRPC server on :50051
python client.py                       # terminal 2: demo of every RPC style
uvicorn main:app --port 8001           # optional: REST gateway -> http://127.0.0.1:8001/docs
pytest -v                              # starts its own server on a spare port
```

Regenerate the Python code after editing `customer.proto`:

```bash
python -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. customer.proto
```

This produces `customer_pb2.py` (messages), `customer_pb2.pyi` (type hints for the IDE)
and `customer_pb2_grpc.py` (stub + servicer). The generated code checks that the
installed `grpcio` / `protobuf` are at least the versions that generated it.

## Files

| File | What it shows |
| --- | --- |
| `customer.proto` | service with 4 RPC styles, enum, `repeated`, `optional`, `Timestamp`, `Empty` |
| `server.py` | servicer methods, `context.abort` status codes, thread safety, interceptor, graceful stop |
| `client.py` | stub calls, `timeout`, `metadata`, streaming in and out, `RpcError`, `MessageToDict` |
| `main.py` | REST gateway: one channel via lifespan, gRPC status code to HTTP status mapping |
| `test_grpc.py` | end-to-end tests against a real server |

## The four RPC styles

| Style | Proto | Server method | Example |
| --- | --- | --- | --- |
| Unary | `rpc A(Req) returns (Res)` | return one message | `GetCustomer` |
| Server streaming | `returns (stream Res)` | `yield` messages | `ListCustomers` |
| Client streaming | `rpc A(stream Req)` | loop over `request_iterator`, return one | `BulkCreateCustomers` |
| Bidirectional | `stream` on both sides | loop over requests and `yield` | `LookupCustomers` |

## Interview reminders

- gRPC runs on **HTTP/2** (multiplexed streams) and serialises with **Protocol Buffers** (binary, smaller and faster than JSON).
- **Field numbers** are the wire identity: never reuse or change one; mark removed fields `reserved`.
- In proto3, scalar fields have no "was it set?" flag unless declared `optional`.
- Always set a **deadline** (`timeout=`) on client calls.
- Status codes to know: `OK`, `INVALID_ARGUMENT`, `NOT_FOUND`, `ALREADY_EXISTS`, `PERMISSION_DENIED`, `UNAUTHENTICATED`, `UNAVAILABLE`, `DEADLINE_EXCEEDED`, `INTERNAL`.
- Async variant: `grpc.aio.server()` and `grpc.aio.insecure_channel()` with `async def` methods.
- Browsers can't call gRPC directly; use gRPC-Web or a REST gateway like `main.py`.
