# Build from repo root: docker build -f api/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY api/pyproject.toml api/poetry.lock* ./api/
COPY vault ./vault
COPY scribe ./scribe
COPY warden ./warden
COPY api ./api

WORKDIR /app/api
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root
RUN pip install pyyaml gitpython
# scribe at /app/scribe; vault at /app/vault; warden at /app/warden
ENV PYTHONPATH=/app:/app/scribe:/app/warden

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
