# Agent Analizy Technicznej

Pobiera dane OHLCV z Yahoo Finance i oblicza 22 wskaźniki techniczne dla spółek GPW i rynków zagranicznych. Generuje sygnały BYCZO / NIEDŹWIEDZIO / NEUTRALNIE i drukuje sformatowany raport w konsoli.

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

## Struktura pakietu

```
agents/technical/
├── agent.py        ← orchestracja: fetch → indicators → signals → print
├── fetcher.py      ← pobieranie OHLCV z Yahoo Finance (yfinance)
├── indicators.py   ← obliczanie 22 wskaźników (pandas-ta + numpy)
├── signals.py      ← 20 funkcji sygnałowych zwracających Signal | None
└── printer.py      ← formatowanie i drukowanie raportu w konsoli
```

## Zależności

- `yfinance` — dane OHLCV
- `pandas-ta ≥ 0.4.71b0` — wskaźniki techniczne (prerelease z poprawkami)
- `numpy` — ręczna implementacja CCI (obejście błędu w pandas-ta)
