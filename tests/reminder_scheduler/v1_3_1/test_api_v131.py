from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = Path(gettempdir()) / f"appointment_agent_reminder_v131_{uuid4().hex}.db"

from fastapi.testclient import TestClient

from appointment_agent_shared.db import Base, get_session
from reminder_scheduler.v1_3_1.reminder_scheduler.app import app
from reminder_scheduler.v1_3_1.reminder_scheduler.service import (
    ReminderAppointmentInput,
    ReminderLifecycleError,
    ReminderMode,
    ReminderPolicyInput,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    ReminderStatus,
    utcnow,
)
from reminder_scheduler.v1_3_1.reminder_scheduler.worker import ReminderSchedulerWorker


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


def _manual_policy(policy_key: str, reminder_count: int = 2) -> ReminderPolicyInput:
    return ReminderPolicyInput(
        tenant_id="default",
        policy_key=policy_key,
        enabled=True,
        mode=ReminderMode.MANUAL,
        reminder_count=reminder_count,
        first_reminder_hours_before=48 if reminder_count >= 1 else None,
        second_reminder_hours_before=24 if reminder_count >= 2 else None,
        third_reminder_hours_before=12 if reminder_count >= 3 else None,
        channel_email_enabled=True,
        channel_voice_enabled=False,
        channel_rcs_sms_enabled=False,
    )


def _appointment(
    policy_key: str,
    minutes_from_now: int = 120,
    appointment_id: str | None = None,
    *,
    simulate_failure: bool = False,
) -> ReminderAppointmentInput:
    start_time = utcnow() + timedelta(minutes=minutes_from_now)
    return ReminderAppointmentInput(
        appointment_external_id=appointment_id or f"appt-{policy_key}",
        title="Reminder Scheduler Pilot",
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        timezone="Europe/Berlin",
        tenant_id="default",
        customer_id="customer-1301",
        email="pilot@example.test",
        phone="+491700000000",
        status="scheduled",
        metadata={"policy_key": policy_key, "simulate_failure": simulate_failure},
    )


def test_reminder_scheduler_v131_api_exposes_help_config_jobs_health_and_lifecycle_routes() -> None:
    client = _client()

    help_response = client.get("/api/reminders/v1.3.1/help")
    config_response = client.get("/api/reminders/v1.3.1/config")
    preview_get_response = client.get("/api/reminders/v1.3.1/config/preview")
    jobs_response = client.get("/api/reminders/v1.3.1/jobs")
    health_response = client.get("/api/reminders/v1.3.1/health")

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.3.1"
    assert "lifecycle_hardening" in help_response.json()["features"]

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["policy"]["policy_key"] == "global"
    assert config_payload["appointment_count"] >= 2

    assert preview_get_response.status_code == 200
    assert preview_get_response.json()["policy"]["policy_key"] == "global"

    assert jobs_response.status_code == 200
    assert jobs_response.json()["version"] == "v1.3.1"

    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload["version"] == "v1.3.1"
    assert health_payload["scheduler_enabled"] is True


