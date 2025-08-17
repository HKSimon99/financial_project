from __future__ import annotations
from core.utils.cache import path, fresh, save_json, load_json
from core.clients.naver import NaverImageSearch


async def get_logo_cached(
    naver: NaverImageSearch, *, company_name: str, stock_code: str | None = None
) -> dict:
    key = stock_code or company_name
    cache_file = path("logos", f"{key}.json")

    # 30일 캐시
    if fresh(cache_file, days=30):
        cached = load_json(cache_file)
        if cached is not None:
            return cached

    # 자격 없으면 graceful degrade
    if not (naver and naver.client_id and naver.client_secret):
        data = {
            "company": company_name,
            "stock_code": stock_code,
            "logo_url": None,
            "cached": False,
            "reason": "missing_naver_credentials",
        }
        save_json(data, cache_file)
        return data

    # 검색 쿼리: 우선 종목코드, 없으면 회사명
    query = f"{stock_code} tradingview" if stock_code else f"{company_name} 로고"
    url = await naver.search_one(query)
    data = {
        "company": company_name,
        "stock_code": stock_code,
        "logo_url": url,
        "cached": False,
    }
    save_json(data, cache_file)
    return data
