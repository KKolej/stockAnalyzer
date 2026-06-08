from __future__ import annotations

from .models import ScreenerFilters, ScreenerRow

_SORT_FIELD = {
    "pe":     lambda r: r.pe,
    "pb":     lambda r: r.pb,
    "roe":    lambda r: r.roe,
    "roa":    lambda r: r.roa,
    "div":    lambda r: r.dividend_yield,
    "cap":    lambda r: r.market_cap,
    "margin": lambda r: r.profit_margin,
    "beta":   lambda r: r.beta,
    "52w":    lambda r: r.week_52_change,
    "fcf":    lambda r: r.fcf_yield,
    "ic":     lambda r: r.interest_coverage,
    "magic":  lambda r: r.magic_rank,
    "ey":     lambda r: r.earnings_yield,
}


def _passes(row: ScreenerRow, f: ScreenerFilters) -> bool:
    if not row.available:
        return False

    def ok_max(val: float | None, limit: float | None) -> bool:
        return limit is None or (val is not None and val <= limit)

    def ok_min(val: float | None, limit: float | None) -> bool:
        return limit is None or (val is not None and val >= limit)

    checks = [
        ok_max(row.pe, f.pe_max),
        ok_min(row.pe, f.pe_min),
        ok_max(row.pb, f.pb_max),
        ok_min(row.roe * 100 if row.roe else None, f.roe_min),
        ok_min(row.roa * 100 if row.roa else None, f.roa_min),
        ok_min(row.profit_margin * 100 if row.profit_margin else None, f.margin_min),
        ok_min(row.dividend_yield * 100 if row.dividend_yield else None, f.div_min),
        ok_max(row.debt_to_equity, f.debt_max),
        ok_max(row.beta, f.beta_max),
        ok_min(row.fcf_yield * 100 if row.fcf_yield else None, f.fcf_yield_min),
        ok_min(row.interest_coverage, f.ic_min),
    ]
    if f.market_cap_min is not None:
        checks.append(ok_min(row.market_cap / 1e6 if row.market_cap else None, f.market_cap_min))
    if f.market_cap_max is not None:
        checks.append(ok_max(row.market_cap / 1e6 if row.market_cap else None, f.market_cap_max))

    return all(checks)


def _apply_magic_formula(rows: list[ScreenerRow]) -> list[ScreenerRow]:
    """
    Greenblatt Magic Formula: rank by Earnings Yield + Return on Capital.
    Earnings Yield = 1/EV_EBITDA (proxy EBIT/EV).
    Return on Capital = ROE (proxy).
    Final rank = rank_EY + rank_ROC (lower = better).
    """
    # Ranking Earnings Yield (wyższy = lepszy → niższy rank)
    with_ey = [(i, r) for i, r in enumerate(rows) if r.earnings_yield is not None]
    with_ey.sort(key=lambda x: x[1].earnings_yield, reverse=True)  # type: ignore
    ey_ranks = {i: rank for rank, (i, _) in enumerate(with_ey, 1)}

    # Ranking ROE (wyższy = lepszy → niższy rank)
    with_roe = [(i, r) for i, r in enumerate(rows) if r.roe is not None]
    with_roe.sort(key=lambda x: x[1].roe, reverse=True)  # type: ignore
    roe_ranks = {i: rank for rank, (i, _) in enumerate(with_roe, 1)}

    for i, r in enumerate(rows):
        ey_r = ey_ranks.get(i, len(rows) + 1)
        roe_r = roe_ranks.get(i, len(rows) + 1)
        r.magic_rank = ey_r + roe_r

    return rows


def apply_filters(rows: list[ScreenerRow], f: ScreenerFilters) -> list[ScreenerRow]:
    filtered = [r for r in rows if _passes(r, f)]

    if f.magic_formula:
        filtered = _apply_magic_formula(filtered)
        f.sort_by = "magic"
        f.sort_asc = True

    getter = _SORT_FIELD.get(f.sort_by, _SORT_FIELD["pe"])

    has_val = [r for r in filtered if getter(r) is not None]
    no_val  = [r for r in filtered if getter(r) is None]

    has_val.sort(key=lambda r: getter(r), reverse=not f.sort_asc)  # type: ignore[arg-type]
    filtered = has_val + no_val

    if f.top:
        filtered = filtered[: f.top]
    return filtered
