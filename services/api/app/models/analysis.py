from pydantic import BaseModel, Field
from typing import List, Optional

class FSRow(BaseModel):
    account_id: Optional[str] = None
    account_nm: Optional[str] = None
    bsns_year: Optional[str] = None
    thstrm_amount: Optional[str] = None
    frmtrm_amount: Optional[str] = None
    fs_div: Optional[str] = None
    reprt_code: Optional[str] = None

class PricePoint(BaseModel):
    date: str
    close: Optional[float] = None

class HealthOut(BaseModel):
    debt_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    roe: Optional[float] = None
    op_margin: Optional[float] = None
    interest_coverage: Optional[float] = None
    z_score: Optional[float] = None
    total_score: Optional[float] = None
    grade: str = "N/A"

class RatiosOut(BaseModel):
    PER: Optional[float] = None
    PBR: Optional[float] = None
    배당수익률: Optional[float] = Field(default=None, alias="배당수익률(%)")

class DCFIn(BaseModel):
    fcf0: float; growth: float; wacc: float; terminal_g: float; shares: float

class RIMIn(BaseModel):
    bps: float; roe: float; cost_of_equity: float; growth: float; years: int; shares: float