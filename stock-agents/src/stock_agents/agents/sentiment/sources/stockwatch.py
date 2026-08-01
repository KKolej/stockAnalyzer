from __future__ import annotations

import urllib.request
from datetime import datetime

from ....ticker_map import STOCKWATCH_SLUGS, is_gpw
from ..models import Mention, SentimentLabel, SourceResult

_BASE = "https://www.stockwatch.pl"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9",
}
# Title of the generic news section — Stockwatch serves it instead of a 404
# when the "walor" tag does not exist. Without this check we get random market news.
_FALLBACK_TITLE_MARK = "giełda od fundament"


def _parse_date(text: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def fetch(ticker: str, company: str) -> SourceResult:
    if not is_gpw(ticker):
        return SourceResult(name="Stockwatch", error="tylko GPW")

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return SourceResult(name="Stockwatch", error="beautifulsoup4 not installed")

    # Company tag page instead of full-text search: `?s=ALE` returned
    # everything with the Polish conjunction "ale" in the slug ("Fed bez podwyżki, ALE rynek…"),
    # because the filter looked for the ticker anywhere in the URL.
    slug = STOCKWATCH_SLUGS.get(ticker.upper(), ticker.lower())
    url = f"{_BASE}/wiadomosci/walor/{slug}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read()
    except Exception as e:
        return SourceResult(name="Stockwatch", error=str(e))

    soup = BeautifulSoup(html, "lxml")

    page_title = (soup.title.text if soup.title else "").lower()
    if _FALLBACK_TITLE_MARK in page_title:
        return SourceResult(
            name="Stockwatch",
            error=f"brak tagu spółki '{slug}' — Stockwatch podstawił ogólny serwis",
        )

    mentions: list[Mention] = []
    for li in soup.select("li.postList"):
        title_tag = li.find("a", class_="title")
        if not title_tag:
            continue

        # Extra safeguard: the article must be tagged with this company.
        tags = {a.get("href", "").rsplit("/", 1)[-1].lower()
                for a in li.select("span.tags a[rel=tag]")}
        if tags and slug not in tags:
            continue

        href = title_tag.get("href", "")
        strong = title_tag.find("strong")
        title = (strong.get_text(strip=True) if strong else title_tag.get_text(strip=True))
        full_url = href if href.startswith("http") else _BASE + href
        time_tag = li.find("time")
        date_text = time_tag.get("datetime", "") if time_tag else ""
        date = _parse_date(date_text) if date_text else None
        if title:
            mentions.append(Mention(
                source="Stockwatch",
                title=title,
                url=full_url,
                date=date,
                score=0.0,
                label=SentimentLabel.NEUTRAL,
            ))

    if not mentions:
        return SourceResult(name="Stockwatch", error="no articles found")
    return SourceResult(name="Stockwatch", mentions=mentions)
