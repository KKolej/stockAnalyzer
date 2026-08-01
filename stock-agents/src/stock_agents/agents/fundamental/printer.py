from __future__ import annotations

from .models import FundamentalData, YearlyRecord
from .signals import Signal

SEPARATOR = "=" * 72
COL = 28
STRENGTH_ORDER = {"strong": 3, "medium": 2, "weak": 1}
SIGNAL_ICON = {"BULLISH": "▲", "BEARISH": "▼", "NEUTRAL": "─"}


def _v(val: float | None, fmt: str = ".2f", suffix: str = "") -> str:
    if val is None:
        return "n/d"
    return f"{val:{fmt}}{suffix}"


def _pct(val: float | None) -> str:
    if val is None:
        return "n/d"
    return f"{val * 100:.1f}%"


def _big(val: float | None, currency: str = "") -> str:
    if val is None:
        return "n/d"
    for div, label in [(1e9, "mld"), (1e6, "mln"), (1e3, "tys")]:
        if abs(val) >= div:
            return f"{val / div:.2f} {label} {currency}".strip()
    return f"{val:.0f} {currency}".strip()


def _big_short(val: float | None) -> str:
    if val is None:
        return "n/d"
    for div, label in [(1e9, "G"), (1e6, "M"), (1e3, "k")]:
        if abs(val) >= div:
            return f"{val / div:.1f}{label}"
    return f"{val:.0f}"


def _row(name: str, value: str) -> None:
    print(f"  {name:<{COL}} {value}")


def _section(title: str) -> None:
    print(f"\n  ▸ {title}")
    print(f"  {'─' * 50}")


def _score(signals: list[Signal]) -> int:
    total = 0
    for s in signals:
        direction = 1 if s["signal"] == "BULLISH" else -1 if s["signal"] == "BEARISH" else 0
        total += direction * STRENGTH_ORDER.get(s["strength"], 1)
    return total


def _verdict(score: int) -> str:
    if score >= 6:
        return "SILNIE BYCZO"
    if score >= 3:
        return "BYCZO"
    if score <= -6:
        return "SILNIE NIEDŹWIEDZIO"
    if score <= -3:
        return "NIEDŹWIEDZIO"
    return "NEUTRALNIE"


def _yoy(current: float | None, prev: float | None) -> str:
    if current is None or prev is None or prev == 0:
        return ""
    pct = (current - prev) / abs(prev) * 100
    sign = "+" if pct >= 0 else ""
    return f"({sign}{pct:.0f}%)"


def _print_history(records: list[YearlyRecord], currency: str) -> None:
    if not records:
        return

    _section("HISTORIA")

    # Header
    yr_w, rev_w, ni_w, mg_w, roe_w, fcf_w = 6, 11, 11, 7, 7, 11
    hdr = (f"  {'Rok':<{yr_w}} {'Przychody':>{rev_w}} {'Zysk netto':>{ni_w}}"
           f"  {'Marża':>{mg_w}} {'ROE':>{roe_w}} {'FCF':>{fcf_w}}")
    print(hdr)
    print(f"  {'─'*yr_w} {'─'*rev_w} {'─'*ni_w}  {'─'*mg_w} {'─'*roe_w} {'─'*fcf_w}")

    for i, r in enumerate(records):
        prev = records[i + 1] if i + 1 < len(records) else None
        rev_yoy = _yoy(r.revenue, prev.revenue if prev else None)
        _yoy(r.net_income, prev.net_income if prev else None)
        rev_str = _big_short(r.revenue)
        ni_str = _big_short(r.net_income)
        mg_str = _pct(r.profit_margin)
        roe_str = _pct(r.roe)
        fcf_str = _big_short(r.free_cash_flow)

        print(f"  {r.year:<{yr_w}} {rev_str:>{rev_w}} {ni_str:>{ni_w}}"
              f"  {mg_str:>{mg_w}} {roe_str:>{roe_w}} {fcf_str:>{fcf_w}}"
              f"  {rev_yoy}")


