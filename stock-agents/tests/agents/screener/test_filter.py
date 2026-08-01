from stock_agents.agents.screener.filter import apply_filters
from stock_agents.agents.screener.models import ScreenerFilters, ScreenerRow


def make_row(ticker: str = "TST", **kw) -> ScreenerRow:
    defaults = dict(
        ticker=ticker, company=ticker, price=100.0, currency="PLN",
        market_cap=1e9, pe=None, pb=None, ps=None, roe=None, roa=None,
        profit_margin=None, dividend_yield=None, debt_to_equity=None,
        week_52_change=None, beta=None,
    )
    defaults.update(kw)
    return ScreenerRow(**defaults)


class TestFiltry:
    def test_pe_max_odrzuca_drogie(self):
        rows = [make_row("A", pe=10.0), make_row("B", pe=30.0)]
        out = apply_filters(rows, ScreenerFilters(pe_max=20.0))
        assert [r.ticker for r in out] == ["A"]

    def test_missing_value_is_rejected_when_filter_active(self):
        rows = [make_row("A", pe=10.0), make_row("B", pe=None)]
        out = apply_filters(rows, ScreenerFilters(pe_max=20.0))
        assert [r.ticker for r in out] == ["A"]

    def test_roe_min_is_given_in_percent(self):
        # roe in the data is a fraction (0.15), the filter expects percent (15)
        rows = [make_row("A", roe=0.20), make_row("B", roe=0.10)]
        out = apply_filters(rows, ScreenerFilters(roe_min=15.0))
        assert [r.ticker for r in out] == ["A"]

    def test_market_cap_in_millions(self):
        rows = [make_row("A", market_cap=5e9), make_row("B", market_cap=1e8)]
        out = apply_filters(rows, ScreenerFilters(market_cap_min=1000.0))  # 1000 mln
        assert [r.ticker for r in out] == ["A"]

    def test_row_with_error_is_always_rejected(self):
        rows = [make_row("A", pe=10.0), make_row("B", pe=5.0, error="boom")]
        out = apply_filters(rows, ScreenerFilters())
        assert [r.ticker for r in out] == ["A"]

    def test_without_filters_everything_passes(self):
        rows = [make_row("A"), make_row("B")]
        assert len(apply_filters(rows, ScreenerFilters())) == 2


class TestSortowanie:
    def test_sort_pe_rosnaco_domyslnie(self):
        rows = [make_row("A", pe=30.0), make_row("B", pe=10.0), make_row("C", pe=20.0)]
        out = apply_filters(rows, ScreenerFilters())
        assert [r.ticker for r in out] == ["B", "C", "A"]

    def test_missing_values_sort_last(self):
        rows = [make_row("A", pe=None), make_row("B", pe=10.0)]
        out = apply_filters(rows, ScreenerFilters())
        assert [r.ticker for r in out] == ["B", "A"]

    def test_sort_malejaco(self):
        rows = [make_row("A", roe=0.10), make_row("B", roe=0.30)]
        out = apply_filters(rows, ScreenerFilters(sort_by="roe", sort_asc=False))
        assert [r.ticker for r in out] == ["B", "A"]

    def test_top_ogranicza_liczbe(self):
        rows = [make_row(t, pe=float(i)) for i, t in enumerate("ABCDE")]
        out = apply_filters(rows, ScreenerFilters(top=2))
        assert len(out) == 2

    def test_unknown_sort_field_falls_back_to_pe(self):
        rows = [make_row("A", pe=30.0), make_row("B", pe=10.0)]
        out = apply_filters(rows, ScreenerFilters(sort_by="nonsens"))
        assert [r.ticker for r in out] == ["B", "A"]


class TestMagicFormula:
    def test_ranking_is_sum_of_ey_and_roe_ranks(self):
        rows = [
            make_row("A", earnings_yield=0.20, roe=0.30, sector="Technology"),
            make_row("B", earnings_yield=0.10, roe=0.10, sector="Technology"),
        ]
        out = apply_filters(rows, ScreenerFilters(magic_formula=True))
        assert out[0].ticker == "A"
        assert out[0].magic_rank == 2  # rank 1 EY + rank 1 ROE
        assert out[1].magic_rank == 4

    def test_finanse_i_utilities_wykluczone(self):
        rows = [
            make_row("BANK", earnings_yield=0.50, roe=0.50, sector="Financial Services"),
            make_row("UTIL", earnings_yield=0.40, roe=0.40, sector="Utilities"),
            make_row("TECH", earnings_yield=0.10, roe=0.10, sector="Technology"),
        ]
        out = apply_filters(rows, ScreenerFilters(magic_formula=True))
        by = {r.ticker: r.magic_rank for r in out}
        assert by["BANK"] is None
        assert by["UTIL"] is None
        assert by["TECH"] is not None
        # companies without a ranking land at the end of the list
        assert out[0].ticker == "TECH"

    def test_missing_data_gets_worst_rank(self):
        rows = [
            make_row("A", earnings_yield=0.20, roe=0.30, sector="Technology"),
            make_row("B", earnings_yield=None, roe=None, sector="Technology"),
        ]
        out = apply_filters(rows, ScreenerFilters(magic_formula=True))
        assert out[0].ticker == "A"
        assert out[1].magic_rank > out[0].magic_rank
