from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from appointment_agent_shared.db import Base, engine, SessionLocal
from appointment_agent_shared.models import AppointmentCacheRecord
from appointment_agent_shared.repositories import (
    AppointmentCacheRepository,
    build_appointment_source_hash,
)


Base.metadata.create_all(bind=engine)


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_build_appointment_source_hash_is_stable_for_same_payload() -> None:
    start_at = _utc(2026, 6, 1, 10)
    end_at = _utc(2026, 6, 1, 10, 30)

    hash_one = build_appointment_source_hash(
        external_appointment_id="appt-hash-1",
        start_at_utc=start_at,
        end_at_utc=end_at,
        timezone="Europe/Berlin",
        status="scheduled",
        contact_email="hash@example.test",
        contact_phone="+491700000001",
        contact_id="customer-1",
        source_system="google",
        source_reference="calendar-a",
        source_metadata={"sync_hash": "ignored", "b": 2, "a": 1},
    )
    hash_two = build_appointment_source_hash(
        external_appointment_id="appt-hash-1",
        start_at_utc=start_at,
        end_at_utc=end_at,
        timezone="Europe/Berlin",
        status="scheduled",
        contact_email="hash@example.test",
        contact_phone="+491700000001",
        contact_id="customer-1",
        source_system="google",
        source_reference="calendar-a",
        source_metadata={"a": 1, "b": 2, "sync_hash": "different"},
    )

    assert hash_one == hash_two


def test_upsert_synced_appointment_is_idempotent_and_can_cancel() -> None:
    session = SessionLocal()
    try:
        repo = AppointmentCacheRepository(session)
        tenant_id = f"tenant-{uuid4().hex[:8]}"
        external_appointment_id = f"appt-{uuid4().hex[:8]}"
        calendar_source_ref = f"calendar-{uuid4().hex[:8]}"
        start_at = _utc(2026, 6, 2, 9)
        end_at = _utc(2026, 6, 2, 9, 30)

        source_hash = build_appointment_source_hash(
            external_appointment_id=external_appointment_id,
            start_at_utc=start_at,
            end_at_utc=end_at,
            timezone="Europe/Berlin",
            status="scheduled",
            contact_email="sync@example.test",
            contact_phone="+491700000002",
            contact_id="customer-2",
            source_system="google",
            source_reference=calendar_source_ref,
            source_metadata={"provider": "calendar-a", "slot": "morning"},
        )

        first_result = repo.upsert_synced_appointment(
            tenant_id=tenant_id,
            external_appointment_id=external_appointment_id,
            calendar_source_type="google",
            calendar_source_ref=calendar_source_ref,
            title="Reminder Sync",
            start_at_utc=start_at,
            end_at_utc=end_at,
            timezone="Europe/Berlin",
            status="scheduled",
            participant_ref="customer-2",
            contact_ref="customer-2",
            email="sync@example.test",
            phone="+491700000002",
            reminder_policy_id=None,
            raw_payload_json={"provider": "calendar-a", "slot": "morning"},
            source_hash=source_hash,
        )

        second_result = repo.upsert_synced_appointment(
            tenant_id=tenant_id,
            external_appointment_id=external_appointment_id,
            calendar_source_type="google",
            calendar_source_ref=calendar_source_ref,
            title="Reminder Sync",
            start_at_utc=start_at,
            end_at_utc=end_at,
            timezone="Europe/Berlin",
            status="scheduled",
            participant_ref="customer-2",
            contact_ref="customer-2",
            email="sync@example.test",
            phone="+491700000002",
            reminder_policy_id=None,
            raw_payload_json={"provider": "calendar-a", "slot": "morning"},
            source_hash=source_hash,
        )

        cancelled_result = repo.reconcile_synced_appointment(
            tenant_id=tenant_id,
            external_appointment_id=external_appointment_id,
            calendar_source_type="google",
            calendar_source_ref=calendar_source_ref,
            title="Reminder Sync",
            start_at_utc=start_at,
            end_at_utc=end_at,
            timezone="Europe/Berlin",
            status="cancelled",
            participant_ref="customer-2",
            contact_ref="customer-2",
            email="sync@example.test",
            phone="+491700000002",
            reminder_policy_id=None,
            raw_payload_json={"provider": "calendar-a", "slot": "morning"},
            source_hash=source_hash,
        )

        assert first_result.created is True
        assert first_result.action == "created"
        assert second_result.action == "unchanged"
        assert second_result.updated is False
        assert cancelled_result.cancelled is True
        assert cancelled_result.action == "cancelled"

        records = repo.list_for_source(
            tenant_id=tenant_id,
            calendar_source_type="google",
            calendar_source_ref=calendar_source_ref,
        )
        assert len(records) == 1
        assert isinstance(records[0], AppointmentCacheRecord)
        assert records[0].status == "cancelled"
        assert records[0].matches_source_hash(source_hash)
        assert records[0].source_identity() == (
            tenant_id,
            external_appointment_id,
            "google",
            calendar_source_ref,
        )
    finally:
        session.close()
