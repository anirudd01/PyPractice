"""FastAPI practice app: wires routers, middleware, exception handlers, lifespan.

Run from the repo root:
    uvicorn pp_fastapi.main:app --reload
    # or: python -m pp_fastapi.main   (not `python pp_fastapi/main.py`: it's a package)
Docs:   http://127.0.0.1:8000/docs  (Swagger)   /redoc  (ReDoc)
Tests:  pytest pp_fastapi -v
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from random import randint

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .exceptions import register_exception_handlers
from .middleware import AccessLogMiddleware, RequestContextMiddleware
from .routers import api_router, health
from .store import ItemStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pp_fastapi")


# ---------- Lifespan: startup / shutdown (replaces @app.on_event) ----------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: create shared resources (DB pools, HTTP clients, ML models...).
    app.state.store = ItemStore()
    app.state.store.create({"name": "Keyboard", "price": 49.99, "tags": ["hardware"]})
    app.state.store.create({"name": "Mouse", "price": 19.5, "tags": ["hardware"]})
    app.state.started_at = time.time()
    app.state.maintenance = False
    logger.info("startup complete")
    yield
    # Shutdown: close what you opened above.
    logger.info("shutdown complete")


def create_app() -> FastAPI:
    """App factory: lets tests build a fresh app instance each time."""
    app = FastAPI(
        title="PyPractice FastAPI",
        version="2.0.0",
        description="Routers, versioning, middleware, dependencies, error handling.",
        lifespan=lifespan,
    )

    # ---------- Middleware (last added = outermost = runs first) ----------
    # `@app.middleware("http")` is just add_middleware(BaseHTTPMiddleware, ...) under the
    # hood, so it obeys the same ordering rule. Declared FIRST here = innermost layer:
    # its 503 still gets the request ID, CORS headers, host check and access log.
    @app.middleware("http")
    async def maintenance_mode(request: Request, call_next):
        # Function-style middleware: can short-circuit without calling call_next.
        if request.app.state.maintenance and request.url.path != "/health":
            return JSONResponse({"detail": "Down for maintenance"}, status_code=503)
        return await call_next(request)

    app.add_middleware(RequestContextMiddleware)  # class-based (BaseHTTPMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # compress big responses
    app.add_middleware(
        CORSMiddleware,  # lets browser JS from these origins call the API
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    app.add_middleware(AccessLogMiddleware)  # pure ASGI, added last = outermost, logs everything
    # Resulting order for a request: AccessLog -> TrustedHost -> CORS -> GZip
    #                                 -> RequestContext -> maintenance_mode -> route

    # ---------- Exception handlers ----------
    register_exception_handlers(app)

    # ---------- Routers ----------
    app.include_router(health.router)
    app.include_router(api_router)

    # Routes can still go straight on the app; fine for one-offs, not for real APIs.
    @app.get("/random", deprecated=True, tags=["legacy"], summary="Use /api/v1/random instead")
    def legacy_random() -> dict:
        return {"data": randint(1, 100)}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Run as a module so the relative imports work:  python -m pp_fastapi.main
    uvicorn.run("pp_fastapi.main:app", host="127.0.0.1", port=8000, reload=True)