def print_fundamental(d: FundamentalData, signals: list[Signal]) -> None:
    cur = d.currency

    print(SEPARATOR)
    if d.error:
        print(f"  {d.ticker.upper()} — {d.company}")
        print(f"  ✗ Błąd: {d.error}")
        print(SEPARATOR)
        print()
        return

    price_str = _v(d.price) if d.price else "n/d"
    cap_str = _big(d.market_cap, cur)
    print(f"  {d.ticker.upper():<12} {price_str:>10} {cur}   Kap: {cap_str}")
    print(f"  {d.company}")
    print(SEPARATOR)

    _section("WYCENA")
    _row("P/E (trailing / forward)", f"{_v(d.pe_trailing, '.1f')} / {_v(d.pe_forward, '.1f')}")
    _row("P/B", _v(d.pb, ".2f"))
    _row("P/S", _v(d.ps_ratio, ".2f"))
    _row("EV/EBITDA", _v(d.ev_ebitda, ".1f"))
    _row("52W High / Low", f"{_v(d.week_52_high)} / {_v(d.week_52_low)}")

    _section("WYNIKI (TTM)")
    _row("Przychody", _big(d.revenue, cur))
    _row("EBITDA", _big(d.ebitda, cur))
    _row("EPS", _v(d.eps))
    _row("Marża netto", _pct(d.profit_margin))
    _row("Marża operacyjna", _pct(d.operating_margin))
    _row("ROE", _pct(d.roe))
    _row("ROA", _pct(d.roa))
    _row("ROIC", _pct(d.roic))

    _section("FINANSE")
    _row("Current ratio", _v(d.current_ratio, ".2f"))
    _row("Quick ratio", _v(d.quick_ratio, ".2f"))
    _row("Dług / Kapitał", f"{_v(d.debt_to_equity, '.0f')}%")
    _row("Dług netto / EBITDA", _v(d.net_debt_ebitda, ".2f"))
    _row("Interest Coverage", f"{_v(d.interest_coverage, '.1f')}x" if d.interest_coverage else "n/d")
    _row("Wartość księgowa / akcję", _v(d.book_value))

    _section("PRZEPŁYWY")
    _row("FCF (TTM)", _big(d.fcf_ttm, cur))
    _row("FCF Yield", _pct(d.fcf_yield))
    _row("EV/FCF", _v(d.ev_fcf, ".1f"))
    _row("P/CF", _v(d.price_to_cf, ".1f"))

    _section("DUPONT (dekompozycja ROE)")
    if d.dupont_margin and d.dupont_asset_turnover and d.dupont_leverage:
        _row("Marża netto", _pct(d.dupont_margin))
        _row("Rotacja aktywów", f"{d.dupont_asset_turnover:.3f}x")
        _row("Dźwignia finansowa", f"{d.dupont_leverage:.2f}x")
        roe_check = d.dupont_margin * d.dupont_asset_turnover * d.dupont_leverage
        _row("ROE (kontrola)", _pct(roe_check))
        # Commentary: what drives ROE
        driver = ""
        if d.dupont_leverage > 3:
            driver = "napędzone głównie dźwignią"
        elif d.dupont_margin > 0.15:
            driver = "napędzone wysoką marżą"
        elif d.dupont_asset_turnover > 1:
            driver = "napędzone rotacją aktywów"
        if driver:
            print(f"  {'':>{COL}} → {driver}")
    else:
        _row("DuPont", "n/d (brak danych aktywów)")

    _section("DYWIDENDA")
    _row("Stopa dywidendy", _pct(d.dividend_yield))
    _row("Payout ratio", _pct(d.payout_ratio))
    _row("Wzrost dywidendy (CAGR)", _pct(d.dividend_cagr) if d.dividend_cagr is not None else "n/d")

    _row("Beta", _v(d.beta, ".2f"))

    # ── Scoring ─────────────────────────────────────────────────────────────
    _section("SCORING")
    # Piotroski F-Score
    if d.piotroski_score is not None:
        bar = "█" * d.piotroski_score + "░" * (d.piotroski_max - d.piotroski_score)
        label = ("silna" if d.piotroski_score >= 7 else
                 "dobra" if d.piotroski_score >= 5 else
                 "słaba" if d.piotroski_score <= 2 else "średnia")
        _row("Piotroski F-Score", f"{d.piotroski_score}/{d.piotroski_max}  {bar}  {label}")
    else:
        _row("Piotroski F-Score", "n/d")

    # Graham Number
    if d.graham_number is not None and d.price:
        diff_pct = (d.price - d.graham_number) / d.graham_number * 100
        sign = "+" if diff_pct >= 0 else ""
        _row("Graham Number", f"{d.graham_number:.2f}  (cena {sign}{diff_pct:.0f}% vs Graham)")
    else:
        _row("Graham Number", "n/d (wymaga EPS > 0 i BVPS > 0)")

    # Altman Z-Score (does not apply to banks and financial firms)
    if d.altman_z is not None:
        is_financial = "financial" in d.sector.lower() or "bank" in d.sector.lower()
        if is_financial:
            _row("Altman Z-Score", f"{d.altman_z:.2f}  (n/d dla banków/finansowych)")
        else:
            zone = ("bezpieczna ✓" if d.altman_z > 2.99 else
                    "szara strefa" if d.altman_z > 1.81 else "ryzyko !")
            _row("Altman Z-Score", f"{d.altman_z:.2f}  ({zone})")
    else:
        _row("Altman Z-Score", "n/d")

    # PEG Ratio
    if d.peg_ratio is not None:
        label = ("tani vs wzrost" if d.peg_ratio < 1 else
                 "drogi vs wzrost" if d.peg_ratio > 2 else "fair")
        _row("PEG Ratio", f"{d.peg_ratio:.2f}  ({label})")
    else:
        _row("PEG Ratio", "n/d")

    _print_history(d.history, cur)

    print(f"\n  {'─' * 50}")
    print("  SYGNAŁY FUNDAMENTALNE")
    print(f"  {'─' * 50}")

    _SCORING = {"Piotroski F-Score", "Graham Number", "Altman Z-Score", "PEG Ratio"}
    _TREND = {"Wzrost przychodów", "Wzrost zysku", "Trend marży", "FCF", "Wzrost dywidendy"}

    snapshot_signals = [s for s in signals if s["indicator"] not in _SCORING | _TREND]
    scoring_signals  = [s for s in signals if s["indicator"] in _SCORING]
    trend_signals    = [s for s in signals if s["indicator"] in _TREND]

    if snapshot_signals:
        print("  Wycena & bieżące:")
        for s in snapshot_signals:
            icon = SIGNAL_ICON.get(s["signal"], "─")
            print(f"    {icon} [{s['strength'].upper():<6}] {s['indicator']:<22} {s['note']}")

    if scoring_signals:
        print("  Scoring:")
        for s in scoring_signals:
            icon = SIGNAL_ICON.get(s["signal"], "─")
            print(f"    {icon} [{s['strength'].upper():<6}] {s['indicator']:<22} {s['note']}")

    if trend_signals:
        print("  Trendy historyczne:")
        for s in trend_signals:
            icon = SIGNAL_ICON.get(s["signal"], "─")
            print(f"    {icon} [{s['strength'].upper():<6}] {s['indicator']:<22} {s['note']}")

    if not signals:
        print("  Brak wyraźnych sygnałów.")

    score = _score(signals)
    print(f"\n  SCORE: {score:+d}   →   {_verdict(score)}")
    print(SEPARATOR)
    print()
