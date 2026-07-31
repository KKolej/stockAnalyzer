from stock_agents.agents.fundamental.models import FundamentalData, YearlyRecord
from stock_agents.agents.fundamental.signals import (
    altman_signal,
    debt_signal,
    dividend_signal,
    earnings_growth_signal,
    fcf_signal,
    generate_signals,
    graham_signal,
    margin_trend_signal,
    pe_signal,
    piotroski_signal,
    revenue_growth_signal,
    roe_signal,
)

_NONE_FIELDS = [
    "price", "market_cap", "pe_trailing", "pe_forward", "pb", "ev_ebitda",
    "ps_ratio", "revenue", "ebitda", "eps", "profit_margin", "operating_margin",
    "roe", "roa", "roic", "current_ratio", "quick_ratio", "debt_to_equity",
    "net_debt_ebitda", "interest_coverage", "fcf_ttm", "fcf_yield", "ev_fcf",
    "dividend_yield", "payout_ratio", "dividend_cagr", "beta",
    "week_52_high", "week_52_low", "book_value",
]


def make_data(**kw) -> FundamentalData:
    base = {f: None for f in _NONE_FIELDS}
    base.update(ticker="TST", company="Test SA", currency="PLN")
    base.update(kw)
    return FundamentalData(**base)


class TestPeSignal:
    def test_progi(self):
        assert pe_signal(make_data(pe_trailing=8.0))["signal"] == "BULLISH"
        assert pe_signal(make_data(pe_trailing=8.0))["strength"] == "strong"
        assert pe_signal(make_data(pe_trailing=13.0))["strength"] == "weak"
        assert pe_signal(make_data(pe_trailing=20.0)) is None
        assert pe_signal(make_data(pe_trailing=30.0))["signal"] == "BEARISH"
        assert pe_signal(make_data(pe_trailing=50.0))["strength"] == "strong"

    def test_brak_lub_ujemne_pe(self):
        assert pe_signal(make_data()) is None
        assert pe_signal(make_data(pe_trailing=-5.0)) is None


class TestRoeSignal:
    def test_progi(self):
        assert roe_signal(make_data(roe=0.25))["signal"] == "BULLISH"
        assert roe_signal(make_data(roe=-0.05))["signal"] == "BEARISH"
        assert roe_signal(make_data(roe=0.08)) is None


class TestDebtSignal:
    def test_de_w_procentach(self):
        # yfinance podaje D/E w %, np. 250 = 250%
        assert debt_signal(make_data(debt_to_equity=20.0))["signal"] == "BULLISH"
        assert debt_signal(make_data(debt_to_equity=250.0))["strength"] == "strong"
        assert debt_signal(make_data(debt_to_equity=150.0))["signal"] == "BEARISH"


class TestDividendSignal:
    def test_zero_dywidendy_bez_sygnalu(self):
        assert dividend_signal(make_data(dividend_yield=0)) is None
        assert dividend_signal(make_data(dividend_yield=0.07))["strength"] == "strong"


class TestTrendy:
    def _history(self, field: str, values_newest_first: list[float]) -> list[YearlyRecord]:
        year = 2025
        return [YearlyRecord(year=str(year - i), **{field: v})
                for i, v in enumerate(values_newest_first)]

    def test_wzrost_przychodow_cagr(self):
        # 100 → 200 przez 4 lata = CAGR ~19% → strong bullish
        d = make_data(history=self._history("revenue", [200.0, 150.0, 120.0, 110.0, 100.0]))
        s = revenue_growth_signal(d)
        assert s["signal"] == "BULLISH" and s["strength"] == "strong"

    def test_spadek_przychodow(self):
        d = make_data(history=self._history("revenue", [50.0, 80.0, 100.0]))
        assert revenue_growth_signal(d)["signal"] == "BEARISH"

    def test_za_malo_danych(self):
        d = make_data(history=self._history("revenue", [100.0]))
        assert revenue_growth_signal(d) is None

    def test_strata_netto_bearish(self):
        d = make_data(history=self._history("net_income", [-10.0, 20.0, 30.0]))
        s = earnings_growth_signal(d)
        assert s["signal"] == "BEARISH" and s["strength"] == "strong"

    def test_marze_rosna(self):
        d = make_data(history=self._history("profit_margin", [0.20, 0.18, 0.10, 0.08]))
        assert margin_trend_signal(d)["signal"] == "BULLISH"

    def test_fcf_zawsze_dodatni(self):
        hist = [YearlyRecord(year=str(2025 - i), operating_cf=100.0, capex=20.0)
                for i in range(3)]
        assert fcf_signal(make_data(history=hist))["signal"] == "BULLISH"

    def test_fcf_zawsze_ujemny(self):
        hist = [YearlyRecord(year=str(2025 - i), operating_cf=10.0, capex=50.0)
                for i in range(3)]
        s = fcf_signal(make_data(history=hist))
        assert s["signal"] == "BEARISH" and s["strength"] == "strong"


class TestScoring:
    def test_piotroski(self):
        assert piotroski_signal(make_data(piotroski_score=8, piotroski_max=9))["signal"] == "BULLISH"
        assert piotroski_signal(make_data(piotroski_score=1, piotroski_max=9))["signal"] == "BEARISH"
        assert piotroski_signal(make_data()) is None

    def test_graham(self):
        s = graham_signal(make_data(price=50.0, graham_number=100.0))
        assert s["signal"] == "BULLISH" and s["strength"] == "strong"
        assert graham_signal(make_data(price=200.0, graham_number=100.0))["signal"] == "BEARISH"

    def test_altman_pomija_banki(self):
        assert altman_signal(make_data(altman_z=1.0, sector="Financial Services")) is None
        assert altman_signal(make_data(altman_z=1.0, sector="Banks - Regional")) is None
        assert altman_signal(make_data(altman_z=1.0, sector="Technology"))["signal"] == "BEARISH"
        assert altman_signal(make_data(altman_z=3.5, sector="Technology"))["signal"] == "BULLISH"


class TestGenerateSignals:
    def test_pusta_spolka_bez_sygnalow(self):
        assert generate_signals(make_data()) == []

    def test_kazdy_sygnal_ma_wymagane_pola(self):
        d = make_data(pe_trailing=8.0, roe=0.25, dividend_yield=0.07,
                      piotroski_score=8, piotroski_max=9)
        for s in generate_signals(d):
            assert set(s) == {"indicator", "signal", "strength", "note"}
            assert s["signal"] in {"BULLISH", "BEARISH", "NEUTRAL"}
