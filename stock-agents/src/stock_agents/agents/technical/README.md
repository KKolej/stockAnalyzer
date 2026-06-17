# Agent Analizy Technicznej

Pobiera dane OHLCV z Yahoo Finance i oblicza 22 wskaźniki techniczne dla spółek GPW i rynków zagranicznych. Wykrywa **poziomy wsparcia/oporu**, liczy **metryki ryzyka** (zmienność roczna, Sharpe, Sortino, max drawdown, beta) i generuje sygnały BYCZO / NIEDŹWIEDZIO / NEUTRALNIE.

Dostępny jako CLI (`stock-agents CDR`) oraz endpoint API (`GET /technical/CDR`).

## Uruchomienie

Komendy uruchamiaj z katalogu głównego projektu (`stock-agents/`) przez `poetry run`:

```bash
cd ~/PycharmProjects/stockAnalyzer/stock-agents

# Jedna spółka GPW
poetry run stock-agents PKO

# Kilka spółek
poetry run stock-agents PKO CDR KGHM

# Spółka zagraniczna (sufiks .US)
poetry run stock-agents TSLA.US AAPL.US

# Zmiana zakresu danych (domyślnie 365 dni)
poetry run stock-agents PKO --days 180
```

## Tickery GPW

Tickery GPW wpisuj bez sufiksu (np. `PKO`, `CDR`, `KGHM`). Agent automatycznie doda `.WA` i zastosuje znane aliasy (np. `KGHM` → `KGH.WA` na Yahoo Finance).

Spółki zagraniczne wpisuj z sufiksem `.US` (np. `TSLA.US`).

## Wskaźniki

### Trend
| Wskaźnik | Parametry | Opis |
|----------|-----------|------|
| SMA | 20 / 50 / 200 | Prosta średnia krocząca |
| EMA | 20 / 50 | Wykładnicza średnia krocząca |
| ADX | 14 | Siła trendu (>25 = wyraźny trend) |
| Supertrend | 7 / 3.0 | Dynamiczny poziom wsparcia/oporu |
| Aroon | 25 | Świeżość ostatnich szczytów i dołków |
| Ichimoku | 9 / 26 / 52 | Chmura Ichimoku |
| Parabolic SAR | 0.02 / 0.2 | Kroczący stop-loss |

### Momentum
| Wskaźnik | Parametry | Opis |
|----------|-----------|------|
| RSI | 14 | Siła względna (>70 wykupienie, <30 wyprzedanie) |
| Stochastic | 14 / 3 / 3 | Oscylator stochastyczny |
| Stochastic RSI | 14 | RSI wygładzony stochastycznie |
| MACD | 12 / 26 / 9 | Zbieżność/rozbieżność średnich |
| TSI | 13 / 25 / 13 | True Strength Index |
| CCI | 20 | Indeks kanału towarowego |
| Williams %R | 14 | Oscylator Williamsa |
| ROC | 10 | Szybkość zmiany ceny |

### Zmienność
| Wskaźnik | Parametry | Opis |
|----------|-----------|------|
| Bollinger Bands | 20 / 2σ | Wstęgi Bollingera |
| Keltner Channel | 20 / 2 | Kanał Keltnera |
| Donchian Channel | 20 | Kanał Donchiana |
| ATR | 14 | Średni rzeczywisty zasięg |

### Wolumen
| Wskaźnik | Parametry | Opis |
|----------|-----------|------|
| OBV | — | On-Balance Volume |
| CMF | 20 | Chaikin Money Flow |
| MFI | 14 | Money Flow Index |

## Sygnały i punktacja

Każdy wskaźnik generuje sygnał od -2 do +2 punktów. Łączny wynik decyduje o sentysmencie:

| Wynik | Ocena |
|-------|-------|
| ≥ 8 | SILNIE BYCZO |
| ≥ 4 | BYCZO |
| -3 do 3 | NEUTRALNIE |
| ≤ -4 | NIEDŹWIEDZIO |
| ≤ -8 | SILNIE NIEDŹWIEDZIO |

## Wsparcie / opór

Moduł `support_resistance.py` wyznacza **poziome poziomy** z wykresu (nie tylko z indykatorów):

- **Swing high/low** + klastrowanie bliskich poziomów (tolerancja 0.6×ATR) w strefy z liczbą dotknięć (siłą)
- **Punkty pivot** (PP / R1 / R2 / S1 / S2) z ostatniej sesji
- **Zniesienia Fibonacciego** od ostatniego istotnego ruchu
- Najbliższe wsparcie/opór z dystansem w % i ATR + sygnał „cena przy strefie"

## Ryzyko / zmienność

Moduł `risk.py` liczy metryki standardu profesjonalnego (roczne):

- **Zmienność roczna**, CAGR, total return
- **Sharpe** i **Sortino** (vs stopa wolna od ryzyka)
- **Max drawdown** + bieżące obsunięcie
- **Beta** vs benchmark (GPW → EWP, US → ^GSPC)
- % dni dodatnich, best/worst day
- Flaga **świeżości danych** (`data_quality`) — wykrywa stale prices

## Struktura pakietu

```
agents/technical/
├── agent.py               ← orchestracja: fetch → indicators → signals → print
├── fetcher.py             ← OHLCV + benchmark + cache TTL + świeżość danych
├── indicators.py          ← obliczanie 22 wskaźników (pandas-ta + numpy)
├── signals.py             ← funkcje sygnałowe (w tym sygnał S/R)
├── support_resistance.py  ← swingi, strefy, pivoty, Fibonacci
├── risk.py                ← zmienność, Sharpe, Sortino, drawdown, beta
└── printer.py             ← formatowanie i drukowanie raportu
```

## Zależności

- `yfinance` — dane OHLCV i benchmarki
- `pandas-ta ≥ 0.4.71b0` — wskaźniki techniczne (prerelease z poprawkami)
- `numpy` — metryki ryzyka i ręczna implementacja CCI (obejście błędu w pandas-ta)
