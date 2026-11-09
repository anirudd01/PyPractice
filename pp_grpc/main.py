"""REST -> gRPC gateway: FastAPI endpoints that call the gRPC server.

Run (inside pp_grpc/, with server.py running):
    uvicorn main:app --port 8001 --reload        -> http://127.0.0.1:8001/docs

Notes:
- The generated gRPC stub is blocking, so routes are plain `def` (FastAPI runs them
  in a thread pool). For `async def` routes, use the asyncio API: `grpc.aio.insecure_channel`.
- gRPC status codes are translated to HTTP status codes in one exception handler.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import grpc
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from client import CustomerClient, to_dict

GRPC_TO_HTTP = {
    grpc.StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    grpc.StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
    grpc.StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    grpc.StatusCode.UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    grpc.StatusCode.DEADLINE_EXCEEDED: status.HTTP_504_GATEWAY_TIMEOUT,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.grpc = CustomerClient()  # one channel for the whole app, reused per request
    yield
    app.state.grpc.close()


app = FastAPI(title="Customer REST gateway", lifespan=lifespan)


@app.exception_handler(grpc.RpcError)
async def grpc_error_handler(request: Request, exc: grpc.RpcError) -> JSONResponse:
    http_status = GRPC_TO_HTTP.get(exc.code(), status.HTTP_502_BAD_GATEWAY)
    return JSONResponse({"grpc_code": exc.code().name, "detail": exc.details()}, status_code=http_status)


class CustomerIn(BaseModel):
    name: str
    email: EmailStr


class CustomerPatch(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


def grpc_client(request: Request) -> CustomerClient:
    return request.app.state.grpc


@app.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(body: CustomerIn, request: Request) -> dict:
    return to_dict(grpc_client(request).create_customer(body.name, body.email))


@app.get("/customers")
def list_customers(request: Request, limit: int = 0) -> list[dict]:
    return [to_dict(c) for c in grpc_client(request).list_customers(page_size=limit)]


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str, request: Request) -> dict:
    return to_dict(grpc_client(request).get_customer(customer_id))


@app.patch("/customers/{customer_id}")
def update_customer(customer_id: str, body: CustomerPatch, request: Request) -> dict:
    return to_dict(grpc_client(request).update_customer(customer_id, body.name, body.email))


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, request: Request) -> None:
    grpc_client(request).delete_customer(customer_id)
