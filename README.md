# EDDA — Enterprise Documentation & Diagram Automation

A self-hosted, air-gapped platform that **generates and maintains C4 architecture diagrams** by analyzing code repositories using a local LLM. EDDA stores the result in a graph database and exposes it via a REST API and an interactive Angular frontend.

Named after the Poetic Edda; components use a Norse-inspired naming scheme (SCRIBE, VAULT, READER, WARDEN; groups such as ODIN, HEIMDALL, ASGARD).

---

## What EDDA does

- **Analyzes** Git repositories (Maven, NPM, Python, Go, Gradle) and infrastructure configs (Docker Compose, Kubernetes, Terraform) to infer systems, containers, and dependencies.
- **Stores** architecture as a graph in Neo4j (VAULT) so you can query and traverse relationships.
- **Serves** a REST API for the READER UI and for integrations.
- **Visualizes** C4 levels (Context → Container → Component) in an Angular app with Cytoscape.js and optional AWS icons for cloud diagrams.
- **Detects drift** (WARDEN): when code has changed but the diagram has not been updated, and can re-run analysis or notify teams.

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Git      │────▶│   SCRIBE    │────▶│   VAULT    │
│  (repos)   │     │  (analyzer) │     │  (Neo4j)   │
└─────────────┘     └──────┬──────┘     └─────┬──────┘
                          │                   │
                    Ollama / Mock             │
                          │                   ▼
                          │            ┌─────────────┐
                          │            │    API     │
                          │            │  (FastAPI) │
                          │            └─────┬──────┘
                          │                  │
                          │                  ▼
                          │            ┌─────────────┐
                          └───────────▶│   READER    │
                            (analyze)  │  (Angular) │
                                       └─────────────┘
                          ┌─────────────┐
                          │   WARDEN    │──── drift alerts
                          │  (scheduler)│
                          └─────────────┘
```

| Component | Role |
|-----------|------|
| **SCRIBE** | Clones/reads repos, extracts deps/configs/APIs, calls LLM (Ollama) or mock, writes C4 model to VAULT. |
| **VAULT** | Neo4j graph: System, Container, Component, ExternalSystem nodes and CONTAINS/DEPENDS_ON/INTEGRATES_WITH. |
| **API** | FastAPI: systems, enterprise view, search, dependencies, groups, optional analyze trigger. |
| **READER** | Angular + Cytoscape.js: C4 drill-down, search, filters, export (PDF/PNG/SVG), design tokens, Norse theming. |
| **WARDEN** | Scheduled job: compare repo last commit vs diagram last_analyzed, alert and optionally re-run SCRIBE. |

---

## Prerequisites

- **Docker** and **Docker Compose** (for Neo4j and optional API/SCRIBE in containers).
- **Python 3.12+** and **Poetry** (for running API and SCRIBE locally).
- **Node 18+** and **npm** (for READER).
- **Ollama** (optional): only needed if you run SCRIBE with a real LLM; use `USE_MOCK_LLM=true` for development without it.

---

## Quick start

### 1. Clone and configure

```bash
git clone <this-repo>
cd symmetrical-enigma
cp .env.example .env
# Edit .env if needed (e.g. NEO4J_PASSWORD, CORS_ORIGINS).
```

### 2. Start Neo4j and apply schema

```bash
docker compose up -d neo4j
# Wait ~20 seconds for Neo4j to be ready, then:
chmod +x scripts/init-neo4j.sh
./scripts/init-neo4j.sh
```

Or apply manually:

```bash
docker compose exec -T neo4j cypher-shell -u neo4j -p eddapassword < vault/scripts/init_schema.cypher
docker compose exec -T neo4j cypher-shell -u neo4j -p eddapassword < vault/scripts/indexes.cypher
```

### 3. Start the API

**Option A — Docker**

```bash
docker compose up -d api
# API: http://localhost:8000
```

**Option B — Local (Poetry, from repo root)**

```bash
cd api && poetry install
cd ..
PYTHONPATH=. poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run SCRIBE (analyze a repo and store in VAULT)

With **mock LLM** (no Ollama):

```bash
cd scribe && poetry install
cd ..
PYTHONPATH=. poetry run python scribe/cli.py analyze /path/to/any/repo --store
```

With a **real LLM** (Ollama running, e.g. Mixtral):

