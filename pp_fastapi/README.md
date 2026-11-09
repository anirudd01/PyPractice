# FastAPI Practice

A small but realistic FastAPI layout to refresh the building blocks quickly.

## Run

```bash
pip install -r pp_fastapi/req.txt
# from the repo root
uvicorn pp_fastapi.main:app --reload     # http://127.0.0.1:8000/docs
pytest pp_fastapi -v
```

v2 endpoints need the header `X-API-Key: dev-key` (use the **Authorize** button in `/docs`).

## Where to look

| Topic | File |
| --- | --- |
| App factory, lifespan (startup/shutdown), middleware order, include_router | `main.py` |
| Versioned routers (`APIRouter`), nesting under `/api`, versioning styles | `routers/__init__.py`, `routers/v1.py`, `routers/v2.py` |
| CRUD, `Path`/`Query` validation, status codes, `response_model`, PATCH | `routers/v1.py` |
| Router-level auth dependency, breaking change, `BackgroundTasks` | `routers/v2.py` |
| Middleware: function, `BaseHTTPMiddleware`, pure ASGI, built-ins | `middleware.py`, `main.py` |
| `Depends`, `Annotated` aliases, security header, `yield` dependency | `dependencies.py` |
| Pydantic v2 models, `Field`, generic `Page[T]`, `extra="forbid"` | `models.py` |
| Custom exceptions + handlers, custom 422 body | `exceptions.py` |
| `TestClient`, `dependency_overrides` | `tests/test_app.py` |

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | unversioned probe |
| GET | `/random` | legacy, `deprecated=True`, defined straight on `app` |
| GET/POST | `/api/v1/items` | list (offset, limit, q) / create (201 + Location) |
| GET/PATCH/DELETE | `/api/v1/items/{id}` | 404 via custom exception |
| GET | `/api/v1/random` | random number + running sum (thread-safe) |
| GET/POST | `/api/v2/items` | API key required, `Page` envelope, `Money` price, background task |
| GET | `/api/v2/items/{id}` | |
| GET | `/api/v2/random` | background task after response |

## Quick reminders

- **`def` vs `async def` routes**: `def` runs in a thread pool; `async def` runs on the event loop, so never block inside it (`time.sleep`, `requests`). Use `await asyncio.sleep`, `httpx.AsyncClient`, or `await run_in_threadpool(fn)`.
- **Middleware order**: the last `add_middleware` call is the outermost layer, and `@app.middleware("http")` counts as an `add_middleware` call at the point it is declared. Declare a short-circuiting middleware first (innermost) so its responses still get CORS headers, request IDs and logging.
- **PATCH and null**: `str | None = None` also accepts an explicit `null`; reject it for fields that must not be null (see `ItemUpdate`).
- **`BaseHTTPMiddleware` vs pure ASGI**: the first is easier; the second is faster and does not interfere with streaming responses.
- **Lifespan** replaces the deprecated `@app.on_event("startup")`.
- **PATCH**: `model.model_dump(exclude_unset=True)` gives only the fields the client sent.
