from datetime import datetime

import pytest

from stock_agents.agents.sentiment.analyzer import (
    analyze_keyword,
    analyze_mentions,
)
from stock_agents.agents.sentiment.models import (
    AnalysisMode,
    Mention,
    SentimentLabel,
)


def _mention(title: str) -> Mention:
    return Mention(
        source="test",
        title=title,
        url="https://example.com",
        date=datetime(2026, 1, 1),
        score=0.0,
        label=SentimentLabel.NEUTRAL,
    )


def test_bullish_keywords():
    m = analyze_keyword(_mention("PKO wzrost zysk rekord"))
    assert m.label == SentimentLabel.BULLISH
    assert m.score > 0


def test_bearish_keywords():
    m = analyze_keyword(_mention("CDR spadek strata problem"))
    assert m.label == SentimentLabel.BEARISH
    assert m.score < 0


def test_neutral_no_keywords():
    m = analyze_keyword(_mention("KGHM wyniki finansowe"))
    assert m.label == SentimentLabel.NEUTRAL
    assert m.score == 0.0


def test_mixed_keywords_near_neutral():
    m = analyze_keyword(_mention("wzrost ale też strata"))
    assert isinstance(m.label, SentimentLabel)


def test_analyze_mentions_keyword_mode():
    mentions = [
        _mention("wzrost wzrost wzrost"),
        _mention("spadek strata"),
    ]
    result = analyze_mentions(mentions, AnalysisMode.KEYWORD, "PKO", "PKO BP")
    assert len(result) == 2
    assert result[0].label == SentimentLabel.BULLISH
    assert result[1].label == SentimentLabel.BEARISH


def test_source_result_counts():
    from stock_agents.agents.sentiment.models import SourceResult

    mentions = [
        Mention("s", "t", "u", None, 0.5, SentimentLabel.BULLISH),
        Mention("s", "t", "u", None, -0.5, SentimentLabel.BEARISH),
        Mention("s", "t", "u", None, 0.0, SentimentLabel.NEUTRAL),
    ]
    sr = SourceResult(name="test", mentions=mentions)
    assert sr.bullish_count == 1
    assert sr.bearish_count == 1
    assert sr.neutral_count == 1
    assert sr.avg_score == pytest.approx(0.0)
    assert sr.available is True


def test_source_result_error():
    from stock_agents.agents.sentiment.models import SourceResult

    sr = SourceResult(name="test", error="connection failed")
    assert sr.available is False
    assert sr.bullish_count == 0


def test_ticker_sentiment_overall():
    from stock_agents.agents.sentiment.models import SourceResult, TickerSentiment

    mentions = [
        Mention("s", "t", "u", None, 0.8, SentimentLabel.BULLISH),
        Mention("s", "t", "u", None, 0.6, SentimentLabel.BULLISH),
    ]
    sr = SourceResult(name="test", mentions=mentions)
    ts = TickerSentiment(ticker="PKO", company="PKO BP", mode=AnalysisMode.KEYWORD, results=[sr])
    assert ts.total_mentions == 2
    assert ts.overall_score == pytest.approx(0.7)
    assert ts.overall_label == SentimentLabel.BULLISH
