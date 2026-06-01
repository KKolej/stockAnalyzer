# Agent Analizy Sentymentu

Zbiera wzmianki o spółce z czterech źródeł (Reddit, Bankier.pl, Stockwatch.pl, Google News) i ocenia ich wydźwięk: BYCZO / NIEDŹWIEDZIO / NEUTRALNIE. Działa w dwóch trybach analizy przełączanych flagą `--mode`.

## Uruchomienie

Komendy uruchamiaj z katalogu głównego projektu (`stock-agents/`) przez `poetry run`:

```bash
cd ~/PycharmProjects/stockAnalyzer/stock-agents

# Tryb domyślny — analiza słów kluczowych (lokalnie, bez kosztów)
poetry run sentiment-agents PKO

# Kilka spółek naraz
poetry run sentiment-agents PKO CDR KGHM

# Spółka zagraniczna
poetry run sentiment-agents TSLA.US

# Tryb Claude — lepsza jakość, wymaga klucza ANTHROPIC_API_KEY
poetry run sentiment-agents PKO --mode claude
```

## Tryby analizy

### `--mode keyword` (domyślny)

Analiza lokalna na podstawie słów kluczowych. Nie wymaga dostępu do API. Szybka, deterministyczna, bezkosztowa. Precyzja niższa niż tryb Claude — bazuje na liście słów byczo/niedźwiedzich.

### `--mode claude`

Wysyła tytuły artykułów do Claude Haiku przez Anthropic API. Rozumie kontekst, ironię i język finansowy. Wymaga zmiennej środowiskowej:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Jeśli klucz jest niedostępny, agent automatycznie wraca do trybu `keyword`.

## Źródła danych

| Źródło | Metoda | Język | Limit |
|--------|--------|-------|-------|
| Reddit | JSON API | EN/PL | 25 postów / subreddit |
| Bankier.pl | Scraping HTML | PL | ~30 artykułów |
| Stockwatch.pl | Scraping HTML | PL | ~30 artykułów |
| Google News | RSS (feedparser) | PL + EN | bez limitu |

Wszystkie źródła są pobierane równolegle (ThreadPoolExecutor). Niedostępne źródło nie blokuje pozostałych.

### Subreddity (Reddit)

- r/wallstreetbets
- r/investing
- r/stocks
- r/polish_stocks
- r/gielda

## Punktacja sentymentu

Każda wzmianka dostaje wynik od -1.0 do +1.0:

| Wynik | Oznaczenie |
|-------|------------|
| > 0.1 | BYCZO |
| < -0.1 | NIEDŹWIEDZIO |
| -0.1 do 0.1 | NEUTRALNIE |

Wynik globalny to średnia ze wszystkich wzmianek ze wszystkich źródeł:

| Wynik globalny | Ocena |
|----------------|-------|
| > 0.5 | SILNIE BYCZO |
| > 0.1 | BYCZO |
| -0.1 do 0.1 | NEUTRALNY |
| < -0.5 | SILNIE NIEDŹWIEDZIO |
| < -0.1 | NIEDŹWIEDZIO |

## Struktura pakietu

```
agents/sentiment/
├── agent.py        ← orchestracja: równoległe fetch → analyze → print
├── analyzer.py     ← logika analizy (keyword i claude)
├── cli.py          ← CLI: argparse, flaga --mode
├── models.py       ← dataclassy: Mention, SourceResult, TickerSentiment
├── printer.py      ← formatowanie raportu w konsoli
└── sources/
    ├── reddit.py       ← Reddit JSON API
    ├── bankier.py      ← scraping Bankier.pl (BeautifulSoup)
    ├── stockwatch.py   ← scraping Stockwatch.pl (BeautifulSoup)
    └── google_news.py  ← RSS Google News (feedparser)
```

## Zależności

- `beautifulsoup4` + `lxml` — parsowanie HTML (Bankier, Stockwatch)
- `feedparser` — RSS Google News
- `anthropic` — Claude API (opcjonalne, tylko tryb `claude`)

## Zmienne środowiskowe

| Zmienna | Opis | Wymagana |
|---------|------|----------|
| `ANTHROPIC_API_KEY` | Klucz API Anthropic | Tylko dla `--mode claude` |
