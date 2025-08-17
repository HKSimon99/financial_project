from __future__ import annotations
import io
import zipfile
import pandas as pd
import httpx
from fastapi import HTTPException
from core.utils.cache import path, fresh, save_parquet, load_parquet


async def corp_table(api_key: str) -> pd.DataFrame:
    """
    Fetch DART corpCode.zip (XML inside) safely.
    - Requires api_key (do NOT read env here).
    - Falls back to cached parquet if DART returns non-zip payloads.
    """
    cache_file = path("corp_codes", "corp_code_list.parquet")
    if fresh(cache_file, days=1):
        df = load_parquet(cache_file)
        if df is not None:
            return df

    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    async with httpx.AsyncClient(timeout=25) as c:
        r = await c.get(url)
        r.raise_for_status()

        # Guard: DART sometimes returns text (error) with 200
        ctype = (r.headers.get("Content-Type") or "").lower()
        is_zipish = "zip" in ctype or r.content[:2] == b"PK"
        if not is_zipish:
            # Fallback to cache if any
            cached = load_parquet(cache_file)
            if cached is not None:
                return cached
            snippet = r.text[:200].replace("\n", " ")
            raise HTTPException(
                status_code=502,
                detail=f"DART corpCode not zip; response hint: {snippet}",
            )

        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                with z.open("CORPCODE.xml") as f:
                    import xml.etree.ElementTree as ET

                    tree = ET.parse(f)
        except zipfile.BadZipFile as e:
            cached = load_parquet(cache_file)
            if cached is not None:
                return cached
            raise HTTPException(status_code=502, detail=f"DART zip parse failed: {e}")

    root = tree.getroot()
    rows = []
    for e in root.findall("list"):
        stock = (e.findtext("stock_code") or "").strip()
        if not stock:
            continue
        rows.append((e.findtext("corp_code"), e.findtext("corp_name"), stock))
    df = pd.DataFrame(rows, columns=["corp_code", "corp_name", "stock_code"])
    df["stock_code"] = df["stock_code"].astype(str).str.zfill(6)
    save_parquet(df, cache_file)
    return df


async def company_info_by_stock(stock_code: str, api_key: str) -> dict | None:
    df = await corp_table(api_key)
    row = df[df["stock_code"] == stock_code]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "corp_name": r["corp_name"],
        "corp_code": r["corp_code"],
        "stock_code": r["stock_code"],
    }
