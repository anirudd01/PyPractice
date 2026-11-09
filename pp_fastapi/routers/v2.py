"""API v2: same resource, breaking response changes, router-wide auth.

Shows:
- Router-level dependency: every v2 route requires the X-API-Key header.
- A breaking change (price -> Money object, list -> Page envelope) kept behind /v2.
- BackgroundTasks: work that runs AFTER the response has been sent.
"""

import logging
import time
from random import randint

from fastapi import APIRouter, BackgroundTasks, Depends, status

from ..dependencies import PaginationDep, StoreDep, require_api_key
from ..exceptions import ItemNotFoundError
from ..models import ItemCreate, ItemV2, Page, RandomNumber

logger = logging.getLogger("pp_fastapi")

router = APIRouter(
    prefix="/v2",
    tags=["v2"],
    dependencies=[Depends(require_api_key)],
    responses={401: {"description": "Missing or invalid API key"}},  # documented in OpenAPI
)


def notify_item_created(item_id: int, name: str) -> None:
    """Sync background task: FastAPI runs it in a thread pool after the response."""
    time.sleep(1)  # pretend to send an email / publish an event
    logger.info("background: notified about item %s (%s)", item_id, name)


@router.get("/items", response_model=Page[ItemV2])
async def list_items(store: StoreDep, page: PaginationDep):
    items, total = store.list(page.offset, page.limit)
    return Page[ItemV2](
        items=[ItemV2.from_item(i) for i in items],
        total=total,
        offset=page.offset,
        limit=page.limit,
    )


@router.get("/items/{item_id}", response_model=ItemV2)
async def get_item(item_id: int, store: StoreDep):
    item = store.get(item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    return ItemV2.from_item(item)


@router.post("/items", response_model=ItemV2, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, store: StoreDep, background_tasks: BackgroundTasks):
    item = store.create(payload.model_dump())
    background_tasks.add_task(notify_item_created, item["id"], item["name"])
    return ItemV2.from_item(item)


# ---------- Random number with a background task (original example) ----------
def log_sleep_log(n: int) -> None:
    logger.info("background: log %s before 3 sec sleep", n)
    time.sleep(3)
    logger.info("background: log %s after 3 sec sleep", n)


@router.get("/random", response_model=RandomNumber, summary="Random number with a background task")
async def get_random(background_tasks: BackgroundTasks) -> RandomNumber:
    number = randint(1, 100)
    # Just add tasks to the injected BackgroundTasks and return normally;
    # FastAPI attaches them to the response for you.
    background_tasks.add_task(log_sleep_log, n=number)
    return RandomNumber(number=number)
