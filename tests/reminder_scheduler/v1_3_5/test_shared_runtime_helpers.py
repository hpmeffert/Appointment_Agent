from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from appointment_agent_shared.db import Base
from appointment_agent_shared.models import AppointmentCacheRecord
from appointment_agent_shared.repositories import (
    AppointmentCacheRepository,
    MessageRepository,
    ReminderAuditRepository,
    ReminderJobRepository,
    ReminderPolicyRepository,
    SlotHoldRepository,
    build_reminder_dispatch_key,
    build_reminder_runtime_health_snapshot,
)


DB_PATH = Path(gettempdir()) / f"appointment_agent_reminder_v135_shared_{uuid4().hex}.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=ENGINE)


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_dispatch_key_is_stable_and_rejects_empty_inputs() -> None:
    key_one = build_reminder_dispatch_key(
        "appointment-123",
        2,
        "email",
        calendar_source="google",
    )
    key_two = build_reminder_dispatch_key(
        "appointment-123",
        2,
        "email",
        calendar_source="google",
    )

    assert key_one == "google:appointment-123:2:email"
    assert key_one == key_two

    with pytest.raises(ValueError):
        build_reminder_dispatch_key("", 1, "email")
    with pytest.raises(ValueError):
        build_reminder_dispatch_key("appointment-123", 0, "email")
    with pytest.raises(ValueError):
        build_reminder_dispatch_key("appointment-123", 1, "   ")


def test_cache_identity_helpers_remain_stable_for_sync_rows() -> None:
    record = AppointmentCacheRecord(
        tenant_id="tenant-sync",
        external_appointment_id="external-1",
        calendar_source_type="google",
        calendar_source_ref="calendar-a",
        title="Reminder Sync",
        description=None,
        location=None,
        start_at_utc=_utc(2026, 7, 1, 10),
        end_at_utc=_utc(2026, 7, 1, 10, 30),
        timezone="Europe/Berlin",
        status="scheduled",
        participant_ref="customer-1",
        contact_ref="customer-1",
        email="sync@example.test",
        phone="+491700000010",
        reminder_policy_id=None,
        raw_payload_json={"slot": "morning"},
        source_hash="hash-123",
    )

    assert record.source_identity() == (
        "tenant-sync",
        "external-1",
        "google",
        "calendar-a",
    )
    assert record.matches_source_hash("hash-123") is True
    assert record.matches_source_hash("hash-other") is False
    assert record.needs_sync_refresh(source_hash="hash-123", status="scheduled") is False
    assert record.needs_sync_refresh(source_hash="hash-123", status="cancelled") is True
    assert record.needs_sync_refresh(source_hash=None, status="scheduled") is True


