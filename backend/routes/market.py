from fastapi import APIRouter, Depends, HTTPException
from httpx import HTTPStatusError
from functools import lru_cache
from core.clients.kis import KISClient
from core.clients.dart import DARTClient
from core.schemas.prices import PriceSeries, PricePoint
from core.schemas.financials import FinancialStatement
from core.services.market_data import (
    kis_daily_price,
    dart_financials,
    kis_financial_ratios,
    kis_investment_opinion,
)
import os

router = APIRouter()


def _env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        # 500 대신 500 + 친절 메시지
        raise HTTPException(500, detail=f"Missing environment variable: {name}")
    return val


@lru_cache(maxsize=1)
def kis_singleton() -> KISClient:
    return KISClient(
        base_url=os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"),
        app_key=os.environ["APP_KEY"],
        app_secret=os.environ["APP_SECRET"],
        oauth_path=os.getenv(
            "KIS_OAUTH_PATH", "/oauth2/tokenP"
        ),  # override to /oauth2/token if prod
    )


async def get_kis() -> KISClient:
    return kis_singleton()


def setup_shutdown(app):
    @app.on_event("shutdown")
    async def _close():
        try:
            await kis_singleton().aclose()
        except Exception:
            pass


async def get_dart() -> DARTClient:
    return DARTClient(api_key=os.environ["API_KEY"])


@router.get("/prices/{stock_code}", response_model=PriceSeries)
async def prices(
    stock_code: str, start_date: str, end_date: str, kis: KISClient = Depends(get_kis)
):
    df = await kis_daily_price(kis, stock_code, start_date, end_date)
    points = [PricePoint(**row) for row in df.to_dict(orient="records")]
    return PriceSeries(ticker=stock_code, points=points)


@router.get("/financials/{corp_code}", response_model=FinancialStatement)
async def financials(corp_code: str, year: int, dart: DARTClient = Depends(get_dart)):
    fs = await dart_financials(dart, corp_code, year)
    if not fs:
        raise HTTPException(404, detail="Financials not found")
    return fs


@router.get("/ratios/{stock_code}")
async def ratios(stock_code: str, kis: KISClient = Depends(get_kis)):
    try:
        df = await kis_financial_ratios(kis, stock_code)
    except HTTPStatusError as e:
        # bubble a clear upstream failure to the client
        raise HTTPException(status_code=502, detail=str(e))
    return {"stock_code": stock_code, "rows": df.to_dict(orient="records")}


@router.get("/opinion/{stock_code}")
async def opinion(stock_code: str, kis: KISClient = Depends(get_kis)):
    """
    KIS 투자 의견/목표가/애널리스트 수를 반환.
    Returns a stable JSON shape so the frontend can rely on fields.
    """
    try:
        data = await kis_investment_opinion(kis, stock_code)
    except HTTPStatusError as e:
        # Map upstream KIS errors (403/429/etc.) to a clear 502 with hint text.
        raise HTTPException(status_code=502, detail=str(e))

    # Normalize output so the UI doesn't depend on optional keys
    return {
        "stock_code": stock_code,
        "opinion": data.get("opinion"),
        "target_price": data.get("target_price"),
        "analyst_count": data.get("analyst_count"),
    }
