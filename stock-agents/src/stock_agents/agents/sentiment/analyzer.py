from __future__ import annotations

import os
import re

from .models import AnalysisMode, Mention, SentimentLabel

BULLISH_KEYWORDS = [
    # Angielskie
    "buy", "bullish", "strong", "beat", "exceeded", "upgraded", "outperform",
    "rally", "surge", "jump", "gain", "profit", "revenue", "positive", "growth",
    "strong buy", "accumulate", "overweight", "upside", "breakout", "record high",
    # Polskie — wyniki
    "wzrost", "rośnie", "zysk", "rekord", "byczo", "kupno", "poprawa", "wzrósł",
    "zwyżkuje", "przewyższa", "pobił", "pobila", "osiągnął", "sukces", "świetny",
    "rewelacyjny", "dobry", "powyżej oczekiwań", "powyżej prognoz", "pobił prognozy",
    # Polskie — dywidenda / skup
    "dywidenda", "skup akcji", "wykup", "wypłata dywidendy", "rekomendacja kupuj",
    # Polskie — strategia / wzrost
    "ekspansja", "akwizycja", "przejęcie", "nowy kontrakt", "nowe zamówienie",
    "odbicie", "zyskuje", "zyskują", "drożeje", "wystrzelił", "wystrzeliły",
    "nowych maksimach", "rajd",
    "zwiększył udział", "poprawił wyniki", "historyczny wynik", "nowe maksimum",
    "podwyżka ceny docelowej", "podniosł rekomendację", "awans", "premia",
]

BEARISH_KEYWORDS = [
    # Angielskie
    "sell", "bearish", "weak", "miss", "missed", "downgraded", "underperform",
    "decline", "drop", "fall", "loss", "negative", "warning", "risk", "concern",
    "trouble", "downside", "below expectations", "cut", "reduce", "underweight",
    # Polskie — wyniki
    "spadek", "spada", "strata", "niedźwiedzio", "rozczarowanie", "pogorszenie",
    "spadł", "zniżkuje", "poniżej", "obniżył", "obniżka", "problem", "słaby",
    "zły", "poniżej oczekiwań", "poniżej prognoz", "chybił prognozy",
    # Polskie — zagrożenia
    "restrukturyzacja", "zwolnienia", "odpis", "odpisał", "korekta", "korekta wartości",
    "utrata kontraktu", "postępowanie sądowe", "kara", "nałożona kara", "grzywna",
    "zmniejszył udział", "obniżył prognozę", "obniżył rekomendację", "redukcja",
    "bankructwo", "upadłość", "likwidacja", "zawieszenie dywidendy", "brak dywidendy",
    "rekomendacja sprzedaj", "rozczarowujący",
    # Polskie — język ruchów cen (częste w nagłówkach)
    "zanurkował", "zanurkowały", "nurkuje", "nurkują", "pod wodą", "tąpnięcie",
    "tąpnął", "runął", "runęły", "runie", "runą", "załamanie", "załamał", "katastrofa",
    "przecena", "wyprzedaż", "wyprzedają", "panika", "tracą", "traci",
    "nowe minimum", "nowych minimach", "nowe minima", "na minimach", "dołek",
    "osunął", "osunęły", "presj",
]


def _keyword_score(text: str) -> float:
    lower = text.lower()
    bull = sum(1 for kw in BULLISH_KEYWORDS if kw in lower)
    bear = sum(1 for kw in BEARISH_KEYWORDS if kw in lower)
    total = bull + bear
    if total == 0:
        return 0.0
    return (bull - bear) / total


def _label_from_score(score: float) -> SentimentLabel:
    if score > 0.1:
        return SentimentLabel.BULLISH
    if score < -0.1:
        return SentimentLabel.BEARISH
    return SentimentLabel.NEUTRAL


def analyze_keyword(mention: Mention) -> Mention:
    text = f"{mention.title}"
    score = _keyword_score(text)
    return Mention(
        source=mention.source,
        title=mention.title,
        url=mention.url,
        date=mention.date,
        score=score,
        label=_label_from_score(score),
    )


def analyze_claude_batch(mentions: list[Mention], ticker: str, company: str) -> list[Mention]:
    try:
        import anthropic
    except ImportError:
        return [analyze_keyword(m) for m in mentions]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return [analyze_keyword(m) for m in mentions]

    client = anthropic.Anthropic(api_key=api_key)

    titles = "\n".join(
        f"{i + 1}. {m.title}" for i, m in enumerate(mentions)
    )
    prompt = (
        f"Analyze the sentiment of each headline about {company} ({ticker}).\n"
        f"For each headline, respond with exactly one word: BULLISH, BEARISH, or NEUTRAL.\n"
        f"Respond with one label per line, numbered to match the input.\n\n"
        f"{titles}"
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(getattr(block, "text", "") for block in message.content).strip()
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        labels: list[SentimentLabel] = []
        for line in lines:
            clean = re.sub(r"^\d+[.)]\s*", "", line).upper()
            if "BULLISH" in clean:
                labels.append(SentimentLabel.BULLISH)
            elif "BEARISH" in clean:
                labels.append(SentimentLabel.BEARISH)
            else:
                labels.append(SentimentLabel.NEUTRAL)
    except Exception:
        return [analyze_keyword(m) for m in mentions]

    result = []
    for i, m in enumerate(mentions):
        label = labels[i] if i < len(labels) else SentimentLabel.NEUTRAL
        if label == SentimentLabel.BULLISH:
            score = 1.0
        elif label == SentimentLabel.BEARISH:
            score = -1.0
        else:
            score = 0.0
        result.append(Mention(
            source=m.source,
            title=m.title,
            url=m.url,
            date=m.date,
            score=score,
            label=label,
        ))
    return result


def analyze_mentions(
    mentions: list[Mention],
    mode: AnalysisMode,
    ticker: str,
    company: str,
) -> list[Mention]:
    if mode == AnalysisMode.KEYWORD:
        return [analyze_keyword(m) for m in mentions]
    return analyze_claude_batch(mentions, ticker, company)
