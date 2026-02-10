# C4 Level 4 (Code) — Implementation Plan

This document is a step-by-step plan to implement the **Code** level of the C4 model in EDDA: zoom into a component and show code elements (classes, interfaces, functions, etc.) and their relationships.

---

## Goals

- **Store** code elements and code-level relationships per component (from SCRIBE).
- **Expose** component detail (with code elements) via the API.
- **Visualize** a code diagram in READER: one component plus its code elements and edges (implements, extends, calls, uses).

---

## Scope and constraints

- **Optional level**: Many teams skip the code level; EDDA should work without it (empty code_elements is fine).
- **Per-component**: Code elements belong to a component; the graph is “one component + its code elements.”
- **ID uniqueness**: Code element ids must be unique in the graph (e.g. `{component_id}:{file_path}:{name}` or UUID).
- **Backward compatibility**: Existing systems/containers/components remain valid; new analysis can add code elements over time.

---

## Phase 1: Data model and persistence

### 1.1 SCRIBE — Models

**File:** `scribe/scribe/models.py`

Add:

```python
class CodeElement(BaseModel):
    id: str
    name: str
    component_id: str
    type: Literal["class", "interface", "enum", "function", "module", "struct"] = "class"
    file_path: str = ""
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: str = ""


class CodeRelationship(BaseModel):
    from_id: str  # CodeElement id
    to_id: str   # CodeElement id
    type: Literal["implements", "extends", "calls", "uses", "references"] = "uses"
    description: str = ""
```

Extend `ArchitectureModel`:

- `code_elements: list[CodeElement] = []`
- `code_relationships: list[CodeRelationship] = []`

Include both in `to_vault_dict()`.

**Design notes:**

- `component_id` ties each code element to a component; SCRIBE/LLM must only emit code elements for components that exist in the same model.
- Keep relationship types narrow so the graph and UI stay simple.

### 1.2 SCRIBE — Prompt

**File:** `scribe/scribe/prompts.py`

- Add to the “Extract the following” list:
  - `code_elements`: array of `{ id, name, component_id, type, file_path, line_start?, line_end?, description }` (can be empty).
  - `code_relationships`: array of `{ from_id, to_id, type (implements|extends|calls|uses|references), description }` (can be empty).
- Clarify: `component_id` must match an existing component id; `from_id`/`to_id` in code_relationships must match code_elements ids.
- Emphasize “optional: many codebases omit code level”; empty arrays are valid.

### 1.3 SCRIBE — Extraction strategy (choose one for v1)

**Option A — LLM-only (recommended for v1)**  
- Rely on the existing LLM flow: prompt asks for code_elements and code_relationships per component.
- Pros: No new dependencies; consistent with current C4 extraction.  
- Cons: Quality and consistency depend on the model; may be coarse (e.g. one class per component).

**Option B — AST + mapping**  
- Use a language-specific parser (e.g. tree-sitter, or language-specific libs) to extract classes/functions and their locations; optionally map them to components (e.g. by file_path / module).  
- Pros: Accurate symbols and line ranges.  
- Cons: Multi-language support and mapping to C4 components add complexity; do as a later phase.

**Recommendation:** Implement Option A first; add Option B later if needed (e.g. “enhance with AST” flag).

### 1.4 SCRIBE — Mock fixture

**File:** `scribe/scribe/analyzer.py`

- In the default mock `ArchitectureModel`, add a few `CodeElement` and `CodeRelationship` instances for one of the existing components (e.g. “API Controller”) so READER can be tested without a real LLM.

---

### 1.5 VAULT — Schema

**File:** `vault/scripts/init_schema.cypher`

- Add constraint:  
  `CREATE CONSTRAINT code_element_id IF NOT EXISTS FOR (e:CodeElement) REQUIRE e.id IS UNIQUE;`

**File:** `vault/scripts/indexes.cypher` (optional)

- If you want search over code elements: add `CodeElement` to the fulltext index (e.g. on `id`, `name`, `file_path`).

---

### 1.6 VAULT — Persistence in `store_architecture()`

**File:** `vault/repository.py`

