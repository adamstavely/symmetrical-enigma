# C4 Model — All 4 Layers: Current Status & Gaps

You **cannot** currently generate all four C4 layers end-to-end. Below is what exists and what needs to be added.

---

## C4 levels (recap)

| Level | Name       | What it shows |
|-------|------------|----------------|
| 1     | **Context**   | System and its users / external systems |
| 2     | **Container** | Applications and data stores inside the system |
| 3     | **Component** | Building blocks inside a container |
| 4     | **Code**      | Classes, interfaces, and other code elements inside a component |

---

## Current implementation

### Level 1 – Context ✅

- **Enterprise view**: all systems and edges (top-level).
- **System view**: one system = context for that system (systems + containers in READER).
- **API**: `GET /api/v1/enterprise`, `GET /api/v1/systems/{id}`.
- **READER**: Drill enterprise → system. Graph shows systems (and external systems) or system + containers.

### Level 2 – Container ✅

- **System detail** includes containers and container–container relationships.
- **API**: `GET /api/v1/systems/{id}`, `GET /api/v1/systems/{id}/containers/{cid}`.
- **READER**: System graph shows containers; drill into a container loads container detail (components list + container dependencies).
- **VAULT**: System → CONTAINS → Container; Container → DEPENDS_ON → Container.

### Level 3 – Component ✅ (fully working)

- **Data model**: `Component` has `container_id`; SCRIBE, VAULT, API, and READER support components and component–component relationships.
- **VAULT**: `store_architecture()` creates `Component` nodes and `(Container)-[:CONTAINS]->(Component)`; relationships can be container–container or component–component (same `DEPENDS_ON`). `get_container_detail()` returns `components` and `component_relationships`.
- **UI**: Container view shows container + components as nodes and both container→container and component→component edges; component nodes use a distinct style.

### Level 4 – Code ❌

- **Not implemented.** No code-level elements (classes, interfaces, functions, etc.) in:
  - SCRIBE (no extraction or LLM output for code elements),
  - VAULT (no `CodeElement`-style nodes),
  - API (no component detail with code elements),
  - READER (no code-level view).
- The reference page states that EDDA focuses on context, container, and component; code is left to IDEs/tools.

---

## What to add for all 4 layers

### Level 3 – Component (make it fully work)

1. **SCRIBE**
   - Add **`container_id`** (or `containerId`) to the `Component` model and to the analysis prompt so each component is tied to a container.
   - Optionally: extend **relationships** (or add a separate list) so the LLM can output **component–component** relationships (e.g. “service A calls service B” within the same container). Today relationships are only container–container (and system–external).

2. **VAULT**
   - In **`store_architecture()`**, after storing containers:
     - For each component (with `container_id`), **MERGE** a `Component` node and **MERGE** `(Container {id: component.container_id})-[:CONTAINS]->(Component)`.
   - Optionally: persist **component–component** relationships (e.g. same `DEPENDS_ON` between two `Component` nodes, or a dedicated relationship type). Then:
     - In **`get_container_detail()`** (or a new **`get_component_detail()`**), also return **component_relationships** (e.g. `(co1:Component)-[:DEPENDS_ON]->(co2:Component)` where both belong to the container).

3. **API**
   - No strict change required for “container with components” if VAULT starts persisting components; existing `GET .../containers/{cid}` already returns `components[]`.
   - If you add a dedicated component view: add **`GET /api/v1/systems/{id}/containers/{cid}/components/{coid}`** returning one component and its code elements (for Level 4).

4. **READER**
   - Optional: add a **component-level** graph view (e.g. when “zoomed” to a container, show only components + component–component edges).
   - Optional: add **`node[level="component"]`** in `graph-style.service.ts` for distinct styling.

### Level 4 – Code (new feature)

1. **SCRIBE**
   - Introduce **code elements** (e.g. classes, interfaces, functions, modules) and **code relationships** (implements, extends, calls, uses).
   - New models (conceptually): e.g. `CodeElement` (id, name, type, file_path, line_start, line_end, **component_id**), `CodeRelationship` (from_id, to_id, type).
   - Either:
     - Ask the LLM to infer high-level code structure per component, or
     - Use static analysis (AST) to extract elements and relationships and map them to components.

2. **VAULT**
   - New node label, e.g. **`CodeElement`**, with properties (id, name, type, file_path, etc.).
   - **`(Component)-[:CONTAINS]->(CodeElement)`**.
   - Optional: **`(CodeElement)-[:DEPENDS_ON|CALLS|IMPLEMENTS|EXTENDS]->(CodeElement)`** for code-level edges.
   - New (or extended) read method: e.g. **`get_component_detail(system_id, container_id, component_id)`** returning component + **code_elements** + **code_relationships**.

3. **API**
   - New endpoint, e.g. **`GET /api/v1/systems/{id}/containers/{cid}/components/{coid}`**, returning component plus code elements and relationships.

4. **READER**
   - New **C4 level**: e.g. `'component'` (single component) and **`'code'`** (component + code elements).
   - State: e.g. **`componentDetail`**, **`currentComponentId`**.
   - Navigation: e.g. click component → load component detail → show **code diagram** (component + code elements + code edges).
   - **`C4Level`** type: extend to `'enterprise' | 'system' | 'container' | 'component' | 'code'` (or keep component as “inside container” and add only `'code'`).

---

## Minimal path to “all 4 layers”

- **Level 3**: Add **`container_id`** to Component in SCRIBE + prompt; add the **persistence loop** in VAULT for Component nodes and Container→Component CONTAINS. Then the existing READER container view will show components as soon as SCRIBE produces them.
- **Level 3 (optional)**: Add component–component relationships (SCRIBE + VAULT + API/READER) for a full component diagram.
- **Level 4**: Implement code elements and code diagram as above (SCRIBE → VAULT → API → READER).

If you want, the next step can be a concrete patch for Level 3 only (SCRIBE `container_id` + VAULT component persistence) so that the current UI can at least display persisted components.
