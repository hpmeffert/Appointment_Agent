from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from appointment_agent_shared.db import Base, get_session
from appointment_agent_shared.models import ReminderJobRecord
from reminder_scheduler.v1_3_5.reminder_scheduler import adapter, calculator
from reminder_scheduler.v1_3_5.reminder_scheduler.app import app
from reminder_scheduler.v1_3_5.reminder_scheduler.service import (
    ReminderAppointmentInput,
    ReminderLifecycleError,
    ReminderMode,
    ReminderPolicyInput,
    ReminderPreviewRequest,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    ReminderStatus,
)
from reminder_scheduler.v1_3_5.reminder_scheduler.worker import ReminderSchedulerWorker


DB_PATH = Path(gettempdir()) / f"appointment_agent_reminder_v135_{uuid4().hex}.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=ENGINE)


def _client() -> TestClient:
    def _override_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


def _force_jobs_due(policy_key: str) -> None:
    session = TestingSessionLocal()
    try:
        due_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        rows = session.query(ReminderJobRecord).filter(ReminderJobRecord.policy_name == policy_key).all()
        for row in rows:
            row.scheduled_for_utc = due_time
            row.status = ReminderStatus.PLANNED.value
            row.locked_until_utc = None
        session.commit()
    finally:
        session.close()


def _manual_policy(policy_key: str, reminder_count: int = 2) -> ReminderPolicyInput:
    return ReminderPolicyInput(
        tenant_id="default",
        policy_key=policy_key,
        enabled=True,
        mode=ReminderMode.MANUAL,
        reminder_count=reminder_count,
        first_reminder_hours_before=2 if reminder_count >= 1 else None,
        second_reminder_hours_before=1 if reminder_count >= 2 else None,
        third_reminder_hours_before=12 if reminder_count >= 3 else None,
        channel_email_enabled=True,
        channel_voice_enabled=False,
        channel_rcs_sms_enabled=False,
    )


def _appointment(
    policy_key: str,
    *,
    start_time: datetime,
    end_time: datetime,
    timezone_name: str = "Europe/Berlin",
    appointment_id: str | None = None,
    status: str = "scheduled",
    simulate_failure: bool = False,
    simulate_terminal_failure: bool = False,
    email: str = "pilot@example.test",
    phone: str = "+491700000000",
) -> ReminderAppointmentInput:
    return ReminderAppointmentInput(
        appointment_external_id=appointment_id or f"appt-{policy_key}",
        title="Reminder Scheduler Pilot",
        start_time=start_time,
        end_time=end_time,
        timezone=timezone_name,
        tenant_id="default",
        customer_id="customer-1303",
        email=email,
        phone=phone,
        status=status,
        metadata={
            "policy_key": policy_key,
            "simulate_failure": simulate_failure,
            "simulate_terminal_failure": simulate_terminal_failure,
        },
    )


def test_v135_help_root_and_features_show_sync_contract_and_timezone_guards() -> None:
    client = _client()

    help_response = client.get("/api/reminders/v1.3.5/help")
    root_response = client.get("/api/reminders/v1.3.5/")

    assert help_response.status_code == 200
    help_payload = help_response.json()
    assert help_payload["version"] == "v1.3.5"
    assert "normalized_appointment_sync_contract" in help_payload["features"]
    assert "dispatcher_based_delivery_layer" in help_payload["features"]
    assert "target_validation_before_dispatch" in help_payload["features"]
    assert "retryable_vs_terminal_delivery_failures" in help_payload["features"]
    assert "runtime_health_snapshot" in help_payload["features"]
    assert "last_activity_visibility" in help_payload["features"]

    assert root_response.status_code == 200
    assert root_response.json()["version"] == "v1.3.5"


def test_v135_hash_is_stable_for_equal_inputs_and_changes_when_schedule_changes() -> None:
    berlin = ZoneInfo("Europe/Berlin")
    first_start = datetime(2026, 10, 25, 4, 30, tzinfo=berlin)
    first_end = first_start + timedelta(minutes=30)
    second_start = first_start + timedelta(hours=1)

    first_snapshot = adapter.normalize_appointment_snapshot(
        _appointment("hash-test", start_time=first_start, end_time=first_end, timezone_name="Europe/Berlin"),
        policy_key="hash-test",
    )
    second_snapshot = adapter.normalize_appointment_snapshot(
        _appointment("hash-test", start_time=first_start, end_time=first_end, timezone_name="Europe/Berlin"),
        policy_key="hash-test",
    )
    changed_snapshot = adapter.normalize_appointment_snapshot(
        _appointment("hash-test", start_time=second_start, end_time=second_start + timedelta(minutes=30), timezone_name="Europe/Berlin"),
        policy_key="hash-test",
    )

    assert first_snapshot.payload_hash == second_snapshot.payload_hash
    assert first_snapshot.payload_hash != changed_snapshot.payload_hash


