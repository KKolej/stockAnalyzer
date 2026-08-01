from __future__ import annotations

from .models import MacroData

SEP = "=" * 72


def _sign(v: float) -> str:
    return "+" if v >= 0 else ""


def _bar(pos: float | None, width: int = 20) -> str:
    if pos is None:
        return " " * width
    filled = round(pos / 100 * width)
    return "▓" * filled + "░" * (width - filled)


def _sector_arrow(change: float) -> str:
    if change > 1.5:
        return "▲▲"
    if change > 0.3:
        return "▲ "
    if change > -0.3:
        return "─ "
    if change > -1.5:
        return "▼ "
    return "▼▼"


def _context_signals(d: MacroData) -> list[tuple[str, str]]:
    signals = []

    # CPI
    if d.cpi_change_pct is not None:
        if d.cpi_change_pct < 2.5:
            signals.append(("▲", f"Inflacja niska ({d.cpi_change_pct:.1f}%) → RPP może obniżyć stopy"))
        elif d.cpi_change_pct > 5.0:
            signals.append(("▼", f"Inflacja wysoka ({d.cpi_change_pct:.1f}%) → stopy wysokie dłużej"))
        else:
            signals.append(("─", f"Inflacja umiarkowana ({d.cpi_change_pct:.1f}%)"))

    # EUR/PLN trend
    eur = next((f for f in d.fx if f.code == "EUR"), None)
    if eur and eur.change_3m is not None:
        if eur.change_3m > 2:
            signals.append(("▼", f"Słabszy PLN (EUR/PLN +{eur.change_3m:.1f}% 3M) "
                                 "→ droższy import, lepsza część eksportu"))
        elif eur.change_3m < -2:
            signals.append(("▲", f"Silniejszy PLN (EUR/PLN {eur.change_3m:.1f}% 3M) "
                                 "→ tańszy import, gorszy eksport"))

    # WIG20 pozycja
    if d.wig20_pos_52w is not None:
        if d.wig20_pos_52w > 80:
            signals.append(("▲", f"WIG20 blisko szczytu 52W ({d.wig20_pos_52w:.0f}%) — momentum bycze"))
        elif d.wig20_pos_52w < 20:
            signals.append(("▼", f"WIG20 blisko dna 52W ({d.wig20_pos_52w:.0f}%) — rynek w korekcie"))

    # Strongest/weakest sector
    if d.sectors:
        best = max(d.sectors, key=lambda s: s.change_1d)
        worst = min(d.sectors, key=lambda s: s.change_1d)
        if best.change_1d > 1.5:
            signals.append(("▲", f"Lider dziś: {best.name} ({best.change_1d:+.1f}%)"))
        if worst.change_1d < -1.5:
            signals.append(("▼", f"Najsłabszy dziś: {worst.name} ({worst.change_1d:+.1f}%)"))

    return signals


def print_macro(d: MacroData) -> None:
    print(SEP)
    print(f"  MAKRO GPW  —  {d.as_of}")
    print(SEP)

    # ── Currencies ──────────────────────────────────────────────────────────
    print("\n  ▸ KURSY WALUT (NBP)")
    print(f"  {'─' * 50}")
    for fx in d.fx:
        trend = f"  3M: {_sign(fx.change_3m)}{fx.change_3m:.1f}%" if fx.change_3m is not None else ""
        print(f"  {fx.code}/PLN  {fx.rate:.4f}  ({fx.date}){trend}")
    if d.gold_pln:
        print(f"  Złoto      {d.gold_pln:.2f} PLN/g  ({d.gold_date})")

    # ── Inflation ────────────────────────────────────────────────────────────
    print("\n  ▸ INFLACJA CPI (GUS/Biznesradar)")
    print(f"  {'─' * 50}")
    if d.cpi_change_pct is not None:
        print(f"  CPI r/r:  {d.cpi_change_pct:+.2f}%   (poziom {d.cpi_value:.2f}, {d.cpi_date})")
    else:
        print("  CPI: brak danych")

    # ── Exchange ─────────────────────────────────────────────────────────────
    print("\n  ▸ WIG20")
    print(f"  {'─' * 50}")
    if d.wig20_price:
        chg_str = f"{_sign(d.wig20_change_1d or 0)}{d.wig20_change_1d:.2f}%" if d.wig20_change_1d is not None else ""
        bar = _bar(d.wig20_pos_52w)
        pos_str = f"  52W: [{bar}] {d.wig20_pos_52w:.0f}%" if d.wig20_pos_52w is not None else ""
        print(f"  WIG20  {d.wig20_price:>8.1f}  {chg_str:>8}{pos_str}")
    else:
        print("  WIG20: brak danych")

    # ── Sektory ──────────────────────────────────────────────────────────────
    if d.sectors:
        print("\n  ▸ SEKTORY GPW (zmiana 1D)")
        print(f"  {'─' * 50}")
        # Sort descending by change
        for s in sorted(d.sectors, key=lambda x: x.change_1d, reverse=True):
            arrow = _sector_arrow(s.change_1d)
            bar = _bar(s.pos_52w, 12)
            pos_str = f" 52W:[{bar}]" if s.pos_52w is not None else ""
            print(f"  {arrow} {s.name:<14} {s.price:>8.1f}  {_sign(s.change_1d)}{s.change_1d:.2f}%{pos_str}")

    # ── Kontekst ─────────────────────────────────────────────────────────────
    signals = _context_signals(d)
    if signals:
        print("\n  ▸ KONTEKST DLA INWESTORA")
        print(f"  {'─' * 50}")
        for icon, note in signals:
            print(f"  {icon}  {note}")

    if d.errors:
        print(f"\n  Błędy: {'; '.join(d.errors[:3])}")

    print()
    print(SEP)
    print()
