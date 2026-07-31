from __future__ import annotations

import yfinance as yf

from ...ticker_map import ticker_to_company, to_yahoo_ticker
from .models import SpeculatorData
from .patterns import run_all_patterns
from .printer import print_speculator
from .signals import build_projections


def get_data(ticker: str) -> SpeculatorData:
    company = ticker_to_company(ticker)
    yahoo_ticker = to_yahoo_ticker(ticker)
    try:
        info = yf.Ticker(yahoo_ticker).info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        currency = info.get("currency", "")
    except Exception as e:
        return SpeculatorData(ticker=ticker, company=company, current_price=0.0, currency="", error=str(e))

    patterns, catalysts = run_all_patterns(yahoo_ticker, ticker, industry=info.get("industry"))
    projections = build_projections(patterns, catalysts)
    return SpeculatorData(
        ticker=ticker.upper(), company=company,
        current_price=float(price), currency=currency,
        catalysts=catalysts, patterns=patterns, projections=projections,
    )


def run(ticker: str) -> None:
    data = get_data(ticker)
    print_speculator(data)


def run_speculator_agent(tickers: list[str]) -> None:
    for ticker in tickers:
        run(ticker)
