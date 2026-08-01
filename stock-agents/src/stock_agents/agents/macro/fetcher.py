from __future__ import annotations

import contextlib
import json
import re
import urllib.request
from datetime import date

import yfinance as yf

from .models import FxRate, MacroData, SectorPerf

_NBP = "https://api.nbp.pl/api"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_FX_CODES = [("usd", "Dolar USD"), ("eur", "Euro EUR"), ("chf", "Frank CHF"), ("gbp", "Funt GBP")]
_SECTORS = [
    ("Banki",    "WIG-BANKI.WA"),
    ("Paliwa",   "WIG-PALIWA.WA"),
    ("Info/Tech","WIG-INFO.WA"),
    ("Odzież",   "WIG-ODZIEZ.WA"),
    ("Budownictwo","WIG-BUDOW.WA"),
    ("Chemia",   "WIG-CHEMIA.WA"),
    ("Media",    "WIG-MEDIA.WA"),
    ("Spożywczy","WIG-SPOZYW.WA"),
]


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())


def _biznesradar_52w(symbol: str) -> tuple[float, float] | None:
    """52-week range of a GPW index from Biznesradar.

    For Polish indices (WIG20.WA, WIG-BANKI.WA…) yfinance returns a SINGLE session's
    range in `fiftyTwoWeekLow/High` — for WIG20 that was 3891.59/3928.98 instead of
    2725.91/3928.98. The resulting "52W position" came out as 77% instead of 99%,
    a completely misleading signal. Stooq (the second source) now serves an anti-bot
    wall, so we use Biznesradar, which we scrape anyway.
    """
    try:
        from bs4 import BeautifulSoup

        name = symbol.removesuffix(".WA")
        req = urllib.request.Request(
            f"https://www.biznesradar.pl/notowania/{name}", headers=_HEADERS
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            soup = BeautifulSoup(r.read(), "lxml")

        text = re.sub(r"\s+", " ", soup.get_text(" "))
        m = re.search(
            r"Min 52 tyg\s*:?\s*([\d\s.,]+?)\s+Max 52 tyg\s*:?\s*([\d\s.,]+?)\s", text
        )
        if not m:
            return None
        low = float(m.group(1).replace(" ", "").replace("\xa0", "").replace(",", "."))
        high = float(m.group(2).replace(" ", "").replace("\xa0", "").replace(",", "."))
        if high <= low:
            return None
        return low, high
    except Exception:
        return None


def _pos_in_range(price: float, low: float, high: float) -> float | None:
    if high <= low:
        return None
    return (price - low) / (high - low) * 100


def _fetch_fx(data: MacroData) -> None:
    for code, name in _FX_CODES:
        try:
            current = _get_json(f"{_NBP}/exchangerates/rates/a/{code}/?format=json")
            rate = current["rates"][0]["mid"]
            rate_date = current["rates"][0]["effectiveDate"]

            # 3M trend
            hist = _get_json(f"{_NBP}/exchangerates/rates/a/{code}/last/65/?format=json")
            rates_hist = hist["rates"]
            change_3m = None
            if len(rates_hist) >= 2:
                old = rates_hist[0]["mid"]
                change_3m = (rate - old) / old * 100

            data.fx.append(FxRate(code=code.upper(), name=name, rate=rate,
                                  date=rate_date, change_3m=change_3m))
        except Exception as e:
            data.errors.append(f"FX {code.upper()}: {e}")


def _fetch_gold(data: MacroData) -> None:
    try:
        d = _get_json(f"{_NBP}/cenyzlota/?format=json")
        data.gold_pln = d[0]["cena"]
        data.gold_date = d[0]["data"]
    except Exception as e:
        data.errors.append(f"Złoto: {e}")


def _fetch_cpi(data: MacroData) -> None:
    # CAUTION: /notowania/CPI is the listed company "CPI FIM SA", NOT the inflation index.
    # Inflation lives in the macro indicator table as an index of 100+x (103.10 -> +3.1% YoY).
    try:
        from bs4 import BeautifulSoup
        req = urllib.request.Request(
            "https://www.biznesradar.pl/wskazniki-makroekonomiczne/inflacja-cpi",
            headers=_HEADERS,
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            soup = BeautifulSoup(r.read(), "lxml")

        table = soup.find("table")
        if not table:
            return
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            # ['Inflacja r/r (M)', '07.2026', '103.00', '+0.50']
            if len(cells) >= 3 and cells[0].startswith("Inflacja r/r"):
                index_val = float(cells[2].replace(",", "."))
                data.cpi_value = index_val
                data.cpi_change_pct = round(index_val - 100, 2)  # indeks → % r/r
                data.cpi_date = cells[1]
                # "Zmiana" column = difference against the previous reading, in percentage points.
                # Without it 3.0% looks "stable", even though it is a jump from 2.5%.
                if len(cells) >= 4:
                    with contextlib.suppress(ValueError):
                        data.cpi_change_pp = round(
                            float(cells[3].replace(",", ".").replace("+", "")), 2
                        )
            elif len(cells) >= 3 and cells[0].startswith("Inflacja m/m"):
                with contextlib.suppress(ValueError):
                    data.cpi_mom_pct = round(float(cells[2].replace(",", ".")) - 100, 2)
    except Exception as e:
        data.errors.append(f"CPI: {e}")


def _fetch_wig20(data: MacroData) -> None:
    try:
        info = yf.Ticker("WIG20.WA").info
        price = info.get("regularMarketPrice")
        prev = info.get("regularMarketPreviousClose")

        if price:
            data.wig20_price = float(price)
        if price and prev and prev > 0:
            data.wig20_change_1d = (price - prev) / prev * 100

        rng = _biznesradar_52w("WIG20")
        if price and rng:
            data.wig20_low_52w, data.wig20_high_52w = rng
            data.wig20_pos_52w = _pos_in_range(float(price), *rng)
            data.wig20_pos_52w_source = "biznesradar"
        elif price:
            data.errors.append("WIG20: brak zakresu 52W (Biznesradar) — pos_52w pominięte")
    except Exception as e:
        data.errors.append(f"WIG20: {e}")


def _fetch_sectors(data: MacroData) -> None:
    for name, sym in _SECTORS:
        try:
            info = yf.Ticker(sym).info
            price = info.get("regularMarketPrice")
            prev = info.get("regularMarketPreviousClose")

            if not price:
                continue

            change_1d = (price - prev) / prev * 100 if prev and prev > 0 else 0.0
            rng = _biznesradar_52w(sym)
            pos_52w = _pos_in_range(float(price), *rng) if rng else None

            data.sectors.append(SectorPerf(
                name=name, symbol=sym,
                price=float(price), change_1d=change_1d, pos_52w=pos_52w,
                low_52w=rng[0] if rng else None,
                high_52w=rng[1] if rng else None,
                pos_52w_source="biznesradar" if rng else None,
            ))
        except Exception:
            pass


def fetch() -> MacroData:
    data = MacroData(as_of=date.today())
    _fetch_fx(data)
    _fetch_gold(data)
    _fetch_cpi(data)
    _fetch_wig20(data)
    _fetch_sectors(data)
    return data
