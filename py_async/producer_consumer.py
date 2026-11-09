#!/usr/bin/env python3
"""Producer / consumer with asyncio.Queue (a work queue: each item goes to ONE consumer).

For "every subscriber gets every message" see pub_sub.py.

Run:  python py_async/producer_consumer.py -p 3 -c 5

Key ideas:
- `await q.put()` / `await q.get()` suspend instead of blocking the thread.
- `q.task_done()` + `await q.join()` = "wait until every queued item is processed".
- Consumers loop forever, so cancel them once the queue is drained.
- `asyncio.Queue(maxsize=N)` adds back-pressure: producers wait when it's full.
"""

import argparse
import asyncio
import os
import random
import time


async def make_item(size: int = 5) -> str:
    return os.urandom(size).hex()


async def rand_sleep(caller: str | None = None) -> None:
    delay = random.uniform(0, 1)
    if caller:
        print(f"{caller} sleeping for {delay:.2f} seconds.")
    await asyncio.sleep(delay)


async def produce(name: int, q: asyncio.Queue) -> None:
    for _ in range(random.randint(0, 5)):
        await rand_sleep(caller=f"Producer {name}")
        item = await make_item()
        await q.put((item, time.perf_counter()))
        print(f"Producer {name} added <{item}> to queue.")


async def consume(name: int, q: asyncio.Queue) -> None:
    while True:
        await rand_sleep(caller=f"Consumer {name}")
        item, queued_at = await q.get()
        print(f"Consumer {name} got element <{item}> in {time.perf_counter() - queued_at:0.5f} seconds.")
        q.task_done()


async def main(nprod: int, ncon: int) -> None:
    q: asyncio.Queue = asyncio.Queue(maxsize=10)
    producers = [asyncio.create_task(produce(n, q)) for n in range(nprod)]
    consumers = [asyncio.create_task(consume(n, q)) for n in range(ncon)]
    await asyncio.gather(*producers)  # all items produced
    await q.join()  # all items processed (task_done called for each)
    for c in consumers:
        c.cancel()
    # Wait for the cancellations to finish; return_exceptions swallows CancelledError.
    await asyncio.gather(*consumers, return_exceptions=True)


if __name__ == "__main__":
    random.seed(444)
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--nprod", type=int, default=5)
    parser.add_argument("-c", "--ncon", type=int, default=10)
    ns = parser.parse_args()
    start = time.perf_counter()
    asyncio.run(main(ns.nprod, ns.ncon))
    print(f"Program completed in {time.perf_counter() - start:0.5f} seconds.")
