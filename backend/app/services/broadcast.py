import os
import asyncio
from typing import Any, Set, Optional


class Broadcast:
    """Simple broadcast service with optional Redis backend."""

    def __init__(self, channel: str = "broadcast") -> None:
        self._channel = channel
        self._subscribers: Set[asyncio.Queue] = set()
        self._redis_url = os.getenv("REDIS_URL")
        self._redis = None  # type: Optional["redis.asyncio.Redis"]
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None

        if self._redis_url:
            try:
                import redis.asyncio as redis_async
            except Exception:  # pragma: no cover - optional dependency
                self._redis_url = None
            else:
                self._redis = redis_async.from_url(
                    self._redis_url, decode_responses=True
                )
                self._pubsub = self._redis.pubsub()

    async def _redis_listener(self) -> None:
        assert self._pubsub is not None
        await self._pubsub.subscribe(self._channel)
        async for message in self._pubsub.listen():
            if message.get("type") == "message":
                await self._broadcast_local(message.get("data"))

    async def _broadcast_local(self, message: Any) -> None:
        for queue in list(self._subscribers):
            await queue.put(message)

    def subscribe(self) -> asyncio.Queue:
        """Return a new queue for the subscriber."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        if self._redis and not self._listener_task:
            self._listener_task = asyncio.create_task(self._redis_listener())
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def publish(self, message: Any) -> None:
        if self._redis:
            await self._redis.publish(self._channel, message)
        await self._broadcast_local(message)


broadcast = Broadcast()
