"""gRPC client wrapper plus a demo of every RPC style.

Run (inside pp_grpc/, with server.py running):  python client.py

Cheat sheet:
- `grpc.insecure_channel(addr)` -> channel; `<Service>Stub(channel)` -> callable RPCs.
- Always pass `timeout=` (a deadline); without it a call can hang forever.
- `metadata=[("key", "value")]` sends headers (keys must be lowercase).
- Failures raise `grpc.RpcError`; inspect `e.code()` and `e.details()`.
- Streaming responses are iterators; streaming requests take an iterator/generator.
"""

from collections.abc import Iterator

import grpc
from google.protobuf.json_format import MessageToDict

import customer_pb2
import customer_pb2_grpc

TIMEOUT_S = 5


class CustomerClient:
    def __init__(self, host: str = "localhost", port: int = 50051) -> None:
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = customer_pb2_grpc.CustomerServiceStub(self.channel)

    def close(self) -> None:
        self.channel.close()

    def __enter__(self) -> "CustomerClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---------- unary ----------
    def create_customer(self, name: str, email: str, tier: int = customer_pb2.TIER_FREE, tags=()) -> customer_pb2.Customer:
        request = customer_pb2.CreateCustomerRequest(name=name, email=email, tier=tier, tags=list(tags))
        return self.stub.CreateCustomer(request, timeout=TIMEOUT_S, metadata=[("x-request-id", "demo-1")])

    def get_customer(self, customer_id: str) -> customer_pb2.Customer:
        return self.stub.GetCustomer(customer_pb2.GetCustomerRequest(id=customer_id), timeout=TIMEOUT_S)

    def update_customer(self, customer_id: str, name: str | None = None, email: str | None = None) -> customer_pb2.Customer:
        # Only set fields that were given, so the server's HasField() sees exactly those.
        request = customer_pb2.UpdateCustomerRequest(id=customer_id)
        if name is not None:
            request.name = name
        if email is not None:
            request.email = email
        return self.stub.UpdateCustomer(request, timeout=TIMEOUT_S)

    def delete_customer(self, customer_id: str) -> None:
        self.stub.DeleteCustomer(customer_pb2.GetCustomerRequest(id=customer_id), timeout=TIMEOUT_S)

    # ---------- server streaming ----------
    def list_customers(self, page_size: int = 0, tier: int = 0) -> Iterator[customer_pb2.Customer]:
        request = customer_pb2.ListCustomersRequest(page_size=page_size, tier=tier)
        yield from self.stub.ListCustomers(request, timeout=TIMEOUT_S)

    # ---------- client streaming ----------
    def bulk_create(self, people: list[tuple[str, str]]) -> customer_pb2.BulkCreateResponse:
        requests = (customer_pb2.CreateCustomerRequest(name=n, email=e) for n, e in people)
        return self.stub.BulkCreateCustomers(requests, timeout=TIMEOUT_S)

    # ---------- bidirectional streaming ----------
    def lookup(self, ids: list[str]) -> Iterator[customer_pb2.Customer]:
        requests = (customer_pb2.GetCustomerRequest(id=i) for i in ids)
        yield from self.stub.LookupCustomers(requests, timeout=TIMEOUT_S)


def to_dict(message) -> dict:
    """Protobuf message -> plain dict (handy for JSON APIs and printing)."""
    return MessageToDict(message, preserving_proto_field_name=True)


def demo() -> None:
    with CustomerClient() as client:
        alice = client.create_customer("Alice", "alice@example.com", customer_pb2.TIER_PREMIUM, ["vip"])
        print("unary create     :", to_dict(alice))
        print("unary update     :", to_dict(client.update_customer(alice.id, name="Alice B")))

        bulk = client.bulk_create([("Bob", "bob@example.com"), ("Cara", "cara@example.com")])
        print("client streaming :", bulk.created_count, "created", list(bulk.ids))

        print("server streaming :", [c.name for c in client.list_customers()])
        print("  premium only   :", [c.name for c in client.list_customers(tier=customer_pb2.TIER_PREMIUM)])
        print("bidi streaming   :", [c.name for c in client.lookup([alice.id, "missing", bulk.ids[0]])])

        client.delete_customer(alice.id)
        try:
            client.get_customer(alice.id)
        except grpc.RpcError as e:
            print("error handling   :", e.code().name, "-", e.details())


if __name__ == "__main__":
    demo()
