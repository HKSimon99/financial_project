import httpx

class DARTClient:
    def __init__(self, api_key: str, *, timeout: float = 10.0):
        self._client = httpx.AsyncClient(timeout=timeout)
        self.api_key = api_key

    async def single_fs(self, corp_code: str, year: int, reprt_code: str, fs_div: str) -> dict:
        r = await self._client.get(
            "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
            params={
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": reprt_code,
                "fs_div": fs_div,
            },
        )
        r.raise_for_status()
        return r.json()