"""Pydantic response models — kontrakt JSON dla endpointów (widoczny w /docs).

Modele są tolerancyjne (pola opcjonalne, `extra="allow"`), by nie gubić danych
przy rozwoju agentów, a jednocześnie dokumentować kontrakt dla konsumentów (n8n).
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
    touches: int = Field(description="liczba dotknięć poziomu = jego siła")
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
    ann_volatility: float | None = Field(default=None, description="zmienność roczna (ułamek)")
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
    """Kluczowe pola; `extra=allow` przepuszcza pełen zestaw wskaźników agenta."""
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
