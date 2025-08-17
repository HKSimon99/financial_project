from __future__ import annotations

from pathlib import Path
import json
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

WATCHLIST_FILE = Path("data/watchlist.json")
STARTER_FILE = Path("seeds/starter_watchlists.json")


def _read_watchlist() -> List[str]:
    if WATCHLIST_FILE.exists():
        with WATCHLIST_FILE.open() as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    return data


def _save_watchlist(items: List[str]) -> None:
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with WATCHLIST_FILE.open("w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _read_starters() -> list[dict]:
    if not STARTER_FILE.exists():
        raise HTTPException(status_code=500, detail="starter watchlists not found")
    with STARTER_FILE.open() as f:
        return json.load(f)


class WatchItem(BaseModel):
    symbol: str


class ApplyIn(BaseModel):
    starter_id: str


@router.get("/", response_model=List[str])
async def list_watchlist() -> List[str]:
    """Return the current user watchlist."""
    return _read_watchlist()


@router.post("/", response_model=List[str])
async def add_watchlist(item: WatchItem) -> List[str]:
    """Add a symbol to the watchlist."""
    data = _read_watchlist()
    if item.symbol not in data:
        data.append(item.symbol)
        _save_watchlist(data)
    return data


@router.delete("/{symbol}", response_model=List[str])
async def remove_watchlist(symbol: str) -> List[str]:
    """Remove a symbol from the watchlist."""
    data = _read_watchlist()
    if symbol not in data:
        raise HTTPException(status_code=404, detail="symbol not found")
    data.remove(symbol)
    _save_watchlist(data)
    return data


@router.get("/starter")
async def starter_watchlists() -> list[dict]:
    """Return predefined starter watchlists."""
    return _read_starters()


@router.post("/apply", response_model=List[str])
async def apply_starter(body: ApplyIn) -> List[str]:
    """Clone a starter watchlist into the user's watchlist."""
    starters = _read_starters()
    selected = next((s for s in starters if s.get("id") == body.starter_id), None)
    if not selected:
        raise HTTPException(status_code=404, detail="starter not found")
    symbols = selected.get("symbols", [])
    _save_watchlist(symbols)
    return symbols
