import os
import asyncio
import json
import random
from datetime import datetime
from typing import Iterable

import aiohttp

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
DEFAULT_IDS = ["bitcoin", "ethereum"]
VS_CURRENCY = "usd"


def _normalize(symbol: str, price: float, source: str) -> dict:
    return {
        "symbol": symbol.upper(),
        "price": float(price),
        "source": source,
        "ts": datetime.utcnow().isoformat(),
    }


async def _poll_coingecko(broadcast, ids: Iterable[str] | None = None) -> None:
    ids = list(ids or DEFAULT_IDS)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {"ids": ",".join(ids), "vs_currencies": VS_CURRENCY}
                async with session.get(
                    COINGECKO_URL, params=params, timeout=10
                ) as resp:
                    data = await resp.json()
                for symbol, payload in data.items():
                    price = payload.get(VS_CURRENCY)
                    if price is None:
                        continue
                    quote = _normalize(symbol, price, "coingecko")
                    await broadcast.publish(channel="quotes", message=json.dumps(quote))
            except Exception:
                pass
            await asyncio.sleep(random.uniform(5, 10))


async def _stream_ws(broadcast, url: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                symbol = data.get("symbol") or data.get("s")
                price = data.get("price") or data.get("p")
                if not symbol or price is None:
                    continue
                quote = _normalize(symbol, float(price), "ws")
                await broadcast.publish(channel="quotes", message=json.dumps(quote))


async def run(broadcast, ids: Iterable[str] | None = None) -> None:
    ws_url = os.getenv("FF_WS_ENDPOINT")
    use_ws = os.getenv("FF_LIVE_WS", "").lower() == "true" and ws_url
    if use_ws:
        while True:
            try:
                await _stream_ws(broadcast, ws_url)
            except Exception:
                await asyncio.sleep(1)
    else:
        await _poll_coingecko(broadcast, ids)
