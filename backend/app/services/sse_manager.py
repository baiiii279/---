import asyncio
import json
from datetime import datetime, timezone


class SSEEventManager:
    def __init__(self, max_queue_size: int = 100):
        self._subscribers: dict[int, list[asyncio.Queue]] = {}
        self._max_queue_size = max_queue_size

    def subscribe(self, paper_id: int) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers.setdefault(paper_id, []).append(queue)
        return queue

    def unsubscribe(self, paper_id: int, queue: asyncio.Queue):
        subs = self._subscribers.get(paper_id, [])
        if queue in subs:
            subs.remove(queue)
            if not subs:
                del self._subscribers[paper_id]

    def emit(self, paper_id: int, event: str, data: dict):
        subs = self._subscribers.get(paper_id, [])
        message = {"event": event, "data": data}
        disconnected = []
        for q in subs:
            if q.full():
                if data.get("critical", True):
                    try:
                        q.put_nowait(message)
                    except asyncio.QueueFull:
                        pass
            else:
                try:
                    q.put_nowait(message)
                except asyncio.QueueFull:
                    disconnected.append(q)
        for q in disconnected:
            self.unsubscribe(paper_id, q)


sse_manager = SSEEventManager()