- Read `code_elements` and `code_relationships` from the model.
- **After** components are stored:
  - For each `code_elements` item with a valid `component_id`:
    - Resolve the component within the current system (e.g. `MATCH (s:System {id: $system_id})-[:CONTAINS]->(c:Container)-[:CONTAINS]->(co:Component {id: $component_id})`).
    - `MERGE (e:CodeElement {id: $id})` with properties: name, type, file_path, line_start, line_end, description, updated_at, manual_override.
    - `MERGE (co)-[:CONTAINS]->(e)`.
  - For each `code_relationships` item:
    - `MATCH (a:CodeElement {id: $from_id}), (b:CodeElement {id: $to_id}) MERGE (a)-[r:DEPENDS_ON]->(b)` (or a dedicated relationship type, e.g. `CODE_RELATES_TO` with a `type` property: implements, extends, calls, uses). Using `DEPENDS_ON` with a `type` property keeps the graph schema simpler.
- Respect `manual_override` on CodeElement if you add it (same pattern as Container/Component).
- **No** version snapshot change required for Level 4: version snapshots stay at system level (system + containers + relationships); component/code detail is always read live from the graph.

---

### 1.7 VAULT — Read: `get_component_detail()`

**File:** `vault/repository.py`

Add:

```text
async def get_component_detail(
    self, system_id: str, container_id: str, component_id: str
) -> dict[str, Any] | None
```

- Match path: `(System {id: system_id})-[:CONTAINS]->(Container {id: container_id})-[:CONTAINS]->(Component {id: component_id})`.
- Return:
  - Component properties (id, name, description, responsibility, file_path, language).
  - `code_elements`: list of CodeElement nodes for this component (from `(Component)-[:CONTAINS]->(CodeElement)`).
  - `code_relationships`: list of relationships between those code elements, e.g.  
    `(e1:CodeElement)-[r:DEPENDS_ON]->(e2:CodeElement)` where both e1 and e2 are in the component’s code_elements.  
    Return shape: `[{ from: e1.id, to: e2.id, type: r.type }]`.
- If the component does not exist or is not under the given system/container, return `None`.

---

## Phase 2: API

### 2.1 New endpoint

**File:** `api/api/routers/systems.py` (or a dedicated `components.py` router if you prefer)

- **GET** `/api/v1/systems/{system_id}/containers/{container_id}/components/{component_id}`
- Handler: call `vault.get_component_detail(system_id, container_id, component_id)`.
- Return 200 with the dict; 404 if `get_component_detail` returns `None`.
- Document response shape (component + code_elements + code_relationships) in OpenAPI (e.g. via a Pydantic response_model or description).

---

## Phase 3: READER (frontend)

### 3.1 Types

**File:** `reader/src/app/models/architecture.ts`

- `CodeElementNode`: id, name, component_id?, type, file_path?, line_start?, line_end?, description?.
- `CodeRelationshipRef`: from, to, type?.
- `ComponentDetail`: extend or mirror the API response: component fields + `code_elements: CodeElementNode[]` + `code_relationships?: CodeRelationshipRef[]`.
- `C4Level`: extend to `'enterprise' | 'system' | 'container' | 'code'`.  
  (You can keep “component” as the drill-down that leads to the code view, i.e. “container” shows components; clicking a component loads component detail and switches to “code” level for the graph.)

### 3.2 API service

**File:** `reader/src/app/core/services/architecture-api.service.ts`

- Add `getComponentDetail(systemId: string, containerId: string, componentId: string): Observable<ComponentDetail>` calling the new GET endpoint.

### 3.3 State

**File:** `reader/src/app/core/services/architecture-state.service.ts`

- Add signals: `componentDetail`, `currentComponentId`.
- Add `loadComponentDetail(systemId, containerId, componentId)` that calls the API and sets component detail and current component id.
- Extend `level` computed: if `componentDetail()` is set, return `'code'`; otherwise keep existing logic (container → 'container', system → 'system', else 'enterprise').
- Extend `graphData` computed: when level is `'code'` and `componentDetail()` is set, return nodes = [component, ...code_elements], edges = code_relationships (and optionally no container→container edges, so the code view is focused).

### 3.4 Graph mapper

**File:** `reader/src/app/core/services/graph-mapper.service.ts`

