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
from reminder_scheduler.v1_3_2.reminder_scheduler.app import app
from reminder_scheduler.v1_3_2.reminder_scheduler import calculator, service as service_module, time_utils
from reminder_scheduler.v1_3_2.reminder_scheduler.service import (
    ReminderAppointmentInput,
    ReminderLifecycleError,
    ReminderMode,
    ReminderPolicyInput,
    ReminderPreviewRequest,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    ReminderStatus,
)
from reminder_scheduler.v1_3_2.reminder_scheduler.worker import ReminderSchedulerWorker


DB_PATH = Path(gettempdir()) / f"appointment_agent_reminder_v132_{uuid4().hex}.db"
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
    simulate_failure: bool = False,
) -> ReminderAppointmentInput:
    return ReminderAppointmentInput(
        appointment_external_id=appointment_id or f"appt-{policy_key}",
        title="Reminder Scheduler Pilot",
        start_time=start_time,
        end_time=end_time,
        timezone=timezone_name,
        tenant_id="default",
        customer_id="customer-1302",
        email="pilot@example.test",
        phone="+491700000000",
        status="scheduled",
        metadata={"policy_key": policy_key, "simulate_failure": simulate_failure},
    )


def test_v132_help_config_jobs_health_and_root_show_version_and_timezone_features() -> None:
    client = _client()

    help_response = client.get("/api/reminders/v1.3.2/help")
    config_response = client.get("/api/reminders/v1.3.2/config")
    jobs_response = client.get("/api/reminders/v1.3.2/jobs")
    health_response = client.get("/api/reminders/v1.3.2/health")
    root_response = client.get("/api/reminders/v1.3.2/")

    assert help_response.status_code == 200
    help_payload = help_response.json()
    assert help_payload["version"] == "v1.3.2"
    assert "canonical_utc_schedule_calculation" in help_payload["features"]
    assert "past_reminders_are_skipped_explicitly" in help_payload["features"]

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["policy"]["policy_key"] == "global"
    assert config_payload["appointment_count"] >= 2

    assert jobs_response.status_code == 200
    assert jobs_response.json()["version"] == "v1.3.2"
    assert health_response.status_code == 200
    assert health_response.json()["version"] == "v1.3.2"
    assert root_response.json()["version"] == "v1.3.2"


def test_v132_preview_normalizes_timezone_and_uses_shared_calculator_path() -> None:
    client = _client()
    berlin = ZoneInfo("Europe/Berlin")
    appointment_start_local = datetime(2026, 10, 25, 4, 30, tzinfo=berlin)
    appointment_end_local = appointment_start_local + timedelta(minutes=30)
    policy = _manual_policy("dst-preview", reminder_count=1)

    call_counter = {"count": 0}
    original_calculate = calculator.calculate_schedule

    def _wrapped_calculate(*args, **kwargs):
        call_counter["count"] += 1
        return original_calculate(*args, **kwargs)

    calculator.calculate_schedule = _wrapped_calculate  # type: ignore[method-assign]
    try:
        preview_response = client.post(
            "/api/reminders/v1.3.2/config/preview",
            json={
                "policy": policy.model_dump(mode="json"),
                "appointments": [
                    _appointment(
                        "dst-preview",
                        start_time=appointment_start_local,
                        end_time=appointment_end_local,
                        timezone_name="Europe/Berlin",
                    ).model_dump(mode="json")
                ],
            },
        )
    finally:
        calculator.calculate_schedule = original_calculate  # type: ignore[method-assign]

    assert preview_response.status_code == 200
    payload = preview_response.json()
    assert call_counter["count"] == 1
    assert payload["preview"][0]["scheduled_for"].endswith("+00:00") or payload["preview"][0]["scheduled_for"].endswith("Z")
    expected_utc = appointment_start_local.astimezone(timezone.utc) - timedelta(hours=2)
    parsed_preview = datetime.fromisoformat(payload["preview"][0]["scheduled_for"].replace("Z", "+00:00"))
    assert parsed_preview == expected_utc


def test_v132_rejects_ambiguous_and_nonexistent_naive_times() -> None:
    client = _client()
    policy = _manual_policy("naive-block", reminder_count=1)

    ambiguous_response = client.post(
        "/api/reminders/v1.3.2/config/preview",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                _appointment(
                    "naive-block",
                    start_time=datetime(2026, 10, 25, 2, 30),
                    end_time=datetime(2026, 10, 25, 3, 0),
                ).model_dump(mode="json")
            ],
        },
    )
    nonexistent_response = client.post(
        "/api/reminders/v1.3.2/config/preview",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [
                _appointment(
                    "naive-block",
                    start_time=datetime(2026, 3, 29, 2, 30),
                    end_time=datetime(2026, 3, 29, 3, 0),
                ).model_dump(mode="json")
            ],
        },
    )

    assert ambiguous_response.status_code == 400
    assert "ambiguous" in ambiguous_response.json()["detail"]["message"]
    assert nonexistent_response.status_code == 400
    assert "does not exist" in nonexistent_response.json()["detail"]["message"]


def test_v132_skips_past_reminders_but_keeps_future_jobs() -> None:
    client = _client()
    fixed_now = datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc)
    original_now = time_utils.utcnow
    time_utils.utcnow = lambda: fixed_now  # type: ignore[method-assign]
    service_module.time_utils.utcnow = lambda: fixed_now  # type: ignore[method-assign]
    try:
        start_time = fixed_now + timedelta(minutes=90)
        rebuild_response = client.post(
            "/api/reminders/v1.3.2/rebuild",
            json={
                "policy": _manual_policy("near-term", reminder_count=2).model_dump(mode="json"),
                "appointments": [
                    _appointment(
                        "near-term",
                        start_time=start_time,
                        end_time=start_time + timedelta(minutes=30),
                        timezone_name="UTC",
                    ).model_dump(mode="json")
                ],
                "replace_existing": True,
            },
        )
        follow_up = client.get("/api/reminders/v1.3.2/config?policy_key=near-term")
    finally:
        time_utils.utcnow = original_now  # type: ignore[method-assign]
        service_module.time_utils.utcnow = original_now  # type: ignore[method-assign]

    assert rebuild_response.status_code == 200
    payload = rebuild_response.json()
    assert payload["planned_jobs"] == 1
    assert payload["skipped_past_jobs"] == 1
    assert any(job["status"] == ReminderStatus.PLANNED.value for job in payload["jobs"])
    assert any(job["status"] == ReminderStatus.SKIPPED.value for job in payload["jobs"]) is False

    follow_up_payload = follow_up.json()
    assert follow_up_payload["skipped_preview_items"] == 1
    assert follow_up_payload["preview"][0]["status"] in {ReminderStatus.SKIPPED.value, ReminderStatus.PLANNED.value}


def test_v132_worker_uses_the_same_calculation_path_as_preview(monkeypatch: pytest.MonkeyPatch) -> None:
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
        worker = ReminderSchedulerWorker(session_factory=TestingSessionLocal)
        preview_session = TestingSessionLocal()
        preview_service = ReminderSchedulerService(preview_session)
        try:
            preview_service.preview(
                ReminderPreviewRequest(
                    policy=policy,
                    appointments=[appointment],
                )
            )
            worker.run_planning_once(policy_key="worker-calc")
        finally:
            preview_service.session.close()

        assert call_counter["count"] >= 2
    finally:
        session.close()


def test_v132_lifecycle_guards_remain_strict() -> None:
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
