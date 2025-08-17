from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import httpx


class KISClient:
    def __init__(
        self,
        base_url: str,
        app_key: str,
        app_secret: str,
        *,
        timeout: float = 10.0,
        oauth_path: str = "/oauth2/tokenP",
    ):
        self.base_url = base_url.rstrip("/")
        self.app_key = app_key
        self.app_secret = app_secret
        self.oauth_path = oauth_path
        self._client = httpx.AsyncClient(timeout=timeout)
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def _ensure_token(self) -> str:
        async with self._lock:
            if self._token and self._expires_at and datetime.now() < self._expires_at:
                return self._token

            # tiny retry to dodge transient 403s
            last_exc = None
            for _ in range(2):
                r = await self._client.post(
                    f"{self.base_url}{self.oauth_path}",
                    json={
                        "grant_type": "client_credentials",
                        "appkey": self.app_key,
                        "appsecret": self.app_secret,
                    },
                )
                try:
                    r.raise_for_status()
                    data = r.json()
                    self._token = data["access_token"]
                    ttl = int(data.get("expires_in", 86400)) - 300
                    self._expires_at = datetime.now() + timedelta(seconds=max(ttl, 600))
                    return self._token
                except httpx.HTTPStatusError as e:
                    last_exc = e
                    await asyncio.sleep(0.2)  # brief backoff

            # surface helpful message
            detail = getattr(last_exc.response, "text", "")[:200].replace("\n", " ")
            raise httpx.HTTPStatusError(
                f"KIS token failed ({last_exc.response.status_code}). Hint: {detail}",
                request=last_exc.request,
                response=last_exc.response,
            )

    async def get(self, path: str, *, tr_id: str, params: Dict[str, Any]) -> dict:
        token = await self._ensure_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }
        r = await self._client.get(
            f"{self.base_url}{path}", params=params, headers=headers
        )
        r.raise_for_status()
        data = r.json()
        if data.get("rt_cd") != "0":
            raise httpx.HTTPStatusError(
                message=data.get("msg1", "KIS error"), request=r.request, response=r
            )
        return data

    async def aclose(self):
        await self._client.aclose()
