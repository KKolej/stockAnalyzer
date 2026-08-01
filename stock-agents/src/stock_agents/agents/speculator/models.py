from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Catalyst:
    name: str
    event_date: date
    days_away: int
    description: str


@dataclass
class PatternResult:
    name: str
    direction: str          # "UP" | "DOWN" | "NEUTRAL"
    strength: str           # "strong" | "medium" | "weak"
    probability: float      # 0.0-1.0, computed from historical data
    sample_size: int        # number of observations
    avg_return: float | None  # average return within the window
    horizon_days: int       # horizon in days
    note: str
    # Catalyst without which the pattern has no trigger. Dividend patterns and
    # pre-earnings drift describe behaviour AROUND an event — when the event is not
    # within the horizon they must not drive projections (CD Projekt pays no
    # dividend, yet "Post-div +7.5%" still inflated the 2-month forecast).
    requires_event: str | None = None
    event_days_away: int | None = None


@dataclass
class Projection:
    horizon_label: str      # "1 tydzień", "1 miesiąc", "2 miesiące"
    horizon_days: int
    direction: str          # "UP" | "DOWN" | "NEUTRAL"
    return_low: float       # dolny zakres zwrotu
    return_high: float      # upper bound of the return range
    # CAUTION: this is weighted signal agreement (0.5-0.82), NOT a probability
    # verified by a backtest. There is no backtest in the system — hence `is_backtested`.
    probability: float
    reasoning: str
    is_backtested: bool = False


@dataclass
class SpeculatorData:
    ticker: str
    company: str
    current_price: float
    currency: str
    catalysts: list[Catalyst] = field(default_factory=list)
    patterns: list[PatternResult] = field(default_factory=list)
    projections: list[Projection] = field(default_factory=list)
    error: str | None = None
