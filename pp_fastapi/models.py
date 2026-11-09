"""Pydantic (v2) schemas.

Cheat sheet:
- Separate models per use case: Create (input), Update (partial input), Read (output).
- `Field(...)` adds validation (min_length, gt, le, pattern...) and OpenAPI examples.
- `response_model=` on a route filters/validates what goes OUT (hides extra fields).
- `model_dump(exclude_unset=True)` is the standard trick for PATCH (only fields sent).
- Generic models (`Page[T]`) give a reusable response envelope.
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


# ---------- v1 schemas ----------
class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50, examples=["Keyboard"])
    price: float = Field(gt=0, description="Price in GBP", examples=[49.99])
    tags: list[str] = Field(default_factory=list)

    # Reject unknown fields instead of silently ignoring them.
    model_config = ConfigDict(extra="forbid")


class ItemUpdate(BaseModel):
    """PATCH body: every field optional, but none may be sent as null.

    `str | None = None` makes a field optional, yet it also ACCEPTS an explicit
    `{"name": null}`, which `exclude_unset=True` keeps (null was "set"). Writing
    that None into a required field breaks every later read, so reject it here.
    (If a field is genuinely nullable, e.g. a description, allow null for that one.)
    """

    name: str | None = Field(default=None, min_length=1, max_length=50)
    price: float | None = Field(default=None, gt=0)
    tags: list[str] | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def no_explicit_nulls(self) -> "ItemUpdate":
        nulls = sorted(f for f in self.model_fields_set if getattr(self, f) is None)
        if nulls:
            raise ValueError(f"fields cannot be null: {', '.join(nulls)}")
        return self


class Item(ItemCreate):
    id: int
    created_at: datetime


# ---------- v2 schemas (a breaking change -> new API version) ----------
class Money(BaseModel):
    amount: float
    currency: str = "GBP"


class ItemV2(BaseModel):
    """v2 changed `price: float` into a structured `price: Money` object.

    Existing v1 clients would break on this, which is exactly why it lives
    under /v2 while /v1 keeps returning the old shape.
    """

    id: int
    name: str
    price: Money
    tags: list[str]
    created_at: datetime

    @classmethod
    def from_item(cls, item: dict) -> "ItemV2":
        return cls(
            id=item["id"],
            name=item["name"],
            price=Money(amount=item["price"]),
            tags=item["tags"],
            created_at=item["created_at"],
        )


class Page(BaseModel, Generic[T]):
    """Pagination envelope used by v2 list endpoints."""

    items: list[T]
    total: int
    offset: int
    limit: int


class RandomNumber(BaseModel):
    number: int
    sum: int | None = None
