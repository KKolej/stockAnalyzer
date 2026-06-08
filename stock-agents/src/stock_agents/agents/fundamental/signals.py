from __future__ import annotations

from .models import FundamentalData, YearlyRecord

Signal = dict[str, str]


def _s(indicator: str, signal: str, strength: str, note: str) -> Signal:
    return {"indicator": indicator, "signal": signal, "strength": strength, "note": note}


def _cagr(start: float, end: float, years: int) -> float | None:
    if start <= 0 or end is None or years < 1:
        return None
    return (end / start) ** (1 / years) - 1


# ── snapshot signals ────────────────────────────────────────────────────────

def pe_signal(d: FundamentalData) -> Signal | None:
    pe = d.pe_trailing
    if pe is None or pe <= 0:
        return None
    if pe < 10:
        return _s("P/E", "BULLISH", "strong", f"P/E={pe:.1f} — bardzo nisko wyceniona")
    if pe < 15:
        return _s("P/E", "BULLISH", "weak", f"P/E={pe:.1f} — poniżej średniej rynkowej")
    if pe > 40:
        return _s("P/E", "BEARISH", "strong", f"P/E={pe:.1f} — mocno przewartościowana")
    if pe > 25:
        return _s("P/E", "BEARISH", "weak", f"P/E={pe:.1f} — powyżej średniej rynkowej")
    return None


def pb_signal(d: FundamentalData) -> Signal | None:
    pb = d.pb
    if pb is None or pb <= 0:
        return None
    if pb < 1.0:
        return _s("P/B", "BULLISH", "strong", f"P/B={pb:.2f} — poniżej wartości księgowej")
    if pb < 1.5:
        return _s("P/B", "BULLISH", "weak", f"P/B={pb:.2f} — blisko wartości księgowej")
    if pb > 5.0:
        return _s("P/B", "BEARISH", "medium", f"P/B={pb:.2f} — wysoka premia do księgi")
    return None


def roe_signal(d: FundamentalData) -> Signal | None:
    roe = d.roe
    if roe is None:
        return None
    if roe > 0.20:
        return _s("ROE", "BULLISH", "strong", f"ROE={roe*100:.1f}% — wysoka rentowność kapitału")
    if roe > 0.12:
        return _s("ROE", "BULLISH", "weak", f"ROE={roe*100:.1f}% — dobra rentowność kapitału")
    if roe < 0:
        return _s("ROE", "BEARISH", "strong", f"ROE={roe*100:.1f}% — ujemna rentowność")
    if roe < 0.05:
        return _s("ROE", "BEARISH", "weak", f"ROE={roe*100:.1f}% — słaba rentowność kapitału")
    return None


def debt_signal(d: FundamentalData) -> Signal | None:
    dte = d.debt_to_equity
    if dte is None:
        return None
    if dte < 30:
        return _s("Dług/Kapitał", "BULLISH", "medium", f"D/E={dte:.0f}% — niskie zadłużenie")
    if dte > 200:
        return _s("Dług/Kapitał", "BEARISH", "strong", f"D/E={dte:.0f}% — wysokie zadłużenie")
    if dte > 100:
        return _s("Dług/Kapitał", "BEARISH", "weak", f"D/E={dte:.0f}% — umiarkowane zadłużenie")
    return None


def margin_signal(d: FundamentalData) -> Signal | None:
    m = d.profit_margin
    if m is None:
        return None
    if m > 0.20:
        return _s("Marża netto", "BULLISH", "strong", f"Marża={m*100:.1f}% — wysoka rentowność")
    if m > 0.10:
        return _s("Marża netto", "BULLISH", "weak", f"Marża={m*100:.1f}% — dobra rentowność")
    if m < 0:
        return _s("Marża netto", "BEARISH", "strong", f"Marża={m*100:.1f}% — strata netto")
    if m < 0.03:
        return _s("Marża netto", "BEARISH", "weak", f"Marża={m*100:.1f}% — bardzo niska marża")
    return None


