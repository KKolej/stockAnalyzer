from datetime import date, timedelta

import pandas as pd

from stock_agents.agents.speculator.gaming_events import (
    EVENT_HISTORY,
    gaming_event_catalysts,
    is_gaming_company,
    upcoming_recurring_events,
)
from stock_agents.agents.speculator.patterns import analyze_gaming_event_runup

_TODAY = date(2026, 7, 31)  # miesiąc przed Gamescomem 2026


class TestIsGamingCompany:
    def test_industry_yahoo_gaming(self):
        assert is_gaming_company("Electronic Gaming & Multimedia")

    def test_industry_lowercase(self):
        assert is_gaming_company("electronic gaming & multimedia")

    def test_bank_nie_jest_gamingiem(self):
        assert not is_gaming_company("Banks - Regional")

    def test_brak_industry(self):
        assert not is_gaming_company(None)
        assert not is_gaming_company("")


class TestGamingEventCatalysts:
    def test_okno_przed_gamescomem(self):
        out = gaming_event_catalysts(_TODAY)
        names = [c.name for c in out]
        assert any("Gamescom" in n for n in names)
        assert all(-7 <= c.days_away <= 120 for c in out)

    def test_posortowanie_wg_odleglosci(self):
        out = gaming_event_catalysts(date(2026, 8, 1))
        assert [c.days_away for c in out] == sorted(c.days_away for c in out)


class TestUpcomingRecurringEvents:
    def test_gamescom_przed_data(self):
        out = upcoming_recurring_events(date(2026, 8, 1))
        by_name = {name: (next_date, past) for name, next_date, past in out}
        assert "Gamescom" in by_name
        next_date, past = by_name["Gamescom"]
        assert next_date == date(2026, 8, 26)
        assert all(d < date(2026, 8, 1) for d in past)

    def test_poza_oknem_pusto(self):
        # tuż po TGA — najbliższe duże targi (Gamescom) dalej niż 120 dni
        out = upcoming_recurring_events(date(2026, 12, 20), window_days=120)
        assert out == []


def _synthetic_history(start: date, end: date, runup_before: list[date]) -> pd.DataFrame:
    """Płaska cena 100, ale w 30 dniach przed każdą datą z runup_before rośnie do 110."""
    rows = []
    d = start
    while d <= end:
        price = 100.0
        for ev in runup_before:
            delta = (ev - d).days
            if 0 < delta <= 30:
                price = 100.0 + 10.0 * (30 - delta) / 30
        rows.append({"Date": pd.Timestamp(d), "Close": price, "Volume": 1000})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


class TestAnalyzeGamingEventRunup:
    def test_wykrywa_runup_przed_gamescomem(self):
        history = [d for d in EVENT_HISTORY["Gamescom"] if d < _TODAY]
        df = _synthetic_history(date(2018, 1, 1), _TODAY, history)
        results = analyze_gaming_event_runup(df, today=_TODAY)
        gamescom = [r for r in results if "Gamescom" in r.name]
        assert len(gamescom) == 1
        r = gamescom[0]
        assert r.direction == "UP"
        assert r.probability >= 0.75
        assert r.sample_size >= 3
        assert r.avg_return is not None and r.avg_return > 0

    def test_plaska_cena_bez_falszywego_up(self):
        df = _synthetic_history(date(2018, 1, 1), _TODAY, [])
        results = analyze_gaming_event_runup(df, today=_TODAY)
        assert all(r.direction != "UP" for r in results)

    def test_pusty_df(self):
        assert analyze_gaming_event_runup(pd.DataFrame(), today=_TODAY) == []
