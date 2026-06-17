from __future__ import annotations

from .models import DCFResult, DCFScenario


def _dcf_value(fcf_ttm: float, growth: float, terminal_growth: float,
               wacc: float, years: int, net_debt: float, shares: float) -> float | None:
    """Zwraca wycenę DCF na akcję."""
    if wacc <= terminal_growth:
        return None
    if shares <= 0:
        return None

    pv = 0.0
    fcf = fcf_ttm
    for t in range(1, years + 1):
        fcf *= (1 + growth)
        pv += fcf / (1 + wacc) ** t

    # Terminal value (Gordon Growth)
    terminal_fcf = fcf * (1 + terminal_growth)
    tv = terminal_fcf / (wacc - terminal_growth)
    pv_tv = tv / (1 + wacc) ** years

    equity_value = pv + pv_tv - net_debt
    return equity_value / shares


def _estimate_wacc(beta: float | None, debt_to_equity: float | None,
                   currency: str) -> float:
    """Prosta aproksymacja WACC na podstawie beta i struktury kapitału."""
    # Risk-free: ~4.5% USD, ~5.5% PLN
    rf = 0.055 if currency == "PLN" else 0.045
    erp = 0.055  # equity risk premium
    b = beta if beta and 0.3 <= beta <= 3.0 else 1.0
    ke = rf + b * erp  # koszt kapitału własnego (CAPM)

    if debt_to_equity and debt_to_equity > 0:
        # D/E w % → ułamek (yfinance podaje np. 50.0 = 50%)
        de_frac = debt_to_equity / 100
        weight_e = 1 / (1 + de_frac)
        weight_d = de_frac / (1 + de_frac)
        kd_after_tax = 0.05 * (1 - 0.19)  # koszt długu po podatku ~4%
        wacc = weight_e * ke + weight_d * kd_after_tax
    else:
        wacc = ke

    return round(max(min(wacc, 0.20), 0.06), 4)


def build_scenarios(result: DCFResult, beta: float | None,
                    debt_to_equity: float | None) -> DCFResult:
    if not result.available:
        return result

    fcf = result.fcf_ttm
    nd = result.net_debt or 0.0
    shares = result.shares or 1.0
    price = result.price or 0.0
    years = result.projection_years

    wacc = _estimate_wacc(beta, debt_to_equity, result.currency)
    result.wacc_base = wacc

    # Warianty: (fcf_growth, terminal_growth, wacc_delta)
    scenario_params = [
        ("Base", 0.08,  0.03,  0.00),
        ("Bull", 0.15,  0.04, -0.01),
        ("Bear", 0.02,  0.02, +0.02),
    ]

    scenarios = []
    for name, g, tg, dw in scenario_params:
        w = round(wacc + dw, 4)
        fv = _dcf_value(fcf, g, tg, w, years, nd, shares)
        upside = (fv / price - 1) if fv and price > 0 else None
        scenarios.append(DCFScenario(
            name=name, fcf_growth=g, terminal_growth=tg, wacc=w,
            fair_value=round(fv, 2) if fv else None,
            upside=round(upside, 4) if upside is not None else None,
        ))

    result.scenarios = scenarios
    return result
