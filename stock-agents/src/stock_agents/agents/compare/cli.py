from __future__ import annotations

import argparse

from .agent import run_compare


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="compare-agents",
        description="Porównanie spółek side-by-side",
    )
    parser.add_argument("tickers", nargs="+", metavar="TICKER")
    args = parser.parse_args()
    run_compare(args.tickers)
