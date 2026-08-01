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
    probability: float      # 0.0–1.0, obliczone z danych historycznych
    sample_size: int        # ile obserwacji
    avg_return: float | None  # średni zwrot w oknie
    horizon_days: int       # horyzont w dniach
    note: str
    # Katalizator, bez którego wzorzec nie ma triggera. Wzorce dywidendowe czy
    # pre-earnings drift opisują zachowanie WOKÓŁ zdarzenia — gdy zdarzenia nie
    # ma w horyzoncie, nie wolno nimi napędzać projekcji (CD Projekt nie płaci
    # dywidendy, a „Post-div +7.5%" i tak podbijał prognozę 2-miesięczną).
    requires_event: str | None = None
    event_days_away: int | None = None


@dataclass
class Projection:
    horizon_label: str      # "1 tydzień", "1 miesiąc", "2 miesiące"
    horizon_days: int
    direction: str          # "UP" | "DOWN" | "NEUTRAL"
    return_low: float       # dolny zakres zwrotu
    return_high: float      # górny zakres zwrotu
    # UWAGA: to zgodność ważonych sygnałów (0.5–0.82), NIE prawdopodobieństwo
    # zweryfikowane backtestem. Backtestu w systemie nie ma — stąd `is_backtested`.
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
