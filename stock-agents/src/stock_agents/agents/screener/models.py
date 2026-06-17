from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScreenerRow:
    ticker: str
    company: str
    price: float | None
    currency: str
    market_cap: float | None
    pe: float | None
    pb: float | None
    ps: float | None
    roe: float | None
    roa: float | None
    profit_margin: float | None
    dividend_yield: float | None
    debt_to_equity: float | None
    week_52_change: float | None
    beta: float | None
    fcf_yield: float | None = None
    interest_coverage: float | None = None
    # Magic Formula (Greenblatt)
    earnings_yield: float | None = None    # EBIT/EV ≈ 1/EV_EBITDA proxy
    sector: str | None = None       # do wykluczania finansów/utilities z Magic Formula
    magic_rank: int | None = None   # ranking Magic Formula (niższy = lepszy)
    error: str | None = None

    @property
    def available(self) -> bool:
        return self.error is None


@dataclass
class ScreenerFilters:
    pe_max: float | None = None
    pe_min: float | None = None
    pb_max: float | None = None
    roe_min: float | None = None
    roa_min: float | None = None
    margin_min: float | None = None
    div_min: float | None = None
    fcf_yield_min: float | None = None
    ic_min: float | None = None
    magic_formula: bool = False           # włącz ranking Magic Formula
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    debt_max: float | None = None
    beta_max: float | None = None
    sort_by: str = "pe"
    sort_asc: bool = True
    top: int | None = None
