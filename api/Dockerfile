# Build from repo root: docker build -f api/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY api/pyproject.toml api/poetry.lock* ./api/
COPY vault ./vault
COPY scribe ./scribe
COPY api ./api

WORKDIR /app/api
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root
RUN pip install pyyaml gitpython
# scribe package lives at /app/scribe/scribe; vault at /app/vault
ENV PYTHONPATH=/app:/app/scribe

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
