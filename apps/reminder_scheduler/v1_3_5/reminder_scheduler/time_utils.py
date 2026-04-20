from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc


def utcnow() -> datetime:
    """Return the current time in canonical UTC.

    The scheduler stores and compares all reminder timestamps in UTC so that
    preview, persistence, dispatch, and worker cycles all speak the same time
    language. Keeping this helper in one place avoids accidental drift across
    modules.
    """

    return datetime.now(UTC)


def coerce_timezone(timezone_name: str) -> ZoneInfo:
    """Return a concrete IANA timezone or raise a friendly validation error."""

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Unknown timezone: {timezone_name}") from exc


def _roundtrip_wall_time(value: datetime, zone: ZoneInfo, fold: int) -> tuple[datetime, object]:
    candidate = value.replace(tzinfo=zone, fold=fold)
    roundtrip = candidate.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    return roundtrip, candidate.utcoffset()


def classify_naive_local_time(value: datetime, zone: ZoneInfo) -> tuple[bool, bool]:
    """Detect whether a naive local time is ambiguous or does not exist.

    Ambiguous wall-clock times occur when clocks move backward and the same
    local time appears twice. Non-existent wall-clock times occur when clocks
    jump forward and a local time is skipped entirely. Both cases are risky for
    reminder planning because they can silently point at different real-world
    instants than the operator intended.
    """

    roundtrip_0, offset_0 = _roundtrip_wall_time(value, zone, fold=0)
    roundtrip_1, offset_1 = _roundtrip_wall_time(value, zone, fold=1)
    ambiguous = roundtrip_0 == value and roundtrip_1 == value and offset_0 != offset_1
    nonexistent = roundtrip_0 != value and roundtrip_1 != value and offset_0 != offset_1
    return ambiguous, nonexistent


def canonicalize_datetime(
    value: datetime,
    *,
    timezone_name: str | None = None,
    field_name: str = "datetime",
) -> datetime:
    """Convert any supported datetime input into canonical UTC.

    Aware timestamps are simply normalized to UTC. Naive timestamps are only
    accepted when an explicit IANA timezone is available and the local wall
    time is not ambiguous or invalid in that zone.
    """

    if value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone(UTC)

    if not timezone_name:
        raise ValueError(f"{field_name} must be timezone-aware or provide an explicit timezone.")

    zone = coerce_timezone(timezone_name)
    ambiguous, nonexistent = classify_naive_local_time(value, zone)
    if ambiguous:
        raise ValueError(f"{field_name} is ambiguous in timezone {timezone_name}; please provide an aware datetime.")
    if nonexistent:
        raise ValueError(f"{field_name} does not exist in timezone {timezone_name}; please choose a valid local time.")

    localized = value.replace(tzinfo=zone, fold=0)
    return localized.astimezone(UTC)
