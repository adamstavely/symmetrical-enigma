"""
Send drift alerts (e.g. Slack webhook). Group by team if desired; single webhook for now.
"""
from __future__ import annotations

import os
from typing import List

from warden.detector import DriftAlert


def send_drift_alerts(alerts: List[DriftAlert], min_severity: str = "medium") -> None:
    """
    Send drift alerts to configured notifiers (e.g. Slack webhook from env).
    Only sends alerts with severity >= min_severity (low < medium < high < critical).
    """
    severity_order = ("low", "medium", "high", "critical")
    try:
        min_idx = severity_order.index(min_severity)
    except ValueError:
        min_idx = 1  # medium
    to_send = [a for a in alerts if severity_order.index(a.severity) >= min_idx]
    if not to_send:
        return
    slack_url = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_url:
        _send_slack(slack_url, to_send)


def _send_slack(webhook_url: str, alerts: List[DriftAlert]) -> None:
    """POST a simple summary to Slack incoming webhook."""
    import httpx
    lines = []
    for a in alerts[:20]:  # cap at 20
        lines.append(
            f"• *{a.system_name}* (`{a.system_id}`): {a.drift_hours:.0f}h drift ({a.severity})"
        )
    if len(alerts) > 20:
        lines.append(f"_... and {len(alerts) - 20} more_")
    text = "EDDA WARDEN – Drift detected\n" + "\n".join(lines)
    try:
        with httpx.Client() as client:
            client.post(webhook_url, json={"text": text}, timeout=10.0)
    except Exception:
        pass  # best-effort
