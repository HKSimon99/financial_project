from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Company
from ..services.screeners import RECIPES, run_screener

router = APIRouter()


class Rule(BaseModel):
    metric: str
    op: Literal["<", "<=", ">", ">=", "=="]
    value: float


class RunIn(BaseModel):
    recipe: Optional[str] = None
    rules: Optional[List[Rule]] = None
    sort_by: Optional[str] = None
    sort_desc: bool = False
    limit: int = 50


@router.post("/run")
def run(body: RunIn, db: Session = Depends(get_db)) -> List[dict]:
    if body.recipe:
        recipe = RECIPES.get(body.recipe)
        if not recipe:
            raise HTTPException(status_code=404, detail="recipe not found")
        rules = recipe["rules"]
        sort_by = body.sort_by or recipe.get("sort_by")
        limit = body.limit or recipe.get("limit", 50)
    else:
        rules = [r.dict() for r in body.rules or []]
        sort_by = body.sort_by
        limit = body.limit

    companies: List[Company] = run_screener(
        db, rules, sort_by=sort_by, sort_desc=body.sort_desc, limit=limit
    )
    return [{"ticker": c.ticker, "name": c.name} for c in companies]


@router.get("/share/{screener_id}")
def share(screener_id: str):
    recipe = RECIPES.get(screener_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="screener not found")
    return recipe
