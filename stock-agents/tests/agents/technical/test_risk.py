import numpy as np
import pandas as pd

from stock_agents.agents.technical.risk import (
    beta,
    compute_risk_metrics,
    max_drawdown,
)


def _df(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=len(closes)),
        "Close": np.array(closes, dtype=float),
    })


def test_max_drawdown_simple():
    # szczyt 100 → dołek 60 = -40%
    mdd = max_drawdown(pd.Series([50.0, 100.0, 80.0, 60.0, 70.0]))
    assert mdd is not None
    assert mdd["max_drawdown"] == -0.4
    # bieżące obsunięcie: 70 vs szczyt 100 = -30%
    assert mdd["current_drawdown"] == -0.3


def test_total_return_and_volatility_positive():
    closes = list(np.linspace(100, 150, 60))  # stały wzrost
    r = compute_risk_metrics(_df(closes))
    assert r["total_return"] == round(150 / 100 - 1, 4)
    assert r["ann_volatility"] is not None and r["ann_volatility"] >= 0
    assert r["positive_days_pct"] == 1.0  # zawsze rośnie


def test_short_series_returns_nulls():
    r = compute_risk_metrics(_df([100.0, 101.0, 102.0]))
    assert r["period_days"] == 3
    assert r["sharpe"] is None
    assert r["ann_volatility"] is None


def test_beta_of_identical_series_is_one():
    s = pd.Series(np.linspace(100, 130, 50) + np.sin(np.arange(50)))
    b = beta(s, s)
    assert b is not None
    assert abs(b - 1.0) < 1e-6


def test_beta_zero_when_benchmark_flat():
    s = pd.Series(np.linspace(100, 130, 50))
    flat = pd.Series([100.0] * 50)
    assert beta(s, flat) is None  # wariancja benchmarku = 0


def test_sharpe_present_for_long_volatile_series():
    rng = np.random.default_rng(42)
    closes = 100 * np.cumprod(1 + rng.normal(0.001, 0.02, 200))
    r = compute_risk_metrics(_df(list(closes)))
    assert r["sharpe"] is not None
    assert r["max_drawdown"] is not None and r["max_drawdown"] <= 0
