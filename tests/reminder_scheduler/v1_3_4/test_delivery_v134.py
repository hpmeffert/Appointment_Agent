from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from appointment_agent_shared.db import Base, engine
from reminder_scheduler.v1_3_4.reminder_scheduler.delivery import (
    DispatchOutcome,
    build_dispatcher_registry,
)


Base.metadata.create_all(bind=engine)


def _job(
    *,
    channel: str,
    target_ref: str | None,
    payload: dict[str, object] | None = None,
    attempt_count: int = 0,
    max_attempts: int = 3,
    job_id: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        job_id=job_id or f"job-{uuid4().hex[:8]}",
        channel=channel,
        target_ref=target_ref,
        payload_json=payload or {},
        attempt_count=attempt_count,
        max_attempts=max_attempts,
    )


def test_email_dispatcher_normalizes_target_and_succeeds() -> None:
    registry = build_dispatcher_registry(
        email_enabled=True,
        voice_enabled=False,
        rcs_sms_enabled=False,
    )
    result = registry.dispatch(
        _job(
            channel="email",
            target_ref="Pilot@Example.Test",
            payload={"appointment_metadata": {"policy_key": "delivery-test"}},
        ),
        now_utc=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert result.success is True
    assert result.outcome == DispatchOutcome.SENT.value
    assert result.validation.is_valid is True
    assert result.validation.normalized_target == "pilot@example.test"
    assert result.provider_message_id is not None
    assert result.provider_message_id.startswith("email-simulator:email:")


def test_voice_dispatcher_rejects_missing_phone_as_terminal_failure() -> None:
    registry = build_dispatcher_registry(
        email_enabled=False,
        voice_enabled=True,
        rcs_sms_enabled=False,
    )
    result = registry.dispatch(_job(channel="voice", target_ref=None))

    assert result.success is False
    assert result.terminal is True
    assert result.retryable is False
    assert result.outcome == DispatchOutcome.TERMINAL_FAILURE.value
    assert result.failure_reason_code == "target_missing"
    assert result.validation.required_target_kind == "phone"


def test_rcs_dispatcher_can_be_disabled_per_policy() -> None:
    registry = build_dispatcher_registry(
        email_enabled=True,
        voice_enabled=True,
        rcs_sms_enabled=False,
    )
    result = registry.dispatch(
        _job(channel="rcs_sms", target_ref="+49 170 123 4567"),
    )

    assert result.success is False
    assert result.terminal is True
    assert result.failure_reason_code == "channel_disabled"
    assert result.validation.is_valid is True


def test_retryable_failure_is_normalized_and_kept_separate_from_terminal_errors() -> None:
    registry = build_dispatcher_registry(
        email_enabled=True,
        voice_enabled=False,
        rcs_sms_enabled=False,
    )
    result = registry.dispatch(
        _job(
            channel="email",
            target_ref="retry@example.test",
            payload={"appointment_metadata": {"simulate_failure": True}},
        ),
    )

    assert result.success is False
    assert result.retryable is True
    assert result.terminal is False
    assert result.outcome == DispatchOutcome.RETRYABLE_FAILURE.value
    assert result.failure_reason_code == "simulated_retryable_failure"
