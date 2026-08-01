"""Risk and return metrics from a price series (professional standard).

Annualised volatility, max drawdown, Sharpe, Sortino, beta against a benchmark
and return statistics. A pure function — no network access.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

TRADING_DAYS = 252
DEFAULT_RISK_FREE = 0.045  # annual risk-free rate (approximation)


def _daily_returns(close: pd.Series) -> pd.Series:
    return close.astype(float).pct_change().dropna()


def max_drawdown(close: pd.Series) -> dict[str, float] | None:
    """Largest peak-to-trough drawdown and the current drawdown from the peak."""
    c = close.astype(float).dropna()
    if len(c) < 2:
        return None
    running_max = c.cummax()
    drawdown = c / running_max - 1.0
    mdd = float(drawdown.min())
    current = float(drawdown.iloc[-1])
    return {"max_drawdown": round(mdd, 4), "current_drawdown": round(current, 4)}


def _to_naive_dates(idx: pd.Index) -> pd.Index:
    out = pd.to_datetime(idx)
    if getattr(out, "tz", None) is not None:
        out = out.tz_localize(None)
    return out.normalize()


def beta(stock_close: pd.Series, benchmark_close: pd.Series) -> float | None:
    """Beta = cov(stock, benchmark) / var(benchmark) over shared dates."""
    s = _daily_returns(stock_close)
    b = _daily_returns(benchmark_close)
    # align on date when the series are time-indexed (different zones/hours)
    if isinstance(s.index, pd.DatetimeIndex):
        s.index = _to_naive_dates(s.index)
    if isinstance(b.index, pd.DatetimeIndex):
        b.index = _to_naive_dates(b.index)
    joined = pd.concat([s, b], axis=1, join="inner").dropna()
    if len(joined) < 20:
        return None
    sv = joined.iloc[:, 0].to_numpy()
    bv = joined.iloc[:, 1].to_numpy()
    # consistent ddof=1 for cov and var (otherwise beta of an identical series != 1)
    var_b = float(np.var(bv, ddof=1))
    if var_b <= 0:
        return None
    cov = float(np.cov(sv, bv)[0, 1])
    return round(cov / var_b, 3)


def compute_risk_metrics(
    df: pd.DataFrame,
    benchmark_close: pd.Series | None = None,
    risk_free: float = DEFAULT_RISK_FREE,
    periods_per_year: int = TRADING_DAYS,
) -> dict[str, Any]:
    """Returns the full set of risk/return metrics for the Close series in df."""
    close = df["Close"].astype(float).dropna()
    out: dict[str, Any] = {
        "period_days": int(len(close)),
        "ann_volatility": None,
        "total_return": None,
        "cagr": None,
        "sharpe": None,
        "sortino": None,
        "max_drawdown": None,
        "current_drawdown": None,
        "best_day": None,
        "worst_day": None,
        "positive_days_pct": None,
        "beta": None,
    }
    if len(close) < 20:
        return out

    rets = _daily_returns(close)
    if rets.empty:
        return out

    ann_vol = float(rets.std(ddof=1) * np.sqrt(periods_per_year))
    ann_return = float(rets.mean() * periods_per_year)

    total_return = float(close.iloc[-1] / close.iloc[0] - 1.0)
    years = len(close) / periods_per_year
    cagr = float((close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1.0) if years > 0 else None

    out["ann_volatility"] = round(ann_vol, 4)
    out["total_return"] = round(total_return, 4)
    out["cagr"] = round(cagr, 4) if cagr is not None else None

    if ann_vol > 0:
        out["sharpe"] = round((ann_return - risk_free) / ann_vol, 2)

    downside = rets[rets < 0]
    if len(downside) >= 2:
        downside_dev = float(downside.std(ddof=1) * np.sqrt(periods_per_year))
        if downside_dev > 0:
            out["sortino"] = round((ann_return - risk_free) / downside_dev, 2)

    mdd = max_drawdown(close)
    if mdd:
        out["max_drawdown"] = mdd["max_drawdown"]
        out["current_drawdown"] = mdd["current_drawdown"]

    out["best_day"] = round(float(rets.max()), 4)
    out["worst_day"] = round(float(rets.min()), 4)
    out["positive_days_pct"] = round(float((rets > 0).mean()), 4)

    if benchmark_close is not None:
        # share price indexed by date — for aligning with the benchmark
        if "Date" in df.columns:
            dated = df[["Date", "Close"]].dropna()
            stock_dated = pd.Series(
                dated["Close"].to_numpy(dtype=float),
                index=pd.to_datetime(dated["Date"]),
            )
        else:
            stock_dated = close
        out["beta"] = beta(stock_dated, benchmark_close)

    return out
