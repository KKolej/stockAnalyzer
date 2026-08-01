from __future__ import annotations

import argparse

from .agent import run
from .models import ScreenerFilters


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="screener-agents",
        description="Screener spółek — filtruj i rankinguj podaną listę tickerów",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  screener-agents PKO CDR KGHM PZU LPP ALE MBK --pe-max 15 --roe-min 12
  screener-agents PKO PZU MBK --div-min 4 --sort div
  screener-agents PKO CDR KGHM PZU LPP --sort roe --top 3
  screener-agents PKO CDR KGHM --pe-max 20 --margin-min 10 --sort margin
        """,
    )
    parser.add_argument("tickers", nargs="+", metavar="TICKER")

    # Filtry wyceny
    parser.add_argument("--pe-max",  type=float, metavar="N", help="P/E maksymalnie N")
    parser.add_argument("--pe-min",  type=float, metavar="N", help="P/E minimalnie N")
    parser.add_argument("--pb-max",  type=float, metavar="N", help="P/B maksymalnie N")

    # Profitability filters
    parser.add_argument("--roe-min",    type=float, metavar="N", help="ROE minimalnie N%%")
    parser.add_argument("--roa-min",    type=float, metavar="N", help="ROA minimalnie N%%")
    parser.add_argument("--margin-min", type=float, metavar="N", help="Marża netto min N%%")

    # Dividend and balance sheet filters
    parser.add_argument("--div-min",        type=float, metavar="N", help="Stopa dywidendy min N%%")
    parser.add_argument("--market-cap-min", type=float, metavar="N", help="Kapitalizacja min N mln PLN")
    parser.add_argument("--market-cap-max", type=float, metavar="N", help="Kapitalizacja max N mln PLN")
    parser.add_argument("--debt-max",       type=float, metavar="N", help="D/E maksymalnie N%%")
    parser.add_argument("--beta-max",       type=float, metavar="N", help="Beta maksymalnie N")
    parser.add_argument("--fcf-yield-min",  type=float, metavar="N", help="FCF Yield min N%%")
    parser.add_argument("--ic-min",         type=float, metavar="N", help="Interest Coverage min Nx")
    parser.add_argument("--magic-formula",  action="store_true", help="Ranking Magic Formula (Greenblatt)")

    # Sortowanie i limit
    parser.add_argument(
        "--sort", default="pe",
        choices=["pe", "pb", "roe", "roa", "div", "cap", "margin", "beta", "52w", "fcf", "ic", "magic", "ey"],
        help="Pole sortowania (domyślnie: pe)",
    )
    parser.add_argument("--desc", action="store_true", help="Sortuj malejąco")
    parser.add_argument("--top",  type=int, metavar="N", help="Pokaż tylko top N wyników")

    args = parser.parse_args()

    filters = ScreenerFilters(
        pe_max=args.pe_max,
        pe_min=args.pe_min,
        pb_max=args.pb_max,
        roe_min=args.roe_min,
        roa_min=args.roa_min,
        margin_min=args.margin_min,
        div_min=args.div_min,
        fcf_yield_min=args.fcf_yield_min,
        ic_min=args.ic_min,
        market_cap_min=args.market_cap_min,
        market_cap_max=args.market_cap_max,
        debt_max=args.debt_max,
        beta_max=args.beta_max,
        sort_by=args.sort,
        sort_asc=not args.desc,
        top=args.top,
        magic_formula=args.magic_formula,
    )

    run(args.tickers, filters)
