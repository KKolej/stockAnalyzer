"""Pydantic response models — the JSON contract for the endpoints (visible in /docs).

The models are permissive (optional fields, `extra="allow"`) so agent development
does not drop data, while still documenting the contract for consumers (n8n).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow")


# ── Technical ────────────────────────────────────────────────────────────────
class Indicators(_Base):
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    sma20: float | None = None
    sma50: float | None = None
    ema20: float | None = None
    ema50: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    adx: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None
    atr: float | None = None
    cmf: float | None = None
    mfi: float | None = None
    supertrend: float | None = None
    cci: float | None = None


class TechnicalSignal(_Base):
    indicator: str
    signal: str = Field(description="BULLISH | BEARISH | NEUTRAL")
    strength: str = Field(description="strong | medium | weak")
    note: str


class SRZone(_Base):
    price: float
    touches: int = Field(description="number of touches on the level = its strength")
    last_idx: int | None = None
    kind: str | None = Field(default=None, description="support | resistance")
    dist_pct: float | None = None
    dist_atr: float | None = None


class Pivots(_Base):
    pp: float
    r1: float
    r2: float
    s1: float
    s2: float


class Fibonacci(_Base):
    direction: str = Field(description="up | down")
    high: float
    low: float
    levels: dict[str, float]


class SupportResistance(_Base):
    price: float | None = None
    atr: float | None = None
    support: list[SRZone] = []
    resistance: list[SRZone] = []
    nearest_support: SRZone | None = None
    nearest_resistance: SRZone | None = None
    pivots: Pivots | None = None
    fibonacci: Fibonacci | None = None


class Risk(_Base):
    period_days: int | None = None
    ann_volatility: float | None = Field(default=None, description="annualised volatility (fraction)")
    total_return: float | None = None
    cagr: float | None = None
    sharpe: float | None = None
    sortino: float | None = None
    max_drawdown: float | None = None
    current_drawdown: float | None = None
    best_day: float | None = None
    worst_day: float | None = None
    positive_days_pct: float | None = None
    beta: float | None = None


class DataQuality(_Base):
    last_date: str | None = None
    age_days: int | None = None
    expected_last_session: str | None = None
    missing_sessions: int | None = None
    is_stale: bool | None = None


class TechnicalResponse(_Base):
    ticker: str
    price: float | None = None
    indicators: Indicators | None = None
    signals: list[TechnicalSignal] = []
    support_resistance: SupportResistance | None = None
    risk: Risk | None = None
    data_quality: DataQuality | None = None
    score: int | None = None
    error: str | None = None


# ── Fundamental ──────────────────────────────────────────────────────────────
class FundamentalSignal(_Base):
    indicator: str
    signal: str = Field(description="BULLISH | BEARISH | NEUTRAL")
    strength: str
    note: str
    category: str | None = None


class FundamentalData(_Base):
    """Key fields; `extra=allow` passes through the agent's full indicator set."""
    ticker: str | None = None
    company: str | None = None
    currency: str | None = None
    price: float | None = None
    market_cap: float | None = None
    pe_trailing: float | None = None
    pe_forward: float | None = None
    pb: float | None = None
    ps_ratio: float | None = None
    ev_ebitda: float | None = None
    roe: float | None = None
    roa: float | None = None
    roic: float | None = None
    profit_margin: float | None = None
    fcf_ttm: float | None = None
    fcf_yield: float | None = None
    dividend_yield: float | None = None
    piotroski_score: int | None = None
    altman_z: float | None = None
    error: str | None = None


class FundamentalResponse(_Base):
    data: FundamentalData
    signals: list[FundamentalSignal] = []


# ── Broker (Alpaca) ──────────────────────────────────────────────────────────
class AccountResponse(_Base):
    mode: str = Field(default="paper", description="paper (demo) | live")
    status: str | None = None
    currency: str | None = None
    cash: str | None = None
    equity: str | None = None
    portfolio_value: str | None = None
    buying_power: str | None = None
    long_market_value: str | None = None
    pattern_day_trader: bool | None = None
    trading_blocked: bool | None = None


class Position(_Base):
    symbol: str
    qty: str | None = None
    side: str | None = None
    avg_entry_price: str | None = None
    current_price: str | None = None
    market_value: str | None = None
    unrealized_pl: str | None = None
    unrealized_plpc: str | None = None


class Order(_Base):
    id: str | None = None
    symbol: str | None = None
    side: str | None = None
    qty: str | None = None
    notional: str | None = None
    type: str | None = None
    time_in_force: str | None = None
    status: str | None = None
    filled_qty: str | None = None
    filled_avg_price: str | None = None
    limit_price: str | None = None
    submitted_at: str | None = None


class OrderRequest(BaseModel):
    """Body of POST /broker/orders. Pass `qty` OR `notional`."""
    symbol: str = Field(description="e.g. AAPL, TSLA")
    side: str = Field(description="buy | sell")
    qty: float | None = Field(default=None, description="share count")
    notional: float | None = Field(default=None, description="amount in USD (instead of qty)")
    order_type: str = "market"
    time_in_force: str = "day"
    limit_price: float | None = None
    stop_price: float | None = None


# ── DCF ──────────────────────────────────────────────────────────────────────
class DCFScenario(_Base):
    name: str = Field(description="Base | Bull | Bear")
    fcf_growth: float = Field(description="annual FCF growth in phase 1 (fraction)")
    terminal_growth: float = Field(description="terminal growth (fraction)")
    wacc: float = Field(description="discount rate")
    fair_value: float | None = None
    upside: float | None = Field(default=None, description="fair_value / price - 1")


