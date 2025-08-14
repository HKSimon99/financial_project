from __future__ import annotations
import os, json
from datetime import datetime, timedelta
import pandas as pd
from typing import Any

BASE = os.getenv("CORE_CACHE_DIR", os.path.join("data", "cache"))

def path(*parts: str) -> str:
    p = os.path.join(BASE, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def fresh(p: str, days: int = 1) -> bool:
    if not os.path.exists(p):
        return False
    mt = datetime.fromtimestamp(os.path.getmtime(p))
    return (datetime.now() - mt) < timedelta(days=days)

# JSON helpers

def save_json(obj: Any, p: str) -> None:
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(p: str) -> Any | None:
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# Parquet helpers

def save_parquet(df: pd.DataFrame, p: str) -> None:
    df.to_parquet(p, index=False)

def load_parquet(p: str) -> pd.DataFrame | None:
    try:
        return pd.read_parquet(p)
    except Exception:
        return None