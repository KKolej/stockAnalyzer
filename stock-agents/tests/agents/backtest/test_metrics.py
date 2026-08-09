from __future__ import annotations

import numpy as np
import pandas as pd

from stock_agents.agents.backtest.metrics import (
    MIN_SAMPLE,
    forward_returns,
    summarize,
    verdict,
)


def test_forward_return_is_measured_forward_not_backward() -> None:
    close = pd.Series([100.0, 110.0, 121.0])
    fwd = forward_returns(close, 1)
    # From day 0 the next close is 110 -> +10%. The last row has no future and must be NaN.
    assert round(float(fwd.iloc[0]), 4) == 0.1
    assert pd.isna(fwd.iloc[-1])


def test_edge_is_relative_to_baseline_not_to_fifty_percent() -> None:
    """A signal that fires on ordinary days has no edge, even with a high hit rate."""
    # Series rising on every single day: any signal shows a 100% hit rate.
    close = pd.Series(np.linspace(100, 200, 300))
    fwd = forward_returns(close, 5)
    events = pd.Series(False, index=close.index)
    events.iloc[50:150] = True

    stats = summarize(events, fwd, 5)
    assert stats is not None
    assert stats["hit_rate_pct"] == 100.0
    # ...but holding gave the same thing, so the edge is nil.
    assert stats["baseline_hit_rate_pct"] == 100.0
    assert stats["edge_pp"] == 0.0
    assert abs(stats["excess_return_pct"]) < 0.5


def test_real_edge_is_detected() -> None:
    rng = np.random.default_rng(7)
    steps = rng.normal(0.0, 0.005, 600)
    events = pd.Series(False, index=pd.RangeIndex(600))
    # Every 25th day a jump follows, so those days genuinely carry information.
    for i in range(50, 550, 25):
        steps[i + 1] += 0.05
        events.iloc[i] = True
    close = pd.Series(100 * np.exp(np.cumsum(steps)))

    stats = summarize(events, forward_returns(close, 5), 5)
    assert stats is not None
    assert stats["sample_size"] >= MIN_SAMPLE
    assert stats["excess_return_pct"] > 3.0
    assert stats["reliable"] is True


def test_overlapping_windows_shrink_the_sample() -> None:
    close = pd.Series(np.linspace(100, 130, 400))
    events = pd.Series(True, index=close.index)
    stats = summarize(events, forward_returns(close, 21), 21)
    assert stats is not None
    # Firing every single day: 21-day windows overlap almost completely, so the
    # independent count collapses to roughly one per horizon.
    assert abs(stats["effective_sample"] - stats["sample_size"] // 21) <= 1
    assert stats["effective_sample"] < stats["sample_size"] / 10


def test_events_spread_out_are_counted_as_independent() -> None:
    """Rare signals must not be punished for the horizon being long."""
    close = pd.Series(np.linspace(100, 300, 1500))
    events = pd.Series(False, index=close.index)
    for i in range(100, 1300, 100):          # co 100 sesji, horyzont 21 -> bez nakładania
        events.iloc[i] = True
    stats = summarize(events, forward_returns(close, 21), 21)
    assert stats is not None
    assert stats["effective_sample"] == stats["sample_size"]


def test_thin_sample_never_gets_a_verdict() -> None:
    close = pd.Series(np.linspace(100, 160, 200))
    events = pd.Series(False, index=close.index)
    events.iloc[10] = True
    events.iloc[20] = True
    stats = summarize(events, forward_returns(close, 5), 5)
    assert stats is not None
    assert stats["sample_size"] == 2
    assert stats["reliable"] is False
    assert "za mało" in verdict(stats, "bullish")


def test_signal_working_in_reverse_is_named() -> None:
    stats = {
        "sample_size": 40,
        "excess_return_pct": -4.0,
        "t_stat": -3.1,
        "reliable": True,
    }
    assert "ODWROTNIE" in verdict(stats, "bullish")
    assert "potwierdzony" in verdict(stats, "bearish")


def test_signal_that_never_fired_returns_nothing() -> None:
    close = pd.Series(np.linspace(100, 110, 100))
    events = pd.Series(False, index=close.index)
    assert summarize(events, forward_returns(close, 5), 5) is None


def test_unmeasurable_significance_is_not_reported_as_no_edge() -> None:
    """Long horizon + few events = too few independent windows; that is not 'no edge'."""
    close = pd.Series(np.linspace(100, 200, 400))
    events = pd.Series(False, index=close.index)
    for i in range(100, 146, 2):             # 23 zdarzenia stłoczone w 46 sesji
        events.iloc[i] = True
    stats = summarize(events, forward_returns(close, 63), 63)
    assert stats is not None
    assert stats["sample_size"] >= MIN_SAMPLE
    assert stats["effective_sample"] == 1
    assert stats["t_stat"] is None
    assert "niezależnych okien" in verdict(stats, "bullish")
