from __future__ import annotations

import dataclasses as dc
import functools
import math

import yfinance as yf

from ...ticker_map import is_gpw, to_yahoo_ticker
from .models import FundamentalData, YearlyRecord
from .sources.biznesradar import FIELD_MAP
from .sources.biznesradar import fetch_history as br_history
from .sources.biznesradar import fetch_snapshot as br_snapshot

# Maps internal FIELD_MAP names to FundamentalData fields (no conversion)
_BR_DIRECT: dict[str, str] = {
    "pe_trailing":        "pe_trailing",
    "pb":                 "pb",
    "eps":                "eps",
    "book_value":         "book_value",
    "ps_ratio":           "ps_ratio",
    "debt_to_equity_raw": "debt_to_equity",
    "net_debt_ebitda":    "net_debt_ebitda",
}
# Percentage fields from Biznesradar (value in %, model stores a fraction)
_BR_PCT: dict[str, str] = {
    "roe_pct":              "roe",
    "roa_pct":              "roa",
    "roic_pct":             "roic",
    "profit_margin_pct":    "profit_margin",
    "operating_margin_pct": "operating_margin",
}


# Piotroski's F-Score is defined on 9 criteria; we evaluate the subset yfinance covers.
_PIOTROSKI_SCALE = 9


def _normalize_yield(val: float | None) -> float | None:
    if val is None:
        return None
    normalized = val / 100 if val > 1.0 else val
    return normalized if normalized <= 0.25 else None


def _get(info: dict, *keys: str) -> float | None:
    for key in keys:
        val = info.get(key)
        if val is not None and val != "Infinity" and val != float("inf"):
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def _empty(ticker: str, company: str, error: str) -> FundamentalData:
    return FundamentalData(
        ticker=ticker, company=company, currency="",
        price=None, market_cap=None, pe_trailing=None, pe_forward=None,
        pb=None, ev_ebitda=None, ps_ratio=None, revenue=None, ebitda=None,
        eps=None, profit_margin=None, operating_margin=None, roe=None,
        roa=None, roic=None, current_ratio=None, quick_ratio=None,
        debt_to_equity=None, net_debt_ebitda=None, interest_coverage=None,
        fcf_ttm=None, fcf_yield=None, ev_fcf=None,
        dividend_yield=None, payout_ratio=None, dividend_cagr=None,
        beta=None, week_52_high=None, week_52_low=None,
        book_value=None, error=error,
    )


def _col_get(df, col: object, *rows: str) -> float | None:
    """Extracts a value from DataFrame df for the given column and first matching row."""
    for r in rows:
        try:
            v = df.loc[r, col]
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                return float(v)
        except (KeyError, TypeError, ValueError):
            pass
    return None


def _col_for_col(col: object, df, *rows: str) -> float | None:
    """Variant of `_col_get` with the column first (for `functools.partial`)."""
    return _col_get(df, col, *rows)


