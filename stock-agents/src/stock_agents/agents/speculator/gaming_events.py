"""Kalendarz targów i wydarzeń branży gier — katalizatory dla spółek gamingowych.

Ceny spółek gamingowych często rosną PRZED dużymi targami (zapowiedzi, trailery,
pokazy wydawców) — run-up budowany tygodnie wcześniej. Ten moduł dokłada targi
do listy katalizatorów spekulanta dla spółek z branży.

UWAGA: daty trzeba raz w roku odświeżyć (oficjalne strony wydarzeń).
Daty oznaczone "orientacyjna" bazują na typowym terminie z lat ubiegłych.
"""
from __future__ import annotations

from datetime import date

from .models import Catalyst

# Spółki gamingowe: GPW (kod bez sufiksu) + zagraniczne (sufiks .US).
# Uzupełniane o wykrywanie po yfinance `industry` (patrz is_gaming_company).
GAMING_TICKERS: set[str] = {
    # GPW
    "CDR", "11B", "TEN", "PLW", "CRJ", "BLO", "HUU", "VVD", "GOP",
    "MOV", "ALL", "CIG", "BBT", "PCF", "DTR", "ULG",
    # zagraniczne
    "TTWO.US", "EA.US", "RBLX.US", "U.US", "NTDOY.US", "SONY.US",
}

_GAMING_INDUSTRY_KEYWORDS = ("gaming", "electronic gaming", "multimedia")

# (nazwa, data startu, opis) — opis krótki, trafia do LLM-a przez API
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


def is_gaming_company(ticker: str, industry: str | None = None) -> bool:
    if ticker.upper() in GAMING_TICKERS:
        return True
    if industry:
        low = industry.lower()
        return any(kw in low for kw in _GAMING_INDUSTRY_KEYWORDS)
    return False


def gaming_event_catalysts(today: date | None = None) -> list[Catalyst]:
    """Nadchodzące targi gier w oknie -7..+120 dni (run-up + samo wydarzenie)."""
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
