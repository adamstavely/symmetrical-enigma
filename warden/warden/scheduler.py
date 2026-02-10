"""
WARDEN scheduler: run drift detection on a schedule (e.g. daily).
Uses APScheduler; schedule from env DRIFT_CHECK_SCHEDULE (cron: "0 2 * * *" = 02:00 daily).
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Allow importing vault when run from project root or container
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _run_drift_job() -> None:
    """Sync entrypoint for APScheduler: run detect_drift -> send alerts -> optional auto_update."""
    schedule = os.environ.get("DRIFT_CHECK_SCHEDULE", "0 2 * * *")  # 02:00 daily
    min_severity = os.environ.get("DRIFT_ALERT_MIN_SEVERITY", "high")
    auto_update_max = int(os.environ.get("DRIFT_AUTO_UPDATE_MAX", "3"))
    run_auto_update = os.environ.get("DRIFT_AUTO_UPDATE", "false").lower() in ("1", "true", "yes")

    async def _job() -> None:
        from vault.repository import ArchitectureRepository
        from warden.detector import DriftDetector
        from warden.notifiers import send_drift_alerts

        vault = ArchitectureRepository()
        try:
            detector = DriftDetector(vault)
            alerts = await detector.detect_drift()
            if not alerts:
                return
            send_drift_alerts(alerts, min_severity=min_severity)
            if run_auto_update and auto_update_max > 0:
                await detector.auto_update_drifted_systems(alerts, max_updates=auto_update_max)
        finally:
            await vault.close()

    asyncio.run(_job())


def main() -> None:
    """Run scheduler loop or one-shot."""
    run_once = os.environ.get("WARDEN_RUN_ONCE", "false").lower() in ("1", "true", "yes")
    if run_once:
        _run_drift_job()
        return

    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    schedule_str = os.environ.get("DRIFT_CHECK_SCHEDULE", "0 2 * * *")
    # Parse simple cron "0 2 * * *" -> minute=0, hour=2, ...
    parts = schedule_str.split()
    if len(parts) >= 5:
        minute, hour, day, month, day_of_week = parts[0], parts[1], parts[2], parts[3], parts[4]
    else:
        minute, hour, day, month, day_of_week = "0", "2", "*", "*", "*"

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _run_drift_job,
        CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
        id="drift_check",
    )
    scheduler.start()


if __name__ == "__main__":
    main()