- Add `componentDetailToElements(detail: ComponentDetail): { nodes, edges }`:
  - One node for the component (level `'component'`).
  - One node per code element (e.g. level `'code'`, optional `type` for styling).
  - Edges from `code_relationships` (and optionally component → “summary” or no extra edges).
- Use this in the architecture view when `level === 'code'`.

### 3.5 Graph style

**File:** `reader/src/app/core/services/graph-style.service.ts`

- Add `node[level="code"]` style (e.g. smaller, distinct color) and optionally styles by `data(type)` (class, interface, function) for variety.

### 3.6 Navigation

**File:** `reader/src/app/pages/architecture-view/architecture-view.component.ts` (and template)

- When the user selects a **component** node (e.g. in the container view), instead of doing nothing or only showing a sidebar:
  - Call `state.loadComponentDetail(systemId, containerId, componentId)`.
  - The graph recomputes and shows the code-level diagram (component + code elements + code_relationships).
- Breadcrumb: add a segment for the selected component and “Code” (e.g. System > Container > Component Name > Code).
- “Back” or breadcrumb click: clear component detail (and optionally go back to container view) so level returns to `'container'`.

### 3.7 Component list / sidebar

- In the container view, ensure component nodes are clickable and trigger the above flow.
- Optionally show a “View code” link in the system-detail/panel when a component is selected, which does the same load.

---

## Phase 4: Versioning and search (optional)

- **Versioning:** Component/code detail is read live from the graph; it is not stored in ArchitectureVersion snapshots. If you need historical code view, either snapshot component detail in the version JSON or add a separate “code version” concept later.
- **Search:** If code elements are in the fulltext index, extend the search API/UI to return and link to CodeElement hits (e.g. open the component and code view with that element highlighted).

---

## Implementation order (checklist)

| # | Task | Owner / notes |
|---|------|----------------|
| 1 | SCRIBE: Add `CodeElement`, `CodeRelationship`, extend `ArchitectureModel` and `to_vault_dict` | |
| 2 | SCRIBE: Extend prompt for code_elements and code_relationships | |
| 3 | SCRIBE: Add mock code elements/relationships for one component | |
| 4 | VAULT: Schema constraint (and optional index) for CodeElement | |
| 5 | VAULT: Persist code_elements and code_relationships in `store_architecture()` | |
| 6 | VAULT: Implement `get_component_detail()` | |
| 7 | API: Add GET `.../components/{component_id}` and wire to VAULT | |
| 8 | READER: Types (CodeElementNode, CodeRelationshipRef, ComponentDetail); extend C4Level | |
| 9 | READER: API service `getComponentDetail()` | |
| 10 | READER: State (componentDetail, currentComponentId, loadComponentDetail, level/graphData for 'code') | |
| 11 | READER: Graph mapper `componentDetailToElements()` and style for `code` (and optional type) | |
| 12 | READER: Architecture view — on component node select, load component detail and show code graph | |
| 13 | READER: Breadcrumb and back navigation for code level | |
| 14 | Docs/tests: Update C4 reference page; add a short test or manual test script for Level 4 | |

---

## Testing suggestions

- **SCRIBE:** Unit test that a model with code_elements/code_relationships validates and `to_vault_dict()` includes them.
- **VAULT:** Integration test: store a model with one component and two code elements and one code_relationship; call `get_component_detail` and assert code_elements and code_relationships.
- **API:** GET the new endpoint and assert 200/404 and response shape.
- **READER:** With mock data, drill to a container, click a component, assert code-level graph and breadcrumb.

---

## Risks and mitigations

- **LLM quality:** Code-level output may be noisy or empty. Mitigation: keep code level optional; allow empty arrays; consider AST-based enhancement later.
- **Id collisions:** Code element ids must be unique. Mitigation: use a deterministic scheme (e.g. component_id + file_path + name + line) or UUIDs from SCRIBE.
- **Scale:** Large components could have hundreds of code elements. Mitigation: limit or paginate code_elements in the API/UI if needed; or cap per component in SCRIBE (e.g. top N by importance).

---

## Summary

Level 4 adds **code elements** and **code relationships** to the C4 model, persisted under components in VAULT, exposed via a new **component detail** endpoint, and visualized in READER as a **code diagram** when the user drills into a component. Implementing in the order above (data model → persistence → API → READER) keeps each step testable and avoids big-bang changes.
