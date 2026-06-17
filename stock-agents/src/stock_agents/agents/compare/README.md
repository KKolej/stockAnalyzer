# Agent Compare (porównawczy)

Porównanie wielu spółek side-by-side w jednej tabeli. Oznacza gwiazdką (`*`) najlepszą wartość w każdej kategorii.

## Uruchomienie

```bash
poetry run compare-agents CDR PKO KGHM
poetry run compare-agents CDR TTWO.US EA.US        # mix GPW + US
```

## API

```
GET /compare?tickers=CDR,PKO,KGHM,TTWO.US
```

## Metryki

**Wycena:** P/E (trailing + forward), P/B, P/S, EV/EBITDA

**Rentowność:** ROE, ROA, marża netto, marża operacyjna

**Zdrowie finansowe:** D/E, IC (EBIT/odsetki), Beta, dywidenda

**Dane:** FCF TTM, przychody, market cap, cena

## Struktura

```
agents/compare/
├── agent.py    ← fetch równoległy (ThreadPoolExecutor)
├── printer.py  ← tabela z oznaczeniem najlepszych wartości
└── cli.py      ← argparse
```