```bash
USE_MOCK_LLM=false PYTHONPATH=. poetry run python scribe/cli.py analyze /path/to/repo --store
```

### 5. Open READER (Angular)

```bash
cd reader && npm install && npm start
# READER: http://localhost:4200 (ensure CORS_ORIGINS includes it in .env).
```

### 6. Verify

- **Health:** `curl http://localhost:8000/health`
- **Enterprise view:** `curl http://localhost:8000/api/v1/enterprise`
- **Groups:** `curl http://localhost:8000/api/v1/groups`
- **OpenAPI:** http://localhost:8000/docs

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt URL. |
| `NEO4J_USER` / `NEO4J_PASSWORD` | `neo4j` / `eddapassword` | VAULT credentials. |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API (for SCRIBE when not using mock). |
| `OLLAMA_MODEL` | `mixtral:8x7b-instruct-v0.1-q4_K_M` | Model name for SCRIBE. |
| `USE_MOCK_LLM` | `true` | If `true`, SCRIBE uses fixture data (no GPU/Ollama). |
| `MOCK_MODEL_PATH` | (empty) | Optional path to a JSON fixture for mock analysis. |
| `API_PORT` | `8000` | API listen port. |
| `CORS_ORIGINS` | `http://localhost:4200,http://localhost:3000` | Allowed origins for READER. |
| `GIT_BASE_URL` / `GIT_TOKEN` | — | For WARDEN and SCRIBE when cloning private repos. |
| `DRIFT_CHECK_SCHEDULE` | `0 2 * * *` | Cron for WARDEN drift check. |
| `SLACK_WEBHOOK_URL` | (empty) | Optional Slack notifications for drift. |

See `.env.example` for the full list.

---

## Project structure

```
├── api/                 # FastAPI app
│   ├── api/
│   │   ├── main.py      # App, CORS, router wiring
│   │   ├── routers/    # systems, search, dependencies, groups, analyze
│   │   └── models/     # Request/response schemas
│   ├── Dockerfile
│   └── pyproject.toml
├── vault/               # Neo4j schema and data access
│   ├── repository.py    # ArchitectureRepository (async)
│   └── scripts/        # init_schema.cypher, indexes.cypher
├── scribe/              # Analysis engine
│   ├── scribe/
│   │   ├── models.py    # ArchitectureModel (Pydantic)
│   │   ├── analyzer.py # RepositoryAnalyzer + mock LLM
│   │   ├── prompts.py
│   │   └── extractors/  # dependencies, configs, apis
│   ├── cli.py           # analyze [--store] <path_or_url>
│   ├── Dockerfile
│   └── pyproject.toml
├── reader/              # Angular frontend
│   ├── src/
│   │   ├── app/         # components, core services, models, pages
│   │   ├── styles/      # _tokens.scss (design tokens)
│   │   └── environments/
│   └── package.json
├── warden/              # Drift detection (scheduler, notifiers)
├── scripts/
│   └── init-neo4j.sh   # Apply VAULT schema and indexes
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness. |
| GET | `/api/v1/enterprise` | All systems and edges (top-level C4 view). |
| GET | `/api/v1/systems` | List systems (query: `group`, `skip`, `limit`). |
| GET | `/api/v1/systems/{system_id}` | System detail with containers and relationships. |
| GET | `/api/v1/systems/{system_id}/containers/{container_id}` | Container with components and dependencies. |
| POST | `/api/v1/search` | Full-text search (body: `query`, `filters`). |
| GET | `/api/v1/dependencies/{node_id}` | Upstream/downstream (query: `direction`, `depth`). |
| GET | `/api/v1/groups` | List groups (ODIN, HEIMDALL, etc.). |
| POST | `/api/v1/analyze` | Trigger SCRIBE analysis for a repo (body: `repository_url`). |
| WS | `/api/v1/ws/analysis` | Optional WebSocket for analysis progress. |
| GET | `/api/v1/systems/{id}/versions` | List architecture versions (point-in-time). |
| GET | `/api/v1/systems/{id}?version=<id>` | System detail at a specific version. |
| PATCH | `/api/v1/systems/{id}/nodes/{node_id}/override` | Set manual override (query: `override`, `node_type`). |
| PATCH | `/api/v1/relationships/override` | Set manual override on a relationship (query: `from_id`, `to_id`, `override`). |

**Auth (optional):** Set `EDDA_API_KEY` in env to require `X-API-Key` header on requests. Extension point for SAML/LDAP + RBAC in production.

Interactive docs: **http://localhost:8000/docs**

---

## SCRIBE CLI

```bash
# Analyze a local directory (output to stdout, no store)
PYTHONPATH=. poetry run python scribe/cli.py analyze /path/to/repo

