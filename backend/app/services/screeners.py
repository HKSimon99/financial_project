from __future__ import annotations

import json
from pathlib import Path
from typing import List, Any

from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import Session, aliased

from ..models import Company, MetricAggregate

RECIPES_FILE = Path("seeds/screeners.json")
if RECIPES_FILE.exists():
    with RECIPES_FILE.open() as f:
        RECIPES = {r["id"]: r for r in json.load(f)}
else:
    RECIPES = {}

_OP_MAP = {
    ">": lambda c, v: c > v,
    ">=": lambda c, v: c >= v,
    "<": lambda c, v: c < v,
    "<=": lambda c, v: c <= v,
    "==": lambda c, v: c == v,
}


def run_screener(
    db: Session,
    rules: List[dict],
    sort_by: str | None = None,
    sort_desc: bool = False,
    limit: int = 50,
):
    query = db.query(Company)
    aliases: dict[str, Any] = {}

    for rule in rules:
        name = rule["metric"]
        alias = aliases.get(name)
        if not alias:
            alias = aliased(MetricAggregate)
            aliases[name] = alias
            query = query.join(
                alias, and_(alias.company_id == Company.id, alias.name == name)
            )
        query = query.filter(_OP_MAP[rule["op"]](alias.value, rule["value"]))

    if sort_by:
        alias = aliases.get(sort_by)
        if not alias:
            alias = aliased(MetricAggregate)
            query = query.join(
                alias, and_(alias.company_id == Company.id, alias.name == sort_by)
            )
        order = desc if sort_desc else asc
        query = query.order_by(order(alias.value))

    return query.limit(limit).all()
