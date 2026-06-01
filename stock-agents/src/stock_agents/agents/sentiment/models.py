from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class SentimentLabel(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class AnalysisMode(StrEnum):
    KEYWORD = "keyword"
    CLAUDE = "claude"


@dataclass
class Mention:
    source: str
    title: str
    url: str
    date: datetime | None
    score: float
    label: SentimentLabel


@dataclass
class SourceResult:
    name: str
    mentions: list[Mention] = field(default_factory=list)
    error: str | None = None

    @property
    def available(self) -> bool:
        return self.error is None

    @property
    def bullish_count(self) -> int:
        return sum(1 for m in self.mentions if m.label == SentimentLabel.BULLISH)

    @property
    def bearish_count(self) -> int:
        return sum(1 for m in self.mentions if m.label == SentimentLabel.BEARISH)

    @property
    def neutral_count(self) -> int:
        return sum(1 for m in self.mentions if m.label == SentimentLabel.NEUTRAL)

    @property
    def avg_score(self) -> float:
        if not self.mentions:
            return 0.0
        return sum(m.score for m in self.mentions) / len(self.mentions)


@dataclass
class TickerSentiment:
    ticker: str
    company: str
    mode: AnalysisMode
    results: list[SourceResult]

    @property
    def total_mentions(self) -> int:
        return sum(len(r.mentions) for r in self.results)

    @property
    def overall_score(self) -> float:
        all_mentions = [m for r in self.results for m in r.mentions]
        if not all_mentions:
            return 0.0
        return sum(m.score for m in all_mentions) / len(all_mentions)

    @property
    def overall_label(self) -> SentimentLabel:
        score = self.overall_score
        if score > 0.1:
            return SentimentLabel.BULLISH
        if score < -0.1:
            return SentimentLabel.BEARISH
        return SentimentLabel.NEUTRAL
