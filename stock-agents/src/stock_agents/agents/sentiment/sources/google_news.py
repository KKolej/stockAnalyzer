from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

from ..models import Mention, SentimentLabel, SourceResult

_RSS_URL = "https://news.google.com/rss/search?q={query}&hl={lang}&gl={country}&ceid={ceid}"
# Google News RSS bywa kapryśne bez User-Agenta przeglądarki.
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36",
}


def _make_url(query: str, lang: str, country: str, ceid: str) -> str:
    return _RSS_URL.format(
        query=urllib.parse.quote(query),
        lang=lang,
        country=country,
        ceid=ceid,
    )


def _parse_date(text: str) -> datetime | None:
    try:
        return parsedate_to_datetime(text)
    except Exception:
        return None


def _fetch_feed(url: str) -> list[Mention]:
    """Pobiera i parsuje RSS Google News czystym stdlib (bez zależności feedparser).

    Wcześniej używaliśmy `feedparser`, którego NIE było w zależnościach — przez co
    źródło zawsze zwracało puste wyniki. ElementTree wystarcza dla prostego RSS.
    """
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception:
        return []

    mentions: list[Mention] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate") or ""
        date = _parse_date(pub) if pub else None
        if title:
            mentions.append(Mention(
                source="Google News",
                title=title,
                url=link,
                date=date,
                score=0.0,
                label=SentimentLabel.NEUTRAL,
            ))
    return mentions


def fetch(ticker: str, company: str) -> SourceResult:
    mentions: list[Mention] = []

    # Polish-language feed for GPW stocks — "akcje" disambiguates from sponsored events
    base_query = company if len(company) > 3 else ticker
    pl_url = _make_url(f"{base_query} akcje", "pl", "PL", "PL:pl")
    mentions.extend(_fetch_feed(pl_url))

    # English-language feed for broader coverage
    en_url = _make_url(f"{base_query} stock", "en", "US", "US:en")
    mentions.extend(_fetch_feed(en_url))

    if not mentions:
        return SourceResult(name="Google News", error="no articles found")

    seen: set[str] = set()
    unique: list[Mention] = []
    for m in mentions:
        if m.title not in seen:
            seen.add(m.title)
            unique.append(m)

    return SourceResult(name="Google News", mentions=unique)
