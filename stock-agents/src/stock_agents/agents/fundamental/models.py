from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class YearlyRecord:
    year: str
    revenue: float | None = None
    net_income: float | None = None
    ebitda: float | None = None
    operating_income: float | None = None
    eps: float | None = None
    roe: float | None = None
    profit_margin: float | None = None
    operating_cf: float | None = None
    capex: float | None = None

    @property
    def free_cash_flow(self) -> float | None:
        if self.operating_cf is not None and self.capex is not None:
            return self.operating_cf - self.capex
        return None


@dataclass
class FundamentalData:
    ticker: str
    company: str
    currency: str

    # Wycena
    price: float | None
    market_cap: float | None
    pe_trailing: float | None
    pe_forward: float | None
    pb: float | None
    ev_ebitda: float | None
    ps_ratio: float | None

    # Wyniki bieżące
    revenue: float | None
    ebitda: float | None
    eps: float | None
    profit_margin: float | None
    operating_margin: float | None
    roe: float | None
    roa: float | None
    roic: float | None

    # Zdrowie finansowe
    current_ratio: float | None
    quick_ratio: float | None
    debt_to_equity: float | None
    net_debt_ebitda: float | None
    interest_coverage: float | None    # EBIT / Interest Expense

    # Przepływy pieniężne
    fcf_ttm: float | None              # Free Cash Flow TTM
    fcf_yield: float | None            # FCF / Market Cap
    ev_fcf: float | None               # EV / FCF

    # Dywidenda
    dividend_yield: float | None
    payout_ratio: float | None
    dividend_cagr: float | None        # roczny wzrost dywidendy (5L)

    # Inne
    beta: float | None
    week_52_high: float | None
    week_52_low: float | None
    book_value: float | None

    # Historia (ostatnie 5 lat, od najnowszego)
    history: list[YearlyRecord] = field(default_factory=list)

    # Sektor (z yfinance)
    sector: str = ""

    # DuPont decomposition (ROE = marża × rotacja aktywów × dźwignia)
    dupont_margin: float | None = None         # marża netto
    dupont_asset_turnover: float | None = None # przychody / aktywa
    dupont_leverage: float | None = None       # aktywa / kapitał własny

    # Price to Cash Flow
    price_to_cf: float | None = None           # cena / CFO na akcję

    # Scoring (obliczane z danych finansowych)
    piotroski_score: int | None = None          # 0–9 (lub mniej jeśli brak danych)
    piotroski_max: int | None = None            # max możliwy wynik (brakujące kryteria obniżają)
    graham_number: float | None = None          # sqrt(22.5 × EPS × BVPS)
    altman_z: float | None = None               # Z'' score
    peg_ratio: float | None = None              # P/E / CAGR zysku

    error: str | None = None
