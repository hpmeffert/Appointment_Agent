from __future__ import annotations

from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types

import pytest


ROOT = Path(__file__).resolve().parents[3]
REMINDER_PACKAGE_ROOT = ROOT / "apps" / "reminder_scheduler" / "v1_3_0" / "reminder_scheduler"


def _ensure_namespace(name: str, path: Path) -> None:
    """Register a namespace package so we can load submodules without side effects."""

    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_module(module_name: str, file_name: str):
    """Load a module directly from disk without importing the package __init__."""

    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = spec_from_file_location(module_name, REMINDER_PACKAGE_ROOT / file_name)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive loader guard
        raise RuntimeError(f"Cannot load module {module_name}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ensure_namespace("reminder_scheduler", ROOT / "apps" / "reminder_scheduler")
_ensure_namespace("reminder_scheduler.v1_3_0", ROOT / "apps" / "reminder_scheduler" / "v1_3_0")
_ensure_namespace("reminder_scheduler.v1_3_0.reminder_scheduler", REMINDER_PACKAGE_ROOT)

schemas = _load_module("reminder_scheduler.v1_3_0.reminder_scheduler.schemas", "schemas.py")
validation = _load_module("reminder_scheduler.v1_3_0.reminder_scheduler.validation", "validation.py")
calculator = _load_module("reminder_scheduler.v1_3_0.reminder_scheduler.calculator", "calculator.py")

ReminderPolicySchema = schemas.ReminderPolicySchema
ReminderPreviewRequest = schemas.ReminderPreviewRequest
calculate_preview = calculator.calculate_preview
calculate_schedule_items = calculator.calculate_schedule_items
validate_policy = validation.validate_policy


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_calculate_schedule_items_manual_mode_uses_explicit_hours() -> None:
    policy = ReminderPolicySchema(
        tenant_id="tenant-1",
        policy_name="manual",
        mode="manual",
        reminder_count=3,
        first_reminder_hours_before=72,
        second_reminder_hours_before=48,
        third_reminder_hours_before=24,
        channel_email_enabled=True,
        channel_voice_enabled=True,
        channel_rcs_sms_enabled=False,
    )

    items = calculate_schedule_items(policy, _utc(2026, 4, 8, 12), appointment_id="apt-1")

    assert [item.reminder_sequence for item in items] == [1, 2, 3]
    assert [item.hours_before_appointment for item in items] == [72, 48, 24]
    assert [item.channel for item in items] == ["email", "voice", "voice"]
    assert [item.scheduled_for_utc for item in items] == [
        _utc(2026, 4, 5, 12),
        _utc(2026, 4, 6, 12),
        _utc(2026, 4, 7, 12),
    ]
    assert items[0].reminder_label == "Reminder 1 for apt-1"


def test_calculate_preview_auto_distributed_builds_even_timeline() -> None:
    policy = ReminderPolicySchema(
        tenant_id="tenant-2",
        policy_name="auto",
        mode="auto_distributed",
        reminder_count=3,
        max_span_between_first_and_last_reminder_hours=24,
        last_reminder_gap_before_appointment_hours=24,
        channel_email_enabled=False,
        channel_voice_enabled=False,
        channel_rcs_sms_enabled=False,
    )
    request = ReminderPreviewRequest(
        tenant_id="tenant-2",
        appointment_id="apt-2",
        appointment_start_utc=_utc(2026, 4, 8, 12),
        policy=policy,
    )

    preview = calculate_preview(request)

    assert preview.appointment_id == "apt-2"
    assert preview.appointment_start_utc == _utc(2026, 4, 8, 12)
    assert [item.hours_before_appointment for item in preview.items] == [48, 36, 24]
    assert [item.channel for item in preview.items] == ["email", "email", "email"]
    assert preview.warnings == [
        "No reminder channel is enabled. Email will be used as a safe fallback for previews."
    ]


def test_validate_policy_rejects_missing_manual_hours() -> None:
    policy = ReminderPolicySchema(
        mode="manual",
        reminder_count=2,
        first_reminder_hours_before=24,
        second_reminder_hours_before=None,
        channel_email_enabled=True,
    )

    with pytest.raises(ValueError, match="Manual reminder mode requires explicit reminder hour values"):
        validate_policy(policy)


def test_validate_policy_rejects_too_small_auto_span() -> None:
    policy = ReminderPolicySchema(
        mode="auto_distributed",
        reminder_count=3,
        max_span_between_first_and_last_reminder_hours=1,
        last_reminder_gap_before_appointment_hours=24,
        channel_email_enabled=True,
    )

    with pytest.raises(ValueError, match="Auto distributed reminder mode needs a larger span"):
        validate_policy(policy)

