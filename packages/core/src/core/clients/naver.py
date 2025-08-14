from __future__ import annotations
import os
import httpx
from typing import Optional
from datetime import datetime, timedelta
from core.utils.cache import path, fresh, load_json, save_json

NAVER_ID = os.getenv("NAVER_SEARCH_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_SEARCH_CLIENT_SECRET")

async def company_logo(company_name: str, stock_code: str | None = None) -> str | None:
    cache = path("logos", f"{company_name}.json")
    if fresh(cache, days=30):
        data = load_json(cache)
        if data and data.get("logo_url") and data.get("logo_url") != "NO_LOGO":
            return data["logo_url"]

    if not stock_code or not NAVER_ID or not NAVER_SECRET:
        return None

    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(
            "https://openapi.naver.com/v1/search/image",
            headers={"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET},
            params={"query": f"{stock_code} tradingview", "display": 1, "sort": "sim"},
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        logo_url = items[0]["link"] if items else "NO_LOGO"
        save_json({
            "company_name": company_name,
            "logo_url": logo_url,
            "expiry_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }, cache)
        return None if logo_url == "NO_LOGO" else logo_url
    
class NaverImageSearch:
    def __init__(self, client_id: Optional[str], client_secret: Optional[str], *, timeout: float = 5.0):
        self.client_id = client_id
        self.client_secret = client_secret
        self._client = httpx.AsyncClient(timeout=timeout)

    def _enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def search_one(self, query: str) -> str | None:
        if not self._enabled():
            # 자격 없으면 조용히 None
            return None
        r = await self._client.get(
            "https://openapi.naver.com/v1/search/image",
            headers={"X-Naver-Client-Id": self.client_id, "X-Naver-Client-Secret": self.client_secret},
            params={"query": query, "display": 1, "sort": "sim"},
        )
        # 네이버 API는 200이어도 items 비어있을 수 있음
        if r.status_code // 100 != 2:
            return None
        data = r.json()
        items = data.get("items") or []
        return items[0]["link"] if items else None