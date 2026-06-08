from __future__ import annotations

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
    try:
        from bs4 import BeautifulSoup
        req = urllib.request.Request(
            "https://www.biznesradar.pl/notowania/CPI",
            headers=_HEADERS
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            soup = BeautifulSoup(r.read(), "lxml")

        p = soup.find(class_="profile_quotation")
        if not p:
            return
        text = p.get_text(strip=True)
        # Format: "66.30+1.40(+2.16%)25 maj 12:41"
        m_val = re.match(r"([\d,\.]+)", text)
        m_pct = re.search(r"\(([+\-][\d,\.]+)%\)", text)
        m_date = re.search(r"(\d+ \w+ \d{2}:\d{2})", text)

        if m_val:
            data.cpi_value = float(m_val.group(1).replace(",", "."))
        if m_pct:
            data.cpi_change_pct = float(m_pct.group(1).replace(",", "."))
        if m_date:
            data.cpi_date = m_date.group(1)
    except Exception as e:
        data.errors.append(f"CPI: {e}")


def _fetch_wig20(data: MacroData) -> None:
    try:
        info = yf.Ticker("WIG20.WA").info
        price = info.get("regularMarketPrice")
        prev = info.get("regularMarketPreviousClose")
        high52 = info.get("fiftyTwoWeekHigh")
        low52 = info.get("fiftyTwoWeekLow")

        if price:
            data.wig20_price = float(price)
        if price and prev and prev > 0:
            data.wig20_change_1d = (price - prev) / prev * 100
        if price and high52 and low52 and high52 != low52:
            data.wig20_pos_52w = (price - low52) / (high52 - low52) * 100
    except Exception as e:
        data.errors.append(f"WIG20: {e}")


def _fetch_sectors(data: MacroData) -> None:
    for name, sym in _SECTORS:
        try:
            info = yf.Ticker(sym).info
            price = info.get("regularMarketPrice")
            prev = info.get("regularMarketPreviousClose")
            high52 = info.get("fiftyTwoWeekHigh")
            low52 = info.get("fiftyTwoWeekLow")

            if not price:
                continue

            change_1d = (price - prev) / prev * 100 if prev and prev > 0 else 0.0
            pos_52w = None
            if high52 and low52 and high52 != low52:
                pos_52w = (price - low52) / (high52 - low52) * 100

            data.sectors.append(SectorPerf(
                name=name, symbol=sym,
                price=float(price), change_1d=change_1d, pos_52w=pos_52w
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
