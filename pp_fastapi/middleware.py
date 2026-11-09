"""Middleware examples.

Middleware wraps EVERY request: code before `call_next` runs on the way in,
code after it runs on the way out. Three ways to write one:

1. Function middleware   -> `@app.middleware("http")`         (see main.py)
2. BaseHTTPMiddleware    -> subclass with `dispatch()`         (RequestContextMiddleware)
3. Pure ASGI middleware  -> class with `__call__(scope, receive, send)` (AccessLogMiddleware)
   Lower level but faster, and it doesn't buffer streaming responses/background tasks.

Built-ins you'll use most (added in main.py): CORSMiddleware, GZipMiddleware,
TrustedHostMiddleware, HTTPSRedirectMiddleware.

ORDER: `app.add_middleware()` puts each new middleware OUTSIDE the previous ones,
so the LAST one added runs FIRST on the request and LAST on the response.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("pp_fastapi")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds a request ID (reused from the caller if sent) and the processing time."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        # request.state is per-request storage that routes/dependencies can read.
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response


class AccessLogMiddleware:
    """Pure ASGI middleware that logs method, path, status and duration."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # let websocket/lifespan events pass straight through
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("%s %s -> %s (%.1f ms)", scope["method"], scope["path"], status_code, elapsed_ms)
