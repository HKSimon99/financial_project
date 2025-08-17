from __future__ import annotations
import pandas as pd
import asyncio
from core.clients.kis import KISClient
from core.clients.dart import DARTClient
from core.utils.cache import path, fresh, save_parquet, load_parquet
from core.schemas.financials import FinancialStatement, FSRow


# ------------------
# KIS: daily price
# ------------------
async def kis_daily_price(
    kis: KISClient, stock_code: str, start_date: str, end_date: str
) -> pd.DataFrame:
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    cache_file = path(
        "prices", stock_code, f"kis_{start_dt:%Y%m%d}_{end_dt:%Y%m%d}.parquet"
    )
    if fresh(cache_file, days=1):
        cached = load_parquet(cache_file)
        if cached is not None:
            return cached

    data = await kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        tr_id="FHKST01010400",
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": f"{start_dt:%Y%m%d}",
            "FID_INPUT_DATE_2": f"{end_dt:%Y%m%d}",
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "1",
        },
    )

    df = pd.DataFrame(data.get("output", []))
    if df.empty:
        return df

    df = df.rename(
        columns={
            "stck_bsop_date": "date",
            "stck_oprc": "open",
            "stck_hgpr": "high",
            "stck_lwpr": "low",
            "stck_clpr": "close",
            "acml_vol": "volume",
            "acml_tr_pbmn": "transaction_amount",
            "prdy_vrss": "change",
        }
    )

    cols = [
        c
        for c in [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "transaction_amount",
            "change",
        ]
        if c in df.columns
    ]
    for c in cols:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
    df = df[cols].sort_values("date").reset_index(drop=True)
    save_parquet(df, cache_file)
    return df


# ------------------
# DART: financials
# ------------------
REPORTS = [
    ("11011", "사업보고서"),
    ("11014", "3분기보고서"),
    ("11012", "반기보고서"),
    ("11013", "1분기보고서"),
]
FSDIVS = [("CFS", "연결"), ("OFS", "별도")]


async def dart_financials(
    dart: DARTClient, corp_code: str, year: int
) -> FinancialStatement | None:
    """Return the first available FS for (corp_code, year) with a friendly report name.
    Caches raw rows as parquet for 7 days.
    """
    for rp_code, rp_name in REPORTS:
        for fs_div, fs_name in FSDIVS:
            cache_file = path(
                "financials", corp_code, f"{year}_{rp_code}_{fs_div}.parquet"
            )
            if fresh(cache_file, days=7):
                cached = load_parquet(cache_file)
                if cached is not None:
                    return FinancialStatement(
                        corp_code=corp_code,
                        year=year,
                        report_name=f"{rp_name} - {fs_name}",
                        rows=[FSRow(**r) for r in cached.to_dict(orient="records")],
                    )

            data = await dart.single_fs(corp_code, year, rp_code, fs_div)
            if data.get("status") == "000" and data.get("list"):
                df = pd.DataFrame(data["list"])  # store raw
                save_parquet(df, cache_file)
                return FinancialStatement(
                    corp_code=corp_code,
                    year=year,
                    report_name=f"{rp_name} - {fs_name}",
                    rows=[FSRow(**r) for r in data["list"]],
                )
    return None


async def kis_prices_panel(
    kis: KISClient, stock_codes: list[str], start_date: str, end_date: str
) -> pd.DataFrame:
    async def one(code: str) -> pd.Series:
        df = await kis_daily_price(kis, code, start_date, end_date)
        if df is None or df.empty:
            return pd.Series(name=code, dtype=float)
        s = df.set_index("date")["close"].astype(float)
        s.index = pd.to_datetime(s.index)
        s.name = code
        return s

    series_list = await asyncio.gather(*[one(c) for c in stock_codes])
    panel = pd.concat(series_list, axis=1).sort_index()
    returns = panel.pct_change().dropna(how="all")
    return returns


async def kis_financial_ratios(kis: KISClient, stock_code: str) -> pd.DataFrame:
    data = await kis.get(
        "/uapi/domestic-stock/v1/finance/financial-ratio",
        tr_id="FHKST66430300",
        params={
            "fid_div_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        },
    )
    df = pd.DataFrame(data.get("output", []))
    if df.empty:
        return df
    cols = {
        "stac_yymm": "결산년월",
        "grs_rt": "매출총이익률",
        "bsop_prfi_inrt": "영업이익률",
        "thtr_ntin_inrt": "당기순이익률",
        "roe_val": "ROE",
        "eps": "EPS",
        "bps": "BPS",
        "pbr": "PBR",
        "dvd_yd_rt": "배당수익률",
    }
    df = df[[k for k in cols if k in df.columns]].rename(columns=cols)
    for c in df.columns:
        if c != "결산년월":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


async def kis_investment_opinion(kis: KISClient, stock_code: str) -> dict:
    data = await kis.get(
        "/uapi/domestic-stock/v1/quotations/invest-opinion",
        tr_id="FHKST663300C0",
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "16633",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": pd.Timestamp.today().strftime("%Y0101"),
            "FID_INPUT_DATE_2": pd.Timestamp.today().strftime("%Y%m%d"),
        },
    )
    out = (data.get("output") or [{}])[0]
    return {
        "opinion": out.get("invt_opnn"),
        "target_price": float(out.get("hts_goal_prc") or 0.0),
        "analyst_count": int(out.get("nm_of_analyst") or 0),
    }
