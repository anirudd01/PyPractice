#!/usr/bin/env python3
"""In-process publish / subscribe with asyncio (fan-out: EVERY subscriber gets EVERY message).

Compare with producer_consumer.py, where each item goes to only one consumer.

Run:  python py_async/pub_sub.py

Design: the broker keeps one asyncio.Queue per subscriber per topic. Publishing puts
the message into each subscriber's queue, so a slow subscriber never delays the others
(it just builds its own backlog; bounded queues drop the oldest message here).
Same idea as Redis pub/sub, WebSocket broadcast, or Kafka with one consumer group per
subscriber. (Inside ONE Kafka consumer group each message goes to one consumer: that is
the work-queue model of producer_consumer.py.)
"""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class Broker:
    def __init__(self, max_backlog: int = 100) -> None:
        self._topics: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._max_backlog = max_backlog

    def publish(self, topic: str, message: str) -> int:
        """Non-blocking; returns how many subscribers received the message."""
        queues = self._topics.get(topic, set())
        for q in queues:
            if q.full():
                q.get_nowait()  # drop the oldest instead of blocking the publisher
            q.put_nowait(message)
        return len(queues)

    @asynccontextmanager
    async def subscribe(self, topic: str) -> AsyncIterator[asyncio.Queue]:
        """`async with broker.subscribe("news") as q:` auto-unsubscribes on exit."""
        q: asyncio.Queue = asyncio.Queue(self._max_backlog)
        self._topics[topic].add(q)
        try:
            yield q
        finally:
            self._topics[topic].discard(q)


async def subscriber(name: str, broker: Broker, topic: str, ready: asyncio.Event, delay: float) -> list[str]:
    received = []
    async with broker.subscribe(topic) as q:
        ready.set()
        while (message := await q.get()) != "STOP":
            received.append(message)
            print(f"[{name:<5}] {topic}: {message}")
            await asyncio.sleep(delay)  # simulate work; slow subscribers don't block others
    return received


async def main() -> None:
    broker = Broker()
    events = {name: asyncio.Event() for name in ("fast", "slow", "sport")}

    async with asyncio.TaskGroup() as tg:  # Python 3.11+
        fast = tg.create_task(subscriber("fast", broker, "news", events["fast"], 0.01))
        slow = tg.create_task(subscriber("slow", broker, "news", events["slow"], 0.2))
        sport = tg.create_task(subscriber("sport", broker, "sport", events["sport"], 0.01))

        await asyncio.gather(*(e.wait() for e in events.values()))  # everyone subscribed

        for i in range(3):
            n = broker.publish("news", f"headline {i}")
            print(f"published news {i} to {n} subscribers")
        broker.publish("sport", "goal!")
        broker.publish("weather", "rain")  # nobody listening -> dropped
        broker.publish("news", "STOP")
        broker.publish("sport", "STOP")

    print("fast got :", fast.result())
    print("slow got :", slow.result())
    print("sport got:", sport.result())


if __name__ == "__main__":
    asyncio.run(main())
