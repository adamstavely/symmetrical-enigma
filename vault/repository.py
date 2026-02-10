"""
EDDA VAULT - Neo4j data access layer.
Expects architecture data as dicts matching the SCRIBE ArchitectureModel shape.
Supports manual_override (do not overwrite user corrections) and versioned snapshots.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

# Retention: keep at most this many versions per system
VERSION_RETENTION_COUNT = int(os.environ.get("VAULT_VERSION_RETENTION", "10"))


def _to_json_safe(obj: Any) -> Any:
    """Convert Neo4j types (e.g. DateTime) to JSON-serializable values."""
    if obj is None:
        return None
    if hasattr(obj, "iso_format"):
        return obj.iso_format()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_to_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    return obj


def _serialize_for_version(detail: dict[str, Any]) -> dict[str, Any]:
    """Make system detail JSON-serializable (e.g. Neo4j datetime -> ISO string)."""
    out: dict[str, Any] = {}
    for k, v in detail.items():
        if v is None:
            out[k] = None
        elif hasattr(v, "iso_format"):
            out[k] = v.iso_format()
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, list):
            out[k] = [_serialize_for_version(x) if isinstance(x, dict) else x for x in v]
        elif isinstance(v, dict):
            out[k] = _serialize_for_version(v)
        else:
            out[k] = v
    return out


class ArchitectureRepository:
    """Store and query C4 architecture graph in Neo4j."""

    def __init__(self, uri: str | None = None, auth: tuple[str, str] | None = None):
        self._uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = (auth or (os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "eddapassword")))[0]
        password = (auth or (os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "eddapassword")))[1]
        self._auth = (user, password)
        self._driver: Optional[AsyncDriver] = None

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(self._uri, auth=self._auth)
        return self._driver

    async def store_architecture(self, model: dict[str, Any], commit_sha: str | None = None) -> str | None:
        """
        Store a full ArchitectureModel. Does not overwrite nodes/rels with manual_override=true.
        Creates an ArchitectureVersion snapshot. Returns version id.
        """
        system = model["system"]
        containers = model.get("containers", [])
        components = model.get("components", [])
        relationships = model.get("relationships", [])
        external_dependencies = model.get("external_dependencies", [])

        async with self.driver.session() as session:
            # System: MERGE and SET (manual_override respected via separate PATCH API)
            await session.run(
                """
                MERGE (s:System {id: $id})
                ON CREATE SET s.name = $name, s.description = $description, s.team = $team, s.group = $group,
                    s.repository_url = $repository_url, s.last_analyzed = datetime(), s.updated_at = datetime(),
                    s.manual_override = false
                ON MATCH SET s.name = $name, s.description = $description, s.team = $team, s.group = $group,
                    s.repository_url = $repository_url, s.last_analyzed = datetime(), s.updated_at = datetime()
                """,
                **{k: v for k, v in system.items() if k in ("id", "name", "description", "team", "group", "repository_url")},
            )

            for c in containers:
                await session.run(
                    """
                    MATCH (s:System {id: $system_id})
                    MERGE (c:Container {id: $id})
                    ON CREATE SET c.name = $name, c.description = $description, c.technology = $technology,
                        c.type = $type, c.port = $port, c.repository_path = $repository_path,
                        c.updated_at = datetime(), c.manual_override = false
                    ON MATCH SET c.name = $name, c.description = $description, c.technology = $technology,
                        c.type = $type, c.port = $port, c.repository_path = $repository_path, c.updated_at = datetime()
                    WITH s, c
                    MERGE (s)-[:CONTAINS]->(c)
                    """,
                    system_id=system["id"],
                    id=c["id"],
                    name=c.get("name", ""),
                    description=c.get("description", ""),
                    technology=c.get("technology", ""),
                    type=c.get("type", "service"),
                    port=c.get("port"),
                    repository_path=c.get("repository_path"),
                )

            for rel in relationships:
                await session.run(
                    """
                    MATCH (from {id: $from_id})
                    MATCH (to {id: $to_id})
                    MERGE (from)-[r:DEPENDS_ON]->(to)
                    ON CREATE SET r.type = $type, r.protocol = $protocol, r.description = $description, r.manual_override = false
                    ON MATCH SET r.type = $type, r.protocol = $protocol, r.description = $description
                    """,
                    from_id=rel["from_id"],
                    to_id=rel["to_id"],
                    type=rel.get("type", "calls_api"),
                    protocol=rel.get("protocol"),
                    description=rel.get("description", ""),
                )

            for ext in external_dependencies:
                await session.run(
                    """
                    MERGE (e:ExternalSystem {id: $id})
                    SET e.name = $name, e.vendor = $vendor, e.type = $type
                    WITH e
                    MATCH (s:System {id: $system_id})
                    MERGE (s)-[:INTEGRATES_WITH]->(e)
                    """,
                    id=ext["id"],
                    name=ext.get("name", ""),
                    vendor=ext.get("vendor", ""),
                    type=ext.get("type", "saas"),
                    system_id=system["id"],
                )

            # Build snapshot for version (current system detail shape)
            detail = await self.get_system_detail(system["id"])
            if not detail:
                return None
            snapshot_json = json.dumps(_serialize_for_version(detail))
            version_id = str(uuid.uuid4())
            await session.run(
                """
                MATCH (s:System {id: $system_id})
                CREATE (v:ArchitectureVersion {id: $version_id, analyzed_at: datetime(), commit_sha: $commit_sha, snapshot: $snapshot})
                MERGE (s)-[:HAS_VERSION]->(v)
                """,
                system_id=system["id"],
                version_id=version_id,
                commit_sha=commit_sha or "",
                snapshot=snapshot_json,
            )
            # Retention: remove oldest versions beyond N
            await session.run(
                """
                MATCH (s:System {id: $system_id})-[:HAS_VERSION]->(v:ArchitectureVersion)
                WITH v ORDER BY v.analyzed_at DESC
                SKIP $retain
                DETACH DELETE v
                """,
                system_id=system["id"],
                retain=VERSION_RETENTION_COUNT,
            )
            return version_id

    async def get_enterprise_view(self) -> dict[str, Any]:
        """All systems and inter-system / external relationships for the top-level view."""
        async with self.driver.session() as session:
            systems_result = await session.run("MATCH (s:System) RETURN s ORDER BY s.name")
            systems = [dict(record["s"]) for record in await systems_result.data()]

            # Inter-system: container in s1 depends on container in s2 => edge s1 -> s2
            edges_result = await session.run(
                """
                MATCH (s1:System)-[:CONTAINS]->(c1:Container)-[:DEPENDS_ON]->(c2:Container)<-[:CONTAINS]-(s2:System)
                WHERE s1.id <> s2.id
                RETURN DISTINCT s1.id AS source, s2.id AS target, 'depends_on' AS type
                """
            )
            edges = [dict(r) for r in await edges_result.data()]

            # System -> external
            ext_result = await session.run(
                """
                MATCH (s:System)-[:INTEGRATES_WITH]->(e:ExternalSystem)
                RETURN s.id AS source, e.id AS target, 'integrates_with' AS type
                """
            )
            edges.extend([dict(r) for r in await ext_result.data()])

            return {"systems": _to_json_safe(systems), "edges": edges}

    async def get_system_versions(self, system_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """List versions for a system (newest first)."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (s:System {id: $system_id})-[:HAS_VERSION]->(v:ArchitectureVersion)
                RETURN v.id AS id, v.analyzed_at AS analyzed_at, v.commit_sha AS commit_sha
                ORDER BY v.analyzed_at DESC
                LIMIT $limit
                """,
                system_id=system_id,
                limit=limit,
            )
            rows = await result.data()
            return _to_json_safe([{"id": r["id"], "analyzed_at": r["analyzed_at"], "commit_sha": r["commit_sha"] or None} for r in rows])

    async def get_system_detail(self, system_id: str, version_id: str | None = None) -> dict[str, Any] | None:
        """System with its containers and relationships. If version_id given, return snapshot from that version."""
        if version_id:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (s:System {id: $system_id})-[:HAS_VERSION]->(v:ArchitectureVersion {id: $version_id})
                    RETURN v.snapshot AS snapshot
                    """,
                    system_id=system_id,
                    version_id=version_id,
                )
                record = await result.single()
                if not record or not record.get("snapshot"):
                    return None
                return json.loads(record["snapshot"])
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (s:System {id: $system_id})
                OPTIONAL MATCH (s)-[:CONTAINS]->(c:Container)
                OPTIONAL MATCH (c)-[r:DEPENDS_ON]->(c2:Container)
                WITH s, collect(DISTINCT c) AS containers, collect(DISTINCT {from: c, to: c2, rel: r}) AS rels
                RETURN s, containers,
                       [x IN rels WHERE x.from IS NOT NULL AND x.to IS NOT NULL | {from: x.from.id, to: x.to.id, type: x.rel.type}] AS relationships
                """,
                system_id=system_id,
            )
            record = await result.single()
            if not record or not record["s"]:
                return None
            rels = record["relationships"] or []
            return _to_json_safe({
                "id": record["s"]["id"],
                "name": record["s"].get("name"),
                "description": record["s"].get("description"),
                "team": record["s"].get("team"),
                "group": record["s"].get("group"),
                "repository_url": record["s"].get("repository_url"),
                "containers": [dict(c) for c in (record["containers"] or []) if c],
                "relationships": [r for r in rels if isinstance(r, dict)],
                "last_analyzed": record["s"].get("last_analyzed"),
            })

    async def get_container_detail(self, system_id: str, container_id: str) -> dict[str, Any] | None:
        """Container with its components and dependencies."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (s:System {id: $system_id})-[:CONTAINS]->(c:Container {id: $container_id})
                OPTIONAL MATCH (c)-[:CONTAINS]->(co:Component)
                OPTIONAL MATCH (c)-[r:DEPENDS_ON]->(c2:Container)
                RETURN c,
                       collect(DISTINCT co) AS components,
                       collect(DISTINCT {target: c2.id, type: r.type, description: r.description}) AS deps
                """,
                system_id=system_id,
                container_id=container_id,
            )
            record = await result.single()
            if not record or not record["c"]:
                return None
            c = record["c"]
            deps = [d for d in (record["deps"] or []) if d and d.get("target")]
            return _to_json_safe({
                "id": c["id"],
                "name": c.get("name"),
                "description": c.get("description"),
                "technology": c.get("technology"),
                "type": c.get("type"),
                "port": c.get("port"),
                "components": [dict(co) for co in (record["components"] or []) if co],
                "dependencies": deps,
            })

    async def get_all_systems(
        self,
        group: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List systems with optional group filter and pagination."""
        async with self.driver.session() as session:
            if group:
                result = await session.run(
                    "MATCH (s:System) WHERE s.group = $group RETURN s ORDER BY s.name SKIP $skip LIMIT $limit",
                    group=group,
                    skip=skip,
                    limit=limit,
                )
            else:
                result = await session.run(
                    "MATCH (s:System) RETURN s ORDER BY s.name SKIP $skip LIMIT $limit",
                    skip=skip,
                    limit=limit,
                )
            return _to_json_safe([dict(record["s"]) for record in await result.data()])

    async def get_all_groups(self) -> list[str]:
        """Distinct group values (ODIN, HEIMDALL, etc.)."""
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (s:System) WHERE s.group IS NOT NULL AND s.group <> '' RETURN DISTINCT s.group AS g ORDER BY g"
            )
            return [r["g"] for r in await result.data()]

    async def get_dependencies(
        self,
        node_id: str,
        direction: str = "both",
        depth: int = 1,
    ) -> dict[str, Any]:
        """Upstream/downstream/both dependencies for a node up to given depth."""
        async with self.driver.session() as session:
            if direction == "upstream":
                q = """
                MATCH (target {id: $node_id})<-[r:DEPENDS_ON*1..$depth]-(source)
                RETURN source.id AS id, 'upstream' AS dir
                """
            elif direction == "downstream":
                q = """
                MATCH (source {id: $node_id})-[r:DEPENDS_ON*1..$depth]->(target)
                RETURN target.id AS id, 'downstream' AS dir
                """
            else:
                q = """
                MATCH (n {id: $node_id})
                OPTIONAL MATCH (n)<-[r1:DEPENDS_ON*1..$depth]-(u)
                OPTIONAL MATCH (n)-[r2:DEPENDS_ON*1..$depth]->(d)
                RETURN collect(DISTINCT u.id) AS upstream, collect(DISTINCT d.id) AS downstream
                """
            result = await session.run(q, node_id=node_id, depth=depth)
            record = await result.single()
            if not record:
                return {"upstream": [], "downstream": []}
            if direction == "both":
                return {
                    "upstream": [x for x in (record.get("upstream") or []) if x],
                    "downstream": [x for x in (record.get("downstream") or []) if x],
                }
            return {"nodes": [record["id"]] if record.get("id") else [], "direction": direction}

    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Full-text search across systems, containers, components. Filters optional (e.g. group)."""
        async with self.driver.session() as session:
            try:
                cypher = """
                CALL db.index.fulltext.queryNodes('search_index', $query)
                YIELD node, score
                WHERE score > 0.3
                """
                params: dict[str, Any] = {"query": query, "limit": limit}
                if filters and filters.get("group"):
                    cypher += " AND node.group = $group"
                    params["group"] = filters["group"]
                cypher += " RETURN node, score ORDER BY score DESC LIMIT $limit"
                result = await session.run(cypher, **params)
                results = []
                async for rec in result:
                    node = rec["node"]
                    label = list(node.labels)[0] if node.labels else "Node"
                    results.append({
                        "type": label.lower(),
                        "id": node.get("id"),
                        "name": node.get("name"),
                        "match_score": float(rec["score"]),
                    })
                return results
            except Exception:
                return []

    async def set_manual_override(
        self,
        node_type: str,
        node_id: str,
        override: bool,
        system_id: str | None = None,
    ) -> bool:
        """Set manual_override on a System, Container, or Component. Returns True if updated."""
        async with self.driver.session() as session:
            if node_type.lower() == "system":
                result = await session.run(
                    "MATCH (s:System {id: $node_id}) SET s.manual_override = $override RETURN s",
                    node_id=node_id,
                    override=override,
                )
            elif node_type.lower() == "container":
                result = await session.run(
                    "MATCH (c:Container {id: $node_id}) SET c.manual_override = $override RETURN c",
                    node_id=node_id,
                    override=override,
                )
            elif node_type.lower() == "component":
                result = await session.run(
                    "MATCH (co:Component {id: $node_id}) SET co.manual_override = $override RETURN co",
                    node_id=node_id,
                    override=override,
                )
            else:
                return False
            record = await result.single()
            return record is not None

    async def set_relationship_override(self, from_id: str, to_id: str, override: bool) -> bool:
        """Set manual_override on a DEPENDS_ON relationship. Returns True if updated."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (a)-[r:DEPENDS_ON]->(b)
                WHERE a.id = $from_id AND b.id = $to_id
                SET r.manual_override = $override
                RETURN r
                """,
                from_id=from_id,
                to_id=to_id,
                override=override,
            )
            record = await result.single()
            return record is not None
