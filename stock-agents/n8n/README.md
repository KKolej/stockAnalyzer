# n8n + stock-agents (wspólny docker-compose)

n8n odpytuje endpointy `stock-api` i przepuszcza dane przez Claude (AI Agent).
Oba serwisy stoją w jednym `docker-compose.yml`, więc n8n dobija się do API po
nazwie serwisu: **`http://stock-api:8000`** (bez `host.docker.internal`).

## 1. Start

```bash
docker compose up -d --build
```

- API:  http://localhost:8000/docs
- n8n:  http://localhost:5678

## 2. Credential do Claude (raz)

W n8n: **Credentials → New → Anthropic** → wklej `ANTHROPIC_API_KEY`.
(Sekret NIE jest w pliku workflow — workflow tylko go referuje.)

## 3. Import workflow

W n8n: menu (☰) → **Import from File** → wskaż `n8n/stock-analysis-workflow.json`.

Po imporcie:
1. Otwórz węzeł **Anthropic Chat Model** → wybierz utworzony credential
   i potwierdź model (domyślnie `claude-sonnet-4-6`; jeśli Twoja wersja n8n
   nie ma go na liście, wpisz/wybierz dostępny model Claude).
2. Kliknij **Open Chat** (dół ekranu) i wpisz ticker, np. `CDR`, `PKO`, `TSLA.US`.

## Jak to działa

Endpointy są podpięte jako **narzędzia (tools)** AI Agenta:
`technical`, `fundamental`, `dcf`, `speculator`, `sentiment`, `macro`.
Agent dla podanego tickera odpytuje wszystkie, a potem robi syntezę po polsku.
Surowe dane liczy `stock-api` — synteza/werdykt to robota LLM (zgodnie z architekturą).

## Zmiana zestawu endpointów

Każde narzędzie to węzeł **HTTP Request Tool**. Aby dodać kolejny endpoint
(np. `/screener`, `/compare`), skopiuj istniejący węzeł-narzędzie, zmień `url`
i `toolDescription`, podłącz wyjście `ai_tool` do AI Agenta.
```
