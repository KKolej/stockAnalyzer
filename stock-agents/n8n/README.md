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

W `wig20-daily.json` etap per-spółkę robi 20 wywołań pod rząd. Jeśli subskrypcja zacznie
przycinać, zmień `"model": "opus"` na `"sonnet"` w węźle `Claude Code (per ticker)` —
etap rankingu (`Claude Code (ranking)`) to jedno tanie wywołanie i może zostać na Opusie.

## Workflowy

### `wig20-daily.json` — dzienny przegląd (schedule 08:00)
Pobiera 5 endpointów × ~20 spółek + makro, robi przegląd w dwóch częściach
(koszyki 🟢/🔴/🟡 + szczegóły) i **wysyła mailem**.

Działa w trybie **map-reduce**, nie jednym wielkim promptem:

1. `Fetch data (sequential)` — pobiera dane i emituje **jeden item na spółkę**.
2. `Loop over tickers` (batch 1) → `Claude Code (per ticker)` — analiza JEDNEJ spółki
   (~9k tokenów). Zwraca `###KOSZYK### / ###LINIA### / ###SZCZEGOLY###`.
3. `Build ranking prompt` → `Claude Code (ranking)` — dostaje tylko 20 jednozdaniowych
   ocen + makro (~15k tokenów) i zwraca `###NAGLOWEK### / ###KOLEJNOSC### / ###MAKRO###`.
4. `Assemble e-mail` — renderuje maila (HTML + wersja tekstowa).

**Etap rankingu NIE przepisuje linii spółek** — w `###KOLEJNOSC###` podaje same tickery
(`🟢: PKO, CDR`), a treść wkleja `Assemble e-mail` dokładnie tak, jak napisał ją etap
per-spółkę. Wcześniej model przepisywał 20 linii i po drodze gubił cyfry.

### Wygląd maila (`Assemble e-mail`)

Mail wychodzi jako **HTML + `text/plain`** (`emailFormat: both`), temat zawiera bilans
koszyków: `WIG20 — przegląd 02.08.2026 · 3🟢 2🔴 15🟡 · ⚠️ dane nieświeże`.

Układ: ciemny nagłówek → trzy kafle z licznikami koszyków → baner ostrzeżeń → nagłówek
dnia → Część 1 (koszyki, ticker w plakietce + jednozdaniowy sygnał + **pasek horyzontów**)
→ tło makro → Część 2 (karta na spółkę 🟢/🔴: **tabela horyzontów** + bloki
**Fakty / Model / Interpretacja**) → stopka z zastrzeżeniem.

### Oceny w horyzontach

Każda spółka — także z koszyka 🟡 — dostaje sześć ocen: **7D, 2T, 1M, 3M, 1R, LT**
(▲ kupuj / ● trzymaj / ▼ sprzedaj / · brak danych). W Części 1 to pasek do skanowania,
w Części 2 tabela z jednozdaniowym uzasadnieniem.

Prompt per-spółkę **przypisuje horyzontom rozłączne źródła danych** (zasada 14) — bo bez
tego model uzasadniał ocenę roczną RSI-em:

| Horyzont | Wolno użyć |
|---|---|
| 7D, 2T | technika, wzorce **z triggerem**, kalendarz katalizatorów |
| 1M, 3M | sezonowość (z `sample_size`), katalizatory w oknie, momentum, cel analityków z datą |
| 1R | wyłącznie fundamenty i wycena — **zakaz** RSI/MACD/Bollingera/52W |
| LT | jakość biznesu: ROIC, trwałość marż, dźwignia, Piotroski, CAGR |

Brak danych na horyzont → `BRAK DANYCH` + powód; zakaz wypełniania „na wyczucie".
Format odpowiedzi to `KOD | OCENA | uzasadnienie`; parser w `Collect review` toleruje
pogrubienia i brakujące wiersze (brakujący horyzont = „brak danych", nigdy dziura w tabeli).

Rzeczy, które **liczy kod, nie model** (arytmetyka na `quality` — nie ma powodu, żeby
prompt mógł się w niej pomylić): liczniki koszyków, data ostatniej sesji, lista spółek
z nieświeżymi danymi, lista spółek bez analizy, temat maila.

Wymagania techniczne, o które łatwo się potknąć przy zmianach:

- **Style tylko inline** — Gmail/Outlook wycinają `<style>`; layout na `<table>`, bez flex/grid.
- Szczegóły są rozbijane po nagłówkach `**Fakty**` / `**Model**` / `**Interpretacja**`
  (dlatego prompt per-spółkę wymaga dokładnie takiego zapisu). Inny zapis nie gubi treści —
  ląduje jako jeden blok bez etykiety.
- Renderer markdownu w węźle ogarnia `**bold**`, `*kursywę*`, `` `kod` `` i wypunktowania;
  reszta składni przechodzi jako tekst, a wszystko jest escape'owane (`&`, `<`, `>`).

**Dlaczego tak:** wersja z jednym promptem padała na `Prompt is too long`
(~1,32 M tokenów przy limicie 1 M) — proxy zwracało wtedy 502, a n8n pokazywał
mylące „Bad gateway" po 5 sekundach. Winowajcą był sentyment: **95% promptu**,
w tym ~10k tokenów na spółkę samych base64-owych URL-i z Google News, których
raport i tak nigdy nie cytuje.

`trimSentiment()` w węźle `Fetch data (sequential)` wycina URL-e, zawęża wzmianki
do 90 dni i tnie do 40 na źródło: **25k → 5,2k tokenów na spółkę**, przy nietkniętych
`total_mentions` i `overall_score` (liczonych przez API na pełnym zbiorze — dlatego
zasada 11 w prompcie mówi modelowi, że widzi wycinek). Wzmianki **nie przychodzą
posortowane po dacie** (Google News wrzuca między świeże newsy pozycje z 2004 r.),
więc kod sortuje je przed cięciem — bez tego cap obcinałby losowe, nie najstarsze.

Odporność: `Claude Code (per ticker)` ma retry ×2 i `continueRegularOutput`, więc jedna
padnięta spółka nie zabija przebiegu (trafia do banera ostrzeżeń w mailu). Gdy padnie etap
rankingu, mail i tak wychodzi w pełnym układzie — bez nagłówka dnia i makro, z kolejnością
spółek w koszykach taką, w jakiej przyszły.

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

W `wig20-daily.json`: węzeł **„Ticker list (edit here)”**, pole `tickers` (CSV).
Nie w kodzie — węzeł `Fetch data (sequential)` czyta listę stamtąd.

Nazwy węzłów i komentarze w kodzie są po angielsku (konwencja z `CLAUDE.md`);
prompty i raport zostają po polsku.
