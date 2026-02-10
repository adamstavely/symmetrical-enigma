# Build from repo root: docker build -f scribe/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY scribe/pyproject.toml scribe/poetry.lock* ./scribe/
COPY vault ./vault
COPY scribe ./scribe

WORKDIR /app/scribe
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root
ENV PYTHONPATH=/app

CMD ["python", "-m", "scribe.cli", "analyze", "--help"]
