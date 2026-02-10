"""
Extract API definitions (OpenAPI, proto) for context.
"""
import re
from pathlib import Path
from typing import Any


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def extract_api_definitions(repo_path: Path) -> dict[str, Any]:
    """Find OpenAPI and proto files; return paths and minimal content for prompt context."""
    apis: dict[str, Any] = {}

    for openapi in repo_path.rglob("openapi.yaml"):
        apis[str(openapi.relative_to(repo_path))] = {"type": "openapi", "snippet": _read_text(openapi)[:3000]}
    for openapi in repo_path.rglob("openapi.yml"):
        apis[str(openapi.relative_to(repo_path))] = {"type": "openapi", "snippet": _read_text(openapi)[:3000]}
    for swagger in repo_path.rglob("swagger.yaml"):
        apis[str(swagger.relative_to(repo_path))] = {"type": "openapi", "snippet": _read_text(swagger)[:3000]}

    for proto in repo_path.rglob("*.proto"):
        apis[str(proto.relative_to(repo_path))] = {"type": "proto", "snippet": _read_text(proto)[:2000]}

    return apis
