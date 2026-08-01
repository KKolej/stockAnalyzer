"""Detection of support and resistance levels from the chart.

Combines three approaches:
  1. Horizontal S/R zones from local peaks/troughs (swing high/low) plus clustering
  2. Classic pivot points (from the last session)
  3. Fibonacci retracements of the last significant move

All results are JSON-friendly structures (dict/list) — used by the printer and API.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

Level = dict[str, Any]

# Default parameters
SWING_WINDOW = 3          # how many candles on each side must be lower/higher
CLUSTER_ATR_MULT = 0.6    # zones closer than 0.6×ATR are merged
NEAR_ATR_MULT = 0.5       # "price at level" when the distance is < 0.5×ATR
FIB_LOOKBACK = 120        # candle range used to determine the move for Fibonacci
FIB_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


def _last_atr(df: pd.DataFrame) -> float | None:
    if "ATR_14" in df.columns:
        atr = df["ATR_14"].iloc[-1]
        if atr is not None and not pd.isna(atr) and atr > 0:
            return float(atr)
    # Fallback: average daily range of the last 14 candles
    if {"High", "Low"}.issubset(df.columns) and len(df) >= 14:
        rng = (df["High"] - df["Low"]).tail(14).mean()
        if rng and not pd.isna(rng) and rng > 0:
            return float(rng)
    return None


def find_swings(df: pd.DataFrame, window: int = SWING_WINDOW) -> list[Level]:
    """Local peaks (High is the max within a ±window) and troughs (Low is the min)."""
    highs = df["High"].to_numpy()
    lows = df["Low"].to_numpy()
    n = len(df)
    swings: list[Level] = []
    for i in range(window, n - window):
        hi = highs[i]
        lo = lows[i]
        if pd.isna(hi) or pd.isna(lo):
            continue
        left = slice(i - window, i)
        right = slice(i + 1, i + 1 + window)
        if hi >= highs[left].max() and hi >= highs[right].max():
            swings.append({"idx": i, "price": float(hi), "type": "high"})
        if lo <= lows[left].min() and lo <= lows[right].min():
            swings.append({"idx": i, "price": float(lo), "type": "low"})
    return swings


def cluster_levels(swings: list[Level], tolerance: float) -> list[Level]:
    """Merges nearby swings (<= tolerance) into zones. Each zone carries a touch count."""
    if not swings or tolerance <= 0:
        return []
    ordered = sorted(swings, key=lambda s: s["price"])
    clusters: list[list[Level]] = [[ordered[0]]]
    for sw in ordered[1:]:
        # assign to the current cluster when close to its mean
        current = clusters[-1]
        mean_price = sum(s["price"] for s in current) / len(current)
        if abs(sw["price"] - mean_price) <= tolerance:
            current.append(sw)
        else:
            clusters.append([sw])

    levels: list[Level] = []
    for cl in clusters:
        price = sum(s["price"] for s in cl) / len(cl)
        levels.append({
            "price": round(price, 4),
            "touches": len(cl),
            "last_idx": max(s["idx"] for s in cl),
        })
    return levels


def pivot_points(df: pd.DataFrame) -> Level | None:
    """Classic pivot points from the last closed session."""
    last = df.iloc[-1]
    high, low, close = last.get("High"), last.get("Low"), last.get("Close")
    if high is None or low is None or close is None:
        return None
    if pd.isna(high) or pd.isna(low) or pd.isna(close):
        return None
    high, low, close = float(high), float(low), float(close)
    pp = (high + low + close) / 3
    rng = high - low
    return {
        "pp": round(pp, 4),
        "r1": round(2 * pp - low, 4),
        "r2": round(pp + rng, 4),
        "s1": round(2 * pp - high, 4),
        "s2": round(pp - rng, 4),
    }


def fibonacci(df: pd.DataFrame, lookback: int = FIB_LOOKBACK) -> Level | None:
    """Fibonacci retracements of the last significant move (swing low <-> high)."""
    window = df.tail(lookback)
    if len(window) < 5:
        return None
    high = window["High"].max()
    low = window["Low"].min()
    if pd.isna(high) or pd.isna(low) or high <= low:
        return None
    hi_pos = int(window["High"].to_numpy().argmax())
    lo_pos = int(window["Low"].to_numpy().argmin())
    # Move direction: a peak formed after the trough -> uptrend (retracements downward)
    direction = "up" if hi_pos > lo_pos else "down"
    high, low = float(high), float(low)
    span = high - low
    levels: dict[str, float] = {}
    for r in FIB_RATIOS:
        # up: 0% = high, 100% = low (support levels below the peak)
        # down: 0% = low, 100% = high (resistance levels above the trough)
        level = high - span * r if direction == "up" else low + span * r
        levels[f"{r:.3f}"] = round(level, 4)
    return {"direction": direction, "high": round(high, 4), "low": round(low, 4), "levels": levels}


def _annotate(level: Level, price: float, atr: float | None, kind: str) -> Level:
    dist_pct = round((level["price"] - price) / price * 100, 2) if price else None
    dist_atr = round((level["price"] - price) / atr, 2) if atr else None
    return {**level, "kind": kind, "dist_pct": dist_pct, "dist_atr": dist_atr}


def analyze_support_resistance(df: pd.DataFrame, window: int = SWING_WINDOW) -> dict[str, Any]:
    """Returns the full S/R analysis: horizontal zones, nearest support/resistance, pivots, Fibo."""
    price = float(df["Close"].iloc[-1])
    atr = _last_atr(df)
    tolerance = (atr * CLUSTER_ATR_MULT) if atr else (price * 0.01)

    swings = find_swings(df, window)
    raw_levels = cluster_levels(swings, tolerance)

    # split by position relative to price plus a distance annotation
    support = [_annotate(lv, price, atr, "support") for lv in raw_levels if lv["price"] < price]
    resistance = [_annotate(lv, price, atr, "resistance") for lv in raw_levels if lv["price"] >= price]

    # nearest: support just below price, resistance just above
    nearest_support = max(support, key=lambda z: z["price"]) if support else None
    nearest_resistance = min(resistance, key=lambda z: z["price"]) if resistance else None

    # sort zones for display: strongest (most touches) first
    support.sort(key=lambda z: (-z["touches"], -z["price"]))
    resistance.sort(key=lambda z: (-z["touches"], z["price"]))

    return {
        "price": round(price, 4),
        "atr": round(atr, 4) if atr else None,
        "support": support,
        "resistance": resistance,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "pivots": pivot_points(df),
        "fibonacci": fibonacci(df),
    }
