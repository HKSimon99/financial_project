from __future__ import annotations
import numpy as np
import pandas as pd

# Safe extract (matches legacy semantics)

def extract_value(df: pd.DataFrame | None, account_name: str) -> float:
    if df is None or df.empty:
        return float("nan")
    row = df[df["account_nm"] == account_name]
    if row.empty:
        return float("nan")
    return float(pd.to_numeric(row.iloc[0].get("thstrm_amount"), errors="coerce"))


def calculate_custom_metrics(df_fs: pd.DataFrame | None, df_price: pd.DataFrame | None) -> dict:
    if df_fs is None or df_fs.empty:
        return {}
    m = {
        "revenue": extract_value(df_fs, "매출액"),
        "operating_income": extract_value(df_fs, "영업이익"),
        "net_income": extract_value(df_fs, "당기순이익"),
        "total_assets": extract_value(df_fs, "자산총계"),
        "total_liabilities": extract_value(df_fs, "부채총계"),
        "total_equity": extract_value(df_fs, "자본총계"),
    }
    if df_price is not None and not df_price.empty:
        m["latest_close_price"] = float(pd.to_numeric(df_price["close"].iloc[-1], errors="coerce"))
    return m


# Piotroski F-score

def calculate_piotroski_f_score(df_curr: pd.DataFrame | None, df_prev: pd.DataFrame | None) -> tuple[int, dict]:
    MAP = {
        "NI": "당기순이익", "CFO": "영업활동으로인한현금흐름",
        "TA": "자산총계", "TL": "부채총계",
        "CA": "유동자산", "CL": "유동부채",
        "REV": "매출액", "COGS": "매출원가",
        "SHARES": "유통주식수",
    }

    def v(df: pd.DataFrame | None, key: str) -> float:
        if df is None or df.empty:
            return float("nan")
        row = df[df["account_nm"] == MAP[key]]
        return float(pd.to_numeric(row["thstrm_amount"].iloc[0], errors="coerce")) if not row.empty else float("nan")

    if df_curr is None or df_prev is None:
        return 0, {}

    detail: dict[str, int] = {}
    roa_c = v(df_curr, "NI") / v(df_curr, "TA")
    detail["1. ROA > 0"] = int(roa_c > 0)
    cfo_c = v(df_curr, "CFO")
    detail["2. CFO > 0"] = int(cfo_c > 0)
    roa_p = v(df_prev, "NI") / v(df_prev, "TA")
    detail["3. ROA 증가"] = int(roa_c > roa_p)
    detail["4. CFO > NI"] = int(cfo_c > v(df_curr, "NI"))
    lev_c = v(df_curr, "TL") / v(df_curr, "TA")
    lev_p = v(df_prev, "TL") / v(df_prev, "TA")
    detail["5. 레버리지 비율 감소"] = int(lev_c < lev_p)
    cr_c = v(df_curr, "CA") / v(df_curr, "CL")
    cr_p = v(df_prev, "CA") / v(df_prev, "CL")
    detail["6. 유동비율 증가"] = int(cr_c > cr_p)
    detail["7. 신주발행 없음"] = int(v(df_curr, "SHARES") <= v(df_prev, "SHARES"))
    gm_c = (v(df_curr, "REV") - v(df_curr, "COGS")) / v(df_curr, "REV")
    gm_p = (v(df_prev, "REV") - v(df_prev, "COGS")) / v(df_prev, "REV")
    detail["8. 총이익률 증가"] = int(gm_c > gm_p)
    at_c = v(df_curr, "REV") / v(df_curr, "TA")
    at_p = v(df_prev, "REV") / v(df_prev, "TA")
    detail["9. 자산회전율 증가"] = int(at_c > at_p)

    return int(sum(detail.values())), detail