from __future__ import annotations

from .models import ScreenerFilters, ScreenerRow

SEPARATOR = "=" * 88


def _v(val: float | None, fmt: str = ".1f", suffix: str = "") -> str:
    if val is None:
        return "n/d"
    return f"{val:{fmt}}{suffix}"


def _pct(val: float | None) -> str:
    if val is None:
        return "n/d"
    return f"{val * 100:.1f}%"


def _cap(val: float | None) -> str:
    if val is None:
        return "n/d"
    for div, label in [(1e9, "G"), (1e6, "M")]:
        if abs(val) >= div:
            return f"{val / div:.1f}{label}"
    return f"{val:.0f}"


def _52w(val: float | None) -> str:
    if val is None:
        return "n/d"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val * 100:.0f}%"


def _filter_summary(f: ScreenerFilters) -> str:
    parts = []
    if f.pe_max is not None:
        parts.append(f"P/E≤{f.pe_max}")
    if f.pe_min is not None:
        parts.append(f"P/E≥{f.pe_min}")
    if f.pb_max is not None:
        parts.append(f"P/B≤{f.pb_max}")
    if f.roe_min is not None:
        parts.append(f"ROE≥{f.roe_min}%")
    if f.roa_min is not None:
        parts.append(f"ROA≥{f.roa_min}%")
    if f.margin_min is not None:
        parts.append(f"Marża≥{f.margin_min}%")
    if f.div_min is not None:
        parts.append(f"Dywidenda≥{f.div_min}%")
    if f.market_cap_min is not None:
        parts.append(f"Kap≥{f.market_cap_min}M")
    if f.market_cap_max is not None:
        parts.append(f"Kap≤{f.market_cap_max}M")
    if f.debt_max is not None:
        parts.append(f"D/E≤{f.debt_max}%")
    if f.beta_max is not None:
        parts.append(f"Beta≤{f.beta_max}")
    if f.fcf_yield_min is not None:
        parts.append(f"FCFYield≥{f.fcf_yield_min}%")
    if f.ic_min is not None:
        parts.append(f"IC≥{f.ic_min}x")
    if getattr(f, "magic_formula", False):
        parts.append("Magic Formula")
    return "  ".join(parts) if parts else "brak filtrów"


def print_screener(
    all_rows: list[ScreenerRow],
    filtered: list[ScreenerRow],
    filters: ScreenerFilters,
) -> None:
    errors = [r for r in all_rows if not r.available]
    total = len(all_rows)

    print(SEPARATOR)
    print(f"  SCREENER   {total} spółek → {len(filtered)} pasuje")
    print(f"  Filtry: {_filter_summary(filters)}   Sortowanie: {filters.sort_by.upper()}")
    if errors:
        print(f"  Błędy pobierania: {len(errors)} spółek ({', '.join(r.ticker for r in errors[:5])})")
    print(SEPARATOR)

    if not filtered:
        print("\n  Żadna spółka nie spełnia kryteriów.\n")
        print(SEPARATOR)
        return

    # Nagłówek
    h = (f"  {'#':>3}  {'TICKER':<8} {'NAZWA':<26} {'CENA':>8}  "
         f"{'P/E':>6} {'P/B':>5} {'ROE':>6} {'MARŻA':>6} {'DYW':>5} "
         f"{'FCFYld':>6} {'IC':>6} {'KAP':>6} {'52W↑':>5}")
    print(h)
    print(f"  {'─'*3}  {'─'*8} {'─'*26} {'─'*8}  "
          f"{'─'*6} {'─'*5} {'─'*6} {'─'*6} {'─'*5} {'─'*6} {'─'*6} {'─'*6} {'─'*5}")

    for i, r in enumerate(filtered, 1):
        cur = r.currency or ""
        price_str = f"{r.price:.2f} {cur}" if r.price else "n/d"
        name = r.company[:25] if r.company else r.ticker
        ic_str = f"{r.interest_coverage:.1f}x" if r.interest_coverage is not None else "n/d"

        print(
            f"  {i:>3}  {r.ticker:<8} {name:<26} {price_str:>10}  "
            f"{_v(r.pe):>6} {_v(r.pb):>5} {_pct(r.roe):>6} {_pct(r.profit_margin):>6} "
            f"{_pct(r.dividend_yield):>5} {_pct(r.fcf_yield):>6} {ic_str:>6} "
            f"{_cap(r.market_cap):>6} {_52w(r.week_52_change):>5}"
        )

    print()
    print(SEPARATOR)
    print()
