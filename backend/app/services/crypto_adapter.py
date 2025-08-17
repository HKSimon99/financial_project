import asyncio
import logging
import random
from typing import Optional

import aiohttp
from broadcast import Broadcast

log = logging.getLogger(__name__)


class CryptoAdapter:
    """Polls CoinGecko for crypto market data and broadcasts updates."""

    def __init__(self, coin_id: str, vs_currency: str = "usd"):
        self.coin_id = coin_id
        self.vs_currency = vs_currency
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
        url = f"https://api.coingecko.com/api/v3/coins/{self.coin_id}/market_chart"
        params = {"vs_currency": self.vs_currency, "days": "1"}
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag
        try:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status in (304, 429):
                    self.backoff = min(self.backoff * 2, 60)
                    return
                resp.raise_for_status()
                self.backoff = 1
                self.etag = resp.headers.get("ETag", self.etag)
                data = await resp.json()
        except Exception as exc:  # pragma: no cover - network failures
            log.exception("CoinGecko fetch error: %s", exc)
            self.backoff = min(self.backoff * 2, 60)
            return

        # Normalize OHLC using the market chart data
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        if not prices:
            return
        open_ = prices[0][1]
        close_ = prices[-1][1]
        high = max(p[1] for p in prices)
        low = min(p[1] for p in prices)
        ts = int(prices[-1][0] / 1000)
        volume = volumes[-1][1] if volumes else 0.0
        payload = {
            "symbol": self.coin_id,
            "ts": ts,
            "open": float(open_),
            "high": float(high),
            "low": float(low),
            "close": float(close_),
            "volume": float(volume),
            "source": "coingecko",
        }
        await self.broadcast.publish(channel="crypto", message=payload)

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
