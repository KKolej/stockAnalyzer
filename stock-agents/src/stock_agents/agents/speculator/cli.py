from __future__ import annotations

import argparse

from .agent import run_speculator_agent


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="speculator-agents",
        description="Analiza spekulacyjna — wzorce, katalyzatory, projekcje 1T–2M",
    )
    parser.add_argument("tickers", nargs="+", metavar="TICKER")
    args = parser.parse_args()
    run_speculator_agent(args.tickers)
