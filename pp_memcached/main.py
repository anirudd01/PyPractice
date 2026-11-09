"""Memcached cheat sheet with pymemcache (the maintained client from Pinterest).

Run:
    docker compose -f pp_memcached/docker-compose.yaml up -d
    python pp_memcached/main.py            # against the real server on 127.0.0.1:11211
    python pp_memcached/main.py --mock     # no server needed (in-process fake; it does not
                                           # mirror every server rule: decr can go below 0,
                                           # replace/expire values come back as bytes)
    docker compose -f pp_memcached/docker-compose.yaml run --rm tester   # tests + demo in Docker

Server address comes from MEMCACHED_HOST / MEMCACHED_PORT (default 127.0.0.1:11211).

Memcached in one breath: an in-memory key -> bytes store with TTLs and LRU eviction.
No persistence, no replication, no queries; clients pick the server by hashing the key.
Keys: max 250 bytes, no spaces/control chars. Values: max 1 MB by default.
"""

import argparse
import json
import os
import time

from pymemcache import serde
from pymemcache.client.base import Client
from pymemcache.client.hash import HashClient

SERVER = (os.getenv("MEMCACHED_HOST", "127.0.0.1"), int(os.getenv("MEMCACHED_PORT", "11211")))


def make_client(mock: bool = False) -> Client:
    if mock:
        from pymemcache.test.utils import MockMemcacheClient

        return MockMemcacheClient(serde=serde.pickle_serde)
    # serde = how Python objects become bytes. pickle_serde handles str/int/dict/...
    # Unpickling runs code chosen by whoever wrote the bytes: only use pickle with a cache
    # nobody untrusted can write to (or use the JSON serde shown below).
    return Client(SERVER, serde=serde.pickle_serde, connect_timeout=2, timeout=2)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def basics(mc: Client) -> None:
    section("set / get / delete")
    mc.set("user:1", {"name": "Ani", "langs": ["python", "go"]})
    print("get user:1          ->", mc.get("user:1"))
    print("get missing         ->", mc.get("user:404"))
    print("get missing default ->", mc.get("user:404", default="n/a"))
    mc.delete("user:1")
    print("after delete        ->", mc.get("user:1"))

    section("add vs replace vs set")
    mc.delete("k")  # start clean so the demo prints the same result on every run
    print("add new key         ->", mc.add("k", "first", noreply=False))   # True: only if absent
    print("add existing key    ->", mc.add("k", "second", noreply=False))  # False
    print("replace existing    ->", mc.replace("k", "third", noreply=False))  # True: only if present
    print("replace missing     ->", mc.replace("nope", "x", noreply=False))   # False
    print("value now           ->", mc.get("k"))
    # Note: noreply=True (the default for set/add/replace) means "don't wait for the
    # server's answer" -> faster, but the call always returns True.


def batch(mc: Client) -> None:
    section("set_many / get_many (one round trip)")
    failed = mc.set_many({"p:1": 10, "p:2": 20, "p:3": 30}, noreply=False)
    print("set_many failed keys ->", failed)  # [] means all stored
    print("get_many            ->", mc.get_many(["p:1", "p:2", "p:3", "p:missing"]))  # missing keys are omitted
    mc.delete_many(["p:1", "p:2", "p:3"])


def counters(mc: Client) -> None:
    section("incr / decr (atomic counters)")
    mc.set("hits", 0)  # stored as the ASCII digits b"0"; incr/decr only work on digits
    mc.incr("hits", 5)
    print("incr by 5           ->", mc.get("hits"))
    print("decr by 2           ->", mc.decr("hits", 2))
    print("decr below zero     ->", mc.decr("hits", 100))  # clamps at 0, never negative
    print("incr missing key    ->", mc.incr("no-such-counter", 1))  # None: key must exist


def ttl(mc: Client) -> None:
    section("expiry (TTL)")
    mc.set("otp", "123456", expire=1)  # seconds; 0 = never expire (until evicted)
    print("right away          ->", mc.get("otp"))
    time.sleep(1.5)
    print("after 1.5 s         ->", mc.get("otp"))


def compare_and_swap(mc: Client) -> None:
    section("gets / cas (optimistic locking)")
    mc.set("stock", 10)
    value, token = mc.gets("stock")  # token changes on every write
    print("gets                ->", value, token)
    print("cas with token      ->", mc.cas("stock", value - 1, token))  # True: nobody wrote in between
    print("cas with old token  ->", mc.cas("stock", value - 2, token))  # False: token is stale
    print("value now           ->", mc.get("stock"))


def cache_aside(mc: Client) -> None:
    section("cache-aside pattern (the one you'll actually use)")

    def slow_db_lookup(product_id: int) -> dict:
        time.sleep(0.3)
        return {"id": product_id, "name": f"Product {product_id}", "price": 9.99}

    def get_product(product_id: int) -> dict:
        key = f"product:{product_id}"
        cached = mc.get(key)
        if cached is not None:
            return cached  # cache hit
        product = slow_db_lookup(product_id)  # cache miss -> load from source
        mc.set(key, product, expire=60)  # populate with a TTL
        return product

    def update_product(product_id: int, changes: dict) -> None:
        # ... write to DB first, then invalidate (delete beats update: avoids stale races)
        mc.delete(f"product:{product_id}")

    for attempt in ("miss", "hit"):
        start = time.perf_counter()
        get_product(7)
        print(f"{attempt:<19} -> {(time.perf_counter() - start) * 1000:.1f} ms")
    update_product(7, {"price": 5})
    print("after invalidation  ->", mc.get("product:7"))


def json_serde_example() -> None:
    section("custom serde (JSON instead of pickle)")

    class JsonSerde:
        # flags tell the deserializer how the bytes were written
        def serialize(self, key, value):
            if isinstance(value, str):
                return value.encode(), 1
            return json.dumps(value).encode(), 2

        def deserialize(self, key, value, flags):
            if flags == 1:
                return value.decode()
            if flags == 2:
                return json.loads(value)
            raise ValueError(f"unknown flags {flags}")

    s = JsonSerde()
    raw, flags = s.serialize("k", {"a": 1})
    print("serialized          ->", raw, "flags", flags)
    print("deserialized        ->", s.deserialize("k", raw, flags))
    print("(use it with Client(..., serde=JsonSerde()); JSON is safer than pickle across languages)")


def sharding_note() -> None:
    section("multiple servers")
    print("HashClient([('cache1', 11211), ('cache2', 11211)]) spreads keys with consistent hashing;")
    print("losing one server only loses that server's share of keys.")
    _ = HashClient  # imported so the class is easy to jump to


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="use an in-process fake instead of a server")
    args = parser.parse_args()

    mc = make_client(args.mock)
    basics(mc)
    batch(mc)
    counters(mc)
    ttl(mc)
    if args.mock:
        print("\n(gets/cas skipped: the mock client doesn't implement gets)")
    else:
        compare_and_swap(mc)
        section("server stats")
        stats = mc.stats()
        for key in (b"curr_items", b"get_hits", b"get_misses", b"evictions"):
            print(f"{key.decode():<19} -> {stats.get(key)}")
    cache_aside(mc)
    json_serde_example()
    sharding_note()
    mc.close()


if __name__ == "__main__":
    main()
