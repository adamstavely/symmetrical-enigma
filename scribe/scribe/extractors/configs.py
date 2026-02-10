"""
Extract infrastructure config from docker-compose, k8s YAML, terraform.
"""
import re
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _safe_yaml_load(path: Path) -> dict[str, Any] | list[Any] | None:
    if not HAS_YAML:
        return None
    try:
        return yaml.safe_load(_read_text(path)) or {}
    except Exception:
        return None


def extract_configs(repo_path: Path) -> dict[str, Any]:
    """Extract docker-compose and k8s configs. Keys are file paths, values are parsed structures."""
    configs: dict[str, Any] = {}

    for compose in repo_path.rglob("docker-compose*.yml"):
        data = _safe_yaml_load(compose)
        if data:
            configs[str(compose.relative_to(repo_path))] = data
    for compose in repo_path.rglob("docker-compose*.yaml"):
        data = _safe_yaml_load(compose)
        if data:
            configs[str(compose.relative_to(repo_path))] = data

    k8s_dir = repo_path / "k8s"
    if k8s_dir.exists():
        for yaml_file in k8s_dir.rglob("*.yaml"):
            data = _safe_yaml_load(yaml_file)
            if data:
                configs[str(yaml_file.relative_to(repo_path))] = data
        for yaml_file in k8s_dir.rglob("*.yml"):
            data = _safe_yaml_load(yaml_file)
            if data:
                configs[str(yaml_file.relative_to(repo_path))] = data

    # Optional: terraform *.tf - just list files for context
    tf_dir = repo_path / "terraform"
    if tf_dir.exists():
        tf_files = list(tf_dir.rglob("*.tf"))[:10]
        configs["_terraform_files"] = [str(p.relative_to(repo_path)) for p in tf_files]

    return configs
