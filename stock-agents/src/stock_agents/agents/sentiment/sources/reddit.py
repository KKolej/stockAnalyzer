from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime

from ..models import Mention, SentimentLabel, SourceResult

_SUBREDDITS = ["wallstreetbets", "investing", "stocks", "polish_stocks", "gielda"]
# TODO: Reddit wymaga OAuth2 od 2023 — zarejestruj app na old.reddit.com/prefs/apps (typ: skrypt),
# wrzuć REDDIT_CLIENT_ID i REDDIT_CLIENT_SECRET do env, zaimplementuj client_credentials flow.
_HEADERS = {"User-Agent": "stock-agents/1.0 (sentiment analysis)"}
_MAX_POSTS = 25


def _fetch_subreddit(subreddit: str, query: str) -> list[Mention]:
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={urllib.parse.quote(query)}&restrict_sr=1&sort=new&limit={_MAX_POSTS}&t=month"
    )
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    mentions = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        title = post.get("title", "")
        permalink = post.get("permalink", "")
        created = post.get("created_utc")
        date = datetime.fromtimestamp(created, tz=UTC) if created else None
        mentions.append(Mention(
            source=f"reddit/r/{subreddit}",
            title=title,
            url=f"https://www.reddit.com{permalink}",
            date=date,
            score=0.0,
            label=SentimentLabel.NEUTRAL,
        ))
    return mentions


def fetch(ticker: str, company: str) -> SourceResult:
    query = company if len(company) > 3 else ticker
    mentions: list[Mention] = []
    errors: list[str] = []

    for sub in _SUBREDDITS:
        try:
            mentions.extend(_fetch_subreddit(sub, query))
        except Exception as e:
            errors.append(f"r/{sub}: {e}")

    if not mentions and errors:
        return SourceResult(name="Reddit", error="; ".join(errors))
    return SourceResult(name="Reddit", mentions=mentions)
