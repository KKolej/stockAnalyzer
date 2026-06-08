from __future__ import annotations

import argparse

from .agent import run_dcf_agent


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dcf-agent",
        description="Wycena DCF (Discounted Cash Flow)",
    )
    parser.add_argument("tickers", nargs="+", metavar="TICKER")
    parser.add_argument(
        "--years", type=int, default=10, metavar="N",
        help="Horyzont prognozy fazy 1 (domyślnie 10)",
    )
    args = parser.parse_args()
    run_dcf_agent(args.tickers, args.years)
