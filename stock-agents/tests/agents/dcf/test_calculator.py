import pytest

from stock_agents.agents.dcf.calculator import _dcf_value, _estimate_wacc, build_scenarios
from stock_agents.agents.dcf.models import DCFResult


def make_result(**kw) -> DCFResult:
    defaults = dict(
        ticker="TST.WA", company="Test SA", currency="PLN",
        price=100.0, shares=1_000_000.0, fcf_ttm=10_000_000.0,
        net_debt=0.0, wacc_base=0.0, projection_years=10,
    )
    defaults.update(kw)
    return DCFResult(**defaults)


class TestDcfValue:
    def test_zerowy_wzrost_i_dyskonto_rowne_fcf_yield(self):
        # growth=0, tg=0: PV(faza 1) + PV(TV) = fcf/wacc (renta wieczysta)
        fcf, wacc, shares = 1000.0, 0.10, 1.0
        val = _dcf_value(fcf, growth=0.0, terminal_growth=0.0, wacc=wacc,
                         years=10, net_debt=0.0, shares=shares)
        assert val == pytest.approx(fcf / wacc, rel=1e-9)

    def test_wacc_ponizej_terminal_growth_zwraca_none(self):
        assert _dcf_value(1000, 0.05, 0.10, 0.08, 10, 0, 1.0) is None
        assert _dcf_value(1000, 0.05, 0.08, 0.08, 10, 0, 1.0) is None

    def test_zero_akcji_zwraca_none(self):
        assert _dcf_value(1000, 0.05, 0.02, 0.10, 10, 0, 0.0) is None
        assert _dcf_value(1000, 0.05, 0.02, 0.10, 10, 0, -5.0) is None

    def test_dlug_netto_obniza_wycene(self):
        bez_dlugu = _dcf_value(1000, 0.05, 0.02, 0.10, 10, net_debt=0.0, shares=10.0)
        z_dlugiem = _dcf_value(1000, 0.05, 0.02, 0.10, 10, net_debt=500.0, shares=10.0)
        assert bez_dlugu is not None and z_dlugiem is not None
        assert z_dlugiem == pytest.approx(bez_dlugu - 50.0)

    def test_wyzszy_wzrost_daje_wyzsza_wycene(self):
        low = _dcf_value(1000, 0.02, 0.02, 0.10, 10, 0, 1.0)
        high = _dcf_value(1000, 0.10, 0.02, 0.10, 10, 0, 1.0)
        assert high > low


class TestEstimateWacc:
    def test_bez_dlugu_czyste_capm_pln(self):
        # rf=5.5% + 1.0 × 5.5% = 11%
        assert _estimate_wacc(1.0, None, "PLN") == pytest.approx(0.11)

    def test_bez_dlugu_czyste_capm_usd(self):
        assert _estimate_wacc(1.0, None, "USD") == pytest.approx(0.10)

    def test_beta_poza_zakresem_traktowana_jak_1(self):
        assert _estimate_wacc(5.0, None, "PLN") == _estimate_wacc(1.0, None, "PLN")
        assert _estimate_wacc(0.1, None, "PLN") == _estimate_wacc(1.0, None, "PLN")
        assert _estimate_wacc(None, None, "PLN") == _estimate_wacc(1.0, None, "PLN")

    def test_dlug_obniza_wacc(self):
        # tani dług po podatku ciągnie średnią w dół
        assert _estimate_wacc(1.0, 100.0, "PLN") < _estimate_wacc(1.0, None, "PLN")

    def test_wacc_w_granicach(self):
        assert 0.06 <= _estimate_wacc(3.0, None, "PLN") <= 0.20
        assert 0.06 <= _estimate_wacc(0.3, 10000.0, "USD") <= 0.20


class TestBuildScenarios:
    def test_trzy_scenariusze_base_bull_bear(self):
        r = build_scenarios(make_result(), beta=1.0, debt_to_equity=None)
        assert [s.name for s in r.scenarios] == ["Base", "Bull", "Bear"]

    def test_bull_powyzej_base_powyzej_bear(self):
        r = build_scenarios(make_result(), beta=1.0, debt_to_equity=None)
        by_name = {s.name: s.fair_value for s in r.scenarios}
        assert by_name["Bull"] > by_name["Base"] > by_name["Bear"]

    def test_upside_liczony_wzgledem_ceny(self):
        r = build_scenarios(make_result(price=50.0), beta=1.0, debt_to_equity=None)
        base = next(s for s in r.scenarios if s.name == "Base")
        assert base.upside == pytest.approx(base.fair_value / 50.0 - 1, abs=1e-3)

    def test_niedostepny_wynik_bez_scenariuszy(self):
        r = build_scenarios(make_result(error="brak danych", fcf_ttm=None),
                            beta=1.0, debt_to_equity=None)
        assert r.scenarios == []

    def test_wacc_base_ustawiony(self):
        r = build_scenarios(make_result(), beta=1.0, debt_to_equity=None)
        assert r.wacc_base == pytest.approx(0.11)
