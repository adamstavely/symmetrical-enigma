// EDDA VAULT - Indexes for query and full-text search

CREATE INDEX system_group IF NOT EXISTS FOR (s:System) ON (s.group);
CREATE INDEX container_tech IF NOT EXISTS FOR (c:Container) ON (c.technology);
CREATE INDEX system_name IF NOT EXISTS FOR (s:System) ON (s.name);
CREATE INDEX system_last_analyzed IF NOT EXISTS FOR (s:System) ON (s.last_analyzed);

// Full-text search (Neo4j 5.x)
CREATE FULLTEXT INDEX search_index IF NOT EXISTS FOR (n:System|Container|Component) ON EACH [n.id, n.name, n.description];
