"""Biznesradar's C/Z and C/WK are computed against ITS OWN quote, which can lag badly.

Copied verbatim they contradicted the price printed next to them: Pekao showed P/E 9.27
beside an EPS of 24.68 that implies 9.95 at the market price of 245.50 (Bankier: 9.95).
Allegro's snapshot quote was 26.36 against a market price of 44.99 — over a year stale.
"""
from stock_agents.agents.fundamental import fetcher
from stock_agents.agents.fundamental.models import FundamentalData


def _data(price: float) -> FundamentalData:
    return FundamentalData(
        ticker="PEO", company="Bank Pekao", currency="PLN", price=price, market_cap=None,
        pe_trailing=None, pe_forward=None, pb=None, ev_ebitda=None, ps_ratio=None,
        revenue=None, ebitda=None, eps=None, profit_margin=None, operating_margin=None,
        roe=None, roa=None, roic=None, current_ratio=None, quick_ratio=None,
        debt_to_equity=None, net_debt_ebitda=None, interest_coverage=None,
        fcf_ttm=None, fcf_yield=None, ev_fcf=None, dividend_yield=None, payout_ratio=None,
        dividend_cagr=None, beta=None, week_52_high=None, week_52_low=None, book_value=None,
    )


_SNAPSHOT = {
    "Kurs": 228.8, "Cena / Zysk": 9.27, "Zysk na akcję": 24.68,
    "Cena / Wartość księgowa": 1.83, "Wartość księgowa na akcję": 125.32,
}


class TestRatioRecomputation:
    def test_ratios_follow_our_price_not_the_snapshot_quote(self, monkeypatch):
        monkeypatch.setattr(fetcher, "br_snapshot", lambda _t: _SNAPSHOT)

        out = fetcher._overlay_biznesradar(_data(245.50), "PEO")

        assert out.eps == 24.68            # per-share values come from the reports — kept
        assert out.book_value == 125.32
        assert out.pe_trailing == 9.95     # 245.50 / 24.68, matches Bankier
        assert out.pb == 1.96              # 245.50 / 125.32

    def test_quality_block_exposes_the_gap(self, monkeypatch):
        monkeypatch.setattr(fetcher, "br_snapshot", lambda _t: _SNAPSHOT)

        quality = fetcher._overlay_biznesradar(_data(245.50), "PEO").quality

        assert quality["price"] == 245.50
        assert quality["biznesradar_price"] == 228.8
        assert "pe_trailing" in quality["ratios_recomputed_on_price"]

    def test_without_a_price_the_snapshot_ratio_is_kept(self, monkeypatch):
        monkeypatch.setattr(fetcher, "br_snapshot", lambda _t: _SNAPSHOT)

        out = fetcher._overlay_biznesradar(_data(None), "PEO")

        assert out.pe_trailing == 9.27
        assert out.quality["ratios_recomputed_on_price"] == []
