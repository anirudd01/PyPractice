"""Integration tests against a REAL memcached server (they check server rules the mock skips).

Run:
    docker compose -f pp_memcached/docker-compose.yaml run --rm tester    # everything in Docker
    # or, with memcached already on localhost:11211:
    cd pp_memcached && pytest -v

Every test is skipped when no server answers within ~10 seconds.
"""

import time
import uuid

import pytest
from pymemcache.exceptions import MemcacheError

from main import SERVER, make_client


@pytest.fixture(scope="module")
def mc():
    client = make_client()
    deadline = time.time() + 10  # the container may still be starting
    while True:
        try:
            client.version()
            break
        except (OSError, MemcacheError):
            if time.time() > deadline:
                pytest.skip(f"no memcached server at {SERVER[0]}:{SERVER[1]}")
            time.sleep(0.5)
    yield client
    client.close()


@pytest.fixture
def key():
    return f"test:{uuid.uuid4().hex[:12]}"  # unique keys: tests never see each other's data


def test_set_get_delete_roundtrip_python_objects(mc, key):
    value = {"name": "Ani", "langs": ["python", "go"], "n": 3}
    assert mc.set(key, value, noreply=False)
    assert mc.get(key) == value
    assert mc.delete(key, noreply=False)
    assert mc.get(key) is None


def test_add_only_if_absent_replace_only_if_present(mc, key):
    assert mc.replace(key, "x", noreply=False) is False
    assert mc.add(key, "first", noreply=False) is True
    assert mc.add(key, "second", noreply=False) is False
    assert mc.replace(key, "third", noreply=False) is True
    assert mc.get(key) == "third"


def test_counters_are_atomic_and_clamp_at_zero(mc, key):
    mc.set(key, 0, noreply=False)
    assert mc.incr(key, 5) == 5
    assert mc.decr(key, 2) == 3
    assert mc.decr(key, 100) == 0  # real server never goes negative (the mock does)
    assert mc.incr(f"{key}:missing", 1) is None


def test_ttl_expires(mc, key):
    mc.set(key, "otp", expire=2, noreply=False)
    assert mc.get(key) == "otp"
    time.sleep(3.2)  # expiry has one-second resolution, so leave a margin both ways
    assert mc.get(key) is None


def test_cas_rejects_stale_token(mc, key):
    mc.set(key, 10, noreply=False)
    value, token = mc.gets(key)
    assert mc.cas(key, value - 1, token, noreply=False) is True
    assert mc.cas(key, value - 2, token, noreply=False) is False  # token changed on the last write
    assert mc.get(key) == 9


def test_get_many_omits_missing_keys(mc, key):
    keys = {f"{key}:{i}": i for i in range(3)}
    assert mc.set_many(keys, noreply=False) == []
    assert mc.get_many([*keys, f"{key}:nope"]) == keys


def test_stats_are_reported(mc):
    stats = mc.stats()
    assert b"curr_items" in stats and b"get_hits" in stats


def test_demo_script_runs_end_to_end(mc, capsys, monkeypatch):
    import main

    monkeypatch.setattr("sys.argv", ["main.py"])
    main.main()
    out = capsys.readouterr().out
    assert "gets / cas (optimistic locking)" in out
    assert "server stats" in out
