from pydantic import BaseModel
from typing import List, Optional


class FSRow(BaseModel):
    account_id: Optional[str] = None
    account_nm: Optional[str] = None
    bsns_year: Optional[str] = None
    thstrm_amount: Optional[str] = None
    frmtrm_amount: Optional[str] = None
    fs_div: Optional[str] = None
    reprt_code: Optional[str] = None


class FinancialStatement(BaseModel):
    corp_code: str
    year: int
    report_name: Optional[str] = None
    rows: List[FSRow] = []