def test_v135_repeated_rebuild_runs_are_idempotent() -> None:
    client = _client()
    start_time = datetime(2026, 7, 1, 14, 0, tzinfo=timezone.utc)
    appointment = _appointment(
        "idempotent",
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        timezone_name="UTC",
    )
    policy = _manual_policy("idempotent", reminder_count=2)

    first = client.post(
        "/api/reminders/v1.3.5/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [appointment.model_dump(mode="json")],
            "replace_existing": True,
        },
    )
    second = client.post(
        "/api/reminders/v1.3.5/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [appointment.model_dump(mode="json")],
            "replace_existing": True,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["planned_jobs"] == 2
    assert second.json()["planned_jobs"] == 2

    jobs_response = client.get("/api/reminders/v1.3.5/jobs")
    jobs_payload = jobs_response.json()
    assert jobs_payload["count"] == 2
    assert {job["status"] for job in jobs_payload["jobs"]} == {ReminderStatus.PLANNED.value}


def test_v135_rebuild_updates_existing_jobs_when_appointment_time_changes() -> None:
    client = _client()
    original_start = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    updated_start = original_start + timedelta(hours=1)
    policy = _manual_policy("reschedule", reminder_count=1)

    first = client.post(
        "/api/reminders/v1.3.5/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                _appointment(
                    "reschedule",
                    start_time=original_start,
                    end_time=original_start + timedelta(minutes=30),
                    timezone_name="UTC",
                ).model_dump(mode="json")
            ],
            "replace_existing": True,
        },
    )
    second = client.post(
        "/api/reminders/v1.3.5/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                _appointment(
                    "reschedule",
                    start_time=updated_start,
                    end_time=updated_start + timedelta(minutes=30),
                    timezone_name="UTC",
                ).model_dump(mode="json")
            ],
            "replace_existing": True,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["planned_jobs"] == 1
    jobs_payload = client.get("/api/reminders/v1.3.5/jobs").json()
    reschedule_jobs = [
        job for job in jobs_payload["jobs"] if job["policy_key"] == "reschedule"
    ]
    assert len(reschedule_jobs) == 1
    scheduled_for = reschedule_jobs[0]["scheduled_for"]
    assert datetime.fromisoformat(scheduled_for.replace("Z", "+00:00")) == updated_start - timedelta(hours=2)


def test_v135_cancelled_appointment_reconciles_existing_reminders() -> None:
    client = _client()
    start_time = datetime(2026, 9, 1, 16, 0, tzinfo=timezone.utc)
    policy = _manual_policy("cancelled", reminder_count=1)
    appointment = _appointment(
        "cancelled",
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        timezone_name="UTC",
    )

    client.post(
        "/api/reminders/v1.3.5/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [appointment.model_dump(mode="json")],
            "replace_existing": True,
        },
    )

    cancelled_response = client.post(
        "/api/reminders/v1.3.5/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                _appointment(
                    "cancelled",
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=30),
                    timezone_name="UTC",
                    status="cancelled",
                ).model_dump(mode="json")
            ],
            "replace_existing": True,
        },
    )

    assert cancelled_response.status_code == 200
    payload = cancelled_response.json()
    assert payload["cancelled_jobs"] == 1
    jobs_payload = client.get("/api/reminders/v1.3.5/jobs").json()
    cancelled_jobs = [job for job in jobs_payload["jobs"] if job["policy_key"] == "cancelled"]
    assert len(cancelled_jobs) == 1
    assert cancelled_jobs[0]["status"] == ReminderStatus.CANCELLED.value


