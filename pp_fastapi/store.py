"""A tiny in-memory "database" so the demo runs with no external services.

In a real app this would be a SQLAlchemy session / Mongo client created in the
lifespan handler and handed to routes through a dependency (see dependencies.py).
"""

import threading
from datetime import datetime, timezone


class ItemStore:
    def __init__(self) -> None:
        self._items: dict[int, dict] = {}
        self._next_id = 1
        # Sync (`def`) routes run in a thread pool, so shared state needs a lock.
        self._lock = threading.Lock()

    def list(self, offset: int = 0, limit: int = 10, q: str | None = None) -> tuple[list[dict], int]:
        items = list(self._items.values())
        if q:
            items = [i for i in items if q.lower() in i["name"].lower()]
        return items[offset : offset + limit], len(items)

    def get(self, item_id: int) -> dict | None:
        return self._items.get(item_id)

    def create(self, data: dict) -> dict:
        with self._lock:
            item = {"id": self._next_id, "created_at": datetime.now(timezone.utc), **data}
            self._items[item["id"]] = item
            self._next_id += 1
        return item

    def update(self, item_id: int, changes: dict) -> dict | None:
        with self._lock:
            item = self._items.get(item_id)
            if item is None:
                return None
            item.update(changes)
            return item

    def delete(self, item_id: int) -> bool:
        with self._lock:
            return self._items.pop(item_id, None) is not None
