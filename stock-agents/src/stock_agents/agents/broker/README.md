# Agent Brokera (Alpaca)

Integracja z brokerem **Alpaca** — odczyt **stanu konta** i **egzekucja zleceń** przez REST API.
Zaprojektowane pod agenta AI w n8n: może dopytać o saldo/pozycje i składać/zamykać zlecenia.

> **Domyślnie tryb `paper` (konto DEMO)** — zero realnych pieniędzy. Real wymaga jawnego
> przełączenia `ALPACA_PAPER=0` i osobnych kluczy live.

## Dlaczego Alpaca

XTB wyłączyło publiczne API (14.03.2025 — `ws.xtb.com/demo` zwraca 404). Alpaca to:
- **darmowe API**, czysty **REST** (bez procesu-bramki jak Interactive Brokers),
- **konta paper (demo)** od ręki, prowizja 0,
- dobra dokumentacja, łatwa integracja z n8n.

**Ograniczenie:** rynki **US** (akcje/ETF/krypto), brak GPW. Wzorzec integracji jest jednak
identyczny dla każdego brokera z REST API — można później dołożyć innego.

## Konfiguracja

1. Załóż darmowe konto na <https://app.alpaca.markets/> i wejdź w **Paper Trading**.
2. Wygeneruj klucze (API Keys) i wpisz do `.env`:

```bash
ALPACA_API_KEY=PK...          # klucz paper
ALPACA_API_SECRET=...         # sekret paper
# ALPACA_PAPER=1              # 1 = demo (domyślnie), 0 = real
```

Dane logowania czytane są **wyłącznie z ENV** — nigdy nie trafiają do kodu ani logów.
Bez kluczy endpointy zwracają czysty błąd `503` (nie wywracają aplikacji).

## Endpointy

| Metoda | Endpoint | Opis |
|---|---|---|
| `GET` | `/broker/account` | saldo, equity, siła nabywcza, tryb (paper/live) |
| `GET` | `/broker/positions` | otwarte pozycje |
| `GET` | `/broker/positions/{symbol}` | pojedyncza pozycja |
| `GET` | `/broker/orders?status=open` | zlecenia (open/closed/all) |
| `POST` | `/broker/orders` | złóż zlecenie kupna/sprzedaży |
| `DELETE` | `/broker/orders/{order_id}` | anuluj otwarte zlecenie |
| `DELETE` | `/broker/positions/{symbol}` | zamknij całą pozycję |

### Przykłady

```bash
# Stan konta
curl http://localhost:8000/broker/account

# Otwarte pozycje
curl http://localhost:8000/broker/positions

# Kup 3 akcje AAPL po cenie rynkowej
curl -X POST http://localhost:8000/broker/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","side":"buy","qty":3}'

# Kup za 500 USD (notional) z limitem
curl -X POST http://localhost:8000/broker/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"TSLA","side":"buy","notional":500,"order_type":"limit","limit_price":180}'

# Zamknij pozycję
curl -X DELETE http://localhost:8000/broker/positions/AAPL
```

### Ciało zlecenia (`POST /broker/orders`)

| Pole | Wymagane | Opis |
|---|---|---|
| `symbol` | tak | np. `AAPL` |
| `side` | tak | `buy` \| `sell` |
| `qty` | qty **lub** notional | liczba akcji |
| `notional` | qty **lub** notional | kwota w USD |
| `order_type` | nie | `market` (dom.) \| `limit` \| `stop` |
| `time_in_force` | nie | `day` (dom.) \| `gtc` \| ... |
| `limit_price` / `stop_price` | nie | dla zleceń limit/stop |

## Bezpieczeństwo

- **Paper domyślnie** — bez `ALPACA_PAPER=0` nie ruszysz realnych środków.
- Sekrety tylko z ENV, nigdy w logach/odpowiedziach.
- Egzekucją steruje agent w n8n — warto tam dodać twarde limity (max wolumen, whitelist
  symboli, potwierdzenia) przed ewentualnym przejściem na konto real.

## Struktura

```
agents/broker/
├── client.py   ← klient Alpaca (REST/urllib): konto, pozycje, zlecenia
└── README.md
api/routes/broker.py   ← endpointy + mapowanie BrokerError → HTTP
api/schemas.py         ← AccountResponse, Position, Order, OrderRequest
```

## Schemat odpowiedzi

Wszystkie endpointy mają Pydantic `response_model` (kontrakt widoczny w `/docs`).
Modele są tolerancyjne (`extra="allow"`) — przepuszczają pełny obiekt Alpaca, dokumentując
kluczowe pola. Konsument (n8n) dostaje stabilny, opisany kontrakt.
