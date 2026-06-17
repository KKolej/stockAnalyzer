"""Wykrywanie poziomów wsparcia i oporu z wykresu.

Łączy trzy podejścia:
  1. Poziome strefy S/R z lokalnych szczytów/dołków (swing high/low) + klastrowanie
  2. Klasyczne punkty pivot (z ostatniej sesji)
  3. Zniesienia Fibonacciego od ostatniego istotnego ruchu

Wszystkie wyniki to struktury JSON-friendly (dict/list) — używane przez printer i API.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

Level = dict[str, Any]

# Parametry domyślne
SWING_WINDOW = 3          # ile świec po obu stronach musi być niższych/wyższych
CLUSTER_ATR_MULT = 0.6    # strefy bliższe niż 0.6×ATR są łączone
NEAR_ATR_MULT = 0.5       # "cena przy poziomie" gdy dystans < 0.5×ATR
FIB_LOOKBACK = 120        # zakres świec do wyznaczenia ruchu dla Fibonacciego
FIB_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


def _last_atr(df: pd.DataFrame) -> float | None:
    if "ATR_14" in df.columns:
        atr = df["ATR_14"].iloc[-1]
        if atr is not None and not pd.isna(atr) and atr > 0:
            return float(atr)
    # Fallback: średni zakres dzienny z ostatnich 14 świec
    if {"High", "Low"}.issubset(df.columns) and len(df) >= 14:
        rng = (df["High"] - df["Low"]).tail(14).mean()
        if rng and not pd.isna(rng) and rng > 0:
            return float(rng)
    return None


def find_swings(df: pd.DataFrame, window: int = SWING_WINDOW) -> list[Level]:
    """Lokalne szczyty (High to maksimum w oknie ±window) i dołki (Low to minimum)."""
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
    """Łączy bliskie swingi (≤ tolerance) w strefy. Każda strefa ma liczbę dotknięć."""
    if not swings or tolerance <= 0:
        return []
    ordered = sorted(swings, key=lambda s: s["price"])
    clusters: list[list[Level]] = [[ordered[0]]]
    for sw in ordered[1:]:
        # przypisz do bieżącego klastra jeśli blisko jego średniej
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
    """Klasyczne punkty pivot z ostatniej zamkniętej sesji."""
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
    """Zniesienia Fibonacciego od ostatniego istotnego ruchu (swing low ↔ high)."""
    window = df.tail(lookback)
    if len(window) < 5:
        return None
    high = window["High"].max()
    low = window["Low"].min()
    if pd.isna(high) or pd.isna(low) or high <= low:
        return None
    hi_pos = int(window["High"].to_numpy().argmax())
    lo_pos = int(window["Low"].to_numpy().argmin())
    # Kierunek ruchu: jeśli szczyt powstał po dołku → trend wzrostowy (zniesienia w dół)
    direction = "up" if hi_pos > lo_pos else "down"
    high, low = float(high), float(low)
    span = high - low
    levels: dict[str, float] = {}
    for r in FIB_RATIOS:
        # up: 0% = high, 100% = low (poziomy wsparcia poniżej szczytu)
        # down: 0% = low, 100% = high (poziomy oporu powyżej dołka)
        level = high - span * r if direction == "up" else low + span * r
        levels[f"{r:.3f}"] = round(level, 4)
    return {"direction": direction, "high": round(high, 4), "low": round(low, 4), "levels": levels}


def _annotate(level: Level, price: float, atr: float | None, kind: str) -> Level:
    dist_pct = round((level["price"] - price) / price * 100, 2) if price else None
    dist_atr = round((level["price"] - price) / atr, 2) if atr else None
    return {**level, "kind": kind, "dist_pct": dist_pct, "dist_atr": dist_atr}


def analyze_support_resistance(df: pd.DataFrame, window: int = SWING_WINDOW) -> dict[str, Any]:
    """Zwraca pełną analizę S/R: strefy poziome, najbliższe wsparcie/opór, pivoty, Fibo."""
    price = float(df["Close"].iloc[-1])
    atr = _last_atr(df)
    tolerance = (atr * CLUSTER_ATR_MULT) if atr else (price * 0.01)

    swings = find_swings(df, window)
    raw_levels = cluster_levels(swings, tolerance)

    # podział wg pozycji względem ceny + adnotacja dystansu
    support = [_annotate(lv, price, atr, "support") for lv in raw_levels if lv["price"] < price]
    resistance = [_annotate(lv, price, atr, "resistance") for lv in raw_levels if lv["price"] >= price]

    # najbliższe: wsparcie tuż pod ceną, opór tuż nad
    nearest_support = max(support, key=lambda z: z["price"]) if support else None
    nearest_resistance = min(resistance, key=lambda z: z["price"]) if resistance else None

    # sortuj strefy do prezentacji: najmocniejsze (najwięcej dotknięć) najpierw
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
