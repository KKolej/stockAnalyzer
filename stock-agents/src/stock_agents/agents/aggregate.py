"""Zbiorcza analiza jednego tickera — spina wszystkich agentów w jeden werdykt.

Uruchamia agentów współbieżnie (każdy odporny na własne błędy) i wylicza
ważony werdykt zbiorczy. Zaprojektowane pod jeden endpoint API (`/analyze/{ticker}`).
"""
from __future__ import annotations

import concurrent.futures
from typing import Any

from .dcf import fetcher as dcf
from .fundamental import agent as fundamental
from .fundamental.printer import _score as fundamental_score
from .sentiment import agent as sentiment
from .sentiment.models import AnalysisMode
from .speculator import agent as speculator
from .technical import agent as technical

# Wagi agentów w werdykcie zbiorczym (fundamenty ważą najwięcej w średnim terminie)
_WEIGHTS = {"fundamental": 2.0, "technical": 1.5, "dcf": 1.0, "sentiment": 1.0, "speculator": 1.0}


def _clamp(x: float, lo: float = -2.0, hi: float = 2.0) -> float:
    return max(lo, min(hi, x))


def _label(score: float) -> str:
    if score >= 1.0:
        return "SILNIE BYCZO"
    if score >= 0.35:
        return "BYCZO"
    if score <= -1.0:
        return "SILNIE NIEDŹWIEDZIO"
    if score <= -0.35:
        return "NIEDŹWIEDZIO"
    return "NEUTRALNIE"


def _stance(vote: float) -> str:
    return "bullish" if vote >= 0.5 else "bearish" if vote <= -0.5 else "neutral"


def _vote_technical(data: dict[str, Any]) -> float | None:
    if data.get("error"):
        return None
    return _clamp(data.get("score", 0) / 4.0)


def _vote_fundamental(signals: list[dict[str, Any]]) -> float | None:
    if not signals:
        return None
    return _clamp(fundamental_score(signals) / 6.0)


def _vote_dcf(result: Any) -> float | None:
    if not getattr(result, "available", False) or not result.scenarios:
        return None
    base = next((s for s in result.scenarios if s.name == "Base"), result.scenarios[0])
    up = base.upside
    if up is None:
        return None
    if up > 0.3:
        return 2.0
    if up > 0.1:
        return 1.0
    if up < -0.3:
        return -2.0
    if up < -0.1:
        return -1.0
    return 0.0


def _vote_sentiment(ts: Any) -> float | None:
    if ts.total_mentions == 0:
        return None
    return _clamp(ts.overall_score * 4.0)


def _vote_speculator(sd: Any) -> float | None:
    if sd.error or not sd.projections:
        return None
    num = den = 0.0
    for p in sd.projections:
        sign = 1.0 if p.direction == "UP" else -1.0 if p.direction == "DOWN" else 0.0
        num += sign * p.probability
        den += p.probability
    if den == 0:
        return None
    return _clamp(num / den * 2.0)


def analyze(ticker: str, days: int = 180, sentiment_mode: AnalysisMode = AnalysisMode.KEYWORD) -> dict[str, Any]:
    """Uruchamia wszystkich agentów dla tickera i zwraca dane + werdykt zbiorczy."""
    tasks = {
        "technical": lambda: technical.get_data(ticker, days),
        "fundamental": lambda: fundamental.get_data(ticker),
        "dcf": lambda: dcf.fetch(ticker, 10),
        "speculator": lambda: speculator.get_data(ticker),
        "sentiment": lambda: sentiment.get_data(ticker, sentiment_mode),
    }
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for fut in concurrent.futures.as_completed(futures):
            name = futures[fut]
            try:
                results[name] = fut.result()
            except Exception as exc:  # agent nie może wywrócić całości
                errors[name] = str(exc)

    tech = results.get("technical")
    fund = results.get("fundamental")
    fund_data, fund_signals = fund if fund else (None, [])

    votes: dict[str, float | None] = {
        "technical": _vote_technical(tech) if tech else None,
        "fundamental": _vote_fundamental(fund_signals),
        "dcf": _vote_dcf(results["dcf"]) if "dcf" in results else None,
        "sentiment": _vote_sentiment(results["sentiment"]) if "sentiment" in results else None,
        "speculator": _vote_speculator(results["speculator"]) if "speculator" in results else None,
    }

    num = sum(_WEIGHTS[k] * v for k, v in votes.items() if v is not None)
    den = sum(_WEIGHTS[k] for k, v in votes.items() if v is not None)
    composite = round(num / den, 3) if den > 0 else 0.0

    stances = {k: _stance(v) for k, v in votes.items() if v is not None}

    company = ""
    price = tech.get("price") if tech else None
    if fund_data is not None:
        company = getattr(fund_data, "company", "") or ""
        price = price or getattr(fund_data, "price", None)

    return {
        "ticker": ticker.upper(),
        "company": company,
        "price": price,
        "verdict": {
            "label": _label(composite),
            "composite": composite,
            "votes": votes,
            "stances": stances,
        },
        "technical": tech,
        "fundamental": {"data": fund_data, "signals": fund_signals},
        "dcf": results.get("dcf"),
        "speculator": results.get("speculator"),
        "sentiment": results.get("sentiment"),
        "errors": errors,
    }
