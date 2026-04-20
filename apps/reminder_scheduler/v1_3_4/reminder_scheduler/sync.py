from __future__ import annotations

from dataclasses import dataclass

from .adapter import NormalizedAppointmentSnapshot


@dataclass
class AppointmentSyncDecision:
    action: str
    hash_changed: bool
    status_changed: bool


def classify_appointment_sync(
    *,
    existing_hash: str | None,
    existing_status: str | None,
    snapshot: NormalizedAppointmentSnapshot,
) -> AppointmentSyncDecision:
    if existing_hash is None:
        return AppointmentSyncDecision(action="created", hash_changed=True, status_changed=True)
    hash_changed = existing_hash != snapshot.payload_hash
    status_changed = (existing_status or "scheduled") != snapshot.status
    if status_changed and snapshot.status == "cancelled":
        return AppointmentSyncDecision(action="cancelled", hash_changed=hash_changed, status_changed=status_changed)
    if hash_changed or status_changed:
        return AppointmentSyncDecision(action="updated", hash_changed=hash_changed, status_changed=status_changed)
    return AppointmentSyncDecision(action="unchanged", hash_changed=False, status_changed=False)
