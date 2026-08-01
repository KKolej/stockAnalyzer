# n8n + stock-agents (wspólny docker-compose)

n8n odpytuje endpointy `stock-api` i przepuszcza surowe dane przez LLM.
Oba serwisy stoją w jednym `docker-compose.yml`, więc n8n dobija się do API po
nazwie serwisu: **`http://stock-api:8000`** (bez `host.docker.internal`).

## Start

```bash
docker compose up -d --build
```

- API:  http://localhost:8000/docs • **`/version`** = git SHA obrazu (sprawdź po deployu!)
- n8n:  http://localhost:5678

## Dwie drogi do LLM-a

| Droga | Czego wymaga | Używają jej |
|---|---|---|
| **Claude Code przez proxy** (subskrypcja, bez płatnego API) | `scripts/claude_proxy.py` uruchomiony **na hoście**, port 8787 | `wig20-daily.json`, `stock-analysis-claude-code.json` |
| **Anthropic API** (płatny klucz) | credential `ANTHROPIC_API_KEY` w n8n | `stock-analysis-workflow.json` |

Proxy startuje się na hoście (tam, gdzie zalogowany Claude Code), nie w kontenerze:

```bash
python3 scripts/claude_proxy.py     # nasłuchuje na :8787
```

Workflowy proxy wysyłają `"model": "opus"`. Bez tego pola `claude -p` bierze
**domyślny model konta (Sonnet)** — łatwo tego nie zauważyć, bo odpowiedź i tak przychodzi.

## Workflowy

### `wig20-daily.json` — dzienny przegląd (schedule 08:00)
Pobiera 5 endpointów × ~20 spółek + makro, robi przegląd w dwóch częściach
(koszyki 🟢/🔴/🟡 + szczegóły) i **wysyła mailem**.

### `stock-analysis-claude-code.json` — pytanie w czacie
Wpisujesz **dowolne pytanie** („co z CDR przed Gamescomem?”, „porównaj PKO i PEO”),
workflow sam wyłuskuje tickery (do 3), pobiera dla nich komplet danych i **odpowiada
w czacie** — bez maila. Ten sam zestaw reguł antyhalucynacyjnych co przegląd dzienny.
Uruchamianie: otwórz workflow → **Open Chat** (dół ekranu).

### `stock-analysis-workflow.json` — AI Agent (płatne API)
Endpointy podpięte jako narzędzia (tools) AI Agenta; agent sam decyduje, co wywołać.
Wymaga credentiala Anthropic w n8n.

### `stock-test-manual.json` — smoke test
Ręczny trigger, jeden ticker, jeden endpoint. Do sprawdzenia, czy n8n widzi API.

## Import

Menu (☰) → **Import from File** → wskaż plik JSON.
**Workflowy żyją w bazie n8n, nie w repo** — po każdej zmianie pliku trzeba go
zaimportować ponownie, inaczej n8n dalej używa starej wersji.

## Reguły w promptach (dlaczego są takie długie)

Prompty zawierają twarde zakazy, bo bez nich raport potrafił zmyślać: superlatywy
bez przeliczenia zestawu, ceny docelowe cytowane tylko gdy wspierały tezę, „Sharpe 3.06”
podawane jako wynik roczny (a to okno 89 dni), projekcje opisywane jako prognozy
(`is_backtested: false`), sentyment uzasadniany wydarzeniami spoza nagłówków.
Przy zmianach promptu nie usuwaj tych reguł — każda odpowiada konkretnej wpadce.

## Zmiana zestawu spółek

W `wig20-daily.json`: węzeł **„Lista spółek (edytuj)”**, pole `tickers` (CSV).
Nie w kodzie — węzeł `Zbierz dane` czyta listę stamtąd.
