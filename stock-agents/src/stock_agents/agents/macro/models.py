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
    sectors: list[SectorPerf] = field(default_factory=list)

    # Inflacja (Biznesradar/GUS)
    cpi_value: float | None = None
    cpi_change_pct: float | None = None  # YoY %
    cpi_date: str = ""

    errors: list[str] = field(default_factory=list)
