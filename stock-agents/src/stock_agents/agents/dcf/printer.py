from __future__ import annotations

from .models import DCFResult

SEP = "=" * 72


def _fmt_money(val: float | None, currency: str) -> str:
    if val is None:
        return "n/d"
    if abs(val) >= 1e9:
        return f"{val/1e9:.2f}B {currency}"
    if abs(val) >= 1e6:
        return f"{val/1e6:.1f}M {currency}"
    return f"{val:.0f} {currency}"


def _pct(val: float | None) -> str:
    if val is None:
        return "n/d"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val*100:.1f}%"


def _upside_label(upside: float | None) -> str:
    if upside is None:
        return ""
    if upside > 0.20:
        return "  ▲ POTENCJAŁ"
    if upside < -0.20:
        return "  ▼ PRZEWARTOŚCIOWANA"
    return "  ~ FAIR VALUE"


def print_dcf(result: DCFResult) -> None:
    print(SEP)
    print(f"  DCF — {result.ticker}  ({result.company})")
    print(SEP)

    if result.error:
        print(f"  BŁĄD: {result.error}")
        print(SEP)
        return

    price_str = f"{result.price:.2f} {result.currency}" if result.price else "n/d"
    print(f"  Cena rynkowa:  {price_str}")
    print(f"  FCF TTM:       {_fmt_money(result.fcf_ttm, result.currency)}")
    print(f"  Dług netto:    {_fmt_money(result.net_debt, result.currency)}")
    print(f"  WACC bazowy:   {result.wacc_base*100:.1f}%")
    print(f"  Horyzont:      {result.projection_years} lat")
    print()

    if not result.scenarios:
        print("  Brak scenariuszy (niewystarczające dane FCF).")
        print(SEP)
        return

    if result.fcf_ttm is not None and result.fcf_ttm <= 0:
        print("  UWAGA: FCF ≤ 0 — wycena DCF mało wiarygodna dla spółki z ujemnym przepływem.")
        print()

    print(f"  {'SCENARIUSZ':<10}  {'FCF_g':>6}  {'TG':>5}  {'WACC':>6}  "
          f"{'FAIR VALUE':>12}  {'UPSIDE':>8}")
    print(f"  {'─'*10}  {'─'*6}  {'─'*5}  {'─'*6}  {'─'*12}  {'─'*8}")

    for s in result.scenarios:
        fv_str = f"{s.fair_value:.2f} {result.currency}" if s.fair_value else "n/d"
        label = _upside_label(s.upside) if s.name == "Base" else ""
        print(
            f"  {s.name:<10}  {s.fcf_growth*100:>5.0f}%  {s.terminal_growth*100:>4.0f}%  "
            f"{s.wacc*100:>5.1f}%  {fv_str:>12}  {_pct(s.upside):>8}{label}"
        )

    print()
    print(SEP)
    print()
