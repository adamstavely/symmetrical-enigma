"""
Build the LLM prompt from extracted context. Single place for prompt template (DRY).
"""
import json

from scribe.models import ArchitectureModel


def build_analysis_prompt(
    dependencies: dict,
    configs: dict,
    apis: dict,
    repo_name: str = "repository",
) -> str:
    """Build the analysis prompt. Returns a string to send to the LLM."""
    schema = ArchitectureModel.model_json_schema()
    return f"""You are analyzing a codebase to extract C4 architecture.

Repository name: {repo_name}

Dependencies found:
{json.dumps(dependencies, indent=2)}

Infrastructure configs:
{json.dumps(configs, indent=2)}

API definitions:
{json.dumps(apis, indent=2)}

Extract the following and output as valid JSON only:
1. system: object with keys id, name, description, team, group, repository_url (id and name required; use "{repo_name}" for id/name if unknown).
2. containers: array of objects with id, name, description, technology, type (service|database|queue|cache|storage|cdn), port (optional), repository_path (optional).
3. components: array of objects with id, name, description, responsibility, file_path, language (can be empty array).
4. relationships: array of objects with from_id, to_id, type (calls_api|reads_from|writes_to|publishes_to|subscribes_to|authenticates_with), protocol (optional), description.
5. external_dependencies: array of objects with id, name, vendor, type (saas|cloud|partner_api|legacy_system).

CRITICAL: Output ONLY valid JSON. No markdown, no explanation, no code block. The JSON must match this shape:
- "system": {{ "id": "...", "name": "...", "description": "...", "team": "...", "group": "..." }}
- "containers": [ {{ "id": "...", "name": "...", "technology": "...", "type": "service"|"database"|... }} ]
- "components": [ ... ] or []
- "relationships": [ {{ "from_id": "...", "to_id": "...", "type": "calls_api"|... }} ]
- "external_dependencies": [ ... ] or []
"""
