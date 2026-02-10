"""GET /drift — drift alerts from WARDEN detector (VAULT last_analyzed vs Git last commit)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter()

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Optional: ensure warden is importable when run from api dir
_warden_root = _REPO_ROOT / "warden"
if str(_warden_root) not in sys.path:
    sys.path.insert(0, str(_warden_root))


def _serialize_alert(alert) -> dict:
    """Convert DriftAlert to JSON-serializable dict."""
    return {
        "system_id": alert.system_id,
        "system_name": alert.system_name,
        "repository_url": alert.repository_url,
        "last_analyzed": alert.last_analyzed.isoformat() if alert.last_analyzed else None,
        "last_commit": alert.last_commit.isoformat() if alert.last_commit else None,
        "drift_hours": round(alert.drift_hours, 2),
        "severity": alert.severity,
    }


@router.get("/drift")
async def get_drift(
    min_severity: str | None = Query(None, description="Filter: low | medium | high | critical"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Return drift alerts: systems where Git has commits newer than VAULT last_analyzed.
    Uses WARDEN DriftDetector; requires GIT_TOKEN (or local repo) for Git last commit.
    """
    try:
        from vault.repository import ArchitectureRepository
        from warden.detector import DriftDetector
    except ImportError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"VAULT/WARDEN not available: {e}")

    vault = ArchitectureRepository()
    try:
        detector = DriftDetector(vault)
        alerts = await detector.detect_drift(limit=limit)
    finally:
        await vault.close()

    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    if min_severity:
        min_level = severity_order.get(min_severity.lower(), 0)
        alerts = [a for a in alerts if severity_order.get(a.severity, 0) >= min_level]

    return {"alerts": [_serialize_alert(a) for a in alerts]}
