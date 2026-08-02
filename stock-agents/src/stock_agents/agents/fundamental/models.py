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

    # Current results
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

    # Cash flows
    fcf_ttm: float | None              # Free Cash Flow TTM
    fcf_yield: float | None            # FCF / Market Cap
    ev_fcf: float | None               # EV / FCF

    # Dywidenda
    dividend_yield: float | None
    payout_ratio: float | None
    dividend_cagr: float | None        # annual dividend growth (5Y)

    # Inne
    beta: float | None
    week_52_high: float | None
    week_52_low: float | None
    book_value: float | None

    # History (last 5 years, newest first)
    history: list[YearlyRecord] = field(default_factory=list)

    # Where the valuation ratios come from — lets the consumer see that P/E and P/B
    # were recomputed on our price instead of Biznesradar's own (often stale) quote.
    quality: dict[str, object] = field(default_factory=dict)

    # Sector (from yfinance)
    sector: str = ""

    # DuPont decomposition (ROE = margin × asset turnover × leverage)
    dupont_margin: float | None = None         # net margin
    dupont_asset_turnover: float | None = None # przychody / aktywa
    dupont_leverage: float | None = None       # assets / equity

    # Price to Cash Flow
    price_to_cf: float | None = None           # price / CFO per share

    # Scoring (computed from financial data)
    piotroski_score: int | None = None          # criteria met, out of `piotroski_max`
    piotroski_max: int | None = None            # criteria actually checked (missing data lowers it)
    # Canonical F-Score scale. Published without it, "6/7" reads like a broken 0-9 score;
    # what it means is 6 of the 7 criteria we could evaluate, 2 having no data.
    piotroski_scale: int | None = None
    graham_number: float | None = None          # sqrt(22.5 × EPS × BVPS)
    altman_z: float | None = None               # Z'' score
    peg_ratio: float | None = None              # P/E / CAGR zysku

    error: str | None = None
