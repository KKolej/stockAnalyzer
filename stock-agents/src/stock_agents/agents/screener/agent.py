from __future__ import annotations

from .fetcher import fetch_all
from .filter import apply_filters
from .models import ScreenerFilters, ScreenerRow
from .printer import print_screener


def get_data(tickers: list[str], filters: ScreenerFilters) -> tuple[list[ScreenerRow], list[ScreenerRow]]:
    rows = fetch_all(tickers)
    filtered = apply_filters(rows, filters)
    return rows, filtered


def run(tickers: list[str], filters: ScreenerFilters) -> None:
    rows, filtered = get_data(tickers, filters)
    print_screener(rows, filtered, filters)