def dividend_signal(d: FundamentalData) -> Signal | None:
    dy = d.dividend_yield
    if dy is None or dy == 0:
        return None
    if dy > 0.06:
        return _s("Dywidenda", "BULLISH", "strong", f"Yield={dy*100:.1f}% — bardzo atrakcyjna")
    if dy > 0.03:
        return _s("Dywidenda", "BULLISH", "weak", f"Yield={dy*100:.1f}% — atrakcyjna dywidenda")
    return None


def liquidity_signal(d: FundamentalData) -> Signal | None:
    cr = d.current_ratio
    if cr is None:
        return None
    if cr > 2.0:
        return _s("Płynność", "BULLISH", "weak", f"Current ratio={cr:.2f} — dobra płynność")
    if cr < 1.0:
        return _s("Płynność", "BEARISH", "strong", f"Current ratio={cr:.2f} — ryzyko płynności")
    return None


def ev_ebitda_signal(d: FundamentalData) -> Signal | None:
    ev = d.ev_ebitda
    if ev is None or ev <= 0:
        return None
    if ev < 6:
        return _s("EV/EBITDA", "BULLISH", "strong", f"EV/EBITDA={ev:.1f} — nisko wyceniona")
    if ev < 10:
        return _s("EV/EBITDA", "BULLISH", "weak", f"EV/EBITDA={ev:.1f} — umiarkowana wycena")
    if ev > 20:
        return _s("EV/EBITDA", "BEARISH", "medium", f"EV/EBITDA={ev:.1f} — droga wycena")
    return None


# ── trend signals (historical) ───────────────────────────────────────────────

def _valid(records: list[YearlyRecord], field: str) -> list[tuple[str, float]]:
    result = []
    for r in records:
        v = getattr(r, field, None)
        if v is not None:
            result.append((r.year, v))
    return result


def revenue_growth_signal(d: FundamentalData) -> Signal | None:
    pts = _valid(d.history, "revenue")
    if len(pts) < 2:
        return None
    newest_year, newest_val = pts[0]
    oldest_year, oldest_val = pts[-1]
    years = int(newest_year) - int(oldest_year)
    cagr = _cagr(oldest_val, newest_val, years)
    if cagr is None:
        return None
    label = f"CAGR {years}L={cagr*100:+.1f}%"
    if cagr > 0.15:
        return _s("Wzrost przychodów", "BULLISH", "strong", f"Przychody rosną dynamicznie ({label})")
    if cagr > 0.05:
        return _s("Wzrost przychodów", "BULLISH", "weak", f"Przychody rosną stabilnie ({label})")
    if cagr < -0.05:
        return _s("Wzrost przychodów", "BEARISH", "strong", f"Przychody spadają ({label})")
    if cagr < 0:
        return _s("Wzrost przychodów", "BEARISH", "weak", f"Przychody lekko spadają ({label})")
    return None


def earnings_growth_signal(d: FundamentalData) -> Signal | None:
    pts = _valid(d.history, "net_income")
    if len(pts) < 2:
        return None
    newest_year, newest_val = pts[0]
    oldest_year, oldest_val = pts[-1]
    if oldest_val <= 0 or newest_val <= 0:
        if newest_val < 0:
            return _s("Wzrost zysku", "BEARISH", "strong", "Spółka generuje stratę netto")
        return None
    years = int(newest_year) - int(oldest_year)
    cagr = _cagr(oldest_val, newest_val, years)
    if cagr is None:
        return None
    label = f"CAGR {years}L={cagr*100:+.1f}%"
    if cagr > 0.15:
        return _s("Wzrost zysku", "BULLISH", "strong", f"Zysk rośnie dynamicznie ({label})")
    if cagr > 0.05:
        return _s("Wzrost zysku", "BULLISH", "weak", f"Zysk rośnie stabilnie ({label})")
    if cagr < -0.10:
        return _s("Wzrost zysku", "BEARISH", "strong", f"Zysk spada ({label})")
    if cagr < 0:
        return _s("Wzrost zysku", "BEARISH", "weak", f"Zysk lekko spada ({label})")
    return None


