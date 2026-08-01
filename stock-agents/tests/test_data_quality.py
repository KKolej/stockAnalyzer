"""Regression tests for the slips that let bad data through to the WIG20 review."""
from datetime import date

import pandas as pd

from stock_agents.agents.speculator.models import Catalyst, PatternResult
from stock_agents.agents.speculator.signals import _relevant_patterns, build_projections
from stock_agents.agents.technical.fetcher import data_staleness
from stock_agents.ticker_map import BANKIER_SLUGS, company_identity_tokens


def _df(last: str) -> pd.DataFrame:
    return pd.DataFrame({"Date": [pd.Timestamp(last)], "Close": [100.0]})


class TestStaleness:
    def test_missing_friday_session_is_detected_on_saturday(self, monkeypatch):
        # Real case: Saturday 2026-08-01, last candle from Thursday 30.07.
        # The old threshold (age_days > 4) gave age_days=2 -> "fresh", and the whole review
        # ran on data one session old without saying a word about it.
        monkeypatch.setattr(
            pd.Timestamp, "now", classmethod(lambda cls, *a, **k: pd.Timestamp("2026-08-01"))
        )
        st = data_staleness(_df("2026-07-30"))
        assert st["expected_last_session"] == "2026-07-31"
        assert st["missing_sessions"] == 1
        assert st["is_stale"] is True

    def test_friday_session_is_fresh_on_saturday(self, monkeypatch):
        monkeypatch.setattr(
            pd.Timestamp, "now", classmethod(lambda cls, *a, **k: pd.Timestamp("2026-08-01"))
        )
        st = data_staleness(_df("2026-07-31"))
        assert st["missing_sessions"] == 0
        assert st["is_stale"] is False


class TestCompanyIdentity:
    def test_orange_has_its_own_bankier_slug(self):
        # /gielda/notowania/akcje/OPL is Optopol Technology, not Orange Polska
        assert BANKIER_SLUGS["OPL"] == "ORANGEPL"

    def test_tokens_skip_generic_words(self):
        # "Bank" would match every bank on GPW — useless for verification
        assert company_identity_tokens("PEO") == ["pekao"]
        assert company_identity_tokens("ALR") == ["alior"]

    def test_orange_tokens_do_not_match_optopol(self):
        tokens = company_identity_tokens("OPL")
        assert tokens
        assert not any(t in "optopol technology sa (optopol)" for t in tokens)


def _pattern(name: str, **kw) -> PatternResult:
    base = dict(direction="UP", strength="strong", probability=0.8, sample_size=7,
                avg_return=0.075, horizon_days=30, note="")
    base.update(kw)
    return PatternResult(name=name, **base)


class TestPatternGating:
    def test_dividend_pattern_without_ex_div_is_excluded_from_projection(self):
        # CD Projekt allocated all profit to reserve capital — there is no ex-div,
        # yet "Post-div +7.5%" still drove the 2-month projection.
        p = _pattern("Post-div", requires_event="Ex-dywidenda", event_days_away=None)
        assert _relevant_patterns([p], 60) == []

    def test_pattern_with_upcoming_event_is_included(self):
        p = _pattern("Post-div", requires_event="Ex-dywidenda", event_days_away=3)
        assert _relevant_patterns([p], 30) == [p]

    def test_event_beyond_horizon_is_excluded(self):
        p = _pattern("Pre-earnings drift", requires_event="Raport wynikowy", event_days_away=89)
        assert _relevant_patterns([p], 30) == []

    def test_projections_are_flagged_as_not_backtested(self):
        proj = build_projections(
            [_pattern("Batting average")],
            [Catalyst(name="Raport wynikowy", event_date=date(2026, 8, 20),
                      days_away=19, description="")],
        )
        assert proj
        assert all(p.is_backtested is False for p in proj)
