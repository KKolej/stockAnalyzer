# CLAUDE.md — kontekst projektu stock-agents

> Ten plik czytany jest na początku każdej sesji. Opisuje **co chcemy osiągnąć** i
> **jak myśleć o tej aplikacji**. Szczegóły implementacyjne → kod i README agentów.

## Cel

System agentów do analizy giełdowej (**GPW + rynki zagraniczne**). Każdy agent liczy
inny wycinek analizy (techniczna, fundamentalna, wycena, sentyment itd.) i wystawia
**surowe, ustrukturyzowane dane** przez REST API.

## Architektura docelowa (NAJWAŻNIEJSZE)

**Aplikacja to DOSTAWCA DANYCH, nie analityk.**

- Każdy agent = **osobny endpoint** zwracający JSON z danymi/sygnałami/metrykami.
- Konsumentem jest **n8n**, który zbiera endpointy pojedynczo.
- **Syntezę, ocenę i decyzje robi agent AI (LLM) w n8n — NIE ta aplikacja.**
- Cel wdrożeniowy: **chmura** (Docker, `stock-api` na :8000).

### Co z tego wynika — zasady projektowe
1. **Nie budujemy syntezy/werdyktów po naszej stronie.** Werdykty cząstkowe per agent
   są OK jako jeden z sygnałów, ale NIE inwestujemy w „mądrzejsze łączenie" — to robota
   LLM-a. (Endpoint `/analyze` i wewnętrzne wagi istnieją, ale to NIE jest kierunek rozwoju.)
2. **Jakość = jakość danych dla LLM.** Priorytety: poprawność > kompletność > kontrakt
   (schema) > metadane zaufania (świeżość/źródło/wiarygodność) > zwięzłość (tokeny).
3. **Kontrakt schematu.** Endpointy mają mieć Pydantic `response_model` → schemat w `/docs`
   (kontrakt dla n8n). Wzorzec: `api/schemas.py` + `model_validate(to_json(data))`.
   Modele z `extra="allow"` (dokumentują kluczowe pola, nie gubią reszty).
4. **Dane muszą być POPRAWNE u źródła** — LLM nie wyłapie błędu w liczbach. Cenny jest
   cross-check (drugie źródło) i flagi jakości (`data_quality`: świeżość/`is_stale`).
5. **API-first.** Każda funkcja agenta dostępna przez endpoint. CLI to dodatek diagnostyczny.

### Pomysły na rozwój „dla lepszych wyników" (kolejność)
1. **Reliability per sygnał (backtest)** — dołączać do sygnałów hit-rate/IC, żeby LLM
   wiedział, którym ufać. (Backtestu jeszcze NIE ma — to największa dźwignia jakości.)
2. ~~Response models na pozostałych endpointach~~ **ZROBIONE** — wszystkie endpointy danych
   mają `response_model` (technical, fundamental, dcf, speculator, screener, sentiment, macro,
   compare, broker). Bez modelu został tylko `/analyze` (świadomie — endpoint syntezy, nie kierunek).
3. **Drugie źródło GPW (Stooq)** — pełna historia (yfinance daje 1 dzień dla indeksów PL)
   + cross-check danych.
4. **Quality/source flags na wszystkich endpointach.**
5. **Wspólny cache `.info` z yfinance** (latencja/rate-limity pod n8n).

## Agenci (każdy = endpoint)

| Agent | Endpoint | Daje |
|---|---|---|
| Technical | `GET /technical/{t}` | 22 wskaźniki, wsparcie/opór, ryzyko (Sharpe/Sortino/DD/beta), sygnały, score |
| Fundamental | `GET /fundamental/{t}` | P/E, ROE, ROIC, Piotroski, Altman Z, DuPont, FCF, historia |
| Screener | `GET /screener?tickers=` | filtry + ranking (w tym Magic Formula) |
| Speculator | `GET /speculator/{t}` | wzorce sezonowe/zdarzeniowe, katalizatory, projekcje |
| Sentiment | `GET /sentiment/{t}` | Bankier, Stockwatch, Google News, Reddit (403) |
| DCF | `GET /dcf/{t}` | wycena DCF (Base/Bull/Bear) |
| Compare | `GET /compare?tickers=` | porównanie side-by-side |
| Macro | `GET /macro` | NBP (waluty, złoto), CPI, WIG20, sektory |
| Broker | `GET /broker/account`, `POST /broker/orders` | Alpaca: stan konta + egzekucja (paper/demo, rynki US) |
| Analyze | `GET /analyze/{t}` | zbiorczy (istnieje, ale NIE jest kierunkiem — patrz wyżej) |

## Stack i komendy

- Python 3.12, Poetry, FastAPI + uvicorn, pandas/pandas-ta/numpy, yfinance, BeautifulSoup+lxml.
- Jakość (uruchamiaj przed końcem zmian): `poetry run ruff check src/ tests/` •
  `poetry run mypy src/` • `poetry run pytest -q`
- API lokalnie: `poetry run stock-api` • Docker: `docker compose up -d` (port 8000, `/docs`, `/health`).
- ENV: `ANTHROPIC_API_KEY` (opcjonalny, sentiment claude), `CACHE_TTL`/`CACHE_ENABLED`, `API_PORT`.

## Tickery i benchmarki

- **GPW**: bez sufiksu (`PKO`, `CDR`) → kod dodaje `.WA` + aliasy (`KGHM`→`KGH.WA`).
- **Zagraniczne**: sufiks `.US` (`TSLA.US`).
- **Benchmark bety**: GPW → `EWP` (iShares MSCI Poland; `WIG20.WA` w yf daje tylko 1 dzień!),
  US → `^GSPC`.