def margin_trend_signal(d: FundamentalData) -> Signal | None:
    pts = _valid(d.history, "profit_margin")
    if len(pts) < 3:
        return None
    recent = [v for _, v in pts[:2]]
    older = [v for _, v in pts[2:]]
    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    diff = avg_recent - avg_older
    if diff > 0.05:
        return _s("Trend marży", "BULLISH", "medium",
                  f"Marże rosną ({avg_older*100:.1f}% → {avg_recent*100:.1f}%)")
    if diff < -0.05:
        return _s("Trend marży", "BEARISH", "medium",
                  f"Marże spadają ({avg_older*100:.1f}% → {avg_recent*100:.1f}%)")
    return None


def fcf_signal(d: FundamentalData) -> Signal | None:
    fcf_vals = [r.free_cash_flow for r in d.history if r.free_cash_flow is not None]
    if len(fcf_vals) < 2:
        return None
    positive = sum(1 for v in fcf_vals if v > 0)
    if positive == len(fcf_vals):
        return _s("FCF", "BULLISH", "medium", f"Wolne przepływy dodatnie przez {positive} lat z rzędu")
    if positive == 0:
        return _s("FCF", "BEARISH", "strong", "FCF ujemny — spółka spala gotówkę")
    neg = len(fcf_vals) - positive
    if neg >= 2:
        return _s("FCF", "BEARISH", "weak", f"FCF ujemny w {neg}/{len(fcf_vals)} ostatnich latach")
    return None


def interest_coverage_signal(d: FundamentalData) -> Signal | None:
    ic = d.interest_coverage
    if ic is None:
        return None
    if ic > 10:
        return _s("Interest Coverage", "BULLISH", "medium", f"IC={ic:.1f}x — bardzo bezpieczny poziom")
    if ic > 3:
        return _s("Interest Coverage", "BULLISH", "weak", f"IC={ic:.1f}x — bezpieczny poziom (>3x)")
    if ic < 1:
        return _s("Interest Coverage", "BEARISH", "strong", f"IC={ic:.1f}x — nie pokrywa odsetek!")
    if ic < 1.5:
        return _s("Interest Coverage", "BEARISH", "medium", f"IC={ic:.1f}x — niebezpiecznie nisko")
    return None


def fcf_yield_signal(d: FundamentalData) -> Signal | None:
    fy = d.fcf_yield
    if fy is None or fy <= 0:
        return None
    if fy > 0.08:
        return _s("FCF Yield", "BULLISH", "strong", f"FCF Yield={fy*100:.1f}% — bardzo atrakcyjny")
    if fy > 0.05:
        return _s("FCF Yield", "BULLISH", "medium", f"FCF Yield={fy*100:.1f}% — atrakcyjny (>5%)")
    if fy > 0.03:
        return _s("FCF Yield", "BULLISH", "weak", f"FCF Yield={fy*100:.1f}% — umiarkowany")
    return None


def ev_fcf_signal(d: FundamentalData) -> Signal | None:
    ef = d.ev_fcf
    if ef is None or ef <= 0:
        return None
    if ef < 10:
        return _s("EV/FCF", "BULLISH", "strong", f"EV/FCF={ef:.1f} — tania wycena (<10x)")
    if ef < 15:
        return _s("EV/FCF", "BULLISH", "weak", f"EV/FCF={ef:.1f} — umiarkowana wycena")
    if ef > 30:
        return _s("EV/FCF", "BEARISH", "medium", f"EV/FCF={ef:.1f} — droga wycena (>30x)")
    return None


def dividend_cagr_signal(d: FundamentalData) -> Signal | None:
    cagr = d.dividend_cagr
    if cagr is None:
        return None
    if cagr > 0.10:
        return _s("Wzrost dywidendy", "BULLISH", "strong", f"CAGR={cagr*100:.1f}%/rok — dynamiczny wzrost")
    if cagr > 0.05:
        return _s("Wzrost dywidendy", "BULLISH", "weak", f"CAGR={cagr*100:.1f}%/rok — stabilny wzrost")
    if cagr < -0.10:
        return _s("Wzrost dywidendy", "BEARISH", "medium", f"CAGR={cagr*100:.1f}%/rok — dywidenda spada")
    return None


