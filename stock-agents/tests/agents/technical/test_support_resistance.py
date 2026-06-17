import numpy as np
import pandas as pd

from stock_agents.agents.technical.signals import support_resistance_signal
from stock_agents.agents.technical.support_resistance import (
    analyze_support_resistance,
    cluster_levels,
    fibonacci,
    find_swings,
    pivot_points,
)


def _df_from_closes(closes: list[float]) -> pd.DataFrame:
    """Buduje OHLC z listy zamknięć (High/Low = ±0.5 wokół Close), stały ATR."""
    closes_arr = np.array(closes, dtype=float)
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=len(closes)),
        "Open": closes_arr,
        "High": closes_arr + 0.5,
        "Low": closes_arr - 0.5,
        "Close": closes_arr,
        "Volume": np.full(len(closes), 1000.0),
        "ATR_14": np.full(len(closes), 1.0),
    })


def test_find_swings_detects_peak_and_trough():
    # wyraźny szczyt na idx 3, dołek na idx 7
    df = _df_from_closes([10, 11, 12, 15, 12, 11, 10, 7, 9, 10, 11])
    swings = find_swings(df, window=2)
    highs = [s["price"] for s in swings if s["type"] == "high"]
    lows = [s["price"] for s in swings if s["type"] == "low"]
    assert max(highs) == 15.5  # 15 + 0.5
    assert min(lows) == 6.5    # 7 - 0.5


def test_cluster_merges_close_levels_and_counts_touches():
    swings = [
        {"idx": 1, "price": 100.0, "type": "high"},
        {"idx": 5, "price": 100.3, "type": "low"},
        {"idx": 9, "price": 100.1, "type": "high"},
        {"idx": 12, "price": 110.0, "type": "high"},
    ]
    levels = cluster_levels(swings, tolerance=1.0)
    assert len(levels) == 2
    strong = max(levels, key=lambda lv: lv["touches"])
    assert strong["touches"] == 3
    assert abs(strong["price"] - 100.13) < 0.1


def test_pivot_points_classic_formula():
    df = _df_from_closes([10] * 5)
    # ostatnia świeca: High=10.5, Low=9.5, Close=10 → PP=10, R1=10.5, S1=9.5
    piv = pivot_points(df)
    assert piv["pp"] == 10.0
    assert piv["r1"] == 10.5
    assert piv["s1"] == 9.5


def test_fibonacci_uptrend_direction_and_levels():
    # rosnący ciąg → dołek przed szczytem → trend "up"
    df = _df_from_closes(list(range(10, 40)))
    fib = fibonacci(df, lookback=30)
    assert fib["direction"] == "up"
    # 0% = high, 100% = low
    assert fib["levels"]["0.000"] == fib["high"]
    assert fib["levels"]["1.000"] == fib["low"]
    # 50% pomiędzy
    assert fib["low"] < fib["levels"]["0.500"] < fib["high"]


def test_analyze_splits_support_below_resistance_above():
    df = _df_from_closes([10, 14, 10, 14, 10, 14, 10, 14, 12])  # cena 12 w środku
    sr = analyze_support_resistance(df, window=1)
    assert sr["nearest_support"] is None or sr["nearest_support"]["price"] < sr["price"]
    assert sr["nearest_resistance"] is None or sr["nearest_resistance"]["price"] >= sr["price"]


def test_sr_signal_bullish_near_support():
    sr = {
        "price": 100.2, "atr": 1.0,
        "nearest_support": {"price": 100.0, "touches": 3},
        "nearest_resistance": {"price": 110.0, "touches": 2},
    }
    sig = support_resistance_signal(sr)
    assert sig is not None
    assert sig["signal"] == "BULLISH"
    assert sig["strength"] == "strong"


def test_sr_signal_none_when_price_far_from_levels():
    sr = {
        "price": 105.0, "atr": 1.0,
        "nearest_support": {"price": 100.0, "touches": 3},
        "nearest_resistance": {"price": 110.0, "touches": 2},
    }
    assert support_resistance_signal(sr) is None
