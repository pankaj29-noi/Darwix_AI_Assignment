"""In-process WebSocket fan-out."""

from __future__ import annotations

import asyncio
from collections import defaultdict


class Hub:
    def __init__(self) -> None:
        self.queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self.history: dict[str, list[dict]] = defaultdict(list)

    def subscribe(self, call_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self.queues[call_id].append(queue)
        return queue

    def unsubscribe(self, call_id: str, queue: asyncio.Queue) -> None:
        if queue in self.queues[call_id]:
            self.queues[call_id].remove(queue)

    async def publish(self, call_id: str, event: dict) -> None:
        self.history[call_id].append(event)
        for queue in list(self.queues[call_id]):
            await queue.put(event)
