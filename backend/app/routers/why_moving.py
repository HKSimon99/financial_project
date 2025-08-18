from __future__ import annotations

import os
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query

from core.clients.kis import KISClient


def _env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise HTTPException(500, detail=f"Missing environment variable: {name}")
    return val


router = APIRouter()


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
    slug: str, window: int = Query(20, ge=5, le=120), kis: KISClient = Depends(get_kis)
):  # <-- add colon here
    # minimal body so it parses; replace with real logic
    return {"slug": slug, "window": window}
