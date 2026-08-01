from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DCFScenario:
    name: str          # "Base", "Bull", "Bear"
    fcf_growth: float  # annual FCF growth in phase 1 (e.g. 0.10 = 10%)
    terminal_growth: float  # terminal growth (e.g. 0.03)
    wacc: float        # discount rate
    fair_value: float | None = None
    upside: float | None = None   # (fair_value / price - 1)


@dataclass
class DCFResult:
    ticker: str
    company: str
    currency: str

    price: float | None
    shares: float | None       # share count (in units)
    fcf_ttm: float | None      # FCF ostatnie 12M
    net_debt: float | None     # net debt
    wacc_base: float           # WACC bazowy

    projection_years: int      # phase 1 horizon (10 by default)
    scenarios: list[DCFScenario] = field(default_factory=list)

    error: str | None = None

    @property
    def available(self) -> bool:
        return self.error is None and self.fcf_ttm is not None
