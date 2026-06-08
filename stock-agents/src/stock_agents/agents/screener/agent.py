from __future__ import annotations

from .fetcher import fetch_all
from .filter import apply_filters
from .models import ScreenerFilters
from .printer import print_screener


def run(tickers: list[str], filters: ScreenerFilters) -> None:
    rows = fetch_all(tickers)
    filtered = apply_filters(rows, filters)
    print_screener(rows, filtered, filters)
