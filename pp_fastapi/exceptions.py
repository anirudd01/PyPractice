"""Custom exceptions and exception handlers.

Cheat sheet:
- `raise HTTPException(404, "...")` is the quick way inside routes.
- For domain errors, raise your own exception and map it to a response in ONE place
  with `app.add_exception_handler(MyError, handler)` (or `@app.exception_handler`).
- Override `RequestValidationError` to change the default 422 body shape.
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ItemNotFoundError(Exception):
    def __init__(self, item_id: int) -> None:
        self.item_id = item_id
        super().__init__(f"Item {item_id} not found")


async def item_not_found_handler(request: Request, exc: ItemNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "item_not_found", "detail": str(exc), "item_id": exc.item_id},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # jsonable_encoder: error contexts can hold non-JSON objects (e.g. ValueError).
    return JSONResponse(
        status_code=422,  # constant name changed across Starlette versions, so use the number
        content={"error": "validation_error", "detail": jsonable_encoder(exc.errors())},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ItemNotFoundError, item_not_found_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
