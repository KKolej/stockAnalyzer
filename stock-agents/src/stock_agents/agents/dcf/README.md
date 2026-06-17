# Agent DCF (Discounted Cash Flow)

Wycena spółki metodą zdyskontowanych przepływów pieniężnych. Generuje trzy scenariusze: Base, Bull, Bear.

## Uruchomienie

```bash
poetry run dcf-agents CDR KGHM TTWO.US
poetry run dcf-agents CDR --years 5      # krótszy horyzont
```

## API

```
GET /dcf/{ticker}?years=10
```

## Metodologia

### Faza 1 — projekcja FCF
FCF rośnie przez `N` lat (domyślnie 10) ze stałą stopą wzrostu scenariuszową.

### Faza 2 — terminal value (Gordon Growth)
```
TV = FCF_N × (1 + g) / (WACC - g)
```

### WACC — aproksymacja z CAPM
- Koszt kapitału własnego: `Ke = Rf + β × ERP`
- Rf: 4.5% (USD) / 5.5% (PLN), ERP: 5.5%
- Beta: z yfinance, fallback = 1.0
- Wagi D/E z yfinance `debtToEquity`

### Scenariusze

| Scenariusz | FCF_g | Terminal g | WACC delta |
|---|---|---|---|
| Base | 8% | 3% | 0 |
| Bull | 15% | 4% | -1% |
| Bear | 2% | 2% | +2% |

### Wycena akcji
```
Fair Value = (PV fazy 1 + PV terminal value - dług netto) / liczba akcji
```

## Ograniczenia

- FCF ≤ 0: wycena jest matematycznie możliwa, ale ekonomicznie bez sensu — agent to sygnalizuje.
- Zakładamy stały WACC i stałą stopę wzrostu — uproszczenie.
- FCF pochodzi z `freeCashflow` yfinance (TTM). Dla spółek GPW dane mogą być niekompletne.

## Struktura

```
agents/dcf/
├── fetcher.py      ← pobiera FCF, dług netto, akcje z yfinance
├── calculator.py   ← WACC, DCF, scenariusze
├── models.py       ← DCFResult, DCFScenario
├── printer.py      ← formatowanie raportu
├── agent.py        ← orchestracja
└── cli.py          ← argparse
```
