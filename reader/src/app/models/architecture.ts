/**
 * EDDA READER — Architecture API types.
 * Single source of truth; aligned with API response shapes (VAULT/PRD §3.3).
 */

export interface SystemNode {
  id: string;
  name?: string;
  description?: string;
  team?: string;
  group?: string;
  repository_url?: string;
  last_analyzed?: string;
  updated_at?: string;
}

export interface Edge {
  source: string;
  target: string;
  type: 'depends_on' | 'integrates_with';
}

export interface EnterpriseView {
  systems: SystemNode[];
  edges: Edge[];
}

export interface ContainerNode {
  id: string;
  name?: string;
  description?: string;
  technology?: string;
  type?: string;
  port?: number;
  repository_path?: string;
  updated_at?: string;
}

export interface RelationshipRef {
  from?: string;
  to?: string;
  type?: string;
}

export interface SystemDetail {
  id: string;
  name?: string;
  description?: string;
  team?: string;
  group?: string;
  repository_url?: string;
  containers: ContainerNode[];
  relationships: RelationshipRef[];
  last_analyzed?: string;
}

export interface ComponentNode {
  id: string;
  name?: string;
  description?: string;
  responsibility?: string;
  file_path?: string;
  language?: string;
}

export interface ContainerDependency {
  target: string;
  type?: string;
  description?: string;
}

export interface ComponentRelationshipRef {
  from: string;
  to: string;
  type?: string;
}

export interface ContainerDetail {
  id: string;
  name?: string;
  description?: string;
  technology?: string;
  type?: string;
  port?: number;
  components: ComponentNode[];
  component_relationships?: ComponentRelationshipRef[];
  dependencies: ContainerDependency[];
}

export interface SearchFilters {
  group?: string;
  technology?: string;
}

export interface SearchResultItem {
  type: string;
  id: string;
  name?: string;
  match_score?: number;
}

export interface DependenciesResponse {
  upstream?: string[];
  downstream?: string[];
  nodes?: string[];
  direction?: string;
}

export type C4Level = 'enterprise' | 'system' | 'container';

export interface ArchitectureVersion {
  id: string;
  analyzed_at?: string;
  commit_sha?: string | null;
}

/** Version diff: what changed between two architecture versions */
export interface VersionDiff {
  system_id: string;
  from_version_id: string;
  to_version_id: string;
  containers_added: ContainerNode[];
  containers_removed: ContainerNode[];
  containers_changed: Array<{ id: string; from: ContainerNode; to: ContainerNode }>;
  relationships_added: RelationshipRef[];
  relationships_removed: RelationshipRef[];
}

export interface DriftAlert {
  system_id: string;
  system_name: string;
  repository_url: string | null;
  last_analyzed: string | null;
  last_commit: string | null;
  drift_hours: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface DriftAlertsResponse {
  alerts: DriftAlert[];
}

export interface AnalyzeRequest {
  repository_url: string;
}

export interface AnalyzeResponse {
  status: string;
  system_id: string;
  system_name: string;
  containers: number;
  relationships: number;
}
