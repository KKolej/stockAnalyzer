from __future__ import annotations

from .fetcher import fetch
from .printer import print_dcf


def run(ticker: str, projection_years: int = 10) -> None:
    result = fetch(ticker, projection_years)
    print_dcf(result)


def run_dcf_agent(tickers: list[str], projection_years: int = 10) -> None:
    for ticker in tickers:
        run(ticker, projection_years)
