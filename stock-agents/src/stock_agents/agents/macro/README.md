# Agent Makro

Kontekst rynkowy dla inwestora GPW — kursy walut, inflacja, indeksy, sektory.

## Użycie

```bash
macro-agents
```

Bez argumentów. Pobiera aktualne dane i wyświetla raport makro.

## Co pokazuje

### Kursy walut (NBP API)
USD/PLN, EUR/PLN, CHF/PLN, GBP/PLN z datą publikacji + zmiana 3M.  
Źródło: `api.nbp.pl/api/exchangerates/rates/a/{code}/` — darmowe, bez klucza.

### Złoto
Cena złota w PLN/g z NBP API.  
Źródło: `api.nbp.pl/api/cenyzlota/`

### Inflacja CPI
Aktualny odczyt CPI (r/r %) z Biznesradaru.  
Źródło: scraping `biznesradar.pl/notowania/CPI`

### WIG20
Aktualny poziom indeksu + zmiana 1D + pozycja w zakresie 52W.  
Źródło: yfinance `WIG20.WA`

### Sektory GPW (zmiana 1D)
8 indeksów sektorowych posortowanych malejąco:
- WIG-BANKI, WIG-PALIWA, WIG-INFO, WIG-ODZIEZ, WIG-BUDOW, WIG-CHEMIA, WIG-MEDIA, WIG-SPOZYW  
Każdy z pozycją w zakresie 52W (pasek wizualny).

### Kontekst dla inwestora
Automatyczne wnioski z danych:
- Inflacja < 2.5% → potencjalne obniżki stóp → korzystne dla obligacji i akcji wzrostowych
- Silny/słaby PLN → wpływ na eksporterów (KGHM, PKN) vs importerów
- WIG20 blisko 52W szczytu/dna → momentum vs korekta
- Najsilniejszy/najsłabszy sektor dnia

## Czego brakuje (niedostępne)
- **Stopa referencyjna NBP** — brak JSON API od NBP; strona JS-rendered
- **WIBOR3M** — brak na Biznesradar, nie w yfinance
- **Historyczne dane WIG20** — yfinance zwraca tylko 1 dzień dla polskich indeksów

## Struktura plików

```
macro/
├── agent.py    # run()
├── cli.py      # entry point
├── fetcher.py  # NBP API + yfinance + Biznesradar CPI
├── models.py   # MacroData, FxRate, SectorPerf
└── printer.py  # formatowanie raportu
```
