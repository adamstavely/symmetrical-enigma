#!/usr/bin/env sh
# Run from repo root. Requires Neo4j to be up (e.g. docker compose up -d neo4j).
set -e
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-eddapassword}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_DIR="$REPO_ROOT/vault/scripts"
docker compose exec -T neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" < "$SCRIPT_DIR/init_schema.cypher"
docker compose exec -T neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" < "$SCRIPT_DIR/indexes.cypher"
echo "Neo4j schema and indexes applied."
