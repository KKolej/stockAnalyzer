"""Forward-return statistics for a signal — the numbers that say whether to trust it.

Three decisions here carry the credibility of the whole module:

1. **Everything is measured AGAINST A BASELINE.** A hit rate of 58% sounds like an edge
   until you notice the stock rose on 57% of all days in that period. What is reported
   is the difference against holding blindly over the same horizon, not the raw number.

2. **Overlapping windows are discounted — by counting, not by dividing.** Events three
   days apart share almost the same 21-day forward window, so 60 such observations are
   nowhere near 60 independent ones. The effective sample is the largest subset of events
   spaced at least `horizon` sessions apart. Dividing n by the horizon (the obvious
   shortcut) punishes the opposite case: 22 RSI crossings spread over seven years ARE
   independent, and the shortcut would have collapsed them to one.

3. **A verdict is refused when the sample is thin.** Below `MIN_SAMPLE` events the answer
   is "za mało danych", not a percentage — a hit rate off six events is noise with a
   decimal point.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

# Below this many events the statistics are reported but never called reliable.
MIN_SAMPLE = 20
# |t| above this is treated as "unlikely to be noise" (~5% two-sided for a normal).
T_SIGNIFICANT = 2.0


def _independent_count(mask: pd.Series, horizon: int) -> int:
    """Largest subset of events spaced at least `horizon` sessions apart.

    Greedy from the left, which is optimal for this kind of interval selection.
    """
    last: int | None = None
    count = 0
    for position, fired in enumerate(mask.tolist()):
        if not fired:
            continue
        if last is None or position - last >= horizon:
            count += 1
            last = position
    return max(count, 1)


def forward_returns(close: pd.Series, horizon: int) -> pd.Series:
    """Return from the close of day t to the close of day t+horizon."""
    return close.shift(-horizon) / close - 1.0


def _pct(value: float) -> float:
    return round(float(value) * 100.0, 2)


def summarize(
    events: pd.Series,
    fwd: pd.Series,
    horizon: int,
) -> dict[str, Any] | None:
    """Statistics for one signal on one horizon, or None when the signal never fired."""
    usable = events.fillna(False).astype(bool) & fwd.notna()
    sample = fwd[usable]
    n = int(sample.shape[0])
    if n == 0:
        return None

    # The baseline is every day of the same window: "what would holding have given".
    baseline = fwd.dropna()
    base_mean = float(baseline.mean()) if not baseline.empty else 0.0
    base_hit = float((baseline > 0).mean()) if not baseline.empty else 0.0

    mean_ret = float(sample.mean())
    hit_rate = float((sample > 0).mean())

    effective_n = _independent_count(usable, horizon)
    std = float(sample.std(ddof=1)) if n > 1 else 0.0
    t_stat: float | None = None
    if std > 0 and effective_n > 1:
        t_stat = (mean_ret - base_mean) / (std / math.sqrt(effective_n))

    reliable = n >= MIN_SAMPLE and t_stat is not None and abs(t_stat) >= T_SIGNIFICANT

    return {
        "horizon_days": horizon,
        "sample_size": n,
        "effective_sample": effective_n,
        "hit_rate_pct": _pct(hit_rate),
        "baseline_hit_rate_pct": _pct(base_hit),
        "edge_pp": round(_pct(hit_rate) - _pct(base_hit), 2),
        "mean_return_pct": _pct(mean_ret),
        "median_return_pct": _pct(float(sample.median())),
        "baseline_mean_return_pct": _pct(base_mean),
        "excess_return_pct": round(_pct(mean_ret) - _pct(base_mean), 2),
        "worst_return_pct": _pct(float(sample.min())),
        "best_return_pct": _pct(float(sample.max())),
        "t_stat": round(t_stat, 2) if t_stat is not None else None,
        "reliable": reliable,
    }


def verdict(stats: dict[str, Any], direction: str) -> str:
    """One-line reading of the numbers — including "works the other way round"."""
    if stats["sample_size"] < MIN_SAMPLE:
        return f"za mało zdarzeń ({stats['sample_size']}) — nie wyciągaj wniosków"
    # "Nie dało się policzyć" to nie to samo co "policzone i wyszło zero" — przy długim
    # horyzoncie okna tak mocno na siebie nachodzą, że niezależnych obserwacji jest kilka.
    if stats["t_stat"] is None:
        return (
            f"za mało niezależnych okien ({stats['effective_sample']} przy {stats['sample_size']} "
            f"zdarzeniach) — istotności nie da się ocenić"
        )
    excess = stats["excess_return_pct"]
    expected_up = direction == "bullish"
    if not stats["reliable"]:
        return f"bez przewagi ponad szum (t={stats['t_stat']}, próba {stats['sample_size']})"
    if (excess > 0) == expected_up:
        return f"potwierdzony: {excess:+.2f} p.p. ponad zwykły ruch, próba {stats['sample_size']}"
    return (
        f"DZIAŁAŁ ODWROTNIE niż podręcznikowo: {excess:+.2f} p.p. ponad zwykły ruch, "
        f"próba {stats['sample_size']}"
    )
