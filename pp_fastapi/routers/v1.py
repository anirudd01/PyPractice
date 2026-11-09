"""API v1: a separate APIRouter instead of decorating `app` directly.

Cheat sheet:
- `APIRouter(prefix=..., tags=[...])` groups routes; tags group them in /docs.
- The router knows nothing about the app; main.py mounts it with `include_router`.
- Path/Query/Body params are validated from type hints + `Path(...)` / `Query(...)`.
- Set the success status per route: `status_code=201` for create, `204` for delete.
- `def` routes run in a thread pool (OK to block); `async def` routes run on the
  event loop (never call blocking code like time.sleep or requests in them).
"""

import threading
from random import randint
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from ..dependencies import PaginationDep, StoreDep, audit_scope
from ..exceptions import ItemNotFoundError
from ..models import Item, ItemCreate, ItemUpdate, RandomNumber

router = APIRouter(prefix="/v1", tags=["v1"])

ItemId = Annotated[int, Path(ge=1, description="Item ID")]


# ---------- Items CRUD ----------
@router.get("/items", response_model=list[Item], summary="List items")
def list_items(
    store: StoreDep,
    page: PaginationDep,
    q: Annotated[str | None, Query(min_length=2, description="Name contains")] = None,
):
    items, _total = store.list(page.offset, page.limit, q)
    return items


@router.get("/items/{item_id}", response_model=Item)
def get_item(item_id: ItemId, store: StoreDep):
    item = store.get(item_id)
    if item is None:
        raise ItemNotFoundError(item_id)  # mapped to a 404 in exceptions.py
    return item


@router.post(
    "/items",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(audit_scope)],  # route-level dependency (return value unused)
)
def create_item(payload: ItemCreate, store: StoreDep, response: Response):
    item = store.create(payload.model_dump())
    response.headers["Location"] = f"/api/v1/items/{item['id']}"
    return item


@router.patch("/items/{item_id}", response_model=Item)
def update_item(item_id: ItemId, payload: ItemUpdate, store: StoreDep):
    # exclude_unset -> only the fields the client actually sent.
    item = store.update(item_id, payload.model_dump(exclude_unset=True))
    if item is None:
        raise ItemNotFoundError(item_id)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: ItemId, store: StoreDep) -> None:
    if not store.delete(item_id):
        raise ItemNotFoundError(item_id)


# ---------- Random number with running sum (original example) ----------
_running_sum = 0
_sum_lock = threading.Lock()  # `def` route -> thread pool -> protect shared state


@router.get("/random", response_model=RandomNumber, summary="Random number along with running sum")
def get_random() -> RandomNumber:
    global _running_sum
    number = randint(1, 100)
    with _sum_lock:
        _running_sum += number
        total = _running_sum
    return RandomNumber(number=number, sum=total)
