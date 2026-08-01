"""Calendar of gaming industry trade shows — catalysts for gaming companies.

Gaming stocks often rise BEFORE big shows (announcements, trailers, publisher
showcases) — a run-up built weeks in advance. This module adds trade shows to the
speculator's catalyst list for companies detected via `industry` from yfinance.

CAUTION: the dates need refreshing once a year (from official event pages).
Dates marked "orientacyjna" are based on the usual slot in previous years.
"""
from __future__ import annotations

from datetime import date

from .models import Catalyst

# Detected via the yfinance `industry` field — Yahoo classifies gaming companies
# (GPW ones too) as "Electronic Gaming & Multimedia".
_GAMING_INDUSTRY_KEYWORDS = ("gaming", "video game")

# (name, start date, description) — description is short, it reaches the LLM through the API
GAMING_EVENTS: list[tuple[str, date, str]] = [
    ("Gamescom (Kolonia)", date(2026, 8, 26),
     "Największe targi gier w Europie — zapowiedzi/trailery, częsty run-up cen przed targami"),
    ("PAX West (Seattle)", date(2026, 9, 4),
     "Duże targi US — pokazy gier i community buzz (data orientacyjna)"),
    ("Tokyo Game Show", date(2026, 9, 24),
     "Największe targi w Azji — istotne dla wydawców z ekspozycją na Azję (data orientacyjna)"),
    ("Steam Next Fest (październik)", date(2026, 10, 12),
     "Festiwal dem na Steam — widoczność wishlist dla mniejszych wydawców (data orientacyjna)"),
    ("Poznań Game Arena", date(2026, 10, 23),
     "Największe targi gier w Polsce — medialność polskich spółek z GPW (data orientacyjna)"),
    ("The Game Awards", date(2026, 12, 10),
     "Gala + world premieres — nominacje i zapowiedzi potrafią ruszyć kursem (data orientacyjna)"),
    ("Steam Next Fest (luty)", date(2027, 2, 22),
     "Festiwal dem na Steam (data orientacyjna)"),
    ("Digital Dragons (Kraków)", date(2027, 5, 17),
     "Konferencja branżowa PL — networking/deale wydawnicze (data orientacyjna)"),
    ("Summer Game Fest", date(2027, 6, 4),
     "Letni sezon pokazów (następca E3) — duża fala zapowiedzi (data orientacyjna)"),
]


# Historical start dates of recurring trade shows — for the run-up backtest
# (±1-2 days of accuracy is irrelevant with a 30-day window).
EVENT_HISTORY: dict[str, list[date]] = {
    "Gamescom": [
        date(2018, 8, 21), date(2019, 8, 20), date(2020, 8, 27),
        date(2021, 8, 25), date(2022, 8, 24), date(2023, 8, 23),
        date(2024, 8, 21), date(2025, 8, 20), date(2026, 8, 26),
    ],
    "Tokyo Game Show": [
        date(2018, 9, 20), date(2019, 9, 12), date(2020, 9, 23),
        date(2021, 9, 30), date(2022, 9, 15), date(2023, 9, 21),
        date(2024, 9, 26), date(2025, 9, 25), date(2026, 9, 24),
    ],
    "The Game Awards": [
        date(2018, 12, 6), date(2019, 12, 12), date(2020, 12, 10),
        date(2021, 12, 9), date(2022, 12, 8), date(2023, 12, 7),
        date(2024, 12, 12), date(2025, 12, 11), date(2026, 12, 10),
    ],
}


def upcoming_recurring_events(today: date | None = None, window_days: int = 120) -> list[tuple[str, date, list[date]]]:
    """Recurring trade shows in the upcoming window plus their historical dates (for backtesting)."""
    today = today or date.today()
    out: list[tuple[str, date, list[date]]] = []
    for name, dates in EVENT_HISTORY.items():
        future = [d for d in dates if 0 <= (d - today).days <= window_days]
        if not future:
            continue
        next_date = min(future)
        past = [d for d in dates if d < today]
        out.append((name, next_date, past))
    return out


def is_gaming_company(industry: str | None) -> bool:
    if not industry:
        return False
    low = industry.lower()
    return any(kw in low for kw in _GAMING_INDUSTRY_KEYWORDS)


def gaming_event_catalysts(today: date | None = None) -> list[Catalyst]:
    """Upcoming gaming trade shows in a -7..+120 day window (run-up plus the event itself)."""
    today = today or date.today()
    out: list[Catalyst] = []
    for name, event_date, description in GAMING_EVENTS:
        days = (event_date - today).days
        if -7 <= days <= 120:
            out.append(Catalyst(
                name=f"Targi gier: {name}", event_date=event_date,
                days_away=days, description=description,
            ))
    return out
