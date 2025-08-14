from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import pandas as pd
from core.clients.kis import KISClient
from core.services.market_data import kis_prices_panel
from core.services.portfolio import optimize_portfolio, backtest_portfolio

router = APIRouter()

class OptimizeIn(BaseModel):
    tickers: List[str]
    start_date: str
    end_date: str
    risk_free: float = 0.02

class OptimizeOut(BaseModel):
    weights: List[float]
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    success: bool

class BacktestIn(BaseModel):
    tickers: List[str]
    start_date: str
    end_date: str
    weights: List[float]

class CurvePoint(BaseModel):
    date: str
    value: float

class BacktestOut(BaseModel):
    curve: List[CurvePoint]
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    max_drawdown: float

async def get_kis() -> KISClient:
    return KISClient(
        base_url=os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"),
        app_key=os.environ["APP_KEY"],
        app_secret=os.environ["APP_SECRET"],
    )

@router.post("/optimize", response_model=OptimizeOut)
async def optimize(body: OptimizeIn, kis: KISClient = Depends(get_kis)):
    rets = await kis_prices_panel(kis, body.tickers, body.start_date, body.end_date)
    if rets is None or rets.empty:
        raise HTTPException(404, detail="no returns data")
    result = optimize_portfolio(rets, risk_free_rate=body.risk_free)
    if not result.get("success"):
        raise HTTPException(500, detail="optimization failed")
    # weights as list for JSON
    result["weights"] = list(map(float, result["weights"]))
    return result

@router.post("/backtest", response_model=BacktestOut)
async def backtest(body: BacktestIn, kis: KISClient = Depends(get_kis)):
    # build prices panel (close-only) matching ticker order
    async def one(code: str) -> pd.Series:
        from core.services.market_data import kis_daily_price
        df = await kis_daily_price(kis, code, body.start_date, body.end_date)
        s = df.set_index("date")["close"].astype(float)
        s.index = pd.to_datetime(s.index)
        s.name = code
        return s
    import asyncio
    series_list = await asyncio.gather(*[one(t) for t in body.tickers])
    price_df = pd.concat(series_list, axis=1)

    result = backtest_portfolio(price_df, np.array(body.weights, dtype=float))
    curve = [CurvePoint(date=str(d.date()), value=float(v)) for d, v in result["cumulative_returns"].items()]

    return BacktestOut(
        curve=curve,
        annual_return=float(result["annual_return"]),
        annual_volatility=float(result["annual_volatility"]),
        sharpe_ratio=float(result["sharpe_ratio"]),
        max_drawdown=float(result["max_drawdown"]),
    )