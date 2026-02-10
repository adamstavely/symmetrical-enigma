"""
WARDEN - Drift detection: compare VAULT last_analyzed to Git last commit.
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from warden.git_client import get_last_commit_date


@dataclass
class DriftAlert:
    system_id: str
    system_name: str
    repository_url: Optional[str]
    last_analyzed: Optional[datetime]
    last_commit: Optional[datetime]
    drift_hours: float
    severity: str  # "low" | "medium" | "high" | "critical"


def _parse_last_analyzed(value: Any) -> Optional[datetime]:
    """Convert Neo4j datetime or ISO string to timezone-aware datetime."""
    if value is None:
        return None
    if hasattr(value, "iso_format"):
        return datetime.fromisoformat(value.iso_format().replace("Z", "+00:00"))
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def _severity(drift_hours: float) -> str:
    if drift_hours >= 168:  # 1 week
        return "critical"
    if drift_hours >= 72:  # 3 days
        return "high"
    if drift_hours >= 24:
        return "medium"
    return "low"


class DriftDetector:
    """Detect drift between VAULT last_analyzed and Git last commit per system."""

    def __init__(self, vault: Any, git_client: Any = None):
        """
        vault: object with async get_all_systems(limit=...) returning list of system dicts
               with id, name, repository_url, last_analyzed.
        git_client: optional override; default uses get_last_commit_date from env.
        """
        self._vault = vault
        self._git_client = git_client or get_last_commit_date

    async def detect_drift(self, limit: int = 500) -> List[DriftAlert]:
        """
        For each system in VAULT with a repository_url, compare last_analyzed
        to Git last commit; append to DriftAlert list (system_id, drift_hours, severity).
        """
        systems = await self._vault.get_all_systems(skip=0, limit=limit)
        alerts: List[DriftAlert] = []
        for s in systems:
            repo_url = (s.get("repository_url") or "").strip() or None
            last_analyzed = _parse_last_analyzed(s.get("last_analyzed"))
            if not repo_url:
                continue
            # Get last commit: try GitLab API first (no clone), else None if no token
            last_commit = self._git_client(repo_url, None)
            if last_commit is None:
                continue
            if last_analyzed is None:
                # Never analyzed -> treat as infinite drift
                drift_hours = 8760.0  # 1 year
            else:
                if last_commit.tzinfo is None:
                    last_commit = last_commit.replace(tzinfo=timezone.utc)
                delta = last_commit - last_analyzed
                drift_hours = max(0, delta.total_seconds() / 3600)
            alerts.append(
                DriftAlert(
                    system_id=s.get("id", ""),
                    system_name=s.get("name", ""),
                    repository_url=repo_url,
                    last_analyzed=last_analyzed,
                    last_commit=last_commit,
                    drift_hours=drift_hours,
                    severity=_severity(drift_hours),
                )
            )
        return sorted(alerts, key=lambda a: -a.drift_hours)

    async def auto_update_drifted_systems(
        self,
        alerts: List[DriftAlert],
        max_updates: int = 5,
        clone_dir: Optional[Path] = None,
    ) -> int:
        """
        Sort alerts by drift, trigger SCRIBE for top N, then store in VAULT.
        Returns number of systems updated.
        """
        try:
            from scribe.analyzer import RepositoryAnalyzer
        except ImportError:
            return 0
        clone_dir = clone_dir or Path(os.environ.get("WARDEN_CLONE_DIR", "/tmp/warden-repos"))
        clone_dir.mkdir(parents=True, exist_ok=True)
        updated = 0
        for alert in alerts[:max_updates]:
            if not alert.repository_url:
                continue
            try:
                repo_path = _clone_repo(alert.repository_url, clone_dir, alert.system_id)
                if not repo_path:
                    continue
                analyzer = RepositoryAnalyzer()
                model = await analyzer.analyze_repository(repo_path)
                await self._vault.store_architecture(model.to_vault_dict())
                updated += 1
            except Exception:
                continue
        return updated


def _clone_repo(url: str, base_dir: Path, system_id: str) -> Optional[Path]:
    """Clone repo into base_dir/system_id; return path if success."""
    try:
        import git
    except ImportError:
        return None
    dest = base_dir / system_id.replace("/", "_").replace(" ", "_")
    if dest.exists():
        try:
            repo = git.Repo(dest)
            repo.remotes.origin.pull()
            return dest
        except Exception:
            pass
    try:
        git.Repo.clone_from(url, dest, depth=1)
        return dest
    except Exception:
        return None
