"""
Thin wrapper to get last commit date for a repo: GitLab API or GitPython (clone + log).
Uses GIT_BASE_URL, GIT_TOKEN from env for GitLab; otherwise GitPython on local path.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path


def get_last_commit_date(repository_url: Optional[str], repo_path: Optional[Path] = None) -> Optional[datetime]:
    """
    Return the last commit datetime (UTC) for the repo.
    - If repo_path is a local directory: use GitPython to get last commit.
    - If repository_url is set and GIT_TOKEN is set: use GitLab API (project id or URL).
    - Otherwise returns None (no drift check possible).
    """
    if repo_path and repo_path.is_dir():
        return _last_commit_via_gitpython(repo_path)
    if repository_url and os.environ.get("GIT_TOKEN"):
        return _last_commit_via_gitlab_api(repository_url)
    return None


def _last_commit_via_gitpython(repo_path: Path) -> Optional[datetime]:
    """Use GitPython to get the last commit date on the default branch."""
    try:
        import git
    except ImportError:
        return None
    try:
        repo = git.Repo(repo_path)
        head = repo.head.commit
        # GitPython committer_date is datetime with timezone or naive
        committed = head.committed_datetime
        if committed.tzinfo is None:
            committed = committed.replace(tzinfo=timezone.utc)
        return committed.astimezone(timezone.utc)
    except Exception:
        return None


def _last_commit_via_gitlab_api(repository_url: str) -> Optional[datetime]:
    """Call GitLab API to get last activity / last commit for the project."""
    import httpx
    base = (os.environ.get("GIT_BASE_URL") or "https://gitlab.com").rstrip("/")
    token = os.environ.get("GIT_TOKEN")
    if not token:
        return None
    # Resolve project path from URL: https://base/group/project -> group%2Fproject
    try:
        # e.g. https://gitlab.com/org/my-repo or https://gitlab.com/org/my-repo.git
        if repository_url.startswith(base):
            path = repository_url.replace(base, "").strip("/").replace(".git", "")
        else:
            # URL might be from different host; try to extract path
            from urllib.parse import urlparse
            parsed = urlparse(repository_url)
            path = parsed.path.strip("/").replace(".git", "")
        encoded = path.replace("/", "%2F")
    except Exception:
        return None
    url = f"{base}/api/v4/projects/{encoded}/repository/commits?per_page=1"
    try:
        with httpx.Client() as client:
            r = client.get(url, headers={"PRIVATE-TOKEN": token}, timeout=15.0)
            r.raise_for_status()
            data = r.json()
            if not data:
                return None
            committed = data[0].get("committed_date")  # ISO 8601
            if not committed:
                return None
            return datetime.fromisoformat(committed.replace("Z", "+00:00"))
    except Exception:
        return None
