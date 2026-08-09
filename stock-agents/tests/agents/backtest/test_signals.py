from __future__ import annotations

import numpy as np
import pandas as pd

from stock_agents.agents.backtest.signals import RULES, _cross_above, _cross_below


def _frame(**cols: list[float]) -> pd.DataFrame:
    return pd.DataFrame(cols)


def test_crossing_fires_once_not_every_day_below_the_level() -> None:
    rsi = pd.Series([40.0, 35.0, 28.0, 25.0, 22.0, 31.0])
    fired = _cross_below(rsi, 30.0)
    # Only the day the level is broken counts; staying below is the same episode.
    assert fired.tolist() == [False, False, True, False, False, False]


def test_crossing_up_needs_the_previous_day_below() -> None:
    macd = pd.Series([-1.0, -0.5, 0.5, 1.0])
    sig = pd.Series([0.0, 0.0, 0.0, 0.0])
    assert _cross_above(macd, sig).tolist() == [False, False, True, False]


def test_volume_spike_ignores_its_own_day_in_the_average() -> None:
    rule = next(r for r in RULES if r.key == "volume_spike_up")
    close = [100.0] * 24 + [101.0]
    volume = [1000.0] * 24 + [5000.0]
    fired = rule.detect(_frame(Close=close, Volume=volume))
    # The spike day itself must not lift the baseline it is compared against.
    assert bool(fired.iloc[-1]) is True
    assert not fired.iloc[:-1].any()


def test_rules_survive_missing_columns() -> None:
    """A ticker without ADX or volume must not blow up the whole backtest."""
    bare = _frame(Close=list(np.linspace(100, 120, 60)))
    for rule in RULES:
        fired = rule.detect(bare)
        assert len(fired) == len(bare)
        assert fired.dtype == bool or fired.isna().all() or set(fired.dropna().unique()) <= {True, False}


def test_52w_high_compares_against_history_not_including_today() -> None:
    rule = next(r for r in RULES if r.key == "new_52w_high")
    close = [100.0] * 252 + [150.0]
    fired = rule.detect(_frame(Close=close))
    assert bool(fired.iloc[-1]) is True


def test_every_rule_has_a_stable_key_and_polish_note() -> None:
    keys = [r.key for r in RULES]
    assert len(keys) == len(set(keys))
    for rule in RULES:
        assert rule.direction in {"bullish", "bearish"}
        assert rule.note and rule.note[0].isupper()