class DCFResponse(_Base):
    ticker: str
    company: str | None = None
    currency: str | None = None
    price: float | None = None
    shares: float | None = Field(default=None, description="share count (units)")
    fcf_ttm: float | None = Field(default=None, description="FCF za 12M")
    net_debt: float | None = None
    wacc_base: float | None = None
    projection_years: int | None = None
    scenarios: list[DCFScenario] = []
    available: bool | None = None
    error: str | None = None


# ── Speculator ───────────────────────────────────────────────────────────────
class Catalyst(_Base):
    name: str
    event_date: str | None = Field(default=None, description="ISO date")
    days_away: int | None = None
    description: str | None = None


class PatternResult(_Base):
    name: str
    direction: str = Field(description="UP | DOWN | NEUTRAL")
    strength: str = Field(description="strong | medium | weak")
    probability: float = Field(description="0.0–1.0 z danych historycznych")
    sample_size: int = Field(description="number of observations")
    avg_return: float | None = None
    horizon_days: int | None = None
    note: str | None = None


class Projection(_Base):
    horizon_label: str
    horizon_days: int
    direction: str = Field(description="UP | DOWN | NEUTRAL")
    return_low: float
    return_high: float
    probability: float
    reasoning: str | None = None


class SpeculatorResponse(_Base):
    ticker: str
    company: str | None = None
    current_price: float | None = None
    currency: str | None = None
    catalysts: list[Catalyst] = []
    patterns: list[PatternResult] = []
    projections: list[Projection] = []
    error: str | None = None


# ── Screener ─────────────────────────────────────────────────────────────────
class ScreenerRow(_Base):
    ticker: str
    company: str | None = None
    price: float | None = None
    currency: str | None = None
    market_cap: float | None = None
    pe: float | None = None
    pb: float | None = None
    ps: float | None = None
    roe: float | None = None
    roa: float | None = None
    profit_margin: float | None = None
    dividend_yield: float | None = None
    debt_to_equity: float | None = None
    week_52_change: float | None = None
    beta: float | None = None
    fcf_yield: float | None = None
    interest_coverage: float | None = None
    earnings_yield: float | None = Field(default=None, description="EBIT/EV (Magic Formula)")
    sector: str | None = None
    magic_rank: int | None = Field(default=None, description="Magic Formula ranking (lower = better)")
    available: bool | None = None
    error: str | None = None


class ScreenerResponse(_Base):
    total: int = Field(description="number of companies analysed")
    matched: int = Field(description="number matching the filters")
    filters: dict[str, object] = {}
    rows: list[ScreenerRow] = []
    errors: list[ScreenerRow] = []


# ── Sentiment ────────────────────────────────────────────────────────────────
class Mention(_Base):
    source: str
    title: str | None = None
    url: str | None = None
    date: str | None = Field(default=None, description="ISO datetime")
    score: float
    label: str = Field(description="BULLISH | BEARISH | NEUTRAL")


class SourceResult(_Base):
    name: str
    mentions: list[Mention] = []
    available: bool | None = None
    bullish_count: int | None = None
    bearish_count: int | None = None
    neutral_count: int | None = None
    avg_score: float | None = None
    error: str | None = None


class SentimentResponse(_Base):
    ticker: str
    company: str | None = None
    mode: str = Field(description="keyword | claude")
    results: list[SourceResult] = []
    total_mentions: int | None = None
    overall_score: float | None = None
    overall_label: str | None = Field(default=None, description="BULLISH | BEARISH | NEUTRAL")


# ── Macro ────────────────────────────────────────────────────────────────────
class FxRate(_Base):
    code: str = Field(description="USD | EUR | CHF | GBP")
    name: str | None = None
    rate: float = Field(description="PLN per 1 unit")
    date: str | None = None
    change_3m: float | None = Field(default=None, description="% change 3M")


class SectorPerf(_Base):
    name: str
    symbol: str
    price: float | None = None
    change_1d: float | None = Field(default=None, description="% change 1D")
    pos_52w: float | None = Field(default=None, description="pozycja w zakresie 52W (0-100%)")


class MacroResponse(_Base):
    as_of: str | None = Field(default=None, description="ISO date")
    fx: list[FxRate] = []
    gold_pln: float | None = None
    gold_date: str | None = None
    wig20_price: float | None = None
    wig20_change_1d: float | None = None
    wig20_pos_52w: float | None = None
    sectors: list[SectorPerf] = []
    cpi_value: float | None = None
    cpi_change_pct: float | None = Field(default=None, description="YoY inflation %")
    cpi_date: str | None = None
    errors: list[str] = []


# ── Compare ──────────────────────────────────────────────────────────────────
class CompareRow(_Base):
    ticker: str
    company: str | None = None
    currency: str | None = None
    price: float | None = None
    market_cap: float | None = None
    pe: float | None = None
    pe_fwd: float | None = None
    pb: float | None = None
    ps: float | None = None
    ev_ebitda: float | None = None
    roe: float | None = None
    roa: float | None = None
    margin: float | None = None
    op_margin: float | None = None
    div_yield: float | None = None
    debt_equity: float | None = None
    beta: float | None = None
    fcf: float | None = None
    revenue: float | None = None
    w52_high: float | None = None
    w52_low: float | None = None
    interest_coverage: float | None = None
    sector: str | None = None
    error: str | None = None


class CompareResponse(_Base):
    tickers: list[str] = []
    data: list[CompareRow] = []