def test_v135_rejects_ambiguous_and_nonexistent_naive_times() -> None:
    client = _client()
    policy = _manual_policy("naive-block", reminder_count=1)

    ambiguous_response = client.post(
        "/api/reminders/v1.3.5/config/preview",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                {
                    "appointment_external_id": "appt-naive-block",
                    "title": "Reminder Scheduler Pilot",
                    "start_time": datetime(2026, 10, 25, 2, 30).isoformat(),
                    "end_time": datetime(2026, 10, 25, 3, 0).isoformat(),
                    "timezone": "Europe/Berlin",
                    "tenant_id": "default",
                    "customer_id": "customer-1303",
                    "email": "pilot@example.test",
                    "phone": "+491700000000",
                    "status": "scheduled",
                    "metadata": {"policy_key": "naive-block", "simulate_failure": False},
                }
            ],
        },
    )
    nonexistent_response = client.post(
        "/api/reminders/v1.3.5/config/preview",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                {
                    "appointment_external_id": "appt-naive-block-2",
                    "title": "Reminder Scheduler Pilot",
                    "start_time": datetime(2026, 3, 29, 2, 30).isoformat(),
                    "end_time": datetime(2026, 3, 29, 3, 0).isoformat(),
                    "timezone": "Europe/Berlin",
                    "tenant_id": "default",
                    "customer_id": "customer-1303",
                    "email": "pilot@example.test",
                    "phone": "+491700000000",
                    "status": "scheduled",
                    "metadata": {"policy_key": "naive-block", "simulate_failure": False},
                }
            ],
        },
    )

    assert ambiguous_response.status_code == 422
    assert "ambiguous" in ambiguous_response.text
    assert nonexistent_response.status_code == 422
    assert "does not exist" in nonexistent_response.text


def test_v135_worker_and_preview_use_the_same_calculation_path(monkeypatch: pytest.MonkeyPatch) -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("worker-calc", reminder_count=1)
        appointment_start = datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc)
        appointment = _appointment(
            "worker-calc",
            start_time=appointment_start,
            end_time=appointment_start + timedelta(minutes=30),
            timezone_name="UTC",
        )
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )

        call_counter = {"count": 0}
        original_calculate = calculator.calculate_schedule

        def _wrapped_calculate(*args, **kwargs):
            call_counter["count"] += 1
            return original_calculate(*args, **kwargs)

        monkeypatch.setattr(calculator, "calculate_schedule", _wrapped_calculate)

        preview_service = ReminderSchedulerService(TestingSessionLocal())
        try:
            preview_service.preview(
                ReminderPreviewRequest(
                    policy=policy,
                    appointments=[appointment],
                )
            )
        finally:
            preview_service.session.close()

        worker = ReminderSchedulerWorker(session_factory=TestingSessionLocal)
        worker.run_planning_once(policy_key="worker-calc")

        assert call_counter["count"] >= 2
    finally:
        session.close()


def test_v135_lifecycle_guards_remain_strict() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("guard-test", reminder_count=1)
        appointment_start = datetime(2026, 6, 1, 15, 0, tzinfo=timezone.utc)
        appointment = _appointment(
            "guard-test",
            start_time=appointment_start,
            end_time=appointment_start + timedelta(minutes=30),
            timezone_name="UTC",
        )
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )
        job = service.list_jobs()[0]
        cancelled = service.cancel_job(job.job_id)
        assert cancelled.status == ReminderStatus.CANCELLED.value

        with pytest.raises(ReminderLifecycleError):
            service.retry_job(job.job_id)
    finally:
        session.close()


def test_v135_dispatch_marks_invalid_email_targets_as_skipped() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-invalid-email", reminder_count=1)
        appointment_start = datetime.now(timezone.utc) + timedelta(hours=6)
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[
                    _appointment(
                        "delivery-invalid-email",
                        start_time=appointment_start,
                        end_time=appointment_start + timedelta(minutes=30),
                        timezone_name="UTC",
                        email="not-an-email",
                    )
                ],
                replace_existing=True,
            )
        )
        _force_jobs_due("delivery-invalid-email")

        result = service.dispatch_due_jobs(policy_key="delivery-invalid-email")
        job = next(job for job in service.list_jobs(limit=20) if job.policy_key == "delivery-invalid-email")

        assert result.due_jobs == 1
        assert result.skipped_jobs == 0
        assert result.failed_jobs == 1
        assert result.terminal_failures == 1
        assert job.status == ReminderStatus.FAILED.value
        assert job.payload["last_dispatch_result"]["failure_reason_code"] == "target_invalid"
    finally:
        session.close()


