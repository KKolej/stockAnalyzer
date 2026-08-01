from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class FxRate:
    code: str            # USD, EUR, CHF, GBP
    name: str
    rate: float          # PLN per 1 unit
    date: str
    change_3m: float | None = None   # % change over 3M


@dataclass
class SectorPerf:
    name: str            # e.g. "Banki"
    symbol: str          # e.g. "WIG-BANKI.WA"
    price: float
    change_1d: float     # % change 1D
    pos_52w: float | None = None  # position within the 52W range (0-100%)
    low_52w: float | None = None
    high_52w: float | None = None
    # Source of the 52W range: "biznesradar" (trustworthy) or None when the fetch failed.
    # For Polish indices yfinance reports a single-day range as the "52-week" one —
    # which is why we do not use it here at all.
    pos_52w_source: str | None = None


@dataclass
class MacroData:
    as_of: date

    # Currencies (NBP)
    fx: list[FxRate] = field(default_factory=list)
    gold_pln: float | None = None
    gold_date: str = ""

    # Exchange
    wig20_price: float | None = None
    wig20_change_1d: float | None = None
    wig20_pos_52w: float | None = None
    wig20_low_52w: float | None = None
    wig20_high_52w: float | None = None
    wig20_pos_52w_source: str | None = None
    sectors: list[SectorPerf] = field(default_factory=list)

    # Inflation (Biznesradar/GUS)
    cpi_value: float | None = None
    cpi_change_pct: float | None = None  # YoY %
    # Change of the YoY reading against the previous month, in percentage points.
    # Without this field there is no way to tell stable inflation from rising inflation.
    cpi_change_pp: float | None = None
    cpi_mom_pct: float | None = None      # month-over-month inflation in %
    cpi_date: str = ""

    errors: list[str] = field(default_factory=list)
