from __future__ import annotations

from datetime import date

from .models import Catalyst, PatternResult, Projection

_HORIZONS = [
    ("1 tydzień",    7),
    ("1 miesiąc",   30),
    ("2 miesiące",  60),
]


def _relevant_patterns(patterns: list[PatternResult], horizon_days: int) -> list[PatternResult]:
    return [p for p in patterns if p.horizon_days <= horizon_days * 1.5]


def _weighted_direction(patterns: list[PatternResult]) -> tuple[float, float]:
    """Zwraca (bull_score, bear_score) ważone siłą sygnału."""
    weights = {"strong": 3, "medium": 2, "weak": 1}
    bull, bear = 0.0, 0.0
    for p in patterns:
        w = weights.get(p.strength, 1)
        if p.direction == "UP":
            bull += w * p.probability
        elif p.direction == "DOWN":
            bear += w * p.probability
    return bull, bear


def _estimate_return_range(
    patterns: list[PatternResult],
    direction: str,
    catalysts: list[Catalyst],
    horizon_days: int,
) -> tuple[float, float]:
    """Szacuje zakres zwrotu (low, high) na podstawie wzorców."""
    relevant = [p for p in patterns if p.direction == direction and p.avg_return is not None]
    if not relevant:
        base = 0.02 if direction == "UP" else -0.03
        return (base * 0.5, base * 1.5) if direction == "UP" else (base * 1.5, base * 0.5)

    returns = [abs(p.avg_return) for p in relevant]
    avg_abs = sum(returns) / len(returns)
    sign = 1 if direction == "UP" else -1

    # Skaluj do horyzontu
    scale = min(horizon_days / 30, 1.5)
    low = sign * avg_abs * 0.5 * scale
    high = sign * avg_abs * 1.5 * scale
    if direction == "UP":
        return (min(low, high), max(low, high))
    return (min(low, high), max(low, high))


def _catalyst_note(catalysts: list[Catalyst], horizon_days: int) -> str:
    upcoming = [c for c in catalysts if 0 <= c.days_away <= horizon_days]
    if not upcoming:
        return ""
    return ", ".join(f"{c.name} za {c.days_away}d" for c in upcoming)


def build_projections(
    patterns: list[PatternResult],
    catalysts: list[Catalyst],
) -> list[Projection]:
    projections = []

    for label, days in _HORIZONS:
        relevant = _relevant_patterns(patterns, days)
        if not relevant:
            continue

        bull, bear = _weighted_direction(relevant)
        total = bull + bear
        if total == 0:
            direction = "NEUTRAL"
            prob = 0.5
        elif bull > bear:
            direction = "UP"
            prob = min(bull / total, 0.82)
        else:
            direction = "DOWN"
            prob = min(bear / total, 0.82)

        ret_low, ret_high = _estimate_return_range(relevant, direction, catalysts, days)
        cat_note = _catalyst_note(catalysts, days)

        reasoning_parts = []
        top = sorted(relevant, key=lambda p: p.probability, reverse=True)[:2]
        for p in top:
            reasoning_parts.append(p.name)
        if cat_note:
            reasoning_parts.append(cat_note)
        reasoning = " + ".join(reasoning_parts)

        projections.append(Projection(
            horizon_label=label,
            horizon_days=days,
            direction=direction,
            return_low=ret_low,
            return_high=ret_high,
            probability=prob,
            reasoning=reasoning,
        ))

    return projections
