from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Protocol


EMAIL_TARGET_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_TARGET_RE = re.compile(r"^\+?[0-9]{6,15}$")


class DispatchOutcome(str, Enum):
    """Normalized outcome vocabulary for every reminder delivery attempt."""

    SENT = "sent"
    RETRYABLE_FAILURE = "retryable_failure"
    TERMINAL_FAILURE = "terminal_failure"


@dataclass(frozen=True)
class DispatchTargetValidationResult:
    """Normalized validation result for the delivery target.

    The dispatch layer validates the target before it attempts any delivery.
    This keeps the service layer free from channel-specific parsing logic and
    makes the resulting errors easy to reason about in tests and audits.
    """

    channel: str
    target_ref: Optional[str]
    normalized_target: Optional[str]
    required_target_kind: str
    is_valid: bool
    retryable: bool
    reason_code: Optional[str] = None
    reason_text: Optional[str] = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "target_ref": self.target_ref,
            "normalized_target": self.normalized_target,
            "required_target_kind": self.required_target_kind,
            "is_valid": self.is_valid,
            "retryable": self.retryable,
            "reason_code": self.reason_code,
            "reason_text": self.reason_text,
        }


@dataclass(frozen=True)
class DispatchResult:
    """Normalized delivery result returned by every channel dispatcher."""

    channel: str
    target_ref: Optional[str]
    validation: DispatchTargetValidationResult
    outcome: str
    retryable: bool
    terminal: bool
    provider_name: str
    provider_message_id: Optional[str] = None
    failure_reason_code: Optional[str] = None
    failure_reason_text: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.outcome == DispatchOutcome.SENT.value

    def to_payload(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "target_ref": self.target_ref,
            "validation": self.validation.to_payload(),
            "outcome": self.outcome,
            "retryable": self.retryable,
            "terminal": self.terminal,
            "provider_name": self.provider_name,
            "provider_message_id": self.provider_message_id,
            "failure_reason_code": self.failure_reason_code,
            "failure_reason_text": self.failure_reason_text,
            "metadata": self.metadata,
        }

    @classmethod
    def sent(
        cls,
        *,
        channel: str,
        target_ref: Optional[str],
        validation: DispatchTargetValidationResult,
        provider_name: str,
        provider_message_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "DispatchResult":
        return cls(
            channel=channel,
            target_ref=target_ref,
            validation=validation,
            outcome=DispatchOutcome.SENT.value,
            retryable=False,
            terminal=False,
            provider_name=provider_name,
            provider_message_id=provider_message_id,
            metadata=metadata or {},
        )

    @classmethod
    def retryable_failure(
        cls,
        *,
        channel: str,
        target_ref: Optional[str],
        validation: DispatchTargetValidationResult,
        provider_name: str,
        failure_reason_code: str,
        failure_reason_text: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "DispatchResult":
        return cls(
            channel=channel,
            target_ref=target_ref,
            validation=validation,
            outcome=DispatchOutcome.RETRYABLE_FAILURE.value,
            retryable=True,
            terminal=False,
            provider_name=provider_name,
            failure_reason_code=failure_reason_code,
            failure_reason_text=failure_reason_text,
            metadata=metadata or {},
        )

    @classmethod
    def terminal_failure(
        cls,
        *,
        channel: str,
        target_ref: Optional[str],
        validation: DispatchTargetValidationResult,
        provider_name: str,
        failure_reason_code: str,
        failure_reason_text: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "DispatchResult":
        return cls(
            channel=channel,
            target_ref=target_ref,
            validation=validation,
            outcome=DispatchOutcome.TERMINAL_FAILURE.value,
            retryable=False,
            terminal=True,
            provider_name=provider_name,
            failure_reason_code=failure_reason_code,
            failure_reason_text=failure_reason_text,
            metadata=metadata or {},
        )


class ReminderDispatcherProtocol(Protocol):
    channel_name: str

    def validate_target(self, job: Any) -> DispatchTargetValidationResult:
        ...

    def dispatch(self, job: Any, *, now_utc: Optional[datetime] = None) -> DispatchResult:
        ...


def _payload_dict(job: Any) -> dict[str, Any]:
    payload = getattr(job, "payload_json", {}) or {}
    return payload if isinstance(payload, dict) else {}


def _first_non_empty_string(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_email_target(value: str) -> Optional[str]:
    normalized = value.strip().lower()
    if EMAIL_TARGET_RE.fullmatch(normalized):
        return normalized
    return None


def _normalize_phone_target(value: str) -> Optional[str]:
    stripped = value.strip()
    digits = "".join(character for character in stripped if character.isdigit())
    if not digits:
        return None
    normalized = f"+{digits}" if stripped.startswith("+") else digits
    if PHONE_TARGET_RE.fullmatch(normalized):
        return normalized
    return None


@dataclass(frozen=True)
class BaseReminderDispatcher:
    """Common dispatcher logic shared by the three supported channels."""

    channel_name: str
    provider_name: str
    required_target_kind: str
    channel_enabled: bool = True

    def _resolve_target_ref(self, job: Any) -> Optional[str]:
        payload = _payload_dict(job)
        appointment_metadata = payload.get("appointment_metadata")
        appointment_metadata = appointment_metadata if isinstance(appointment_metadata, dict) else {}
        delivery_target = payload.get("delivery_target")
        delivery_target = delivery_target if isinstance(delivery_target, dict) else {}

        # The reminder worker always sees a single, flattened target string.
        # We still look in a few stable places so future integrations can pass
        # richer payloads without breaking this release line.
        if self.required_target_kind == "email":
            return _first_non_empty_string(
                getattr(job, "target_ref", None),
                delivery_target.get("email"),
                appointment_metadata.get("email"),
                payload.get("email"),
            )
        return _first_non_empty_string(
            getattr(job, "target_ref", None),
            delivery_target.get("phone"),
            delivery_target.get("msisdn"),
            appointment_metadata.get("phone"),
            appointment_metadata.get("msisdn"),
            payload.get("phone"),
            payload.get("msisdn"),
        )

    def _validation_failure(
        self,
        *,
        target_ref: Optional[str],
        reason_code: str,
        reason_text: str,
        normalized_target: Optional[str] = None,
    ) -> DispatchTargetValidationResult:
        return DispatchTargetValidationResult(
            channel=self.channel_name,
            target_ref=target_ref,
            normalized_target=normalized_target,
            required_target_kind=self.required_target_kind,
            is_valid=False,
            retryable=False,
            reason_code=reason_code,
            reason_text=reason_text,
        )

    def validate_target(self, job: Any) -> DispatchTargetValidationResult:
        target_ref = self._resolve_target_ref(job)
        if target_ref is None:
            return self._validation_failure(
                target_ref=None,
                reason_code="target_missing",
                reason_text=f"{self.required_target_kind} target is required before dispatch.",
            )

        if self.required_target_kind == "email":
            normalized_target = _normalize_email_target(target_ref)
        else:
            normalized_target = _normalize_phone_target(target_ref)

        if normalized_target is None:
            return self._validation_failure(
                target_ref=target_ref,
                reason_code="target_invalid",
                reason_text=f"{self.required_target_kind} target is not valid for the {self.channel_name} channel.",
            )

        return DispatchTargetValidationResult(
            channel=self.channel_name,
            target_ref=target_ref,
            normalized_target=normalized_target,
            required_target_kind=self.required_target_kind,
            is_valid=True,
            retryable=False,
        )

    def _dispatch_failure_mode(self, job: Any) -> tuple[Optional[str], Optional[str]]:
        payload = _payload_dict(job)
        appointment_metadata = payload.get("appointment_metadata")
        appointment_metadata = appointment_metadata if isinstance(appointment_metadata, dict) else {}
        failure_kind = appointment_metadata.get("delivery_failure_kind") or payload.get("delivery_failure_kind")
        if appointment_metadata.get("simulate_terminal_failure") or payload.get("simulate_terminal_failure"):
            failure_kind = "terminal"
        elif appointment_metadata.get("simulate_failure") or payload.get("simulate_failure"):
            failure_kind = failure_kind or "retryable"

        if failure_kind == "retryable":
            return "simulated_retryable_failure", "Simulated transient delivery failure"
        if failure_kind == "terminal":
            return "simulated_terminal_failure", "Simulated terminal delivery failure"
        return None, None

    def _provider_message_id(self, job: Any, *, now_utc: Optional[datetime] = None) -> str:
        timestamp_fragment = now_utc.isoformat() if now_utc is not None else "delivery"
        return f"{self.provider_name}:{self.channel_name}:{getattr(job, 'job_id', 'job')}:{timestamp_fragment}"

    def dispatch(self, job: Any, *, now_utc: Optional[datetime] = None) -> DispatchResult:
        validation = self.validate_target(job)
        target_ref = validation.target_ref

        if not self.channel_enabled:
            return DispatchResult.terminal_failure(
                channel=self.channel_name,
                target_ref=target_ref,
                validation=validation,
                provider_name=self.provider_name,
                failure_reason_code="channel_disabled",
                failure_reason_text=f"{self.channel_name} delivery is disabled for the active reminder policy.",
            )

        if not validation.is_valid:
            return DispatchResult.terminal_failure(
                channel=self.channel_name,
                target_ref=target_ref,
                validation=validation,
                provider_name=self.provider_name,
                failure_reason_code=validation.reason_code or "target_invalid",
                failure_reason_text=validation.reason_text or "Delivery target validation failed.",
            )

        failure_code, failure_text = self._dispatch_failure_mode(job)
        if failure_code is not None and failure_text is not None:
            failure_kind = "retryable" if failure_code == "simulated_retryable_failure" else "terminal"
            if failure_kind == "retryable":
                return DispatchResult.retryable_failure(
                    channel=self.channel_name,
                    target_ref=target_ref,
                    validation=validation,
                    provider_name=self.provider_name,
                    failure_reason_code=failure_code,
                    failure_reason_text=failure_text,
                    metadata={
                        "provider": self.provider_name,
                        "channel": self.channel_name,
                        "target": validation.normalized_target,
                    },
                )
            return DispatchResult.terminal_failure(
                channel=self.channel_name,
                target_ref=target_ref,
                validation=validation,
                provider_name=self.provider_name,
                failure_reason_code=failure_code,
                failure_reason_text=failure_text,
                metadata={
                    "provider": self.provider_name,
                    "channel": self.channel_name,
                    "target": validation.normalized_target,
                },
            )

        # The provider message id is a deterministic simulator identifier. In
        # the next release line this hook can be swapped for a real transport
        # adapter without changing the service contract.
        return DispatchResult.sent(
            channel=self.channel_name,
            target_ref=target_ref,
            validation=validation,
            provider_name=self.provider_name,
            provider_message_id=self._provider_message_id(job, now_utc=now_utc),
            metadata={
                "provider": self.provider_name,
                "channel": self.channel_name,
                "target": validation.normalized_target,
            },
        )


@dataclass(frozen=True)
class EmailDispatcher(BaseReminderDispatcher):
    def __init__(self, *, channel_enabled: bool = True, provider_name: str = "email-simulator") -> None:
        super().__init__(
            channel_name="email",
            provider_name=provider_name,
            required_target_kind="email",
            channel_enabled=channel_enabled,
        )


@dataclass(frozen=True)
class VoiceDispatcher(BaseReminderDispatcher):
    def __init__(self, *, channel_enabled: bool = True, provider_name: str = "voice-simulator") -> None:
        super().__init__(
            channel_name="voice",
            provider_name=provider_name,
            required_target_kind="phone",
            channel_enabled=channel_enabled,
        )


@dataclass(frozen=True)
class RcsSmsDispatcher(BaseReminderDispatcher):
    def __init__(self, *, channel_enabled: bool = True, provider_name: str = "rcs-sms-simulator") -> None:
        super().__init__(
            channel_name="rcs_sms",
            provider_name=provider_name,
            required_target_kind="phone",
            channel_enabled=channel_enabled,
        )


@dataclass(frozen=True)
class ReminderDispatcherRegistry:
    """Stable channel registry used by the service layer."""

    dispatchers: dict[str, ReminderDispatcherProtocol]

    def get(self, channel_name: str) -> ReminderDispatcherProtocol:
        dispatcher = self.dispatchers.get(channel_name)
        if dispatcher is None:
            raise ValueError(f"Unsupported reminder delivery channel: {channel_name}")
        return dispatcher

    def validate_target(self, job: Any) -> DispatchTargetValidationResult:
        return self.get(getattr(job, "channel")).validate_target(job)

    def dispatch(self, job: Any, *, now_utc: Optional[datetime] = None) -> DispatchResult:
        return self.get(getattr(job, "channel")).dispatch(job, now_utc=now_utc)


def build_dispatcher_registry(
    *,
    email_enabled: bool,
    voice_enabled: bool,
    rcs_sms_enabled: bool,
) -> ReminderDispatcherRegistry:
    """Build the channel registry for one policy snapshot.

    The registry is intentionally policy-scoped so a policy update changes
    which channels are allowed without changing the job contract itself.
    """

    return ReminderDispatcherRegistry(
        dispatchers={
            "email": EmailDispatcher(channel_enabled=email_enabled),
            "voice": VoiceDispatcher(channel_enabled=voice_enabled),
            "rcs_sms": RcsSmsDispatcher(channel_enabled=rcs_sms_enabled),
        }
    )
