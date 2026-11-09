# Memcached Practice

`main.py` is a runnable cheat sheet for Memcached using **pymemcache** (the actively
maintained client; the older `python-memcached` package is no longer developed).

## Run

```bash
pip install -r pp_memcached/req.txt
docker compose -f pp_memcached/docker-compose.yaml up -d   # server + admin UI (http://localhost:8080)
python pp_memcached/main.py                                # against the real server
python pp_memcached/main.py --mock                         # no Docker needed
```

### Full test in Docker (nothing but Docker needed on the machine)

```bash
docker compose -f pp_memcached/docker-compose.yaml run --rm tester
docker compose -f pp_memcached/docker-compose.yaml down
```

`run tester` builds the image from `Dockerfile` (Python 3.12 + pymemcache + pytest), starts the
`memcached` container it depends on, runs `test_memcached.py` against it, then runs the full demo
(including `gets`/`cas` and server stats, which the mock can't do). The tests check real server
rules the mock skips, such as `decr` stopping at 0. Without a reachable server they are skipped.

| File | Purpose |
| --- | --- |
| `docker-compose.yaml` | `memcached`, `memcachedadmin` (UI on :8080), and `tester` (profile `test`, only runs on demand) |
| `Dockerfile` | test-runner image; server address comes from `MEMCACHED_HOST` / `MEMCACHED_PORT` |
| `test_memcached.py` | integration tests: add/replace, counters, TTL, CAS, get_many, stats, the demo itself |

## What the script covers

- `set`, `get` (with default), `delete`
- `add` (only if absent) vs `replace` (only if present) vs `set` (always)
- `set_many` / `get_many` in one round trip
- Atomic counters with `incr` / `decr`
- Expiry (TTL)
- `gets` / `cas` for optimistic locking (real server only)
- The **cache-aside** pattern with invalidation on write
- Serialisation (`serde`): pickle by default, a JSON example
- `HashClient` for spreading keys over several servers

## Memcached vs Redis (common interview question)

| | Memcached | Redis |
| --- | --- | --- |
| Data types | strings/bytes only | strings, lists, hashes, sets, sorted sets, streams |
| Persistence | none | RDB snapshots / AOF |
| Replication / clustering | client-side hashing | built-in replication, Sentinel, Cluster |
| Threads | multi-threaded | mostly single-threaded command execution |
| Pub/Sub, Lua, transactions | no | yes |
| Best for | simple, very fast cache | cache plus data structures, queues, rate limiters |
