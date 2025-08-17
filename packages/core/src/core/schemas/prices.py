from pydantic import BaseModel
from typing import List, Optional


class PricePoint(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    transaction_amount: Optional[float] = None
    change: Optional[float] = None


class PriceSeries(BaseModel):
    ticker: str
    points: List[PricePoint] = []
