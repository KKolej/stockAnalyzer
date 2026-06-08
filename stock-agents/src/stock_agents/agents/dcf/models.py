from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DCFScenario:
    name: str          # "Base", "Bull", "Bear"
    fcf_growth: float  # roczny wzrost FCF w fazie 1 (np. 0.10 = 10%)
    terminal_growth: float  # wzrost terminalny (np. 0.03)
    wacc: float        # stopa dyskontowa
    fair_value: float | None = None
    upside: float | None = None   # (fair_value / price - 1)


@dataclass
class DCFResult:
    ticker: str
    company: str
    currency: str

    price: float | None
    shares: float | None       # liczba akcji (w szt.)
    fcf_ttm: float | None      # FCF ostatnie 12M
    net_debt: float | None     # dług netto
    wacc_base: float           # WACC bazowy

    projection_years: int      # horyzont fazy 1 (domyślnie 10)
    scenarios: list[DCFScenario] = field(default_factory=list)

    error: str | None = None

    @property
    def available(self) -> bool:
        return self.error is None and self.fcf_ttm is not None
