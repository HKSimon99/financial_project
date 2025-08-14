from __future__ import annotations
import logging
from typing import Dict, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# -----------------------------
# Internal helpers
# -----------------------------

def _coerce_number(value: Any) -> float:
    """Convert DART numeric strings like "1,234" → float, else NaN."""
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return np.nan
        s = str(value).replace(",", "").strip()
        if s == "" or s.lower() == "nan":
            return np.nan
        return float(s)
    except Exception:
        return np.nan


def _get_account_value(fs_df: pd.DataFrame, account_name: str) -> float:
    """Safely extract `thstrm_amount` for an exact account name from DART FS df."""
    if fs_df is None or fs_df.empty:
        return np.nan
    if "account_nm" not in fs_df.columns:
        return np.nan
    try:
        row = fs_df[fs_df["account_nm"] == account_name]
        if row.empty:
            return np.nan
        value = row.iloc[0].get("thstrm_amount")
        return _coerce_number(value)
    except Exception:
        return np.nan


# -----------------------------
# Public API (pure functions)
# -----------------------------

def dcf_intrinsic_price(*, fcf0: float, growth: float, wacc: float, terminal_g: float, shares: float) -> float:
    """5Y DCF + Gordon terminal; returns price per share."""
    years = np.arange(1, 6)
    fcfs = fcf0 * (1.0 + growth) ** years
    pv_fcfs = (fcfs / (1.0 + wacc) ** years).sum()
    terminal_value = (fcfs[-1] * (1.0 + terminal_g)) / (wacc - terminal_g)
    pv_terminal = terminal_value / (1.0 + wacc) ** 5
    equity_value = pv_fcfs + pv_terminal
    return float(equity_value / shares) if shares else float("nan")


def rim_intrinsic_price(*, bps: float, roe: float, cost_of_equity: float, growth: float, years: int, shares: float) -> float:
    """Residual Income Model with BV compounding, returns price per share."""
    bv = float(bps)
    residuals: list[float] = []
    for t in range(years):
        ni = bv * roe
        bv = bv + ni - (bv * growth)  # retain earnings; simplistic payout modelling
        ri = ni - (cost_of_equity * bv)
        residuals.append(ri)
    pv_residuals = sum(ri / (1.0 + cost_of_equity) ** (i + 1) for i, ri in enumerate(residuals))
    intrinsic = bps + pv_residuals
    return float(intrinsic / shares) if shares else float("nan")


def calculate_financial_health(fs_df: pd.DataFrame) -> Dict[str, float | str]:
    """Compute debt/current ratios, ROE, op margin, interest coverage, Z-score-ish, score & grade."""
    if fs_df is None or fs_df.empty:
        return {
            "debt_ratio": np.nan, "current_ratio": np.nan, "roe": np.nan, "op_margin": np.nan,
            "interest_coverage": np.nan, "z_score": np.nan, "total_score": np.nan, "grade": "N/A"
        }

    total_assets = _get_account_value(fs_df, "자산총계")
    total_liabilities = _get_account_value(fs_df, "부채총계")
    equity = _get_account_value(fs_df, "자본총계")
    current_assets = _get_account_value(fs_df, "유동자산")
    current_liabilities = _get_account_value(fs_df, "유동부채")
    revenue = _get_account_value(fs_df, "매출액")
    operating_income = _get_account_value(fs_df, "영업이익")
    net_income = _get_account_value(fs_df, "당기순이익")
    interest_expense = _get_account_value(fs_df, "이자비용")

    debt_ratio = (total_liabilities / equity) * 100.0 if equity else np.nan
    current_ratio = (current_assets / current_liabilities) * 100.0 if current_liabilities else np.nan
    roe = (net_income / equity) * 100.0 if equity else np.nan
    op_margin = (operating_income / revenue) * 100.0 if revenue else np.nan
    interest_coverage = (operating_income / interest_expense) if interest_expense else np.nan

    def safe_div(a: float, b: float) -> float:
        return a / b if (a is not None and b not in (None, 0, np.nan)) else np.nan

    wca = safe_div(current_assets - current_liabilities, total_assets)
    rea = safe_div(equity, total_assets)
    eita = safe_div(operating_income, total_assets)
    mvel = safe_div(equity, total_liabilities)
    sta = safe_div(revenue, total_assets)

    parts = [wca, rea, eita, mvel, sta]
    z_score = (
        (1.2 * (0.0 if np.isnan(wca) else wca)) +
        (1.4 * (0.0 if np.isnan(rea) else rea)) +
        (3.3 * (0.0 if np.isnan(eita) else eita)) +
        (0.6 * (0.0 if np.isnan(mvel) else mvel)) +
        (1.0 * (0.0 if np.isnan(sta) else sta))
    ) if not all(np.isnan(x) for x in parts) else np.nan

    scores = {
        "debt_ratio": max(0.0, min(100.0, 100.0 - (debt_ratio if not np.isnan(debt_ratio) else 100.0))),
        "current_ratio": max(0.0, min(100.0, (current_ratio if not np.isnan(current_ratio) else 0.0))),
        "roe": max(0.0, min(100.0, (roe if not np.isnan(roe) else 0.0))),
        "op_margin": max(0.0, min(100.0, (op_margin if not np.isnan(op_margin) else 0.0))),
        "interest_coverage": max(0.0, min(100.0, ((interest_coverage * 10.0) if not np.isnan(interest_coverage) else 0.0))),
        "z_score": max(0.0, min(100.0, ((z_score * 20.0) if not np.isnan(z_score) else 0.0))),
    }

    total_score = (
        (scores["debt_ratio"] * 0.2) + (scores["current_ratio"] * 0.2) + (scores["roe"] * 0.2) +
        (scores["op_margin"] * 0.15) + (scores["interest_coverage"] * 0.15) + (scores["z_score"] * 0.1)
    ) if not all(np.isnan(v) for v in scores.values()) else np.nan

    if np.isnan(total_score):
        grade = "N/A"
    elif total_score >= 80.0:
        grade = "A"
    elif total_score >= 60.0:
        grade = "B"
    else:
        grade = "C"

    return {
        "debt_ratio": float(debt_ratio) if not np.isnan(debt_ratio) else np.nan,
        "current_ratio": float(current_ratio) if not np.isnan(current_ratio) else np.nan,
        "roe": float(roe) if not np.isnan(roe) else np.nan,
        "op_margin": float(op_margin) if not np.isnan(op_margin) else np.nan,
        "interest_coverage": float(interest_coverage) if not np.isnan(interest_coverage) else np.nan,
        "z_score": float(z_score) if not np.isnan(z_score) else np.nan,
        "total_score": float(total_score) if not np.isnan(total_score) else np.nan,
        "grade": grade,
    }


