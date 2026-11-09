"""Tests with FastAPI's TestClient (httpx under the hood, no server needed).

Cheat sheet:
- `with TestClient(app) as client:` runs the lifespan (startup/shutdown).
- `app.dependency_overrides[real_dep] = fake_dep` swaps dependencies in tests.
"""

import pytest
from fastapi.testclient import TestClient

from pp_fastapi.dependencies import API_KEY, get_store
from pp_fastapi.main import create_app
from pp_fastapi.store import ItemStore

AUTH = {"X-API-Key": API_KEY}


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health_and_middleware_headers(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.status_code == 200
    assert r.json()["request_id"] == "abc123"
    assert r.headers["X-Request-ID"] == "abc123"
    assert "X-Process-Time-Ms" in r.headers


def test_v1_crud_flow(client):
    r = client.post("/api/v1/items", json={"name": "Monitor", "price": 199.0})
    assert r.status_code == 201
    item = r.json()
    assert r.headers["Location"] == f"/api/v1/items/{item['id']}"

    r = client.patch(f"/api/v1/items/{item['id']}", json={"price": 149.0})
    assert r.json()["price"] == 149.0 and r.json()["name"] == "Monitor"

    assert client.delete(f"/api/v1/items/{item['id']}").status_code == 204
    r = client.get(f"/api/v1/items/{item['id']}")
    assert r.status_code == 404
    assert r.json()["error"] == "item_not_found"


def test_v1_validation_error_shape(client):
    r = client.post("/api/v1/items", json={"name": "", "price": -1, "colour": "red"})
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "validation_error"
    assert {e["loc"][-1] for e in body["detail"]} == {"name", "price", "colour"}


def test_v1_pagination_and_search(client):
    assert len(client.get("/api/v1/items?limit=1").json()) == 1
    assert [i["name"] for i in client.get("/api/v1/items?q=mou").json()] == ["Mouse"]
    assert client.get("/api/v1/items?limit=0").status_code == 422


def test_v1_random_running_sum(client):
    first = client.get("/api/v1/random").json()
    second = client.get("/api/v1/random").json()
    assert second["sum"] == first["sum"] + second["number"]


def test_v2_requires_api_key(client):
    assert client.get("/api/v2/items").status_code == 401
    r = client.get("/api/v2/items", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["items"][0]["price"] == {"amount": 49.99, "currency": "GBP"}


def test_dependency_override(client):
    empty = ItemStore()
    client.app.dependency_overrides[get_store] = lambda: empty
    assert client.get("/api/v2/items", headers=AUTH).json()["total"] == 0
    client.app.dependency_overrides.clear()


def test_patch_rejects_explicit_null(client):
    r = client.patch("/api/v1/items/1", json={"name": None})
    assert r.status_code == 422
    assert client.get("/api/v1/items").status_code == 200  # store not corrupted


def test_maintenance_mode_short_circuits(client):
    client.app.state.maintenance = True
    r = client.get("/api/v1/items")
    assert r.status_code == 503
    assert "X-Request-ID" in r.headers  # innermost, so outer middleware still wraps the 503
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/items", headers={"Host": "evil.com"}).status_code == 400  # host check first


def test_legacy_route_is_deprecated_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert spec["paths"]["/random"]["get"]["deprecated"] is True
