# Agent Spekulanta

Analiza spekulacyjna oparta na wzorcach historycznych z prawdopodobieństwami.
Horyzont projekcji: **1 tydzień – 2 miesiące**.

## Użycie

```bash
speculator-agents PKO CDR TSLA.US
```

## Co analizuje

### Katalyzatory
Nadchodzące zdarzenia w oknie -30..+120 dni:
- **Ex-dywidenda** — dzień odcięcia prawa do dywidendy
- **Raport wynikowy** — planowana publikacja wyników kwartalnych

Źródło: `yf.Ticker.calendar`

### Wzorce historyczne (backtesting)

| Wzorzec | Metoda | Okno |
|---------|--------|------|
| Pre-div rally | Zwrot ceny 35→2 dni przed każdą ex-datą | 30 dni |
| Post-div | Zwrot ceny 1→31 dni po każdej ex-dacie | 30 dni |
| Pre-earnings drift | Zwrot ceny 12→1 dni przed każdym raportem | 12 dni |
| Batting average | % beatów EPS ważone magnitudą niespodzianki | 5 dni |
| Anomalia wolumenu | Dzisiejszy wolumen vs 20-dniowa średnia | 7 dni |
| Pozycja 52W | Gdzie cena jest w rocznym przedziale H-L | 30 dni |
| Momentum vs WIG20 | Relative return 5D i 20D vs benchmark | 5/20 dni |
| Momentum vs sektor | Relative return 20D vs indeks sektorowy WIG-* | 20 dni |
| Sezonowość | Historyczna skuteczność bieżącego miesiąca | 30 dni |
| Rekomendacje analityków | Kupuj/Trzymaj/Sprzedaj + cel cenowy z Biznesradaru | 60 dni |

### Prawdopodobieństwa
Każdy wzorzec ma prawdopodobieństwo wyliczone z danych historycznych:
- **Wzorce cenowe** (div, earnings, sezonowość): `liczba_pozytywnych / n`
- **Batting average**: ważone magnitudą niespodzianki EPS, nie tylko licznikiem
- **Rekomendacje**: `buys / total` z small-sample discount (cap 80%)
- **Projekcje**: max 82% — brak pewności absolutnej

### Sektory GPW

| Ticker | Indeks sektorowy |
|--------|-----------------|
| PKO, MBK, PZU | WIG-BANKI.WA |
| PKN | WIG-PALIWA.WA |
| LPP, CCC | WIG-ODZIEZ.WA |
| CDR, OPL | WIG-INFO.WA |
| BDX | WIG-BUDOW.WA |

### Projekcja
Agregacja wzorców ważona siłą sygnału (strong=3, medium=2, weak=1) × prawdopodobieństwo.
Zakres zwrotu wyliczany z historycznych avg_return wzorców w danym horyzoncie.

## Źródła danych

| Źródło | Dane |
|--------|------|
| **yfinance** | Historia cen (8 lat), dywidendy, earnings dates, calendar |
| **Biznesradar** | Rekomendacje analityków (`/rekomendacje-spolki/TICKER`) |

## Ograniczenia

- Wzorce dywidendowe mają małe próbki (PKO: ~7 ex-dat) — traktuj jako wskazówkę, nie wyrok
- Batting average bazuje na `yf.earnings_dates` — dla GPW dane mogą być niekompletne
- **Insiderzy TODO**: Biznesradar nie udostępnia transakcji ESPI przez scraping; KNF udostępnia dane krótkich pozycji

## Struktura plików

```
speculator/
├── agent.py      # orkiestracja
├── cli.py        # entry point CLI
├── models.py     # Catalyst, PatternResult, Projection, SpeculatorData
├── patterns.py   # wszystkie wzorce + pobieranie danych
├── signals.py    # agregacja wzorców → projekcje
└── printer.py    # wyświetlanie
```
