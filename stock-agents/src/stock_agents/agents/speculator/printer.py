from __future__ import annotations

from datetime import date

from .models import Catalyst, PatternResult, Projection, SpeculatorData

SEPARATOR = "=" * 72
ICON_DIR = {"UP": "▲", "DOWN": "▼", "NEUTRAL": "─"}
ICON_CAT = {"Ex-dywidenda": "💰", "Raport wynikowy": "📊"}


def _pct(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v*100:.1f}%"


def _prob(v: float) -> str:
    return f"{v*100:.0f}%"


def _days_label(days: int) -> str:
    if days < 0:
        return f"{abs(days)} dni temu"
    if days == 0:
        return "dziś"
    return f"za {days} dni"


def _section(title: str) -> None:
    print(f"\n  ▸ {title}")
    print(f"  {'─' * 50}")


def _print_catalyst(c: Catalyst) -> None:
    icon = ICON_CAT.get(c.name, "📅")
    days_str = _days_label(c.days_away)
    print(f"  {icon}  {c.name:<20} {str(c.event_date)}  ({days_str})")


def _print_pattern(p: PatternResult) -> None:
    icon = ICON_DIR.get(p.direction, "─")
    strength_str = p.strength.upper()
    prob_str = _prob(p.probability)
    sample_str = f"n={p.sample_size}" if p.sample_size > 1 else ""
    avg_str = f"  avg {_pct(p.avg_return)}" if p.avg_return is not None else ""
    print(f"  {icon} [{strength_str:<6}] [{prob_str:>4} szansy] {p.note}{avg_str}  {sample_str}")


def _print_projection(proj: Projection) -> None:
    icon = ICON_DIR.get(proj.direction, "─")
    direction_pl = {"UP": "WZROST", "DOWN": "SPADEK", "NEUTRAL": "NEUTRAL"}[proj.direction]

    if proj.direction == "UP":
        range_str = f"{_pct(proj.return_low)} do {_pct(proj.return_high)}"
    elif proj.direction == "DOWN":
        range_str = f"{_pct(proj.return_low)} do {_pct(proj.return_high)}"
    else:
        range_str = "bez wyraźnego kierunku"

    prob_str = _prob(proj.probability)
    print(f"  {icon}  {proj.horizon_label:<14} {direction_pl:<8}  {range_str:<20}  [{prob_str} szansy]")
    if proj.reasoning:
        print(f"              oparty na: {proj.reasoning}")


def print_speculator(data: SpeculatorData) -> None:
    print(SEPARATOR)

    if data.error:
        print(f"  SPEKULANT: {data.ticker.upper()} — {data.error}")
        print(SEPARATOR)
        print()
        return

    print(f"  SPEKULANT: {data.ticker.upper()} — {data.company}")
    print(f"  Cena: {data.current_price:.2f} {data.currency}   Horyzont: 1 tydzień – 2 miesiące")
    print(SEPARATOR)

    if data.catalysts:
        _section("KATALYZATORY")
        for c in data.catalysts:
            _print_catalyst(c)

    if data.patterns:
        _section("WZORCE HISTORYCZNE")
        up_patterns = [p for p in data.patterns if p.direction == "UP"]
        down_patterns = [p for p in data.patterns if p.direction == "DOWN"]
        neutral_patterns = [p for p in data.patterns if p.direction == "NEUTRAL"]

        for p in sorted(up_patterns, key=lambda x: x.probability, reverse=True):
            _print_pattern(p)
        for p in sorted(down_patterns, key=lambda x: x.probability, reverse=True):
            _print_pattern(p)
        for p in neutral_patterns:
            _print_pattern(p)
    else:
        print("\n  Brak wzorców — niewystarczające dane historyczne.")

    if data.projections:
        _section("PROJEKCJA")
        for proj in data.projections:
            _print_projection(proj)

    print()
    print(SEPARATOR)
    print()
