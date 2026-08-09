"""Reliability backtest — how a signal actually behaved on this stock's history.

The point of this agent is what every other agent lacks: a signal shipped WITH its
track record. `/technical` says "RSI 28, wyprzedanie"; this says that on this ticker
the same event was followed by +1.8 p.p. over the market's own drift across 34 cases,
or that it did nothing at all. The LLM consuming the API can then weigh signals instead
of treating them as equally true.

Deliberately NOT a price predictor. It answers "co się działo po tym sygnale
historycznie", never "ile będzie kosztować za tydzień".
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from stock_agents.agents.backtest.metrics import MIN_SAMPLE, forward_returns, summarize, verdict
from stock_agents.agents.backtest.signals import RULES
from stock_agents.agents.technical.fetcher import FetchError, data_staleness, fetch_ohlcv
from stock_agents.agents.technical.indicators import add_all_indicators

# ~1 week, 2 weeks, 1 month, 3 months of sessions — the horizons the daily review uses.
DEFAULT_HORIZONS: tuple[int, ...] = (5, 10, 21, 63)
# A signal that last fired this long ago is no longer "active" for today's decision.
ACTIVE_WINDOW_SESSIONS = 5
# 252 sessions ≈ a year; the 52-week rules need a full year before they can fire at all.
MIN_SESSIONS = 300

CAVEATS = (
    "Wyniki liczone na jednej spółce i jednym okresie — to nie jest dowód, że sygnał "
    "działa gdzie indziej ani że zadziała dalej.",
    "Okna zwrotów nachodzą na siebie; istotność liczona na próbie efektywnej "
    "(liczba zdarzeń / horyzont), a nie na wszystkich zdarzeniach.",
    "Sprawdzanych jest kilkadziesiąt kombinacji sygnał × horyzont — przy takiej liczbie "
    "testów część wyników 'istotnych' to przypadek. Ufaj tym z dużą próbą.",
    "Zwroty bez kosztów transakcyjnych, podatku i poślizgu.",
    "Historia z yfinance jest skorygowana o splity i dywidendy (auto_adjust).",
)


def _sessions_since(events: pd.Series) -> int | None:
    fired = events.fillna(False).astype(bool)
    if not fired.any():
        return None
    positions = [i for i, v in enumerate(fired.tolist()) if v]
    return int(len(fired) - 1 - positions[-1])


def get_data(
    ticker: str,
    years: int = 5,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
) -> dict[str, Any]:
    try:
        df = fetch_ohlcv(ticker, days_back=int(years * 365) + 30)
    except FetchError as exc:
        return {"ticker": ticker.upper(), "error": str(exc)}

    sessions = int(df.shape[0])
    if sessions < MIN_SESSIONS:
        return {
            "ticker": ticker.upper(),
            "error": (
                f"Za krótka historia: {sessions} sesji, potrzeba co najmniej {MIN_SESSIONS}. "
                "Backtest na takiej próbie mówiłby więcej o szumie niż o spółce."
            ),
        }

    df = add_all_indicators(df)
    close = pd.to_numeric(df["Close"], errors="coerce")
    fwd_by_horizon = {h: forward_returns(close, h) for h in horizons}

    signals: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    for rule in RULES:
        events = rule.detect(df)
        total = int(events.fillna(False).astype(bool).sum())
        per_horizon = []
        for h in horizons:
            stats = summarize(events, fwd_by_horizon[h], h)
            if stats is None:
                continue
            stats["reading"] = verdict(stats, rule.direction)
            per_horizon.append(stats)
        if not per_horizon:
            continue

        ago = _sessions_since(events)
        entry = {
            "key": rule.key,
            "note": rule.note,
            "direction": rule.direction,
            "occurrences": total,
            "sessions_since_last": ago,
            "horizons": per_horizon,
        }
        signals.append(entry)
        if ago is not None and ago <= ACTIVE_WINDOW_SESSIONS:
            # Reliability of the horizon the daily review leans on most, so the consumer
            # does not have to dig through the table to see whether today's signal counts.
            best = max(per_horizon, key=lambda s: abs(s["excess_return_pct"]))
            active.append(
                {
                    "key": rule.key,
                    "note": rule.note,
                    "direction": rule.direction,
                    "sessions_ago": ago,
                    "reliable_on_any_horizon": any(s["reliable"] for s in per_horizon),
                    "strongest": {
                        "horizon_days": best["horizon_days"],
                        "excess_return_pct": best["excess_return_pct"],
                        "sample_size": best["sample_size"],
                        "reliable": best["reliable"],
                        "reading": best["reading"],
                    },
                }
            )

    # Ranking by measured edge, not by how the textbook describes the signal.
    ranked = [
        {
            "key": s["key"],
            "note": s["note"],
            "horizon_days": h["horizon_days"],
            "excess_return_pct": h["excess_return_pct"],
            "edge_pp": h["edge_pp"],
            "sample_size": h["sample_size"],
            "t_stat": h["t_stat"],
            "reading": h["reading"],
        }
        for s in signals
        for h in s["horizons"]
        if h["reliable"]
    ]
    ranked.sort(key=lambda r: abs(r["excess_return_pct"]), reverse=True)

    # `normalize_ohlcv` keeps Date as a column and resets the index, so dates are read
    # from the column — the index here is a plain RangeIndex.
    dates = pd.to_datetime(df["Date"], errors="coerce").dropna()
    return {
        "ticker": ticker.upper(),
        "is_backtested": True,
        "period": {
            "from": str(dates.min().date()) if not dates.empty else None,
            "to": str(dates.max().date()) if not dates.empty else None,
            "sessions": sessions,
            "years": round(sessions / 252.0, 2),
        },
        "horizons_days": list(horizons),
        "min_sample_for_verdict": MIN_SAMPLE,
        "signals": signals,
        "active_signals": active,
        "reliable_signals": ranked,
        "data_quality": data_staleness(df),
        "caveats": list(CAVEATS),
    }
