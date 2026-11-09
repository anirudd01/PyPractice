"""End-to-end test: starts the real gRPC server on a free port, then calls it.

Run (inside pp_grpc/):  pytest -v
"""

import socket

import grpc
import pytest
from fastapi.testclient import TestClient

import customer_pb2
import main
from client import CustomerClient
from server import serve


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PORT = _free_port()


@pytest.fixture(scope="module")
def client():
    server = serve(PORT)
    with CustomerClient(port=PORT) as c:
        yield c
    server.stop(grace=None)


def test_unary_crud(client):
    created = client.create_customer("Ann", "ann@example.com")
    assert client.get_customer(created.id).name == "Ann"

    updated = client.update_customer(created.id, email="new@example.com")
    assert (updated.name, updated.email) == ("Ann", "new@example.com")  # name untouched

    client.delete_customer(created.id)
    with pytest.raises(grpc.RpcError) as err:
        client.get_customer(created.id)
    assert err.value.code() == grpc.StatusCode.NOT_FOUND


def test_validation_error(client):
    with pytest.raises(grpc.RpcError) as err:
        client.create_customer("", "")
    assert err.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_streaming_styles(client):
    bulk = client.bulk_create([("B1", "b1@x.com"), ("B2", "b2@x.com"), ("B3", "b3@x.com")])
    assert bulk.created_count == 3

    assert len(list(client.list_customers(page_size=2))) == 2

    found = [c.id for c in client.lookup([bulk.ids[0], "nope", bulk.ids[2]])]
    assert found == [bulk.ids[0], bulk.ids[2]]

    premium = client.create_customer("P", "p@x.com", customer_pb2.TIER_PREMIUM)
    assert [c.id for c in client.list_customers(tier=customer_pb2.TIER_PREMIUM)] == [premium.id]


def test_rest_gateway_maps_grpc_errors(client, monkeypatch):
    monkeypatch.setattr(main, "CustomerClient", lambda: CustomerClient(port=PORT))
    with TestClient(main.app) as http:
        r = http.post("/customers", json={"name": "Gw", "email": "gw@example.com"})
        assert r.status_code == 201
        cid = r.json()["id"]
        assert http.patch(f"/customers/{cid}", json={"name": "Gw2"}).json()["name"] == "Gw2"
        assert http.delete(f"/customers/{cid}").status_code == 204
        r = http.get(f"/customers/{cid}")
        assert r.status_code == 404 and r.json()["grpc_code"] == "NOT_FOUND"
