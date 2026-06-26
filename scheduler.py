"""
Dead Man's Switch — Scheduler
Deadline calculation, check-in logic, and countdown formatting.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Any

_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


def _parse(dt_str: str) -> datetime:
    try:
        return datetime.strptime(dt_str, _ISO_FORMAT)
    except ValueError as exc:
        raise ValueError(f"Deadline format invalide: {dt_str!r}") from exc


def _fmt(dt: datetime) -> str:
    return dt.strftime(_ISO_FORMAT)


def new_deadline(interval_days: int) -> str:
    """Return an ISO datetime string N days from now."""
    return _fmt(_now() + timedelta(days=interval_days))


def is_triggered(deadline_str: str | None) -> bool:
    """Return True if the deadline has passed (or was never set)."""
    if not deadline_str:
        return False
    return _now() >= _parse(deadline_str)


def time_remaining(deadline_str: str | None) -> timedelta:
    """Return the timedelta until the deadline. Returns zero if already passed."""
    if not deadline_str:
        return timedelta(0)
    delta = _parse(deadline_str) - _now()
    return delta if delta.total_seconds() > 0 else timedelta(0)


def format_countdown(deadline_str: str | None) -> str:
    """Return a human-readable countdown string like '5j 14h 32m'."""
    if not deadline_str:
        return "non configuré"
    remaining = time_remaining(deadline_str)
    if remaining.total_seconds() <= 0:
        return "DÉCLENCHÉ"
    total_seconds = int(remaining.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{days}j {hours}h {minutes}m"


def checkin(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record a check-in: return a new config dict with updated last_checkin and deadline.
    Does NOT mutate the input dict — does not save to disk.
    """
    import copy
    updated = copy.copy(cfg)
    updated["last_checkin"] = _fmt(_now())
    updated["deadline"] = new_deadline(updated.get("interval_days", 7))
    return updated
