from __future__ import annotations

import urllib.request
from datetime import datetime

from ..models import Mention, SentimentLabel, SourceResult
from ....ticker_map import is_gpw

_BASE = "https://www.bankier.pl"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9",
}


def _parse_date(text: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def fetch(ticker: str, company: str) -> SourceResult:
    if not is_gpw(ticker):
        return SourceResult(name="Bankier", error="tylko GPW")

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return SourceResult(name="Bankier", error="beautifulsoup4 not installed")

    import re

    url = f"{_BASE}/gielda/notowania/akcje/{ticker.upper()}/wiadomosci"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read()
    except Exception as e:
        return SourceResult(name="Bankier", error=str(e))

    soup = BeautifulSoup(html, "lxml")
    mentions: list[Mention] = []

    for li in soup.select("li.m-listing-article-list__item"):
        a = li.find("a", href=True)
        if not a:
            continue
        full_text = a.get_text(strip=True)
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})(.*)", full_text)
        if m:
            date = _parse_date(m.group(1))
            title = m.group(2).strip()
        else:
            date = None
            title = full_text
        href = a["href"]
        full_url = href if href.startswith("http") else _BASE + href
        if title:
            mentions.append(Mention(
                source="Bankier",
                title=title,
                url=full_url,
                date=date,
                score=0.0,
                label=SentimentLabel.NEUTRAL,
            ))

    if not mentions:
        return SourceResult(name="Bankier", error="no articles found")
    return SourceResult(name="Bankier", mentions=mentions)
