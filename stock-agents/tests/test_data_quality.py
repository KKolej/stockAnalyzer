"""Testy regresyjne dla wpadek, które przepuściły złe dane do przeglądu WIG20."""
from datetime import date

import pandas as pd

from stock_agents.agents.speculator.models import Catalyst, PatternResult
from stock_agents.agents.speculator.signals import _relevant_patterns, build_projections
from stock_agents.agents.technical.fetcher import data_staleness
from stock_agents.ticker_map import BANKIER_SLUGS, company_identity_tokens


def _df(last: str) -> pd.DataFrame:
    return pd.DataFrame({"Date": [pd.Timestamp(last)], "Close": [100.0]})


class TestStaleness:
    def test_brak_piatkowej_sesji_w_sobote_jest_wykryty(self, monkeypatch):
        # Realny przypadek: sobota 2026-08-01, ostatnia świeca z czwartku 30.07.
        # Stary próg (age_days > 4) dawał age_days=2 → "świeże", i cały przegląd
        # jechał na danych o sesję starszych, nie mówiąc o tym ani słowa.
        monkeypatch.setattr(
            pd.Timestamp, "now", classmethod(lambda cls, *a, **k: pd.Timestamp("2026-08-01"))
        )
        st = data_staleness(_df("2026-07-30"))
        assert st["expected_last_session"] == "2026-07-31"
        assert st["missing_sessions"] == 1
        assert st["is_stale"] is True

    def test_piatkowa_sesja_w_sobote_jest_swieza(self, monkeypatch):
        monkeypatch.setattr(
            pd.Timestamp, "now", classmethod(lambda cls, *a, **k: pd.Timestamp("2026-08-01"))
        )
        st = data_staleness(_df("2026-07-31"))
        assert st["missing_sessions"] == 0
        assert st["is_stale"] is False


class TestCompanyIdentity:
    def test_orange_ma_wlasny_slug_bankiera(self):
        # /gielda/notowania/akcje/OPL to Optopol Technology, nie Orange Polska
        assert BANKIER_SLUGS["OPL"] == "ORANGEPL"

    def test_tokeny_pomijaja_ogolniki(self):
        # "Bank" pasowałby do każdego banku na GPW — nie nadaje się do weryfikacji
        assert company_identity_tokens("PEO") == ["pekao"]
        assert company_identity_tokens("ALR") == ["alior"]

    def test_tokeny_orange_nie_pasuja_do_optopolu(self):
        tokens = company_identity_tokens("OPL")
        assert tokens
        assert not any(t in "optopol technology sa (optopol)" for t in tokens)


def _pattern(name: str, **kw) -> PatternResult:
    base = dict(direction="UP", strength="strong", probability=0.8, sample_size=7,
                avg_return=0.075, horizon_days=30, note="")
    base.update(kw)
    return PatternResult(name=name, **base)


class TestPatternGating:
    def test_wzorzec_dywidendowy_bez_ex_div_nie_wchodzi_do_projekcji(self):
        # CD Projekt cały zysk przeznaczył na kapitał zapasowy — nie ma ex-div,
        # a "Post-div +7.5%" i tak napędzał projekcję na 2 miesiące.
        p = _pattern("Post-div", requires_event="Ex-dywidenda", event_days_away=None)
        assert _relevant_patterns([p], 60) == []

    def test_wzorzec_z_nadchodzacym_zdarzeniem_wchodzi(self):
        p = _pattern("Post-div", requires_event="Ex-dywidenda", event_days_away=3)
        assert _relevant_patterns([p], 30) == [p]

    def test_zdarzenie_poza_horyzontem_nie_wchodzi(self):
        p = _pattern("Pre-earnings drift", requires_event="Raport wynikowy", event_days_away=89)
        assert _relevant_patterns([p], 30) == []

    def test_projekcje_sa_oznaczone_jako_niezbacktestowane(self):
        proj = build_projections(
            [_pattern("Batting average")],
            [Catalyst(name="Raport wynikowy", event_date=date(2026, 8, 20),
                      days_away=19, description="")],
        )
        assert proj
        assert all(p.is_backtested is False for p in proj)
