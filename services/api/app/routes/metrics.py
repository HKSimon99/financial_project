from fastapi import APIRouter, Depends
import pandas as pd
from pydantic import BaseModel
from typing import List
from core.services.metrics import calculate_custom_metrics, calculate_piotroski_f_score

router = APIRouter()

class FSSnapshot(BaseModel):
    rows: List[dict]

@router.post("/custom")
async def custom_metrics(body: FSSnapshot):
    df = pd.DataFrame(body.rows)
    return calculate_custom_metrics(df, None)

class FSCompare(BaseModel):
    curr: List[dict]
    prev: List[dict]

@router.post("/piotroski")
async def piotroski(body: FSCompare):
    dfc = pd.DataFrame(body.curr)
    dfp = pd.DataFrame(body.prev)
    score, detail = calculate_piotroski_f_score(dfc, dfp)
    return {"score": score, "detail": detail}