## Pułapki danych (twarda wiedza — łatwo się sparzy)

- **Biznesradar = TYSIĄCE zł**, separator tysięcy = **spacja** (`2 027` = 2027). Parser
  musi usuwać spacje PRZED wyodrębnieniem liczby; wartości pieniężne ×1000 do PLN.
- **`/notowania/CPI` to spółka „CPI FIM SA", NIE inflacja!** Inflacja jest w
  `/wskazniki-makroekonomiczne/inflacja-cpi` (indeks 100+x → 103.1 = +3.1% r/r).
- **`lxml`, `beautifulsoup4`, `numpy` muszą być w `pyproject` deps** — inaczej scraping
  pada w Dockerze (`poetry install --only main`).
- **yfinance**: rate-limity/blokady → cache; stale prices → flaga świeżości; indeksy PL = 1 dzień.
- **`fiftyTwoWeekLow/High` z yfinance dla indeksów PL to ZAKRES JEDNEJ SESJI**, nie 52 tygodni
  (WIG20: 3891/3928 zamiast 2726/3929 → „pozycja 52W" 77% zamiast 99%). Zakres 52W indeksów
  bierzemy z Biznesradaru (`/notowania/WIG20`, `Min/Max 52 tyg`). **Stooq odpada** — od 2026
  stawia ścianę anty-botową (JS proof-of-work), CSV nie działa.
- **Bankier trzyma HISTORYCZNE skróty**: `/akcje/OPL` to **Optopol Technology** (wycofana),
  nie Orange Polska (`ORANGEPL`). Każdy scraper po slugu MUSI weryfikować nazwę spółki ze strony
  (`ticker_map.company_identity_tokens`), inaczej cicho zwraca newsy innej firmy.
- **Stockwatch: `?s=<ticker>` to szukajka pełnotekstowa** — dla `ALE` łapała każdy artykuł ze
  spójnikiem „ale" w slugu. Używać strony tagu: `/wiadomosci/walor/<ticker>`; brak tagu = podstawiony
  ogólny serwis (tytuł „Giełda od fundamentów"), trzeba to wykryć.
- **Świeżość liczyć w SESJACH, nie dniach kalendarzowych** — w sobotę brak piątkowej sesji daje
  `age_days=2` i stary próg (>4 dni) go przepuszczał.
- **`/technical` bierze cenę z `history()`, reszta agentów z `info["currentPrice"]`** — potrafią się
  różnić o kilka % (PGE 9,74 vs 10,11), gdy yfinance nie domknął ostatniej sesji.
- **Stary obraz w Dockerze wygląda jak świeży** — `/health` zwraca „ok" niezależnie od wersji kodu.
  Po deployu sprawdzać `/version` (git SHA + czas builda), inaczej łatwo o dobę na starym kodzie
  (tak zniknął cały Google News z sentymentu).
- **DuPont**: dźwignia = aktywa/kapitał (z bilansu), NIE `ROE/(marża×rotacja)` (dawało <1).
- **Magic Formula** wyklucza `Financial Services` i `Utilities` (Greenblatt).
- Reddit zwraca 403 (blokuje scraping) — znane, sentyment leci z pozostałych źródeł.
- **XTB: padł WebSocket, ale socket xAPI żyje** (sprawdzone 09.08.2026). `ws.xtb.com/demo|real`
  dalej zwraca 404 — i to na tej podstawie uznaliśmy kiedyś, że „XTB nie ma API". To był
  błędny wniosek: **`xapi.xtb.com:5124` (demo) i `:5112` (real) stoją**, TLS kończy handshake
  ważnym certyfikatem `*.xtb.com` (Sectigo, `Verify return code: 0`). To inny transport —
  JSON po gołym sockecie TLS, nie WebSocket. `ping` bez sesji nie odpowiada, więc **czy
  `login` przechodzi, wie tylko ktoś z danymi konta** — niesprawdzone. Uwaga przy wpinaniu:
  xAPI **nie ma zakresu read-only**, te same dane logowania pozwalają składać zlecenia.
- **Broker = Alpaca** (zaimplementowany, `/broker/*`): darmowe, REST, paper/demo, ale tylko rynki US.
  Domyślnie paper (`ALPACA_PAPER=1`). Dla GPW z egzekucją alternatywą byłby Interactive Brokers.
- `docker exec python` ≠ venv aplikacji — apka działa przez `poetry run` (.venv).

## Konwencje pracy

- Po większych zmianach: ruff + mypy + pytest muszą być zielone (mypy ma ~51 znanych
  błędów na granicy bibliotek — nie dokładać nowych).
- **Język: kod po angielsku, treść po polsku.** Po angielsku: komentarze, docstringi,
  nazwy zmiennych/funkcji/testów, `Field(description=...)` i opisy endpointów (kontrakt
  OpenAPI dla n8n), nazwy węzłów n8n. Po polsku zostaje wszystko, co widzi użytkownik lub
  co trafia do raportu: noty wzorców (`PatternResult.note`), opisy katalizatorów, komunikaty
  błędów w JSON, wydruki CLI (`printer.py`), teksty pomocy CLI, prompty systemowe dla LLM,
  README i ten plik. Wyjątek: komentarz może cytować polski tekst, gdy opisuje realne dane
  (nagłówek ze scrapingu, nazwa kolumny na Biznesradarze) — inaczej przestaje opisywać rzeczywistość.
- Nie psuć kontraktu istniejących endpointów (n8n od nich zależy).
