from stock_agents.ticker_map import is_gpw, ticker_to_company, to_yahoo_ticker


class TestToYahooTicker:
    def test_gpw_dodaje_sufiks_wa(self):
        assert to_yahoo_ticker("PKO") == "PKO.WA"
        assert to_yahoo_ticker("CDR") == "CDR.WA"

    def test_male_litery_normalizowane(self):
        assert to_yahoo_ticker("pko") == "PKO.WA"
        assert to_yahoo_ticker("tsla.us") == "TSLA"

    def test_override_kghm(self):
        # KGHM w Yahoo to KGH.WA — alias musi działać
        assert to_yahoo_ticker("KGHM") == "KGH.WA"

    def test_us_usuwa_sufiks(self):
        assert to_yahoo_ticker("TSLA.US") == "TSLA"
        assert to_yahoo_ticker("AAPL.US") == "AAPL"


class TestIsGpw:
    def test_gpw_bez_sufiksu(self):
        assert is_gpw("PKO") is True
        assert is_gpw("pko") is True

    def test_us_z_sufiksem(self):
        assert is_gpw("TSLA.US") is False
        assert is_gpw("tsla.us") is False


class TestTickerToCompany:
    def test_znana_spolka(self):
        assert ticker_to_company("PKO") == "PKO BP"
        assert ticker_to_company("CDR") == "CD Projekt"

    def test_nieznana_spolka_zwraca_ticker(self):
        assert ticker_to_company("XYZ") == "XYZ"

    def test_us_zwraca_symbol_bez_sufiksu(self):
        assert ticker_to_company("TSLA.US") == "TSLA"
