from __future__ import annotations

import re
import urllib.request
from typing import Any

from ..models import YearlyRecord

_BASE = "https://www.biznesradar.pl"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9",
}
_SNAPSHOT_PAGES = [
    "wskazniki-wartosci-rynkowej",
    "wskazniki-rentownosci",
    "wskazniki-zadluzenia",
]
_HISTORY_YEARS = 5


def _fetch_html(path: str, ticker: str) -> str:
    url = f"{_BASE}/{path}/{ticker.upper()}"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_number(text: str) -> float | None:
    # Biznesradar: a space (or nbsp) is the thousands separator, a comma the decimal point.
    # Strip spaces FIRST and only then extract the number — otherwise "2 027 mln"
    # would be truncated to "2" (the thousands separator read as end of number).
    clean = text.strip().replace("\xa0", "").replace(" ", "")
    m = re.match(r"-?[\d.,]+", clean)
    if not m:
        return None
    token = m.group(0)
    if "," in token:
        # comma = decimal point; any dots are thousands separators
        token = token.replace(".", "").replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def _soup(html: str) -> Any:
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "lxml")


def _extract_newest(html: str) -> dict[str, float]:
    soup = _soup(html)
    table = soup.find("table", class_="report-table")
    if not table:
        return {}
    result: dict[str, float] = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        label = cells[0].get_text(strip=True)
        newest = row.find(["td", "th"], class_=lambda c: c and "newest" in c)
        if not newest:
            continue
        span = newest.find("span", class_="value")
        raw = span.get_text(strip=True) if span else newest.get_text(strip=True)
        val = _parse_number(raw)
        if val is not None:
            result[label] = val
    return result


def _extract_history_table(html: str, n: int = _HISTORY_YEARS) -> tuple[list[str], dict[str, list[float | None]]]:
    """Returns (year_labels, {row_label: [val_oldest..val_newest]})"""
    soup = _soup(html)
    table = soup.find("table", class_="report-table")
    if not table:
        return [], {}

    header_row = table.find("tr")
    all_headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

    # Annual columns: "2025(gru 25)" format
    annual_indices = [i for i, h in enumerate(all_headers) if re.match(r"\d{4}\(", h)]

    # Quarterly tables: pick Q4 columns "2025/Q4(gru 25)" as year-end proxies
    if not annual_indices:
        annual_indices = [i for i, h in enumerate(all_headers) if re.match(r"\d{4}/Q4\(", h)]

    selected = annual_indices[-n:] if len(annual_indices) >= n else annual_indices
    years = [re.match(r"(\d{4})", all_headers[i]).group(1) for i in selected]

    data: dict[str, list[float | None]] = {}
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        label = cells[0].get_text(strip=True)
        if not label:
            continue
        vals: list[float | None] = []
        for idx in selected:
            if idx < len(cells):
                span = cells[idx].find("span", class_="value")
                raw = span.get_text(strip=True) if span else cells[idx].get_text(strip=True)
                vals.append(_parse_number(raw))
            else:
                vals.append(None)
        data[label] = vals

    return years, data


def fetch_snapshot(ticker: str) -> dict[str, float]:
    data: dict[str, float] = {}
    for page in _SNAPSHOT_PAGES:
        try:
            html = _fetch_html(page, ticker)
            data.update(_extract_newest(html))
        except Exception:
            pass
    return data


def fetch_history(ticker: str) -> list[YearlyRecord]:
    try:
        income_html = _fetch_html("raporty-finansowe-rachunek-zyskow-i-strat", ticker)
        years, income = _extract_history_table(income_html)
    except Exception:
        return []

    try:
        cf_html = _fetch_html("raporty-finansowe-przeplywy-pieniezne", ticker)
        cf_years, cf = _extract_history_table(cf_html)
    except Exception:
        cf_years, cf = [], {}

    try:
        ratio_html = _fetch_html("wskazniki-rentownosci", ticker)
        ratio_years, ratios = _extract_history_table(ratio_html)
    except Exception:
        ratio_years, ratios = [], {}

    # Build year→index maps for each table
    cf_idx = {y: i for i, y in enumerate(cf_years)}
    ratio_idx = {y: i for i, y in enumerate(ratio_years)}

    def get_income(label: str, year_i: int, *fallbacks: str) -> float | None:
        for key in (label, *fallbacks):
            if key in income and year_i < len(income[key]):
                return income[key][year_i]
        return None

    def get_table(data: dict, idx_map: dict, year: str, *labels: str) -> float | None:
        i = idx_map.get(year)
        if i is None:
            return None
        for label in labels:
            if label in data and i < len(data[label]):
                return data[label][i]
        return None

    # Biznesradar reports amounts in thousands of PLN — we scale to absolute PLN
    # to stay consistent with the TTM data from yfinance (which is in full PLN).
    _K = 1000.0

    def _abs(v: float | None) -> float | None:
        return v * _K if v is not None else None

    records = []
    for i, year in enumerate(years):
        rev = get_income("Przychody ze sprzedaży", i, "Przychody odsetkowe", "Przychody")
        net = get_income("Zysk netto akcjonariuszy jednostki dominującej", i, "Zysk netto")
        ebitda = get_income("EBITDA", i)
        op = get_income("Wynik operacyjny", i)
        eps_val = get_income("Zysk na akcję", i)
        roe_val = get_table(ratios, ratio_idx, year, "ROE")
        margin_val = get_table(ratios, ratio_idx, year, "Marża zysku netto")
        op_cf = get_table(cf, cf_idx, year, "Przepływy pieniężne z działalności operacyjnej")
        capex_val = get_table(cf, cf_idx, year, "CAPEX (niematerialne i rzeczowe)")

        records.append(YearlyRecord(
            year=year,
            revenue=_abs(rev),
            net_income=_abs(net),
            ebitda=_abs(ebitda),
            operating_income=_abs(op),
            eps=eps_val,  # already PLN per share — no scaling
            roe=roe_val / 100 if roe_val is not None else None,
            profit_margin=margin_val / 100 if margin_val is not None else None,
            operating_cf=_abs(op_cf),
            capex=_abs(abs(capex_val)) if capex_val is not None else None,
        ))

    records.reverse()  # newest first
    return records


# Snapshot field mapping: Biznesradar label → FundamentalData field
FIELD_MAP: dict[str, str] = {
    "Cena / Zysk": "pe_trailing",
    "Cena / Wartość księgowa": "pb",
    "Zysk na akcję": "eps",
    "Wartość księgowa na akcję": "book_value",
    "Cena / Przychody ze sprzedaży": "ps_ratio",
    "Przychody ze sprzedaży na akcję": "revenue_per_share",
    "ROE": "roe_pct",
    "ROA": "roa_pct",
    "Marża zysku netto": "profit_margin_pct",
    "Marża zysku operacyjnego": "operating_margin_pct",
    "ROIC": "roic_pct",
    "Zadłużenie ogólne": "debt_ratio",
    "Zadłużenie kapitału własnego": "debt_to_equity_raw",
    "Zadłużenie netto / EBITDA": "net_debt_ebitda",
}
