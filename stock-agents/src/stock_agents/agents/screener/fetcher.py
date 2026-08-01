from __future__ import annotations

import concurrent.futures

import yfinance as yf

from ...ticker_map import ticker_to_company, to_yahoo_ticker
from .models import ScreenerRow


def _safe_float(info: dict, *keys: str) -> float | None:
    for key in keys:
        val = info.get(key)
        if val is not None and val not in ("Infinity", float("inf"), float("-inf")):
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def _normalize_yield(val: float | None) -> float | None:
    if val is None:
        return None
    norm = val / 100 if val > 1.0 else val
    return norm if norm <= 0.25 else None


def _fetch_one(ticker: str) -> ScreenerRow:
    company = ticker_to_company(ticker)
    yahoo = to_yahoo_ticker(ticker)
    try:
        t = yf.Ticker(yahoo)
        info = t.info
        if not info or (info.get("marketCap") is None and info.get("currentPrice") is None):
            return ScreenerRow(
                ticker=ticker.upper(), company=company, price=None, currency="",
                market_cap=None, pe=None, pb=None, ps=None, roe=None, roa=None,
                profit_margin=None, dividend_yield=None, debt_to_equity=None,
                week_52_change=None, beta=None, error="Brak danych",
            )

        price = _safe_float(info, "currentPrice", "regularMarketPrice")
        w52_high = _safe_float(info, "fiftyTwoWeekHigh")
        w52_low = _safe_float(info, "fiftyTwoWeekLow")
        w52_change: float | None = None
        if price and w52_low and w52_high and w52_low > 0:
            # Price change off the 52W low as a momentum proxy
            w52_change = (price - w52_low) / w52_low

        fcf = _safe_float(info, "freeCashflow")
        mc = _safe_float(info, "marketCap")
        fcf_yield = (fcf / mc) if fcf and mc and mc > 0 and fcf > 0 else None

        # Earnings Yield ≈ 1 / EV_EBITDA (proxy EBIT/EV)
        ev_ebitda = _safe_float(info, "enterpriseToEbitda")
        earnings_yield = (1.0 / ev_ebitda) if ev_ebitda and ev_ebitda > 0 else None

        # Interest Coverage = EBIT / Interest Expense (from financials)
        interest_coverage: float | None = None
        try:
            fin = t.financials
            if fin is not None and not fin.empty:
                def _gf(row: str) -> float | None:
                    try:
                        return float(fin.loc[row].iloc[0])
                    except Exception:
                        return None
                ebit = _gf("EBIT")
                if ebit is None:
                    pretax = _gf("Pretax Income")
                    interest_raw = _gf("Interest Expense")
                    if pretax is not None and interest_raw is not None:
                        ebit = pretax + abs(interest_raw)
                interest_exp = _gf("Interest Expense")
                if interest_exp and abs(interest_exp) > 0 and ebit is not None:
                    interest_coverage = round(ebit / abs(interest_exp), 2)
        except Exception:
            pass

        return ScreenerRow(
            ticker=ticker.upper(),
            company=info.get("longName") or company,
            price=price,
            currency=info.get("currency", ""),
            market_cap=mc,
            pe=_safe_float(info, "trailingPE"),
            pb=_safe_float(info, "priceToBook"),
            ps=_safe_float(info, "priceToSalesTrailing12Months"),
            roe=_safe_float(info, "returnOnEquity"),
            roa=_safe_float(info, "returnOnAssets"),
            profit_margin=_safe_float(info, "profitMargins"),
            dividend_yield=_normalize_yield(_safe_float(info, "dividendYield")),
            debt_to_equity=_safe_float(info, "debtToEquity"),
            week_52_change=w52_change,
            beta=_safe_float(info, "beta"),
            fcf_yield=fcf_yield,
            earnings_yield=earnings_yield,
            interest_coverage=interest_coverage,
            sector=info.get("sector"),
        )
    except Exception as e:
        return ScreenerRow(
            ticker=ticker.upper(), company=company, price=None, currency="",
            market_cap=None, pe=None, pb=None, ps=None, roe=None, roa=None,
            profit_margin=None, dividend_yield=None, debt_to_equity=None,
            week_52_change=None, beta=None, fcf_yield=None,
            earnings_yield=None, interest_coverage=None,
            error=str(e)[:60],
        )


def fetch_all(tickers: list[str], workers: int = 10) -> list[ScreenerRow]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in tickers}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    # Preserve input order
    order = {t.upper(): i for i, t in enumerate(tickers)}
    results.sort(key=lambda r: order.get(r.ticker, 999))
    return results
