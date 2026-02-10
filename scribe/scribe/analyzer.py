"""
SCRIBE - Main analysis pipeline: extract context, call LLM (or mock), parse and return ArchitectureModel.
"""
import json
import os
from pathlib import Path
from typing import Any

from scribe.models import ArchitectureModel, Container, Relationship, ExternalDependency
from scribe.extractors import extract_dependencies, extract_configs, extract_api_definitions
from scribe.prompts import build_analysis_prompt


def _load_mock_model(repo_path: Path, mock_path: str | None) -> ArchitectureModel:
    """Load or generate a mock ArchitectureModel for development without Ollama."""
    if mock_path and Path(mock_path).exists():
        data = json.loads(Path(mock_path).read_text())
        return ArchitectureModel.model_validate(data)
    # Default fixture: one system, two containers, one relationship
    name = repo_path.name or "sample-system"
    return ArchitectureModel(
        system={
            "id": name.replace(" ", "-").lower(),
            "name": name,
            "description": "Mock system from SCRIBE (USE_MOCK_LLM=true)",
            "team": "EDDA",
            "group": "ODIN",
            "repository_url": str(repo_path),
        },
        containers=[
            Container(id=f"{name}-api", name=f"{name} API", description="REST API", technology="Spring Boot", type="service", port=8080),
            Container(id=f"{name}-db", name=f"{name} DB", description="Database", technology="PostgreSQL", type="database"),
        ],
        components=[],
        relationships=[
            Relationship(from_id=f"{name}-api", to_id=f"{name}-db", type="writes_to", description="Persists data"),
        ],
        external_dependencies=[],
    )


async def _query_ollama(prompt: str, ollama_url: str, model: str) -> str:
    """Call Ollama generate API. Returns the response text."""
    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=300.0,
        )
        r.raise_for_status()
        return r.json().get("response", "")


def _parse_llm_response(response: str) -> ArchitectureModel:
    """Parse LLM JSON response into ArchitectureModel. Strips markdown code block if present."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    data = json.loads(text)
    return ArchitectureModel.model_validate(data)


class RepositoryAnalyzer:
    """Analyze a repository and produce an ArchitectureModel."""

    def __init__(
        self,
        ollama_url: str | None = None,
        model: str | None = None,
        use_mock: bool | None = None,
        mock_model_path: str | None = None,
    ):
        self.ollama_url = (ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", "mixtral:8x7b-instruct-v0.1-q4_K_M")
        self.use_mock = use_mock if use_mock is not None else os.environ.get("USE_MOCK_LLM", "true").lower() in ("1", "true", "yes")
        self.mock_model_path = mock_model_path or os.environ.get("MOCK_MODEL_PATH")

    async def analyze_repository(self, repo_path: Path) -> ArchitectureModel:
        """Run the full pipeline: extract -> prompt -> LLM or mock -> parse."""
        repo_path = Path(repo_path).resolve()
        if not repo_path.is_dir():
            raise NotADirectoryError(str(repo_path))

        dependencies = extract_dependencies(repo_path)
        configs = extract_configs(repo_path)
        apis = extract_api_definitions(repo_path)
        repo_name = repo_path.name or "unknown"

        if self.use_mock:
            return _load_mock_model(repo_path, self.mock_model_path)

        prompt = build_analysis_prompt(dependencies, configs, apis, repo_name)
        response = await _query_ollama(prompt, self.ollama_url, self.model)
        return _parse_llm_response(response)
