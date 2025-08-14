from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ANNUALIZATION_FACTOR = 252
DEFAULT_RISK_FREE_RATE = 0.02

# ----------------- helpers -----------------

def _annualized(mu_daily: np.ndarray, cov_daily: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return mu_daily * ANNUALIZATION_FACTOR, cov_daily * ANNUALIZATION_FACTOR

# API-safe version of legacy calculate_portfolio_performance

def calculate_portfolio_performance(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> tuple[float, float]:
    if not isinstance(weights, np.ndarray) or weights.ndim != 1 or len(weights) != len(mean_returns):
        return np.nan, np.nan
    if mean_returns.empty or cov_matrix.empty:
        return np.nan, np.nan
    try:
        mu_ann, cov_ann = _annualized(mean_returns.to_numpy(), cov_matrix.to_numpy())
        ret = float(np.sum(mu_ann * weights))
        vol = float(np.sqrt(weights.T @ cov_ann @ weights))
        return vol, ret
    except Exception:
        return np.nan, np.nan

# legacy-compatible negative Sharpe

def negative_sharpe_ratio(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame, risk_free_rate: float = DEFAULT_RISK_FREE_RATE) -> float:
    vol, ret = calculate_portfolio_performance(weights, mean_returns, cov_matrix)
    if np.isnan(vol) or vol == 0:
        return np.inf
    return -((ret - risk_free_rate) / vol)

# ----------------- optimizers -----------------

def optimize_portfolio(returns_df: pd.DataFrame, risk_free_rate: float = DEFAULT_RISK_FREE_RATE) -> dict:
    if returns_df is None or returns_df.empty:
        return {"weights": None, "annual_return": np.nan, "annual_volatility": np.nan, "sharpe_ratio": np.nan, "success": False}

    mean_returns = returns_df.mean()
    cov_matrix = returns_df.cov()
    n = len(mean_returns)

    constraints = ({"type": "eq", "fun": lambda x: np.sum(x) - 1})
    bounds = tuple((0.0, 1.0) for _ in range(n))  # long-only
    x0 = np.full(n, 1.0 / n)

    res = minimize(
        negative_sharpe_ratio,
        x0,
        args=(mean_returns, cov_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 100, "ftol": 1e-9},
    )

    if not res.success:
        return {"weights": None, "annual_return": np.nan, "annual_volatility": np.nan, "sharpe_ratio": np.nan, "success": False}

    w = np.asarray(res.x, dtype=float)
    vol, ret = calculate_portfolio_performance(w, mean_returns, cov_matrix)
    sharpe = float((ret - risk_free_rate) / vol) if vol else np.nan

    return {
        "weights": w,
        "annual_return": ret,
        "annual_volatility": vol,
        "sharpe_ratio": sharpe,
        "success": True,
    }

# ----------------- backtest -----------------

def backtest_portfolio(price_data: pd.DataFrame, weights: np.ndarray) -> dict:
    if price_data is None or price_data.empty or weights is None or len(weights) == 0:
        return {"cumulative_returns": pd.Series(dtype=float), "annual_return": np.nan, "annual_volatility": np.nan, "sharpe_ratio": np.nan, "max_drawdown": np.nan}

    price = price_data.sort_index().ffill().bfill()
    rets = price.pct_change().dropna()
    if rets.empty or len(weights) != rets.shape[1]:
        return {"cumulative_returns": pd.Series(dtype=float), "annual_return": np.nan, "annual_volatility": np.nan, "sharpe_ratio": np.nan, "max_drawdown": np.nan}

    port_rets = (rets * weights).sum(axis=1)
    cum = (1.0 + port_rets).cumprod()

    ann_ret = float(cum.iloc[-1] ** (ANNUALIZATION_FACTOR / len(rets)) - 1.0) if len(rets) else np.nan
    ann_vol = float(port_rets.std() * np.sqrt(ANNUALIZATION_FACTOR)) if len(rets) else np.nan
    sharpe = float((ann_ret - DEFAULT_RISK_FREE_RATE) / ann_vol) if ann_vol else np.nan

    peak = cum.expanding(min_periods=1).max()
    dd = (cum - peak) / peak
    mdd = float(dd.min()) if not dd.empty else np.nan

    return {"cumulative_returns": cum, "annual_return": ann_ret, "annual_volatility": ann_vol, "sharpe_ratio": sharpe, "max_drawdown": mdd}