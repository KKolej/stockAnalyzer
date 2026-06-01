from __future__ import annotations

import argparse

from .agent import run
from .models import AnalysisMode


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sentiment-agents",
        description="Analiza sentymentu rynkowego dla spółek giełdowych",
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        metavar="TICKER",
        help="Ticker spółki (np. PKO, CDR, TSLA.US)",
    )
    parser.add_argument(
        "--mode",
        choices=[m.value for m in AnalysisMode],
        default=AnalysisMode.KEYWORD.value,
        help="Tryb analizy: keyword (domyślny, lokalnie) lub claude (Claude API)",
    )
    args = parser.parse_args()
    mode = AnalysisMode(args.mode)

    for ticker in args.tickers:
        run(ticker, mode)
