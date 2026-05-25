# stock-agents

Agenty do analizy technicznej akcji (GPW i rynki zagraniczne).

## Wymagania

- Python 3.12+
- Poetry

## Instalacja

```bash
poetry install
```

## Konfiguracja

Skopiuj `.env.example` do `.env` i uzupełnij klucz API Stooq:

```bash
cp .env.example .env
# Edytuj .env i wpisz STOOQ_APIKEY
```

## Użycie

```bash
# GPW
poetry run stock-agents PKO CDR KGHM

# Rynki zagraniczne
poetry run stock-agents AAPL.US TSLA.US --days 60
```

## Narzędzia deweloperskie

```bash
poetry run pytest           # testy
poetry run pytest --cov     # testy z pokryciem
poetry run ruff check .     # linter
poetry run mypy src/        # type checking
```
