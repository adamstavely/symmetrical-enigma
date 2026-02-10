# WARDEN: drift detection; needs vault + scribe at runtime for auto_update
FROM python:3.12-slim

WORKDIR /app

# Monorepo: copy vault, scribe, warden so we can import them
COPY vault /app/vault
COPY scribe /app/scribe
COPY warden /app/warden

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir \
    neo4j apscheduler httpx gitpython \
    pydantic pyyaml gitpython \
    httpx

# Default: run scheduler (override with WARDEN_RUN_ONCE=true for one-shot)
CMD ["python", "-m", "warden.scheduler"]
