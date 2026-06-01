from __future__ import annotations

import concurrent.futures

from ...ticker_map import ticker_to_company
from .analyzer import analyze_mentions
from .models import AnalysisMode, SourceResult, TickerSentiment
from .printer import print_sentiment
from .sources import bankier, google_news, reddit, stockwatch


def _fetch_all(ticker: str, company: str) -> list[SourceResult]:
    fetchers = [
        (reddit.fetch, ticker, company),
        (bankier.fetch, ticker, company),
        (stockwatch.fetch, ticker, company),
        (google_news.fetch, ticker, company),
    ]

    results: list[SourceResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn, t, c): fn for fn, t, c in fetchers}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                fn = futures[future]
                results.append(SourceResult(name=fn.__module__.split(".")[-1], error=str(e)))

    return results


def run(ticker: str, mode: AnalysisMode = AnalysisMode.KEYWORD) -> None:
    company = ticker_to_company(ticker)
    raw_results = _fetch_all(ticker, company)

    analyzed: list[SourceResult] = []
    for source in raw_results:
        if source.available and source.mentions:
            analyzed_mentions = analyze_mentions(source.mentions, mode, ticker, company)
            analyzed.append(SourceResult(name=source.name, mentions=analyzed_mentions))
        else:
            analyzed.append(source)

    ts = TickerSentiment(
        ticker=ticker.upper(),
        company=company,
        mode=mode,
        results=analyzed,
    )
    print_sentiment(ts)
