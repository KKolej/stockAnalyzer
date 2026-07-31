from stock_agents.agents.fundamental.sources.biznesradar import (
    _extract_history_table,
    _extract_newest,
    _parse_number,
)


class TestParseNumber:
    def test_spacja_jako_separator_tysiecy(self):
        # Kluczowa pułapka Biznesradar: "2 027" to 2027, nie 2!
        assert _parse_number("2 027") == 2027.0
        assert _parse_number("1 234 567") == 1234567.0

    def test_nbsp_jako_separator(self):
        assert _parse_number("2\xa0027") == 2027.0

    def test_przecinek_jako_dziesietne(self):
        assert _parse_number("12,34") == 12.34
        assert _parse_number("1 234,56") == 1234.56

    def test_kropka_przy_przecinku_to_tysiace(self):
        assert _parse_number("1.234,56") == 1234.56

    def test_liczby_ujemne(self):
        assert _parse_number("-2 027") == -2027.0
        assert _parse_number("-12,5") == -12.5

    def test_sufiksy_ignorowane(self):
        assert _parse_number("12,34%") == 12.34
        assert _parse_number("2 027 tys.") == 2027.0

    def test_smieci_zwracaja_none(self):
        assert _parse_number("") is None
        assert _parse_number("b/d") is None
        assert _parse_number("—") is None


_SNAPSHOT_HTML = """
<table class="report-table">
  <tr><th></th><th>2024</th><th class="h newest">2025</th></tr>
  <tr>
    <td>Cena / Zysk</td>
    <td><span class="value">10,50</span></td>
    <td class="newest"><span class="value">12,30</span></td>
  </tr>
  <tr>
    <td>ROE</td>
    <td><span class="value">14,00</span></td>
    <td class="newest"><span class="value">15,20</span></td>
  </tr>
  <tr><td>Bez wartości</td><td>x</td></tr>
</table>
"""


class TestExtractNewest:
    def test_bierze_kolumne_newest(self):
        out = _extract_newest(_SNAPSHOT_HTML)
        assert out["Cena / Zysk"] == 12.30
        assert out["ROE"] == 15.20

    def test_wiersz_bez_newest_pomijany(self):
        assert "Bez wartości" not in _extract_newest(_SNAPSHOT_HTML)

    def test_brak_tabeli_pusty_dict(self):
        assert _extract_newest("<html><body>nic</body></html>") == {}


_HISTORY_HTML = """
<table class="report-table">
  <tr>
    <th></th>
    <th>2022(gru 22)</th><th>2023(gru 23)</th><th>2024(gru 24)</th>
    <th>zmiana</th>
  </tr>
  <tr>
    <td>Przychody ze sprzedaży</td>
    <td><span class="value">1 000</span></td>
    <td><span class="value">1 500</span></td>
    <td><span class="value">2 027</span></td>
    <td>+35%</td>
  </tr>
  <tr>
    <td>Zysk netto</td>
    <td><span class="value">100</span></td>
    <td><span class="value">-50</span></td>
    <td><span class="value">200</span></td>
    <td>x</td>
  </tr>
</table>
"""


class TestExtractHistoryTable:
    def test_lata_i_wartosci(self):
        years, data = _extract_history_table(_HISTORY_HTML)
        assert years == ["2022", "2023", "2024"]
        assert data["Przychody ze sprzedaży"] == [1000.0, 1500.0, 2027.0]
        assert data["Zysk netto"] == [100.0, -50.0, 200.0]

    def test_kolumna_zmiana_ignorowana(self):
        years, _ = _extract_history_table(_HISTORY_HTML)
        assert "zmiana" not in years

    def test_limit_n_ostatnich_lat(self):
        years, data = _extract_history_table(_HISTORY_HTML, n=2)
        assert years == ["2023", "2024"]
        assert data["Przychody ze sprzedaży"] == [1500.0, 2027.0]

    def test_kwartalne_q4_jako_fallback(self):
        html = _HISTORY_HTML.replace("2022(gru 22)", "2022/Q4(gru 22)") \
                            .replace("2023(gru 23)", "2023/Q4(gru 23)") \
                            .replace("2024(gru 24)", "2024/Q4(gru 24)")
        years, data = _extract_history_table(html)
        assert years == ["2022", "2023", "2024"]
        assert data["Zysk netto"] == [100.0, -50.0, 200.0]

    def test_brak_tabeli(self):
        assert _extract_history_table("<html></html>") == ([], {})