def calculate_custom_ratios(fs_df: pd.DataFrame, price_df: pd.DataFrame) -> Dict[str, float]:
    """Compute PER, PBR, dividend yield from FS + latest price."""
    if fs_df is None or fs_df.empty or price_df is None or price_df.empty:
        return {"PER": np.nan, "PBR": np.nan, "배당수익률(%)": np.nan}

    latest = price_df["close"].dropna()
    latest_price = float(latest.iloc[-1]) if not latest.empty else np.nan
    if np.isnan(latest_price):
        return {"PER": np.nan, "PBR": np.nan, "배당수익률(%)": np.nan}

    shares_outstanding = _get_account_value(fs_df, "발행주식수")
    net_income = _get_account_value(fs_df, "당기순이익")
    total_equity = _get_account_value(fs_df, "자본총계")
    dividends = _get_account_value(fs_df, "배당금총액")

    market_cap = latest_price * shares_outstanding if (not np.isnan(latest_price) and not np.isnan(shares_outstanding)) else np.nan
    per = (market_cap / net_income) if (not np.isnan(market_cap) and not np.isnan(net_income) and net_income != 0) else np.nan
    pbr = (market_cap / total_equity) if (not np.isnan(market_cap) and not np.isnan(total_equity) and total_equity != 0) else np.nan
    dy = ((dividends / market_cap) * 100.0) if (not np.isnan(market_cap) and not np.isnan(dividends) and market_cap != 0) else np.nan

    return {
        "PER": round(float(per), 2) if not np.isnan(per) else np.nan,
        "PBR": round(float(pbr), 2) if not np.isnan(pbr) else np.nan,
        "배당수익률(%)": round(float(dy), 2) if not np.isnan(dy) else np.nan,
    }


def compare_by_industry(df: pd.DataFrame) -> pd.DataFrame:
    """Return simple mean of numeric columns grouped by '업종'."""
    if df is None or df.empty or "업종" not in df.columns:
        return pd.DataFrame()
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if "업종" in numeric_cols:
        numeric_cols.remove("업종")
    if not numeric_cols:
        return pd.DataFrame()
    return df.groupby("업종")[numeric_cols].mean()


def extract_fs_summary(fs_df: pd.DataFrame) -> Dict[str, float]:
    """Pick a few headline FS metrics for a card view."""
    if fs_df is None or fs_df.empty:
        return {"매출액": np.nan, "영업이익": np.nan, "당기순이익": np.nan, "총자산": np.nan, "총부채": np.nan, "자본총계": np.nan}

    def pick(key: str) -> float:
        # use exact match first; fallback to contains
        v = _get_account_value(fs_df, key)
        if np.isnan(v):
            try:
                row = fs_df[fs_df["account_nm"].str.contains(key, na=False, regex=False)]
                if not row.empty:
                    return _coerce_number(row.iloc[0].get("thstrm_amount"))
            except Exception:
                pass
        return v

    return {
        "매출액": pick("매출액"),
        "영업이익": pick("영업이익"),
        "당기순이익": pick("당기순이익"),
        "총자산": pick("자산총계"),
        "총부채": pick("부채총계"),
        "자본총계": pick("자본총계"),
    }