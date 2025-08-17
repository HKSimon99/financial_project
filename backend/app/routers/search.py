from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Dict, List

from fastapi import APIRouter, Query
from rapidfuzz import fuzz, process
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)

router = APIRouter()

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL) if DATABASE_URL else None
metadata = MetaData()

companies = Table(
    "companies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name_kr", String, nullable=False),
    Column("name_en", String, nullable=False),
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\s-]+", "", text)
    return text


@router.get("/search")
def search(q: str = Query(..., min_length=1)) -> Dict[str, Any]:
    norm_q = _normalize(q)
    results: List[Dict[str, Any]] = []
    suggestion: str | None = None

    if engine is not None:
        with engine.connect() as conn:
            norm_col = func.replace(
                func.replace(func.lower(companies.c.name_kr), "-", ""),
                " ",
                "",
            )
            score = func.similarity(norm_col, norm_q)
            stmt = (
                select(
                    companies.c.id,
                    companies.c.name_kr,
                    companies.c.name_en,
                    score.label("score"),
                )
                .where(score > 0.1)
                .order_by(score.desc())
                .limit(10)
            )
            rows = conn.execute(stmt).all()
            results = [
                {
                    "id": r.id,
                    "name_kr": r.name_kr,
                    "name_en": r.name_en,
                    "score": float(r.score),
                }
                for r in rows
            ]

    if not results and engine is not None:
        with engine.connect() as conn:
            all_rows = conn.execute(
                select(companies.c.id, companies.c.name_kr, companies.c.name_en)
            ).all()

        names = [_normalize(r.name_kr) for r in all_rows]
        matches = process.extract(norm_q, names, scorer=fuzz.ratio, limit=10)
        for _, score, idx in matches:
            row = all_rows[idx]
            results.append(
                {
                    "id": row.id,
                    "name_kr": row.name_kr,
                    "name_en": row.name_en,
                    "score": score / 100.0,
                }
            )

    if results:
        top_norm = _normalize(results[0]["name_kr"])
        if top_norm != norm_q:
            suggestion = results[0]["name_kr"]

    payload: Dict[str, Any] = {"results": results}
    if suggestion:
        payload["suggestion"] = suggestion
    return payload
