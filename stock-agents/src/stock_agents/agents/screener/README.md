# Agent Screener

Filtruje i rankinguje podaną listę spółek według kryteriów fundamentalnych. Pobiera dane równolegle — lista 10 spółek zajmuje ~5 sekund.

## Użycie

```bash
screener-agents PKO CDR KGHM PZU LPP ALE MBK DNP BDX PKN [FILTRY] [SORTOWANIE]
```

## Przykłady

```bash
# Najtańsze wg P/E z ROE > 10%
screener-agents PKO CDR KGHM PZU LPP ALE MBK --pe-max 15 --roe-min 10

# Najwyższa dywidenda
screener-agents PKO PZU BDX PKN MBK --sort div --desc

# Top 5 najbardziej rentownych (ROE)
screener-agents PKO CDR KGHM PZU LPP ALE MBK DNP BDX PKN --sort roe --desc --top 5

# Value investing: tanie + dobra marża
screener-agents PKO CDR KGHM PZU LPP --pe-max 20 --margin-min 10 --roe-min 12

# Małe spółki z dywidendą
screener-agents PKO CDR KGHM PZU LPP --market-cap-max 5000 --div-min 3
```

## Filtry

### Wycena
| Flaga | Opis |
|-------|------|
| `--pe-max N` | P/E ≤ N |
| `--pe-min N` | P/E ≥ N |
| `--pb-max N` | P/B ≤ N |

### Rentowność
| Flaga | Opis |
|-------|------|
| `--roe-min N` | ROE ≥ N% |
| `--roa-min N` | ROA ≥ N% |
| `--margin-min N` | Marża netto ≥ N% |

### Finanse i dywidenda
| Flaga | Opis |
|-------|------|
| `--div-min N` | Stopa dywidendy ≥ N% |
| `--market-cap-min N` | Kapitalizacja ≥ N mln PLN |
| `--market-cap-max N` | Kapitalizacja ≤ N mln PLN |
| `--debt-max N` | Dług/Kapitał ≤ N% |
| `--beta-max N` | Beta ≤ N |

## Sortowanie

```bash
--sort pe|pb|roe|roa|div|cap|margin|beta|52w
--desc        # malejąco (domyślnie rosnąco)
--top N       # pokaż tylko N najlepszych wyników
```

Spółki bez wartości danego pola (`n/d`) zawsze trafiają na koniec listy niezależnie od kierunku sortowania.

## Kolumny w tabeli wynikowej

| Kolumna | Opis |
|---------|------|
| TICKER | Symbol giełdowy |
| NAZWA | Pełna nazwa spółki |
| CENA | Kurs aktualny z walutą |
| P/E | Wskaźnik cena/zysk (trailing) |
| P/B | Wskaźnik cena/wartość księgowa |
| ROE | Zwrot na kapitale własnym |
| MARŻA | Marża zysku netto |
| DYW | Stopa dywidendy |
| KAP | Kapitalizacja rynkowa (G=mld, M=mln) |
| 52W↑ | Wzrost kursu od minimum 52-tygodniowego |

## Źródło danych

Wyłącznie **yfinance** (Yahoo Finance). Dane pobierane są równolegle dla wszystkich spółek.

### Znane ograniczenia
- `dividendYield` dla spółek GPW bywa błędny w yfinance — zastosowany cap 25%
- Dane fundamentalne mogą być opóźnione o 1 kwartał względem ostatniego raportu
- Screener nie korzysta z Biznesradaru (tylko szybkie dane z yfinance)

## Struktura plików

```
screener/
├── agent.py    # orkiestracja: fetch → filter → print
├── cli.py      # entry point CLI z argparse
├── fetcher.py  # równoległe pobieranie danych z yfinance
├── filter.py   # aplikacja filtrów i sortowanie
├── models.py   # ScreenerRow, ScreenerFilters
└── printer.py  # formatowanie tabeli wynikowej
```
