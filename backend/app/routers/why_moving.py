from __future__ import annotations

import os
from datetime import datetime, timedelta
from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from core.clients.kis import KISClient
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


def _confidence(z: float) -> float:
    return min(1.0, abs(z) / 3)


@router.get("/{slug}")
async def why_moving(
    slug: str,
    window: int = Query(20, ge=5, le=120),
    kis: KISClient = Depends(get_kis),
):
    """Explain price movement using breakout signals when news is unavailable."""
    if os.getenv("NEWS_API_KEY"):
        return {
            "slug": slug,
            "signals": [],
            "confidence": 0.0,
            "method_note": "News-based analysis not implemented",
        }

    end = datetime.utcnow()
    start = end - timedelta(days=window * 4)
    df = await kis_daily_price(
        kis, slug, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    )
    if df.empty or len(df) < window + 1:
        raise HTTPException(status_code=404, detail="Not enough price data")

    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    recent = df.tail(window + 1)
    today = recent.iloc[-1]
    hist = recent.iloc[:-1]

    price_mean = hist["close"].mean()
    price_std = hist["close"].std(ddof=0)
    volume_mean = hist["volume"].mean()
    volume_std = hist["volume"].std(ddof=0)

    price_z = (today["close"] - price_mean) / price_std if price_std else 0.0
    volume_z = (today["volume"] - volume_mean) / volume_std if volume_std else 0.0

    signals = [
        {
            "type": "price_breakout",
            "zscore": price_z,
            "confidence": _confidence(price_z),
            "method_note": f"{window}-day z-score for closing price",
        },
        {
            "type": "volume_breakout",
            "zscore": volume_z,
            "confidence": _confidence(volume_z),
            "method_note": f"{window}-day z-score for volume",
        },
    ]

    return {
        "slug": slug,
        "signals": signals,
        "confidence": max(s["confidence"] for s in signals),
        "method_note": "Price/volume breakout via Z-score",
    }
