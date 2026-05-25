import argparse

from dotenv import load_dotenv

from stock_agents.agents.technical.agent import run_technical_agent

DEFAULT_DAYS = 365


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="stock-agents",
        description="Analiza techniczna akcji (GPW i rynki zagraniczne)",
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        help="Tickery spółek, np. PKO CDR KGHM lub AAPL.US TSLA.US",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Liczba dni wstecz (domyślnie {DEFAULT_DAYS})",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    run_technical_agent(args.tickers, args.days)
