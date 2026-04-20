from __future__ import annotations

from datetime import datetime, timedelta, timezone
from tempfile import gettempdir
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from appointment_agent_shared.db import Base
from appointment_agent_shared.models import ReminderJobRecord
from reminder_scheduler.v1_3_5.reminder_scheduler.service import (
    ReminderAppointmentInput,
    ReminderMode,
    ReminderPolicyInput,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    ReminderStatus,
)


DB_PATH = f"{gettempdir()}/appointment_agent_reminder_v135_delivery_{uuid4().hex}.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=ENGINE)


def _manual_policy(
    policy_key: str,
    *,
    reminder_count: int = 1,
    channel_email_enabled: bool = True,
    channel_voice_enabled: bool = False,
    channel_rcs_sms_enabled: bool = False,
) -> ReminderPolicyInput:
    return ReminderPolicyInput(
        tenant_id="default",
        policy_key=policy_key,
        enabled=True,
        mode=ReminderMode.MANUAL,
        reminder_count=reminder_count,
        first_reminder_hours_before=1 if reminder_count >= 1 else None,
        second_reminder_hours_before=1 if reminder_count >= 2 else None,
        third_reminder_hours_before=1 if reminder_count >= 3 else None,
        channel_email_enabled=channel_email_enabled,
        channel_voice_enabled=channel_voice_enabled,
        channel_rcs_sms_enabled=channel_rcs_sms_enabled,
    )


def _appointment(
    policy_key: str,
    *,
    start_time: datetime,
    end_time: datetime,
    timezone_name: str = "UTC",
    email: str | None = "pilot@example.test",
    phone: str | None = "+491700000000",
    metadata: dict[str, object] | None = None,
) -> ReminderAppointmentInput:
    return ReminderAppointmentInput(
        appointment_external_id=f"appt-{policy_key}",
        title="Reminder Scheduler Pilot",
        start_time=start_time,
        end_time=end_time,
        timezone=timezone_name,
        tenant_id="default",
        customer_id="customer-1304",
        email=email,
        phone=phone,
        status="scheduled",
        metadata=metadata or {"policy_key": policy_key},
    )


def _force_due_jobs(session) -> None:
    due_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    for record in session.scalars(select(ReminderJobRecord)):
        record.scheduled_for_utc = due_at
        if record.status == ReminderStatus.DISPATCHING.value:
            record.status = ReminderStatus.PLANNED.value
    session.commit()


def _job_for_policy(service: ReminderSchedulerService, policy_key: str):
    return next(job for job in service.list_jobs() if job.policy_key == policy_key)


def test_v135_dispatch_success_marks_job_sent() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-success")
        start_time = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        appointment = _appointment(
            "delivery-success",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
        )
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )
        _force_due_jobs(session)

        result = service.dispatch_due_jobs(policy_key="delivery-success")
        job = _job_for_policy(service, "delivery-success")

        assert result.due_jobs == 1
        assert result.dispatched_jobs == 1
        assert result.retryable_failures == 0
        assert result.terminal_failures == 0
        assert result.failed_jobs == 0
        assert job.status == ReminderStatus.SENT.value
        assert job.payload["last_dispatch_result"]["outcome"] == "sent"
        assert job.sent_at is not None
    finally:
        session.close()


def test_v135_retryable_dispatch_failure_requeues_job() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-retryable")
        start_time = datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc)
        appointment = _appointment(
            "delivery-retryable",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            metadata={"policy_key": "delivery-retryable", "simulate_failure": True},
        )
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )
        _force_due_jobs(session)

        result = service.dispatch_due_jobs(policy_key="delivery-retryable")
        job = _job_for_policy(service, "delivery-retryable")

        assert result.due_jobs == 1
        assert result.dispatched_jobs == 0
        assert result.retryable_failures == 1
        assert result.terminal_failures == 0
        assert result.failed_jobs == 1
        assert job.status == ReminderStatus.PLANNED.value
        assert job.payload["last_dispatch_result"]["outcome"] == "retryable_failure"
        assert job.payload["last_dispatch_result"]["retryable"] is True
    finally:
        session.close()


def test_v135_terminal_dispatch_failure_for_missing_target() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-terminal", channel_email_enabled=False, channel_voice_enabled=True)
        start_time = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)
        appointment = _appointment(
            "delivery-terminal",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            email=None,
            phone=None,
        )
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )
        _force_due_jobs(session)

        result = service.dispatch_due_jobs(policy_key="delivery-terminal")
        job = _job_for_policy(service, "delivery-terminal")

        assert result.due_jobs == 1
        assert result.dispatched_jobs == 0
        assert result.retryable_failures == 0
        assert result.terminal_failures == 1
        assert result.failed_jobs == 1
        assert job.status == ReminderStatus.FAILED.value
        assert job.payload["last_dispatch_result"]["failure_reason_code"] == "target_missing"
        assert job.payload["last_dispatch_result"]["validation"]["is_valid"] is False
    finally:
        session.close()


def test_v135_policy_channel_disable_blocks_delivery() -> None:
    session = TestingSessionLocal()
    try:
        service = ReminderSchedulerService(session)
        policy = _manual_policy("delivery-disabled")
        start_time = datetime(2026, 6, 1, 15, 0, tzinfo=timezone.utc)
        appointment = _appointment(
            "delivery-disabled",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
        )
        service.rebuild(
            ReminderRebuildRequest(
                policy=policy,
                appointments=[appointment],
                replace_existing=True,
            )
        )
        service.save_config(
            policy.model_copy(
                update={
                    "channel_email_enabled": False,
                    "channel_voice_enabled": False,
                    "channel_rcs_sms_enabled": False,
                }
            )
        )
        _force_due_jobs(session)

        result = service.dispatch_due_jobs(policy_key="delivery-disabled")
        job = _job_for_policy(service, "delivery-disabled")

        assert result.due_jobs == 1
        assert result.dispatched_jobs == 0
        assert result.retryable_failures == 0
        assert result.terminal_failures == 1
        assert job.status == ReminderStatus.FAILED.value
        assert job.payload["last_dispatch_result"]["failure_reason_code"] == "channel_disabled"
    finally:
        session.close()