# Analyze and store in VAULT
PYTHONPATH=. poetry run python scribe/cli.py analyze /path/to/repo --store

# Analyze a Git URL (clones into /tmp/repos by default)
PYTHONPATH=. poetry run python scribe/cli.py analyze https://github.com/org/repo.git --store

# Batch analyze multiple repos (from file or positional args)
PYTHONPATH=. poetry run python scribe/cli.py batch --store --repos repos.txt
PYTHONPATH=. poetry run python scribe/cli.py batch --store --concurrency 3 https://github.com/org/a.git https://github.com/org/b.git
```

Set `SCRIBE_CLONE_DIR` to override the clone directory. Use `USE_MOCK_LLM=true` (default) to avoid needing Ollama.

---

## Running with Docker

```bash
# Start Neo4j and API
docker compose up -d neo4j api

# Apply schema (first time)
./scripts/init-neo4j.sh

# Optional: run READER (Angular) in Docker (port 3000; proxies /api to API)
docker compose up -d reader
# READER: http://localhost:3000

# Build and run SCRIBE (from repo root)
docker build -f scribe/Dockerfile -t edda-scribe .
docker run --network symmetrical-enigma_edda \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e NEO4J_PASSWORD=eddapassword \
  -e USE_MOCK_LLM=true \
  -v /path/to/repos:/tmp/repos \
  edda-scribe python -m scribe.cli analyze /tmp/repos/my-repo --store
```

---

## READER (Angular)

- **Design tokens:** All styling via `src/styles/_tokens.scss` (Norse-themed palette, spacing, typography).
- **Components:** Architecture graph, breadcrumb, search bar, system detail, export dialog, **version picker** (point-in-time view); shared UI in `core/` and `shared/`.
- **Version history:** When viewing a system, use the “Point-in-time” dropdown to load a past architecture snapshot (from SCRIBE runs). “Show latest” returns to the current view.
- **Run:** `cd reader && npm install && npm start` → http://localhost:4200. Set the API base URL in `src/environments/environment*.ts`.

---

## WARDEN (drift detection)

WARDEN runs as a Docker service or one-shot. It compares each system’s `last_analyzed` in VAULT with the repository’s last commit (via GitLab API when `GIT_TOKEN` is set) and can send alerts (e.g. Slack) and optionally re-run SCRIBE for drifted systems.

```bash
# Start WARDEN with Neo4j (scheduler runs daily at 02:00 by default)
docker compose up -d neo4j warden

# One-shot drift check (no scheduler)
WARDEN_RUN_ONCE=true docker compose run --rm warden
```

Configure `DRIFT_CHECK_SCHEDULE`, `DRIFT_ALERT_MIN_SEVERITY`, `DRIFT_AUTO_UPDATE`, `DRIFT_AUTO_UPDATE_MAX`, `SLACK_WEBHOOK_URL`, `GIT_BASE_URL`, and `GIT_TOKEN` in `.env`.

---

## Development

- **API and SCRIBE:** Run from repo root with `PYTHONPATH=.` so `vault` and `api`/`scribe` resolve.
- **Neo4j browser:** http://localhost:7474 (after `docker compose up neo4j`).
- **Tests:** `cd api && poetry run pytest`; `cd scribe && poetry run pytest`; `cd warden && poetry run pytest` (add tests under `api/tests/`, `scribe/tests/`, `warden/tests/` as needed).
- **Manual corrections:** Nodes and relationships can be marked with “manual override” via the API so SCRIBE does not overwrite them on the next analysis. Use PATCH endpoints above or a future READER UI.
- **Version retention:** VAULT keeps the last N architecture versions per system (default 10); set `VAULT_VERSION_RETENTION` to change.

---

## License

Open source; see the repository license. AWS Architecture Icons used in READER are under AWS’s icon usage guidelines.
