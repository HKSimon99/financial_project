import asyncio

import pytest

from backend.app.services.broadcast import Broadcast


@pytest.mark.asyncio
async def test_broadcast_sse():
    b = Broadcast()
    queue = b.subscribe()
    await b.publish("ping")
    msg = await asyncio.wait_for(queue.get(), timeout=1)
    assert msg == "ping"