def _yf_history(ticker: str) -> list[YearlyRecord]:
    """Fetches annual data from yfinance (for US stocks)."""
    try:
        t = yf.Ticker(to_yahoo_ticker(ticker))
        fin = t.financials
        cf = t.cashflow
        if fin is None or fin.empty:
            return []

        records = []
        for col in list(fin.columns)[:5]:
            g = functools.partial(_col_for_col, col)
            rev = g(fin, "Total Revenue")
            net = g(fin, "Net Income", "Net Income Common Stockholders")
            ebitda = g(fin, "EBITDA", "Normalized EBITDA")
            op = g(fin, "Operating Income", "EBIT")
            has_cf = cf is not None and not cf.empty
            op_cf = (g(cf, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities")
                     if has_cf else None)
            capex_raw = g(cf, "Capital Expenditure") if has_cf else None
            capex = abs(capex_raw) if capex_raw is not None else None
            margin = net / rev if net and rev else None
            records.append(YearlyRecord(
                year=str(col.year),
                revenue=rev,
                net_income=net,
                ebitda=ebitda,
                operating_income=op,
                profit_margin=margin,
                operating_cf=op_cf,
                capex=capex,
            ))
        return records
    except Exception:
        return []


def _from_yfinance(ticker: str, company: str) -> FundamentalData:
    yahoo_ticker = to_yahoo_ticker(ticker)
    try:
        info = yf.Ticker(yahoo_ticker).info
    except Exception as e:
        return _empty(ticker, company, str(e))

    if not info or (info.get("trailingPE") is None and info.get("marketCap") is None):
        return _empty(ticker, company, "Brak danych fundamentalnych")

    return FundamentalData(
        ticker=ticker,
        company=info.get("longName") or company,
        currency=info.get("currency", ""),
        price=_get(info, "currentPrice", "regularMarketPrice"),
        market_cap=_get(info, "marketCap"),
        pe_trailing=_get(info, "trailingPE"),
        pe_forward=_get(info, "forwardPE"),
        pb=_get(info, "priceToBook"),
        ev_ebitda=_get(info, "enterpriseToEbitda"),
        ps_ratio=_get(info, "priceToSalesTrailing12Months"),
        revenue=_get(info, "totalRevenue"),
        ebitda=_get(info, "ebitda"),
        sector=info.get("sector", "") or "",
        eps=_get(info, "trailingEps"),
        profit_margin=_get(info, "profitMargins"),
        operating_margin=_get(info, "operatingMargins"),
        roe=_get(info, "returnOnEquity"),
        roa=_get(info, "returnOnAssets"),
        roic=None,
        current_ratio=_get(info, "currentRatio"),
        quick_ratio=_get(info, "quickRatio"),
        debt_to_equity=_get(info, "debtToEquity"),
        net_debt_ebitda=None,
        interest_coverage=None,
        fcf_ttm=_get(info, "freeCashflow"),
        fcf_yield=None,
        ev_fcf=None,
        dividend_yield=_normalize_yield(_get(info, "dividendYield")),
        payout_ratio=_get(info, "payoutRatio"),
        dividend_cagr=None,
        beta=_get(info, "beta"),
        week_52_high=_get(info, "fiftyTwoWeekHigh"),
        week_52_low=_get(info, "fiftyTwoWeekLow"),
        book_value=_get(info, "bookValue"),
    )


def _overlay_biznesradar(d: FundamentalData, ticker: str) -> FundamentalData:
    """Overrides yfinance fields with Biznesradar data (GPW data is better on BR than YF)."""
    raw = br_snapshot(ticker)
    if not raw:
        return d
    mapped = {FIELD_MAP[k]: v for k, v in raw.items() if k in FIELD_MAP}
    if not mapped:
        return d

    overrides: dict = {}
    for src, dst in _BR_DIRECT.items():
        if (v := mapped.get(src)) is not None:
            overrides[dst] = v
    for src, dst in _BR_PCT.items():
        if (v := mapped.get(src)) is not None:
            overrides[dst] = v / 100

    # Biznesradar computes C/Z and C/WK against ITS OWN "Kurs", which can lag the market
    # badly (2026-08-02: PEO 228.80 vs 245.50, ALE 26.36 vs 44.99 — Allegro's snapshot was
    # over a year old). Copied verbatim, those ratios landed next to a fresh price and
    # contradicted it: P/E 9.27 printed beside an EPS that implies 9.95. The per-share
    # values come from the reports and are worth taking as they are; every ratio that
    # divides by a price we recompute on OUR price — which is what the market quotes.
    per_share = {
        "pe_trailing": overrides.get("eps", d.eps),
        "pb": overrides.get("book_value", d.book_value),
        "ps_ratio": mapped.get("revenue_per_share"),
    }
    recomputed: list[str] = []
    if d.price and d.price > 0:
        for ratio, value in per_share.items():
            if value and value > 0:
                overrides[ratio] = round(d.price / value, 2)
                recomputed.append(ratio)

    overrides["quality"] = {
        "price": d.price,
        "biznesradar_price": raw.get("Kurs"),
        "ratios_recomputed_on_price": recomputed,
    }
    return dc.replace(d, **overrides)


def _calc_scores(data: FundamentalData, yahoo_ticker: str) -> FundamentalData:
    """Computes scoring, DuPont, P/CF and derived ratios."""
    t = yf.Ticker(yahoo_ticker)
    try:
        info = t.info or {}
        fin = t.financials
        bs = t.balance_sheet
        cf = t.cashflow
    except Exception:
        return data

    # ── DuPont analysis (ROE = margin × turnover × leverage) ────────────────
    # All three factors come from the same balance sheet so the product stays consistent:
    # (NI/Rev) × (Rev/Assets) × (Assets/Equity) = NI/Equity = ROE.
    if data.profit_margin is not None:
        data.dupont_margin = data.profit_margin
    assets_dup: float | None = None
    if data.revenue and data.revenue > 0 and bs is not None and not bs.empty:
        try:
            if "Total Assets" in bs.index:
                assets_dup = float(bs.loc["Total Assets"].iloc[0])
                if assets_dup and assets_dup > 0:
                    data.dupont_asset_turnover = data.revenue / assets_dup
        except Exception:
            pass
    # Leverage = assets / equity (equity multiplier — always >= 1)
    if assets_dup and assets_dup > 0 and bs is not None and not bs.empty:
        try:
            equity_dup = None
            for row in ("Common Stock Equity", "Stockholders Equity",
                        "Total Equity Gross Minority Interest"):
                if row in bs.index:
                    equity_dup = float(bs.loc[row].iloc[0])
                    break
            if equity_dup and equity_dup > 0:
                data.dupont_leverage = assets_dup / equity_dup
        except Exception:
            pass

    # ── Price to Cash Flow (P/CF) ────────────────────────────────────────────
    op_cf_val = info.get("operatingCashflow")
    shares = info.get("sharesOutstanding")
    if op_cf_val and shares and float(shares) > 0 and data.price:
        cf_per_share = float(op_cf_val) / float(shares)
        if cf_per_share > 0:
            data.price_to_cf = round(data.price / cf_per_share, 2)

    # ── Graham Number ────────────────────────────────────────────────────────
    if data.eps and data.book_value and data.eps > 0 and data.book_value > 0:
        data.graham_number = math.sqrt(22.5 * data.eps * data.book_value)

    # ── PEG Ratio ────────────────────────────────────────────────────────────
    if data.pe_trailing and data.pe_trailing > 0 and len(data.history) >= 2:
        ni_vals = [(r.year, r.net_income) for r in data.history if r.net_income and r.net_income > 0]
        if len(ni_vals) >= 2:
            newest_y, newest_ni = ni_vals[0]
            oldest_y, oldest_ni = ni_vals[-1]
            years = int(newest_y) - int(oldest_y)
            if years > 0 and oldest_ni > 0:
                cagr = (newest_ni / oldest_ni) ** (1 / years) - 1
                growth_pct = cagr * 100
                if growth_pct > 1:
                    data.peg_ratio = data.pe_trailing / growth_pct

    # ── Piotroski F-Score & Altman Z-Score ──────────────────────────────────
    if fin is None or fin.empty or bs is None or bs.empty:
        return data

    def gf(df, row: str, col: int = 0) -> float | None:
        try:
            return float(df.loc[row].iloc[col])
        except Exception:
            return None

    ni          = gf(fin, "Net Income")
    ni_prev     = gf(fin, "Net Income", 1)
    rev         = gf(fin, "Total Revenue")
    rev_prev    = gf(fin, "Total Revenue", 1)
    assets      = gf(bs, "Total Assets")
    assets_prev = gf(bs, "Total Assets", 1)
    lt_debt      = gf(bs, "Long Term Debt And Capital Lease Obligation")
    lt_debt_prev = gf(bs, "Long Term Debt And Capital Lease Obligation", 1)
    retained    = gf(bs, "Retained Earnings")
    shares_out  = gf(bs, "Share Issued")
    shares_prev = gf(bs, "Share Issued", 1)
    op_cf_gf    = gf(cf, "Operating Cash Flow") if cf is not None and not cf.empty else None
    total_liab  = gf(bs, "Total Liabilities Net Minority Interest")

    # ── Piotroski F-Score ────────────────────────────────────────────────────
    score, max_score = 0, 0

    def add(condition: bool | None) -> None:
        nonlocal score, max_score
        if condition is None:
            return
        max_score += 1
        if condition:
            score += 1

    add(ni is not None and assets and assets > 0 and ni / assets > 0)       # F_ROA
    add(op_cf_gf is not None and op_cf_gf > 0)                              # F_CFO
    if ni and ni_prev and assets and assets_prev and assets_prev > 0 and assets > 0:
        add(ni / assets > ni_prev / assets_prev)                             # F_ΔROA
    if ni is not None and op_cf_gf is not None:
        add(op_cf_gf > ni)                                                   # F_ACCRUAL
    if lt_debt is not None and lt_debt_prev is not None and assets and assets_prev and assets_prev > 0 and assets > 0:
        add(lt_debt / assets < lt_debt_prev / assets_prev)                  # F_ΔLEVER
    if shares_out is not None and shares_prev is not None:
        add(shares_out <= shares_prev)                                       # EQ_OFFER
    if rev and rev_prev and assets and assets_prev and assets_prev > 0 and assets > 0:
        add(rev / assets > rev_prev / assets_prev)                          # F_ΔTURN

    if max_score >= 4:
        data.piotroski_score = score
        data.piotroski_max = max_score
        data.piotroski_scale = _PIOTROSKI_SCALE

    # ── Altman Z'' Score (non-financial, non-manufacturing) ──────────────────
    # Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
    # X1 = Working Capital / Total Assets (WC level from the balance sheet, NOT the CF change)
    # X2 = Retained Earnings / Total Assets
    # X3 = EBIT / Total Assets
    # X4 = Book Value Equity / Total Liabilities
    if assets and assets > 0:
        ebit = gf(fin, "EBIT")
        if ebit is None:
            pretax = gf(fin, "Pretax Income")
            interest = gf(fin, "Interest Expense")
            if pretax is not None and interest is not None:
                ebit = pretax + abs(interest)

        equity = gf(bs, "Common Stock Equity") or gf(bs, "Stockholders Equity")
        curr_assets = gf(bs, "Current Assets")
        curr_liab   = gf(bs, "Current Liabilities")
        working_capital = (
            (curr_assets - curr_liab)
            if curr_assets is not None and curr_liab is not None
            else None
        )

        x1 = (working_capital / assets) if working_capital is not None else None
        x2 = (retained / assets) if retained else None
        x3 = (ebit / assets) if ebit else None
        x4 = (equity / total_liab) if equity and total_liab and total_liab > 0 else None

        if x3 is not None and x4 is not None:
            z = 6.72 * x3 + 1.05 * x4
            if x1 is not None:
                z += 6.56 * x1
            if x2 is not None:
                z += 3.26 * x2
            data.altman_z = round(z, 2)

    # ── Interest Coverage Ratio (EBIT / Odsetki) ─────────────────────────────
    ebit_ic = gf(fin, "EBIT")
    if ebit_ic is None:
        pretax_ic = gf(fin, "Pretax Income")
        int_ic = gf(fin, "Interest Expense")
        if pretax_ic is not None and int_ic is not None:
            ebit_ic = pretax_ic + abs(int_ic)
    interest_exp = gf(fin, "Interest Expense")
    if ebit_ic and interest_exp and abs(interest_exp) > 0:
        data.interest_coverage = round(ebit_ic / abs(interest_exp), 2)

    # ── TTM FCF from cash flow (for GPW, where yfinance has no freeCashflow) ──
    if data.fcf_ttm is None and cf is not None and not cf.empty:
        op_cf_ttm = gf(cf, "Operating Cash Flow")
        capex_ttm = gf(cf, "Capital Expenditure")
        if op_cf_ttm is not None and capex_ttm is not None:
            data.fcf_ttm = op_cf_ttm + capex_ttm  # capex is negative in yfinance
        elif op_cf_ttm is not None:
            data.fcf_ttm = op_cf_ttm

    # ── FCF Yield & EV/FCF ───────────────────────────────────────────────────
    fcf = data.fcf_ttm
    mc = data.market_cap
    if fcf and mc and mc > 0 and fcf > 0:
        data.fcf_yield = fcf / mc
    ev_val = _get(info, "enterpriseValue")
    if fcf and fcf > 0 and ev_val and ev_val > 0:
        data.ev_fcf = round(ev_val / fcf, 2)

    # ── Dividend CAGR (from yfinance dividend history) ────────────────────────
    try:
        divs = t.dividends
        if divs is not None and len(divs) >= 4:
            divs = divs.copy()
            divs.index = divs.index.tz_localize(None) if divs.index.tz else divs.index
            df_divs = divs.reset_index()
            df_divs.columns = ["Date", "Div"]
            df_divs["Year"] = df_divs["Date"].dt.year
            yearly = df_divs.groupby("Year")["Div"].sum()
            years_list = sorted(yearly.index)
            if len(years_list) >= 3:
                first_y, last_y = years_list[0], years_list[-1]
                n_years = last_y - first_y
                if n_years > 0 and yearly[first_y] > 0 and yearly[last_y] > 0:
                    data.dividend_cagr = (yearly[last_y] / yearly[first_y]) ** (1 / n_years) - 1
    except Exception:
        pass

    return data


def fetch(ticker: str, company: str) -> FundamentalData:
    data = _from_yfinance(ticker, company)
    if data.error:
        return data

    yahoo_ticker = to_yahoo_ticker(ticker)

    if is_gpw(ticker):
        data = _overlay_biznesradar(data, ticker)
        data.history = br_history(ticker)
    else:
        data.history = _yf_history(ticker)

    data = _calc_scores(data, yahoo_ticker)
    return data
