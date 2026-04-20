from __future__ import annotations

import os
from pathlib import Path
from tempfile import gettempdir
from datetime import timedelta
from uuid import uuid4

DB_PATH = Path(gettempdir()) / f"appointment_agent_reminder_v130_{uuid4().hex}.db"
os.environ["APPOINTMENT_AGENT_DB_URL"] = f"sqlite:///{DB_PATH}"

from fastapi.testclient import TestClient

from appointment_agent_shared.db import SessionLocal
from reminder_scheduler.v1_3_0.reminder_scheduler.app import app
from reminder_scheduler.v1_3_0.reminder_scheduler.service import (
    ReminderAppointmentInput,
    ReminderMode,
    ReminderPolicyInput,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    utcnow,
)
from reminder_scheduler.v1_3_0.reminder_scheduler.worker import ReminderSchedulerWorker


def _client() -> TestClient:
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


def _appointment(policy_key: str, minutes_from_now: int = 120, appointment_id: str | None = None) -> ReminderAppointmentInput:
    start_time = utcnow() + timedelta(minutes=minutes_from_now)
    return ReminderAppointmentInput(
        appointment_external_id=appointment_id or f"appt-{policy_key}",
        title="Reminder Scheduler Pilot",
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        timezone="Europe/Berlin",
        tenant_id="default",
        customer_id="customer-1300",
        email="pilot@example.test",
        phone="+491700000000",
        status="scheduled",
        metadata={"policy_key": policy_key},
    )


def test_reminder_scheduler_api_supports_config_preview_jobs_rebuild_and_health() -> None:
    client = _client()

    help_response = client.get("/api/reminders/v1.3.0/help")
    config_response = client.get("/api/reminders/v1.3.0/config")
    preview_get_response = client.get("/api/reminders/v1.3.0/config/preview")
    preview_post_response = client.post(
        "/api/reminders/v1.3.0/config/preview",
        json={
            "policy": _manual_policy("global").model_dump(mode="json"),
            "appointments": [
                _appointment("global", minutes_from_now=180, appointment_id="appt-global-1").model_dump(mode="json"),
                _appointment("global", minutes_from_now=360, appointment_id="appt-global-2").model_dump(mode="json"),
            ],
        },
    )
    rebuild_response = client.post(
        "/api/reminders/v1.3.0/rebuild",
        json={
            "policy": _manual_policy("global").model_dump(mode="json"),
            "appointments": [
                _appointment("global", minutes_from_now=180, appointment_id="appt-global-1").model_dump(mode="json"),
                _appointment("global", minutes_from_now=360, appointment_id="appt-global-2").model_dump(mode="json"),
            ],
            "replace_existing": True,
        },
    )
    jobs_response = client.get("/api/reminders/v1.3.0/jobs")
    health_response = client.get("/api/reminders/v1.3.0/health")

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.3.0"
    assert "/config/preview" in help_response.json()["endpoints"]

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["policy"]["policy_key"] == "global"
    assert config_payload["appointment_count"] >= 2

    assert preview_get_response.status_code == 200
    assert preview_get_response.json()["policy"]["policy_key"] == "global"

    assert preview_post_response.status_code == 200
    preview_payload = preview_post_response.json()
    assert preview_payload["appointment_count"] == 2
    assert len(preview_payload["preview"]) == 4

    assert rebuild_response.status_code == 200
    rebuild_payload = rebuild_response.json()
    assert rebuild_payload["success"] is True
    assert rebuild_payload["planned_jobs"] == 4
    assert len(rebuild_payload["jobs"]) == 4

    assert jobs_response.status_code == 200
    jobs_payload = jobs_response.json()
    assert jobs_payload["version"] == "v1.3.0"
    matching_jobs = [
        job for job in jobs_payload["jobs"] if job["appointment_external_id"] in {"appt-global-1", "appt-global-2"}
    ]
    assert len(matching_jobs) == 4

    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload["version"] == "v1.3.0"
    assert health_payload["scheduler_enabled"] is True
    assert health_payload["reminder_count"] >= 1


def test_reminder_scheduler_worker_plans_and_dispatches_due_jobs() -> None:
    session = SessionLocal()
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

        worker = ReminderSchedulerWorker()
        result = worker.run_cycle_once(policy_key="worker-test")

        assert result["planning"]["created_jobs"] == 1
        assert result["dispatch"]["due_jobs"] == 1
        assert result["dispatch"]["dispatched_jobs"] == 1

        jobs = service.list_jobs()
        worker_jobs = [job for job in jobs if job.policy_key == "worker-test"]
        assert len(worker_jobs) == 1
        assert worker_jobs[0].status == "sent"

        health = service.health("worker-test")
        assert health.job_counts["sent"] == 1
        assert health.next_due_at is None
    finally:
        session.close()
