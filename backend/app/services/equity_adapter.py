import asyncio
import logging
import os
import random
from typing import Optional

import aiohttp
from broadcast import Broadcast

log = logging.getLogger(__name__)


class EquityAdapter:
    """Polls Alpha Vantage for intraday equity data and broadcasts updates."""

    def __init__(
        self, symbol: str, api_key: Optional[str] = None, interval: str = "1min"
    ):
        self.symbol = symbol
        self.interval = interval
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY", "demo")
        self.etag: Optional[str] = None
        self.backoff = 1
        self.broadcast = Broadcast("memory://")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _sleep_with_jitter(self) -> None:
        delay = self.backoff + random.random()
        await asyncio.sleep(delay)

    async def fetch(self) -> None:
        session = await self._get_session()
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": self.symbol,
            "interval": self.interval,
            "apikey": self.api_key,
        }
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag
        try:
            async with session.get(
                "https://www.alphavantage.co/query", params=params, headers=headers
            ) as resp:
                if resp.status in (304, 429):
                    self.backoff = min(self.backoff * 2, 60)
                    return
                resp.raise_for_status()
                self.backoff = 1
                self.etag = resp.headers.get("ETag", self.etag)
                data = await resp.json()
        except Exception as exc:  # pragma: no cover - network failures
            log.exception("Alpha Vantage fetch error: %s", exc)
            self.backoff = min(self.backoff * 2, 60)
            return

        series_key = next((k for k in data if "Time Series" in k), None)
        if not series_key:
            return
        latest_ts, latest = next(iter(data[series_key].items()))
        payload = {
            "symbol": self.symbol,
            "ts": latest_ts,
            "open": float(latest["1. open"]),
            "high": float(latest["2. high"]),
            "low": float(latest["3. low"]),
            "close": float(latest["4. close"]),
            "volume": float(latest["5. volume"]),
            "source": "alphavantage",
        }
        await self.broadcast.publish(channel="equity", message=payload)

    async def run(self) -> None:
        await self.broadcast.connect()
        try:
            while True:
                await self.fetch()
                await self._sleep_with_jitter()
        finally:
            await self.broadcast.disconnect()

    async def close(self) -> None:
        if self._session:
            await self._session.close()
