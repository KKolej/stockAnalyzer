FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root

COPY src/ src/
RUN poetry install --only-root

EXPOSE 8000

CMD ["poetry", "run", "stock-api", "--host", "0.0.0.0", "--port", "8000"]