def test_reminder_scheduler_v131_rebuild_deduplicates_and_updates_reschedules() -> None:
    client = _client()
    start_time = utcnow() + timedelta(hours=72)
    changed_start_time = utcnow() + timedelta(hours=96)

    first_rebuild = client.post(
        "/api/reminders/v1.3.1/rebuild",
        json={
            "policy": _manual_policy("global").model_dump(mode="json"),
            "appointments": [
                _appointment("global", minutes_from_now=72 * 60, appointment_id="appt-global-1").model_dump(mode="json"),
            ],
            "replace_existing": True,
        },
    )
    second_rebuild = client.post(
        "/api/reminders/v1.3.1/rebuild",
        json={
            "policy": _manual_policy("global").model_dump(mode="json"),
            "appointments": [
                _appointment("global", minutes_from_now=72 * 60, appointment_id="appt-global-1").model_dump(mode="json"),
            ],
            "replace_existing": True,
        },
    )
    changed_rebuild = client.post(
        "/api/reminders/v1.3.1/rebuild",
        json={
            "policy": _manual_policy("global").model_dump(mode="json"),
            "appointments": [
                ReminderAppointmentInput(
                    appointment_external_id="appt-global-1",
                    title="Reminder Scheduler Pilot",
                    start_time=changed_start_time,
                    end_time=changed_start_time + timedelta(minutes=30),
                    timezone="Europe/Berlin",
                    tenant_id="default",
                    customer_id="customer-1301",
                    email="pilot@example.test",
                    phone="+491700000000",
                    status="scheduled",
                    metadata={"policy_key": "global"},
                ).model_dump(mode="json")
            ],
            "replace_existing": True,
        },
    )

    assert first_rebuild.status_code == 200
    assert first_rebuild.json()["planned_jobs"] == 2
    assert second_rebuild.status_code == 200
    assert second_rebuild.json()["planned_jobs"] == 2
    assert changed_rebuild.status_code == 200
    assert changed_rebuild.json()["planned_jobs"] == 2

    jobs_response = client.get("/api/reminders/v1.3.1/jobs")
    jobs_payload = jobs_response.json()["jobs"]
    matching_jobs = [
        job
        for job in jobs_payload
        if job["appointment_external_id"] == "appt-global-1" and job["status"] in {"planned", "due", "dispatching"}
    ]
    assert len(matching_jobs) == 2
    original_latest_reminder = start_time - timedelta(hours=24)

    def _as_aware(moment: str) -> datetime:
        parsed = datetime.fromisoformat(moment)
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed

    assert any(_as_aware(job["scheduled_for"]) > original_latest_reminder for job in matching_jobs)


def test_reminder_scheduler_v131_retry_and_lock_reclaim_are_safe() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("worker-test", reminder_count=1)
        appointment = _appointment("worker-test", minutes_from_now=120)
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )

        worker = ReminderSchedulerWorker(session_factory=TestingSessionLocal)
        service = ReminderSchedulerService(session)
        job = next(job for job in service.list_jobs() if job.policy_key == "worker-test")

        original_deliver = service._deliver_job

        def _failing_deliver(record):
            raise RuntimeError("simulated dispatch failure")

        service._deliver_job = _failing_deliver  # type: ignore[method-assign]
        dispatch_failed = service.dispatch_due_jobs("worker-test")
        assert dispatch_failed.due_jobs == 1
        assert dispatch_failed.failed_jobs == 1
        refreshed_job = service.get_job(job.job_id)
        assert refreshed_job.status == ReminderStatus.PLANNED.value
        assert refreshed_job.attempt_count == 1
        assert refreshed_job.last_error == "simulated dispatch failure"

        db_job = service.job_repo.get(job.job_id)
        assert db_job is not None
        db_job.status = ReminderStatus.FAILED.value
        session.commit()

        service._deliver_job = original_deliver  # type: ignore[method-assign]
        retry_job = service.retry_job(job.job_id)
        assert retry_job.status == ReminderStatus.PLANNED.value
        assert retry_job.attempt_count == 1

        db_job = service.job_repo.get(job.job_id)
        assert db_job is not None
        db_job.status = ReminderStatus.DISPATCHING.value
        db_job.locked_until_utc = utcnow() - timedelta(minutes=10)
        db_job.scheduled_for_utc = utcnow() - timedelta(minutes=1)
        session.commit()

        reclaimed = service.dispatch_due_jobs("worker-test")
        assert reclaimed.reclaimed_jobs >= 1
        assert service.get_job(job.job_id).status == ReminderStatus.SENT.value

        worker_cycle = worker.run_cycle_once(policy_key="worker-test")
        assert worker_cycle["dispatch"]["due_jobs"] >= 0
    finally:
        session.close()


def test_reminder_scheduler_v131_lifecycle_guards_reject_invalid_transitions() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("guard-test", reminder_count=1)
        appointment = _appointment("guard-test", minutes_from_now=120)
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
