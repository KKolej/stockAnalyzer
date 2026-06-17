# stock-agents

System agentów do analizy giełdowej (GPW + rynki zagraniczne). Działa jako CLI lub REST API gotowe do integracji z n8n / LangChain / własnym frontendem.

## Agenty

| Agent | CLI | Endpoint | Opis |
|---|---|---|---|
| **Technical** | `stock-agents CDR` | `GET /technical/CDR` | 22 wskaźniki techniczne, sygnały, score |
| **Fundamental** | `fundamental-agents CDR` | `GET /fundamental/CDR` | P/E, ROE, Piotroski, Altman Z, DuPont |
| **Screener** | `screener-agents CDR PKO` | `GET /screener?tickers=CDR,PKO` | Przesiewanie z filtrami |
| **Speculator** | `speculator-agents CDR` | `GET /speculator/CDR` | Wzorce sezonowe, katalyzatory, projekcje |
| **Sentiment** | `sentiment-agents CDR` | `GET /sentiment/CDR` | Bankier, Stockwatch, Reddit, Google News |
| **DCF** | `dcf-agents CDR` | `GET /dcf/CDR` | Wycena DCF (Base / Bull / Bear) |
| **Compare** | `compare-agents CDR PKO KGHM` | `GET /compare?tickers=CDR,PKO,KGHM` | Porównanie side-by-side |
| **Macro** | `macro-agents` | `GET /macro` | WIG20, waluty NBP, sektory GPW |

## Szybki start

### Docker (zalecane)

```bash
git clone <repo>
cd stock-agents
cp .env.example .env          # opcjonalnie: wpisz ANTHROPIC_API_KEY

docker compose up -d
```

API dostępne pod `http://localhost:8000`. Dokumentacja: `http://localhost:8000/docs`.

### Lokalnie (Poetry)

```bash
python3.12 -m pip install poetry
poetry install
poetry run stock-api          # uruchamia API na porcie 8000
```

## REST API

```bash
# Analiza techniczna
curl http://localhost:8000/technical/CDR

# Analiza fundamentalna
curl http://localhost:8000/fundamental/KGHM

# Screener z filtrami
curl "http://localhost:8000/screener?tickers=CDR,PKO,KGHM&pe_max=20&sort_by=roe"

# Wzorce spekulacyjne
curl http://localhost:8000/speculator/CDR

# Sentyment mediów
curl http://localhost:8000/sentiment/CDR

# Wycena DCF
curl "http://localhost:8000/dcf/CDR?years=10"

# Porównanie spółek
curl "http://localhost:8000/compare?tickers=CDR,PKO,KGHM,TTWO.US"

# Dane makro
curl http://localhost:8000/macro
```

Pełna dokumentacja Swagger: `http://localhost:8000/docs`

## CLI

```bash
# Tickery GPW bez sufiksu, zagraniczne z .US
poetry run stock-agents PKO CDR KGHM --days 90
poetry run fundamental-agents CDR KGHM TTWO.US
poetry run screener-agents CDR PKO KGHM --pe-max 20
poetry run speculator-agents CDR OML.US
poetry run sentiment-agents CDR --mode keyword
poetry run dcf-agents CDR TTWO.US --years 10
poetry run compare-agents CDR PKO KGHM TTWO.US
poetry run macro-agents
```

## Zmienne środowiskowe

| Zmienna | Domyślna | Opis |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(opcjonalna)* | Klucz API Claude — włącza tryb `sentiment --mode claude` |
| `API_HOST` | `0.0.0.0` | Adres nasłuchiwania serwera |
| `API_PORT` | `8000` | Port serwera |

## Tickery

- **GPW**: bez sufiksu — `PKO`, `CDR`, `KGHM`, `LPP`, ...
- **Zagraniczne**: z sufiksem `.US` — `TSLA.US`, `AAPL.US`, `TTWO.US`
- Znane aliasy Yahoo Finance są obsługiwane automatycznie (np. `KGHM` → `KGH.WA`)

## Deweloperzy

```bash
poetry run pytest           # testy
poetry run ruff check .     # linter
poetry run mypy src/        # typy
```

## Struktura projektu

```
src/stock_agents/
├── api/                    # FastAPI — REST API
│   ├── app.py
│   ├── server.py
│   ├── serializer.py
│   └── routes/             # jeden plik na agenta
├── agents/
│   ├── technical/          # analiza techniczna (22 wskaźniki)
│   ├── fundamental/        # analiza fundamentalna + scoring
│   ├── screener/           # screener z filtrami
│   ├── speculator/         # wzorce, katalyzatory, projekcje
│   ├── sentiment/          # scraping Bankier, Stockwatch, Reddit
│   ├── dcf/                # wycena DCF
│   ├── compare/            # porównanie side-by-side
│   └── macro/              # dane makro GPW
└── ticker_map.py           # konwersja tickerów (GPW ↔ Yahoo Finance)
```
