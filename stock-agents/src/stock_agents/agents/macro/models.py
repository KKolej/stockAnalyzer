from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class FxRate:
    code: str            # USD, EUR, CHF, GBP
    name: str
    rate: float          # PLN za 1 jednostkę
    date: str
    change_3m: float | None = None   # % zmiana za 3M


@dataclass
class SectorPerf:
    name: str            # np. "Banki"
    symbol: str          # np. "WIG-BANKI.WA"
    price: float
    change_1d: float     # % zmiana 1D
    pos_52w: float | None = None  # pozycja w zakresie 52W (0-100%)
    low_52w: float | None = None
    high_52w: float | None = None
    # Skąd zakres 52W: "biznesradar" (wiarygodne) albo None gdy nie udało się pobrać.
    # yfinance dla indeksów PL podaje zakres jednodniowy jako "52-tygodniowy" —
    # dlatego NIE używamy go tutaj w ogóle.
    pos_52w_source: str | None = None


@dataclass
class MacroData:
    as_of: date

    # Waluty (NBP)
    fx: list[FxRate] = field(default_factory=list)
    gold_pln: float | None = None
    gold_date: str = ""

    # Giełda
    wig20_price: float | None = None
    wig20_change_1d: float | None = None
    wig20_pos_52w: float | None = None
    wig20_low_52w: float | None = None
    wig20_high_52w: float | None = None
    wig20_pos_52w_source: str | None = None
    sectors: list[SectorPerf] = field(default_factory=list)

    # Inflacja (Biznesradar/GUS)
    cpi_value: float | None = None
    cpi_change_pct: float | None = None  # YoY %
    # Zmiana odczytu r/r wobec poprzedniego miesiąca, w punktach procentowych.
    # Bez tego pola nie da się odróżnić inflacji stabilnej od rosnącej.
    cpi_change_pp: float | None = None
    cpi_mom_pct: float | None = None      # inflacja m/m w %
    cpi_date: str = ""

    errors: list[str] = field(default_factory=list)
