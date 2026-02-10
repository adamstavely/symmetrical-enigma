// EDDA VAULT - Neo4j schema (C4 architecture graph)
// Node types: System, Container, Component, ExternalSystem, ArchitectureVersion
// Run once after Neo4j is up

CREATE CONSTRAINT system_id IF NOT EXISTS FOR (s:System) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT container_id IF NOT EXISTS FOR (c:Container) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT component_id IF NOT EXISTS FOR (co:Component) REQUIRE co.id IS UNIQUE;
CREATE CONSTRAINT external_system_id IF NOT EXISTS FOR (e:ExternalSystem) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT architecture_version_id IF NOT EXISTS FOR (v:ArchitectureVersion) REQUIRE v.id IS UNIQUE;