def pcf_signal(d: FundamentalData) -> Signal | None:
    pcf = d.price_to_cf
    if pcf is None or pcf <= 0:
        return None
    if pcf < 8:
        return _s("P/CF", "BULLISH", "strong", f"P/CF={pcf:.1f} — tania wycena przepływów")
    if pcf < 15:
        return _s("P/CF", "BULLISH", "weak", f"P/CF={pcf:.1f} — umiarkowana wycena")
    if pcf > 30:
        return _s("P/CF", "BEARISH", "medium", f"P/CF={pcf:.1f} — droga wycena przepływów")
    return None


def piotroski_signal(d: FundamentalData) -> Signal | None:
    score = d.piotroski_score
    max_s = d.piotroski_max or 9
    if score is None:
        return None
    pct = score / max_s
    label = f"F-Score={score}/{max_s}"
    if pct >= 0.78:
        return _s("Piotroski F-Score", "BULLISH", "strong", f"{label} — silna kondycja fundamentalna")
    if pct >= 0.56:
        return _s("Piotroski F-Score", "BULLISH", "weak", f"{label} — dobra kondycja fundamentalna")
    if pct <= 0.22:
        return _s("Piotroski F-Score", "BEARISH", "strong", f"{label} — słaba kondycja fundamentalna")
    if pct <= 0.44:
        return _s("Piotroski F-Score", "BEARISH", "weak", f"{label} — poniżej średniej kondycji")
    return None


def graham_signal(d: FundamentalData) -> Signal | None:
    gn = d.graham_number
    price = d.price
    if gn is None or price is None or price <= 0:
        return None
    ratio = price / gn
    if ratio < 0.8:
        return _s("Graham Number", "BULLISH", "strong",
                  f"Cena {price:.2f} vs Graham {gn:.2f} — {(1-ratio)*100:.0f}% taniej od wartości")
    if ratio < 1.0:
        return _s("Graham Number", "BULLISH", "weak",
                  f"Cena {price:.2f} vs Graham {gn:.2f} — poniżej wartości Grahama")
    if ratio > 1.5:
        return _s("Graham Number", "BEARISH", "medium",
                  f"Cena {price:.2f} vs Graham {gn:.2f} — {(ratio-1)*100:.0f}% drożej od wartości")
    return None


def altman_signal(d: FundamentalData) -> Signal | None:
    z = d.altman_z
    if z is None:
        return None
    # Banki i firmy finansowe mają naturalnie niskie Z — formuła nie ma zastosowania
    if "financial" in d.sector.lower() or "bank" in d.sector.lower():
        return None
    if z > 2.99:
        return _s("Altman Z-Score", "BULLISH", "medium", f"Z={z:.2f} — strefa bezpieczna (>2.99)")
    if z > 1.81:
        return _s("Altman Z-Score", "NEUTRAL", "weak", f"Z={z:.2f} — szara strefa (1.81–2.99)")
    return _s("Altman Z-Score", "BEARISH", "strong", f"Z={z:.2f} — strefa ryzyka (<1.81)")


def peg_signal(d: FundamentalData) -> Signal | None:
    peg = d.peg_ratio
    if peg is None or peg <= 0:
        return None
    if peg < 1.0:
        return _s("PEG Ratio", "BULLISH", "medium", f"PEG={peg:.2f} — tani względem wzrostu")
    if peg < 1.5:
        return _s("PEG Ratio", "BULLISH", "weak", f"PEG={peg:.2f} — umiarkowanie wyceniony")
    if peg > 3.0:
        return _s("PEG Ratio", "BEARISH", "medium", f"PEG={peg:.2f} — drogi względem wzrostu")
    return None


def generate_signals(d: FundamentalData) -> list[Signal]:
    snapshot = [pe_signal, pb_signal, roe_signal, debt_signal,
                margin_signal, dividend_signal, liquidity_signal, ev_ebitda_signal,
                interest_coverage_signal, fcf_yield_signal, ev_fcf_signal,
                dividend_cagr_signal, pcf_signal]
    scoring = [piotroski_signal, graham_signal, altman_signal, peg_signal]
    trend = [revenue_growth_signal, earnings_growth_signal, margin_trend_signal, fcf_signal]
    return [s for fn in snapshot + scoring + trend if (s := fn(d)) is not None]
