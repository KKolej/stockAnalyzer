from __future__ import annotations

import argparse

from .agent import run_fundamental_agent


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fundamental-agents",
        description="Analiza fundamentalna spółek giełdowych",
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        metavar="TICKER",
        help="Ticker spółki (np. PKO, CDR, TSLA.US)",
    )
    args = parser.parse_args()
    run_fundamental_agent(args.tickers)
