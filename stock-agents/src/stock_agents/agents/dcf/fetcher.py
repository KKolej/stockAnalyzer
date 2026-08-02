from __future__ import annotations

import yfinance as yf

from ...ticker_map import ticker_to_company, to_yahoo_ticker
from .models import DCFResult

# An FCF-based DCF does not describe banks or insurers: for them cash flow is the product,
# not a residual, so "free cash flow" carries no information about owner value. Run anyway
# it produced pure noise dressed up as a valuation — Pekao base 870.97 PLN against a 245.50
# market price, PZU bull 1076.87 — and each report then had to spend a paragraph explaining
# why it was ignoring its own number. Better to say up front that the model does not apply.
_DCF_EXCLUDED_SECTORS = {"financial services", "financials", "insurance"}


def fetch(ticker: str, projection_years: int = 10) -> DCFResult:
    company = ticker_to_company(ticker)
    yahoo = to_yahoo_ticker(ticker)

    try:
        t = yf.Ticker(yahoo)
        info = t.info or {}

        price = (info.get("currentPrice") or info.get("regularMarketPrice"))
        currency = info.get("currency", "")
        shares = info.get("sharesOutstanding")
        fcf_raw = info.get("freeCashflow")
        total_debt = info.get("totalDebt") or 0.0
        cash = info.get("totalCash") or 0.0
        net_debt = float(total_debt) - float(cash)
        beta = info.get("beta")
        dte = info.get("debtToEquity")

        sector = str(info.get("sector") or "").strip().lower()
        if sector in _DCF_EXCLUDED_SECTORS:
            return DCFResult(
                ticker=ticker.upper(), company=info.get("longName") or company, currency=currency,
                price=float(price) if price is not None else None, shares=None, fcf_ttm=None,
                net_debt=net_debt, wacc_base=0.0, projection_years=projection_years,
                error=f"DCF nie ma zastosowania do sektora '{info.get('sector')}' "
                      f"(model FCF nie opisuje banków ani ubezpieczycieli) — "
                      f"użyj P/BV wobec ROE i liczby Grahama.",
            )

        if price is None or shares is None:
            return DCFResult(
                ticker=ticker.upper(), company=company, currency=currency,
                price=None, shares=None, fcf_ttm=None, net_debt=net_debt,
                wacc_base=0.0, projection_years=projection_years,
                error="Brak danych cenowych lub akcji",
            )

        # FCF from info or from the cash flow statement
        fcf: float | None = float(fcf_raw) if fcf_raw is not None else None
        if fcf is None:
            try:
                cf = t.cashflow
                if cf is not None and not cf.empty:
                    def _cf(row: str) -> float | None:
                        try:
                            return float(cf.loc[row].iloc[0])
                        except Exception:
                            return None
                    op = _cf("Operating Cash Flow") or _cf("Total Cash From Operating Activities")
                    cap = _cf("Capital Expenditure") or _cf("Capital Expenditures")
                    if op is not None and cap is not None:
                        fcf = op + cap  # capex is negative in yfinance
            except Exception:
                pass

        result = DCFResult(
            ticker=ticker.upper(),
            company=info.get("longName") or company,
            currency=currency,
            price=float(price),
            shares=float(shares),
            fcf_ttm=fcf,
            net_debt=net_debt,
            wacc_base=0.0,
            projection_years=projection_years,
        )

        from .calculator import build_scenarios
        return build_scenarios(result, beta, dte)

    except Exception as e:
        return DCFResult(
            ticker=ticker.upper(), company=company, currency="",
            price=None, shares=None, fcf_ttm=None, net_debt=None,
            wacc_base=0.0, projection_years=projection_years,
            error=str(e)[:80],
        )
