"""Dependency injection (`Depends`) examples.

Cheat sheet:
- A dependency is any callable; FastAPI resolves its parameters (query, header, other deps).
- `Annotated[Type, Depends(fn)]` aliases keep route signatures short and reusable.
- Dependencies can be attached at three levels:
    route:   @router.get(..., dependencies=[Depends(fn)])
    router:  APIRouter(dependencies=[Depends(fn)])      <- see routers/v2.py
    app:     FastAPI(dependencies=[Depends(fn)])
- `yield` dependencies run setup before the route and teardown after it (DB sessions).
- Results are cached per request: the same dependency used twice runs once.
- Tests can swap any dependency with `app.dependency_overrides[fn] = fake_fn`.
"""

import logging
import os
import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, Security, status
from fastapi.security import APIKeyHeader

from .store import ItemStore

logger = logging.getLogger("pp_fastapi")

# Demo only. Real keys come from a secret store / env, never from source code.
API_KEY = os.getenv("PP_API_KEY", "dev-key")


# 1) Pull a shared resource created in the lifespan handler off app.state.
def get_store(request: Request) -> ItemStore:
    return request.app.state.store


StoreDep = Annotated[ItemStore, Depends(get_store)]


# 2) Reusable, validated query parameters grouped into one object.
@dataclass
class Pagination:
    offset: int
    limit: int


def pagination(
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 10,
) -> Pagination:
    return Pagination(offset=offset, limit=limit)


PaginationDep = Annotated[Pagination, Depends(pagination)]


# 3) Security dependency: API key in a header. Shows up as "Authorize" in /docs.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    # compare_digest: constant-time comparison, so response timing doesn't leak the key.
    if api_key is None or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header",
        )
    return api_key


# 4) `yield` dependency: code after `yield` runs once the response is produced.
#    Typical use: open a DB session, commit/rollback, close it.
def audit_scope(request: Request) -> Iterator[str]:
    request_id = getattr(request.state, "request_id", "-")
    logger.info("audit start  request_id=%s path=%s", request_id, request.url.path)
    try:
        yield request_id
    finally:
        logger.info("audit end    request_id=%s", request_id)
