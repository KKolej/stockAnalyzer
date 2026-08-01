from __future__ import annotations

import re
import urllib.request
from datetime import datetime

from ....ticker_map import BANKIER_SLUGS, company_identity_tokens, is_gpw
from ..models import Mention, SentimentLabel, SourceResult

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


def _page_company(soup: object) -> str:
    """Nazwa spółki z tytułu strony: 'Wiadomości spółki - Orange Polska SA (ORANGEPL) - …'."""
    title = getattr(getattr(soup, "title", None), "text", "") or ""
    return title.split(" - Giełda")[0].replace("Wiadomości spółki - ", "").strip()


def _identity_ok(page_company: str, ticker: str) -> bool:
    """Czy pobrana strona faktycznie dotyczy tej spółki?

    Bankier trzyma historyczne skróty — /akcje/OPL to Optopol, nie Orange Polska.
    Bez tej kontroli sentyment cicho zwracał newsy zupełnie innej spółki.
    """
    tokens = company_identity_tokens(ticker)
    if not tokens:
        return True  # brak nazwy w mapie — nie mamy czym weryfikować
    haystack = page_company.lower()
    return any(t in haystack for t in tokens)


def fetch(ticker: str, company: str) -> SourceResult:
    if not is_gpw(ticker):
        return SourceResult(name="Bankier", error="tylko GPW")

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return SourceResult(name="Bankier", error="beautifulsoup4 not installed")

    slug = BANKIER_SLUGS.get(ticker.upper(), ticker.upper())
    url = f"{_BASE}/gielda/notowania/akcje/{slug}/wiadomosci"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read()
    except Exception as e:
        return SourceResult(name="Bankier", error=str(e))

    soup = BeautifulSoup(html, "lxml")

    page_company = _page_company(soup)
    if not _identity_ok(page_company, ticker):
        return SourceResult(
            name="Bankier",
            error=(f"strona /{slug} dotyczy '{page_company}', nie {company} "
                   f"— pomijam, żeby nie mieszać spółek"),
        )

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
