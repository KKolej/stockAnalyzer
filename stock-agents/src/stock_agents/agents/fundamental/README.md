# Agent Fundamentalny

Analiza fundamentalna spółek GPW i rynków zagranicznych.

## Użycie

```bash
fundamental-agents PKO CDR TSLA.US
```

## Co analizuje

### Wskaźniki bieżące (TTM)
| Kategoria | Wskaźniki |
|-----------|-----------|
| Wycena | P/E (trailing/forward), P/B, P/S, EV/EBITDA, 52W High/Low |
| Wyniki | Przychody, EBITDA, EPS, marża netto, marża operacyjna |
| Rentowność | ROE, ROA, ROIC |
| Finanse | Current ratio, Quick ratio, Dług/Kapitał, Dług netto/EBITDA |
| Dywidenda | Stopa dywidendy, Payout ratio |
| Inne | Beta |

### Historia (ostatnie 5 lat)
Tabela roczna: przychody, zysk netto, marża, ROE, FCF z dynamiką YoY.

### Sygnały

**Wycena & bieżące:**
- P/E < 10 → BULLISH strong, P/E > 40 → BEARISH strong
- P/B < 1 → poniżej wartości księgowej
- ROE > 20% → wysoka rentowność
- Marża netto > 20% → BULLISH strong
- Dywidenda > 6% → BULLISH strong
- D/E < 30% → niskie zadłużenie

**Trendy historyczne:**
- CAGR przychodów i zysku (ostatnie 5 lat)
- Trend marż (porównanie ostatnich 2 lat vs wcześniejsze)
- FCF consistency (ile lat z rzędu dodatnie wolne przepływy)

## Źródła danych

| Źródło | Co dostarcza | Dla kogo |
|--------|-------------|----------|
| **yfinance** | Cena, market cap, P/E forward, dywidenda, 52W, beta, bilans | GPW + US |
| **Biznesradar** | P/E, P/B, ROE, marże z raportów ESPI, historia 5 lat | Tylko GPW |

Dla GPW: Biznesradar ma pierwszeństwo nad yfinance (dokładniejsze dane z raportów kwartalnych).

### Znane ograniczenia
- `dividendYield` z yfinance dla GPW bywa błędny (normalizacja + cap 25% w `fetcher.py`)
- Biznesradar tabela wskaźników rentowności jest kwartalna — parser wybiera kolumny Q4
- Current ratio / Quick ratio często niedostępne dla banków (specyfika sektora)

## Struktura plików

```
fundamental/
├── agent.py          # orkiestracja
├── cli.py            # entry point CLI
├── fetcher.py        # pobieranie i scalanie danych
├── models.py         # FundamentalData, YearlyRecord
├── printer.py        # wyświetlanie wyników
├── signals.py        # generowanie sygnałów
└── sources/
    └── biznesradar.py  # scraper Biznesradar (snapshot + historia)
```
