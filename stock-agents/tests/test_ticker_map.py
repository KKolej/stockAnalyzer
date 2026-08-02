from stock_agents.ticker_map import canonical_ticker, is_gpw, ticker_to_company, to_yahoo_ticker


class TestToYahooTicker:
    def test_gpw_adds_wa_suffix(self):
        assert to_yahoo_ticker("PKO") == "PKO.WA"
        assert to_yahoo_ticker("CDR") == "CDR.WA"

    def test_male_litery_normalizowane(self):
        assert to_yahoo_ticker("pko") == "PKO.WA"
        assert to_yahoo_ticker("tsla.us") == "TSLA"

    def test_override_kghm(self):
        # KGHM is KGH.WA on Yahoo — the alias must work
        assert to_yahoo_ticker("KGHM") == "KGH.WA"

    def test_us_strips_suffix(self):
        assert to_yahoo_ticker("TSLA.US") == "TSLA"
        assert to_yahoo_ticker("AAPL.US") == "AAPL"


class TestIsGpw:
    def test_gpw_without_suffix(self):
        assert is_gpw("PKO") is True
        assert is_gpw("pko") is True

    def test_us_with_suffix(self):
        assert is_gpw("TSLA.US") is False
        assert is_gpw("tsla.us") is False


class TestTickerToCompany:
    def test_known_company(self):
        assert ticker_to_company("PKO") == "PKO BP"
        assert ticker_to_company("CDR") == "CD Projekt"

    def test_unknown_company_returns_ticker(self):
        assert ticker_to_company("XYZ") == "XYZ"

    def test_us_returns_symbol_without_suffix(self):
        assert ticker_to_company("TSLA.US") == "TSLA"


class TestRenamedTickers:
    """SPL.WA turned into a 404 on 2026-04-28 and the company silently left every report."""

    def test_renamed_ticker_resolves_to_current_symbol(self):
        assert to_yahoo_ticker("SPL") == "EBP.WA"
        assert to_yahoo_ticker("spl") == "EBP.WA"

    def test_renamed_ticker_keeps_the_company_name(self):
        assert ticker_to_company("SPL") == "Erste Bank Polska"
        assert ticker_to_company("EBP") == "Erste Bank Polska"

    def test_us_tickers_are_not_renamed(self):
        assert canonical_ticker("SPL.US") == "SPL.US"
        assert to_yahoo_ticker("SPL.US") == "SPL"

    def test_untouched_tickers_pass_through(self):
        assert canonical_ticker("PKO") == "PKO"
