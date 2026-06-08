from __future__ import annotations

import concurrent.futures

import yfinance as yf

from ...ticker_map import ticker_to_company, to_yahoo_ticker
from .printer import print_compare


def _fetch_one(ticker: str) -> dict:
    company = ticker_to_company(ticker)
    yahoo = to_yahoo_ticker(ticker)
    try:
        t = yf.Ticker(yahoo)
        info = t.info or {}

        def _f(*keys: str) -> float | None:
            for k in keys:
                v = info.get(k)
                if v is not None and v not in ("Infinity", float("inf"), float("-inf")):
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
            return None

        # FCF IC z financials
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
                ie = _gf("Interest Expense")
                if ebit is not None and ie and abs(ie) > 0:
                    interest_coverage = round(ebit / abs(ie), 2)
        except Exception:
            pass

        raw_dy = _f("dividendYield")
        div_yield: float | None = None
        if raw_dy is not None:
            norm = raw_dy / 100 if raw_dy > 1.0 else raw_dy
            div_yield = norm if norm <= 0.25 else None

        return {
            "ticker": ticker.upper(),
            "company": info.get("longName") or company,
            "currency": info.get("currency", ""),
            "price": _f("currentPrice", "regularMarketPrice"),
            "market_cap": _f("marketCap"),
            "pe": _f("trailingPE"),
            "pe_fwd": _f("forwardPE"),
            "pb": _f("priceToBook"),
            "ps": _f("priceToSalesTrailing12Months"),
            "ev_ebitda": _f("enterpriseToEbitda"),
            "roe": _f("returnOnEquity"),
            "roa": _f("returnOnAssets"),
            "margin": _f("profitMargins"),
            "op_margin": _f("operatingMargins"),
            "div_yield": div_yield,
            "debt_equity": _f("debtToEquity"),
            "beta": _f("beta"),
            "fcf": _f("freeCashflow"),
            "revenue": _f("totalRevenue"),
            "w52_high": _f("fiftyTwoWeekHigh"),
            "w52_low": _f("fiftyTwoWeekLow"),
            "interest_coverage": interest_coverage,
            "sector": info.get("sector", ""),
            "error": None,
        }
    except Exception as e:
        return {
            "ticker": ticker.upper(), "company": company, "currency": "",
            "error": str(e)[:60],
        }


def run_compare(tickers: list[str]) -> None:
    if len(tickers) < 2:
        print("  Porównanie wymaga co najmniej 2 tickerów.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in tickers}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    order = {t.upper(): i for i, t in enumerate(tickers)}
    results.sort(key=lambda r: order.get(r["ticker"], 999))
    print_compare(results)
