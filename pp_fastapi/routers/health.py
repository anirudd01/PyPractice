"""Unversioned operational endpoints (probes should not change with API versions)."""

import time

from fastapi import APIRouter, Request

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health(request: Request) -> dict:
    return {
        "status": "ok",
        "uptime_s": round(time.time() - request.app.state.started_at, 1),
        "request_id": getattr(request.state, "request_id", None),
    }
