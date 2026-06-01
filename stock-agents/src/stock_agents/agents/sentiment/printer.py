from __future__ import annotations

from .models import SentimentLabel, TickerSentiment

_WIDTH = 72
_COL_TITLE = 44
_COL_LABEL = 10


def _header(text: str) -> None:
    print(f"\n{'=' * _WIDTH}")
    print(f"  {text}")
    print(f"{'=' * _WIDTH}")


def _section(text: str) -> None:
    print(f"\n  {'─' * (_WIDTH - 4)}")
    print(f"  {text.upper()}")
    print(f"  {'─' * (_WIDTH - 4)}")


def _label_str(label: SentimentLabel) -> str:
    if label == SentimentLabel.BULLISH:
        return "[BYCZO   ]"
    if label == SentimentLabel.BEARISH:
        return "[NIEDŹ.  ]"
    return "[NEUTRAL ]"


def _score_bar(score: float, width: int = 20) -> str:
    mid = width // 2
    filled = int(abs(score) * mid)
    filled = min(filled, mid)
    if score > 0.1:
        bar = " " * mid + "+" * filled + " " * (mid - filled)
    elif score < -0.1:
        bar = " " * (mid - filled) + "-" * filled + " " * mid
    else:
        bar = " " * mid + " " * mid
    return f"|{bar}|"


def _overall_verdict(ts: TickerSentiment) -> str:
    label = ts.overall_label
    score = ts.overall_score
    if label == SentimentLabel.BULLISH:
        if score > 0.5:
            return "SILNIE BYCZO"
        return "BYCZO"
    if label == SentimentLabel.BEARISH:
        if score < -0.5:
            return "SILNIE NIEDŹWIEDZIO"
        return "NIEDŹWIEDZIO"
    return "NEUTRALNY"


def print_sentiment(ts: TickerSentiment) -> None:
    mode_label = "Claude AI" if ts.mode == "claude" else "Keyword"
    _header(f"SENTYMENT: {ts.ticker} — {ts.company}  [{mode_label}]")

    print(f"\n  Wzmianek łącznie : {ts.total_mentions}")
    print(f"  Wynik globalny   : {ts.overall_score:+.3f}  {_score_bar(ts.overall_score)}")
    print(f"  Sentyment        : {_overall_verdict(ts)}")

    for source in ts.results:
        _section(source.name)
        if not source.available:
            print(f"    ✗ Błąd: {source.error}")
            continue

        if not source.mentions:
            print("    Brak wzmianek.")
            continue

        print(
            f"    {'TYTUŁ':<{_COL_TITLE}}  {'SENTYMENT':<{_COL_LABEL}}  WYNIK"
        )
        print(f"    {'─' * _COL_TITLE}  {'─' * _COL_LABEL}  ─────")

        for m in source.mentions[:10]:
            title = m.title[:_COL_TITLE] if len(m.title) > _COL_TITLE else m.title
            print(
                f"    {title:<{_COL_TITLE}}  {_label_str(m.label):<{_COL_LABEL}}  {m.score:+.2f}"
            )

        if len(source.mentions) > 10:
            print(f"    … i {len(source.mentions) - 10} więcej")

        print(
            f"\n    Byczo: {source.bullish_count}  "
            f"Niedźwiedzio: {source.bearish_count}  "
            f"Neutralnie: {source.neutral_count}  "
            f"Śr. wynik: {source.avg_score:+.3f}"
        )

    print(f"\n{'=' * _WIDTH}\n")