def test_runtime_health_snapshot_summarizes_delivery_state() -> None:
    session = TestingSessionLocal()
    try:
        policy_repo = ReminderPolicyRepository(session)
        appointment_repo = AppointmentCacheRepository(session)
        job_repo = ReminderJobRepository(session)
        hold_repo = SlotHoldRepository(session)
        message_repo = MessageRepository(session)
        audit_repo = ReminderAuditRepository(session)

        tenant_id = f"tenant-{uuid4().hex[:8]}"
        policy_name = "default"
        policy = policy_repo.upsert(
            tenant_id=tenant_id,
            policy_name=policy_name,
            enabled=True,
            mode="manual",
            reminder_count=1,
            first_reminder_hours_before=2,
        )

        appointment_start = _utc(2026, 7, 2, 12)
        appointment_repo.upsert_synced_appointment(
            tenant_id=tenant_id,
            external_appointment_id="external-appointment-1",
            calendar_source_type="google",
            calendar_source_ref="calendar-a",
            title="Reminder Sync",
            start_at_utc=appointment_start,
            end_at_utc=appointment_start + timedelta(minutes=30),
            timezone="Europe/Berlin",
            status="scheduled",
            participant_ref="customer-1",
            contact_ref="customer-1",
            email="sync@example.test",
            phone="+491700000010",
            reminder_policy_id=policy.id,
            raw_payload_json={"slot": "morning"},
            source_hash="hash-123",
        )

        planned_job = job_repo.upsert(
            job_id="job-planned",
            tenant_id=tenant_id,
            policy_name=policy_name,
            appointment_id="external-appointment-1",
            external_appointment_id="external-appointment-1",
            reminder_policy_id=policy.id,
            reminder_sequence=1,
            scheduled_for_utc=appointment_start - timedelta(hours=2),
            appointment_start_at_utc=appointment_start,
            appointment_timezone="Europe/Berlin",
            channel="email",
            target_ref="sync@example.test",
            status="planned",
            failure_reason_code=None,
            failure_reason_text=None,
            skip_reason_code=None,
            attempt_count=0,
            max_attempts=3,
            dispatch_key="external-appointment-1:1:email",
            locked_until_utc=None,
            dispatched_at_utc=None,
            provider_message_id=None,
            payload_json={"simulate_failure": False},
        )
        job_repo.upsert(
            job_id="job-dispatching",
            tenant_id=tenant_id,
            policy_name=policy_name,
            appointment_id="external-appointment-2",
            external_appointment_id="external-appointment-2",
            reminder_policy_id=policy.id,
            reminder_sequence=1,
            scheduled_for_utc=appointment_start + timedelta(hours=1),
            appointment_start_at_utc=appointment_start + timedelta(hours=1),
            appointment_timezone="Europe/Berlin",
            channel="email",
            target_ref="sync@example.test",
            status="dispatching",
            failure_reason_code=None,
            failure_reason_text=None,
            skip_reason_code=None,
            attempt_count=1,
            max_attempts=3,
            dispatch_key="external-appointment-2:1:email",
            locked_until_utc=appointment_start - timedelta(minutes=1),
            dispatched_at_utc=None,
            provider_message_id=None,
            payload_json={"simulate_failure": False},
        )
        job_repo.upsert(
            job_id="job-failed",
            tenant_id=tenant_id,
            policy_name=policy_name,
            appointment_id="external-appointment-3",
            external_appointment_id="external-appointment-3",
            reminder_policy_id=policy.id,
            reminder_sequence=1,
            scheduled_for_utc=appointment_start - timedelta(hours=4),
            appointment_start_at_utc=appointment_start + timedelta(hours=2),
            appointment_timezone="Europe/Berlin",
            channel="email",
            target_ref="sync@example.test",
            status="failed",
            failure_reason_code="dispatch_error",
            failure_reason_text="simulated delivery failure",
            skip_reason_code=None,
            attempt_count=3,
            max_attempts=3,
            dispatch_key="external-appointment-3:1:email",
            locked_until_utc=None,
            dispatched_at_utc=None,
            provider_message_id=None,
            payload_json={"simulate_failure": True},
        )

        hold_repo.create(
            hold_id="hold-1",
            journey_id="journey-1",
            customer_id="customer-1",
            slot_id="slot-1",
            provider="google",
            slot_label="12:00-12:30",
            start_time_utc=appointment_start,
            end_time_utc=appointment_start + timedelta(minutes=30),
            expires_at_utc=appointment_start + timedelta(minutes=10),
            reason="demo hold",
            details={"source": "tests"},
        )

        message_repo.upsert(
            message_id="message-1",
            provider_message_id="provider-message-1",
            provider_job_id="provider-job-1",
            provider="lekab",
            channel="rcs",
            direction="outbound",
            status="sent",
            customer_id="customer-1",
            contact_reference="contact-1",
            phone_number="+491700000010",
            journey_id="journey-1",
            booking_reference="booking-1",
            message_type="text",
            body="Reminder sent",
            preview_text="Reminder sent",
            actions=[{"label": "Open", "value": "open"}],
            provider_payload={"provider": "lekab"},
            metadata={"delivery": "ok"},
        )

        audit_repo.append(
            audit_id="audit-1",
            tenant_id=tenant_id,
            appointment_id="external-appointment-1",
            reminder_job_id="job-planned",
            reminder_policy_id=policy.id,
            event_type="job.sent",
            human_readable_message="Reminder job sent",
            payload={"job_id": "job-planned"},
        )

        snapshot = build_reminder_runtime_health_snapshot(
            session,
            tenant_id=tenant_id,
            policy_name=policy_name,
            now_utc=appointment_start,
        )

        assert snapshot.tenant_id == tenant_id
        assert snapshot.policy_name == policy_name
        assert snapshot.appointment_count == 1
        assert snapshot.job_counts["planned"] == 1
        assert snapshot.job_counts["dispatching"] == 1
        assert snapshot.job_counts["failed"] == 1
        assert snapshot.active_job_count == 2
        assert snapshot.reclaimable_lock_count == 1
        assert snapshot.next_due_at_utc == (appointment_start - timedelta(hours=2)).replace(tzinfo=None)
        assert snapshot.active_hold_count == 1
        assert snapshot.hold_counts["ACTIVE"] == 1
        assert snapshot.message_counts["sent"] == 1
        assert snapshot.audit_counts["job.sent"] == 1
        assert snapshot.last_job_activity_at_utc is not None
        assert snapshot.last_hold_activity_at_utc is not None
        assert snapshot.last_message_activity_at_utc is not None
        assert snapshot.last_audit_activity_at_utc is not None
        assert snapshot.has_reclaimable_jobs() is True
        assert any("expired dispatch locks" in note for note in snapshot.health_notes)
        assert any("failed and need attention" in note for note in snapshot.health_notes)
        assert any("slot holds are still active" in note for note in snapshot.health_notes)
    finally:
        session.close()
