"""Router composition: versioned routers nested under one /api prefix.

    app
    ├── /health                (health.router, unversioned)
    └── /api                   (api_router)
        ├── /v1/...            (v1.router)
        └── /v2/...            (v2.router)

Other versioning styles (for interviews):
- URL path   /api/v1/items           <- used here; explicit, cache friendly, easy to route
- Header     Accept: application/vnd.myapi.v2+json  or  X-API-Version: 2
- Query      /items?version=2
- Separate sub-apps: app.mount("/v1", v1_app) gives each version its own /docs.
"""

from fastapi import APIRouter

from . import health, v1, v2

api_router = APIRouter(prefix="/api")
api_router.include_router(v1.router)
api_router.include_router(v2.router)

__all__ = ["api_router", "health"]
