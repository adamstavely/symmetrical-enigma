"""Unit tests for WARDEN drift detector."""
from datetime import datetime, timezone

import pytest

from warden.detector import DriftAlert, DriftDetector, _parse_last_analyzed, _severity


def test_parse_last_analyzed_none():
    assert _parse_last_analyzed(None) is None


def test_parse_last_analyzed_iso_string():
    s = "2024-01-15T10:00:00+00:00"
    got = _parse_last_analyzed(s)
    assert got is not None
    assert got.year == 2024 and got.month == 1 and got.day == 15


def test_parse_last_analyzed_datetime():
    dt = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _parse_last_analyzed(dt) == dt


def test_severity():
    assert _severity(0) == "low"
    assert _severity(12) == "low"
    assert _severity(24) == "medium"
    assert _severity(72) == "high"
    assert _severity(168) == "critical"
    assert _severity(200) == "critical"


@pytest.mark.asyncio
async def test_detect_drift_empty_vault():
    class EmptyVault:
        async def get_all_systems(self, skip=0, limit=50):
            return []

    detector = DriftDetector(EmptyVault())
    alerts = await detector.detect_drift()
    assert alerts == []


@pytest.mark.asyncio
async def test_detect_drift_no_repo_url():
    class VaultNoUrl:
        async def get_all_systems(self, skip=0, limit=50):
            return [{"id": "sys1", "name": "Sys", "repository_url": None, "last_analyzed": None}]

    detector = DriftDetector(VaultNoUrl())
    alerts = await detector.detect_drift()
    assert len(alerts) == 0
