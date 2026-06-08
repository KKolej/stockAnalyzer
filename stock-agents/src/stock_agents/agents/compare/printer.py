from __future__ import annotations

SEP = "=" * 80


def _v(val, fmt: str = ".1f", suffix: str = "", none: str = "n/d") -> str:
    if val is None:
        return none
    try:
        return f"{val:{fmt}}{suffix}"
    except (TypeError, ValueError):
        return none


def _pct(val) -> str:
    if val is None:
        return "n/d"
    return f"{val * 100:.1f}%"


def _money(val, cur: str = "") -> str:
    if val is None:
        return "n/d"
    if abs(val) >= 1e12:
        return f"{val/1e12:.2f}T"
    if abs(val) >= 1e9:
        return f"{val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"{val/1e6:.0f}M"
    return f"{val:.0f}"


def _best(rows: list[dict], key: str, higher_is_better: bool = True) -> set[str]:
    vals = [(r["ticker"], r.get(key)) for r in rows if r.get(key) is not None and not r.get("error")]
    if not vals:
        return set()
    best_val = max(v for _, v in vals) if higher_is_better else min(v for _, v in vals)
    return {t for t, v in vals if abs(v - best_val) < 1e-9}


def _row(label: str, rows: list[dict], key: str, fmt_fn,
         higher_is_better: bool | None = None, col_w: int = 14) -> str:
    best: set[str] = set()
    if higher_is_better is not None:
        best = _best(rows, key, higher_is_better)
    cells = []
    for r in rows:
        val = r.get(key)
        cell = fmt_fn(val)
        marker = " *" if r["ticker"] in best else "  "
        cells.append(f"{cell + marker:>{col_w}}")
    return f"  {label:<20}" + "".join(cells)


def print_compare(rows: list[dict]) -> None:
    errors = [r for r in rows if r.get("error")]
    ok_rows = [r for r in rows if not r.get("error")]

    print()
    print(SEP)
    print("  PORÓWNANIE SPÓŁEK")
    print(SEP)

    if errors:
        for e in errors:
            print(f"  [BŁĄD] {e['ticker']}: {e.get('error', '?')}")

    if not ok_rows:
        print(SEP)
        return

    col_w = max(14, 80 // (len(ok_rows) + 1))

    # Nagłówek
    header = f"  {'METRYKA':<20}" + "".join(f"{r['ticker']:>{col_w}}" for r in ok_rows)
    print(header)
    print(f"  {'─'*20}" + "─" * (col_w * len(ok_rows)))

    # Nazwa
    name_row = f"  {'Nazwa':<20}" + "".join(
        f"{(r.get('company', '') or '')[:col_w-2]:>{col_w}}" for r in ok_rows
    )
    print(name_row)
    print(f"  {'Sektor':<20}" + "".join(
        f"{(r.get('sector', '') or '')[:col_w-2]:>{col_w}}" for r in ok_rows
    ))

    # Cena / Kap
    print(f"  {'─'*20}" + "─" * (col_w * len(ok_rows)))
    print(f"  {'Cena':<20}" + "".join(
        f"{(_v(r.get('price'), '.2f') + ' ' + (r.get('currency') or '')):>{col_w}}" for r in ok_rows
    ))
    print(f"  {'Market Cap':<20}" + "".join(
        f"{_money(r.get('market_cap')):>{col_w}}" for r in ok_rows
    ))
    print(f"  {'Przychody':<20}" + "".join(
        f"{_money(r.get('revenue')):>{col_w}}" for r in ok_rows
    ))
    print(f"  {'FCF TTM':<20}" + "".join(
        f"{_money(r.get('fcf')):>{col_w}}" for r in ok_rows
    ))

    # Wycena
    print(f"  {'─'*20}" + "─" * (col_w * len(ok_rows)))
    print(f"  {'── WYCENA ──':<20}")
    print(_row("P/E (trailing)", ok_rows, "pe", lambda v: _v(v, ".1f"), higher_is_better=False, col_w=col_w))
    print(_row("P/E (forward)", ok_rows, "pe_fwd", lambda v: _v(v, ".1f"), higher_is_better=False, col_w=col_w))
    print(_row("P/B", ok_rows, "pb", lambda v: _v(v, ".2f"), higher_is_better=False, col_w=col_w))
    print(_row("P/S", ok_rows, "ps", lambda v: _v(v, ".2f"), higher_is_better=False, col_w=col_w))
    print(_row("EV/EBITDA", ok_rows, "ev_ebitda", lambda v: _v(v, ".1f"), higher_is_better=False, col_w=col_w))

    # Rentowność
    print(f"  {'─'*20}" + "─" * (col_w * len(ok_rows)))
    print(f"  {'── RENTOWNOŚĆ ──':<20}")
    print(_row("ROE", ok_rows, "roe", _pct, higher_is_better=True, col_w=col_w))
    print(_row("ROA", ok_rows, "roa", _pct, higher_is_better=True, col_w=col_w))
    print(_row("Marża netto", ok_rows, "margin", _pct, higher_is_better=True, col_w=col_w))
    print(_row("Marża operacyjna", ok_rows, "op_margin", _pct, higher_is_better=True, col_w=col_w))

    # Zdrowie
    print(f"  {'─'*20}" + "─" * (col_w * len(ok_rows)))
    print(f"  {'── ZDROWIE ──':<20}")
    print(_row("D/E", ok_rows, "debt_equity", lambda v: _v(v, ".1f"), higher_is_better=False, col_w=col_w))
    print(_row("IC (EBIT/Odsetki)", ok_rows, "interest_coverage", lambda v: _v(v, ".1f", "x") if v is not None else "n/d", higher_is_better=True, col_w=col_w))
    print(_row("Beta", ok_rows, "beta", lambda v: _v(v, ".2f"), higher_is_better=None, col_w=col_w))
    print(_row("Dywidenda", ok_rows, "div_yield", _pct, higher_is_better=True, col_w=col_w))

    print()
    print("  * — najlepsza wartość w kategorii")
    print(SEP)
    print()