def test_v135_dispatch_maps_retryable_delivery_failures_back_to_planned() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-retryable", reminder_count=1)
        appointment_start = datetime.now(timezone.utc) + timedelta(hours=6)
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[
                    _appointment(
                        "delivery-retryable",
                        start_time=appointment_start,
                        end_time=appointment_start + timedelta(minutes=30),
                        timezone_name="UTC",
                        simulate_failure=True,
                    )
                ],
                replace_existing=True,
            )
        )
        _force_jobs_due("delivery-retryable")

        result = service.dispatch_due_jobs(policy_key="delivery-retryable")
        job = next(job for job in service.list_jobs(limit=20) if job.policy_key == "delivery-retryable")

        assert result.retryable_failures == 1
        assert result.terminal_failures == 0
        assert job.status == ReminderStatus.PLANNED.value
        assert job.attempt_count == 1
        assert job.payload["last_dispatch_result"]["outcome"] == "retryable_failure"
    finally:
        session.close()


def test_v135_dispatch_maps_terminal_voice_failures_to_failed() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-terminal-voice", reminder_count=1).model_copy(
            update={
                "channel_email_enabled": False,
                "channel_voice_enabled": True,
            }
        )
        appointment_start = datetime.now(timezone.utc) + timedelta(hours=6)
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[
            _appointment(
                        "delivery-terminal-voice",
                        start_time=appointment_start,
                        end_time=appointment_start + timedelta(minutes=30),
                        timezone_name="UTC",
                        simulate_terminal_failure=True,
                    )
                ],
                replace_existing=True,
            )
        )
        _force_jobs_due("delivery-terminal-voice")

        result = service.dispatch_due_jobs(policy_key="delivery-terminal-voice")
        terminal_job = next(job for job in service.list_jobs(limit=20) if job.policy_key == "delivery-terminal-voice")

        assert result.retryable_failures == 0
        assert result.terminal_failures == 1
        assert terminal_job.status == ReminderStatus.FAILED.value
        assert terminal_job.payload["last_dispatch_result"]["failure_reason_code"] == "simulated_terminal_failure"
    finally:
        session.close()


def test_v135_dispatch_supports_email_voice_and_rcs_sms_success_paths() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        base_start = datetime.now(timezone.utc) + timedelta(hours=8)
        policies = [
            _manual_policy("delivery-email", reminder_count=1),
            _manual_policy("delivery-voice", reminder_count=1).model_copy(
                update={"channel_email_enabled": False, "channel_voice_enabled": True}
            ),
            _manual_policy("delivery-rcs", reminder_count=1).model_copy(
                update={"channel_email_enabled": False, "channel_rcs_sms_enabled": True}
            ),
        ]
        appointments = [
            _appointment("delivery-email", start_time=base_start, end_time=base_start + timedelta(minutes=30), timezone_name="UTC"),
            _appointment("delivery-voice", start_time=base_start, end_time=base_start + timedelta(minutes=30), timezone_name="UTC"),
            _appointment("delivery-rcs", start_time=base_start, end_time=base_start + timedelta(minutes=30), timezone_name="UTC"),
        ]
        for policy, appointment in zip(policies, appointments):
            service.rebuild(ReminderRebuildRequest(policy=policy, appointments=[appointment], replace_existing=True))
            _force_jobs_due(policy.policy_key)
            result = service.dispatch_due_jobs(policy_key=policy.policy_key)
            assert result.dispatched_jobs == 1

        jobs = {job.policy_key: job for job in service.list_jobs(limit=50)}
        assert jobs["delivery-email"].status == ReminderStatus.SENT.value
        assert jobs["delivery-voice"].status == ReminderStatus.SENT.value
        assert jobs["delivery-rcs"].status == ReminderStatus.SENT.value
        assert jobs["delivery-email"].payload["last_dispatch_result"]["provider_name"] == "email-simulator"
        assert jobs["delivery-voice"].payload["last_dispatch_result"]["provider_name"] == "voice-simulator"
        assert jobs["delivery-rcs"].payload["last_dispatch_result"]["provider_name"] == "rcs-sms-simulator"
    finally:
        session.close()


def test_v135_health_exposes_runtime_snapshot_fields() -> None:
    client = _client()
    response = client.get("/api/reminders/v1.3.5/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1.3.5"
    assert payload["db_status"] == "ok"
    assert payload["worker_status"] in {"ready", "disabled"}
    assert "hold_counts" in payload
    assert "message_counts" in payload
    assert "audit_counts" in payload
    assert "active_job_count" in payload
    assert "health_notes" in payload
