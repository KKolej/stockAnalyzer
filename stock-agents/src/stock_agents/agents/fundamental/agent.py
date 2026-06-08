from __future__ import annotations

from ...ticker_map import ticker_to_company
from .fetcher import fetch
from .printer import print_fundamental
from .signals import generate_signals


def run(ticker: str) -> None:
    company = ticker_to_company(ticker)
    data = fetch(ticker, company)
    signals = generate_signals(data) if not data.error else []
    print_fundamental(data, signals)


def run_fundamental_agent(tickers: list[str]) -> None:
    for ticker in tickers:
        run(ticker)
