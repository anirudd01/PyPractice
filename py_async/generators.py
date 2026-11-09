#!/usr/bin/env python3
"""Generators cheat sheet (sync and async). Run:  python py_async/generators.py

- A function with `yield` returns a generator: lazy, produces values on demand, keeps state.
- Memory: a generator holds one item at a time; a list holds all of them.
- `yield from sub()` delegates to another generator (and returns its `return` value).
- Generators are single-use: once exhausted, iterate a new one.
- `async def` + `yield` = async generator, consumed with `async for`.
"""

import asyncio
import itertools
import sys
from collections.abc import AsyncIterator, Generator, Iterator


def countdown(n: int) -> Iterator[int]:
    while n > 0:
        yield n
        n -= 1


def chain_countdowns(first: int, second: int) -> Iterator[int]:
    """`yield from` delegates: same as `for x in countdown(first): yield x`."""
    yield from countdown(first)
    yield from countdown(second)


def running_average() -> Generator[float, float, None]:
    """Coroutine-style generator: values are SENT in with .send()."""
    total, count, average = 0.0, 0, 0.0
    while True:
        value = yield average
        total += value
        count += 1
        average = total / count


def read_large_file(lines: list[str]) -> Iterator[str]:
    """Pipeline stage 1 (real code: `with open(path) as f: yield from f`)."""
    yield from lines


def pipeline_demo() -> None:
    raw = ["INFO ok", "ERROR disk full", "INFO ok", "ERROR timeout", "WARN slow"]
    lines = read_large_file(raw)
    errors = (line for line in lines if line.startswith("ERROR"))  # generator expression
    messages = (line.split(" ", 1)[1] for line in errors)
    print("pipeline (nothing runs until consumed):", list(messages))


async def ticker(count: int, delay: float) -> AsyncIterator[int]:
    """Async generator: can `await` between yields (e.g. paging through an API)."""
    for i in range(count):
        await asyncio.sleep(delay)
        yield i


async def async_demo() -> None:
    print("async for           :", [i async for i in ticker(3, 0.01)])


def main() -> None:
    print("countdown(3)        :", list(countdown(3)))
    print("yield from          :", list(chain_countdowns(3, 2)))

    gen = countdown(2)
    print("next() by hand      :", next(gen), next(gen), next(gen, "exhausted"))

    avg = running_average()
    next(avg)  # "prime" it: run up to the first yield
    print("send()              :", [avg.send(x) for x in (10, 20, 30)])

    pipeline_demo()

    squares_list = [x * x for x in range(100_000)]
    squares_gen = (x * x for x in range(100_000))
    print("list vs generator   :", sys.getsizeof(squares_list), "bytes vs", sys.getsizeof(squares_gen), "bytes")

    print("itertools.islice    :", list(itertools.islice(itertools.count(10, 5), 4)))  # infinite, sliced
    print("itertools.batched   :", list(itertools.batched(range(7), 3)) if sys.version_info >= (3, 12) else "3.12+")

    asyncio.run(async_demo())


if __name__ == "__main__":
    main()
