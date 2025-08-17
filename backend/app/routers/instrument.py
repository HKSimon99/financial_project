from __future__ import annotations

import os
from functools import lru_cache
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from starlette.responses import StreamingResponse

from core.clients.kis import KISClient
from core.schemas.prices import PricePoint, PriceSeries
from core.services.market_data import kis_daily_price

router = APIRouter()


def _env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise HTTPException(500, detail=f"Missing environment variable: {name}")
    return val


@lru_cache(maxsize=1)
def kis_singleton() -> KISClient:
    return KISClient(
        base_url=os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"),
        app_key=_env("APP_KEY"),
        app_secret=_env("APP_SECRET"),
        oauth_path=os.getenv("KIS_OAUTH_PATH", "/oauth2/tokenP"),
    )


async def get_kis() -> KISClient:
    return kis_singleton()


@router.get("/{slug}/snapshot")
async def snapshot(slug: str, kis: KISClient = Depends(get_kis)):
    """Return a simple price snapshot for the given instrument."""
    from datetime import datetime

    today = datetime.utcnow().strftime("%Y-%m-%d")
    df = await kis_daily_price(kis, slug, today, today)
    if df.empty:
        raise HTTPException(404, detail="Snapshot not found")
    return {"slug": slug, "snapshot": df.to_dict(orient="records")[-1]}


@router.get("/{slug}/ohlcv", response_model=PriceSeries)
async def ohlcv(
    slug: str,
    start: str,
    end: str,
    request: Request,
    live: bool = False,
    ws: bool = False,
    kis: KISClient = Depends(get_kis),
):
    """Return historical or live OHLCV data for the instrument."""
    if live:
        if ws and os.getenv("FF_LIVE_WS"):
            # WebSocket connections handled by the websocket route
            raise HTTPException(400, detail="Use WebSocket endpoint for live data")
        channel = f"ohlcv:{slug}"

        async def event_stream() -> AsyncIterator[str]:
            async with request.app.state.broadcast.subscribe(channel) as subscriber:
                async for event in subscriber:
                    yield f"data: {event.message}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    df = await kis_daily_price(kis, slug, start, end)
    points = [PricePoint(**row) for row in df.to_dict(orient="records")]
    return PriceSeries(ticker=slug, points=points)


if os.getenv("FF_LIVE_WS"):

    @router.websocket("/{slug}/ohlcv")
    async def ohlcv_ws(websocket: WebSocket, slug: str):
        """Optional WebSocket endpoint for live OHLCV when FF_LIVE_WS is set."""
        await websocket.accept()
        channel = f"ohlcv:{slug}"
        broadcast = websocket.app.state.broadcast
        async with broadcast.subscribe(channel) as subscriber:
            async for event in subscriber:
                await websocket.send_text(event.message)


@router.get("/{slug}/metrics")
async def metrics(slug: str):
    """Return cached or computed metrics for the instrument."""
    return {"slug": slug, "metrics": {}}
