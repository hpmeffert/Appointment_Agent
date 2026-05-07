from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

from .appointment_resolution import AppointmentCandidate


MutationStrategy = Literal["patch_existing", "replace_existing", "no_mutation", "abort_due_to_risk"]


@dataclass
class AppointmentMutationContext:
    requested_action: str
    has_new_schedule: bool = False
    force_replace_existing: bool = False
    provider_requires_replace: bool = False
    current_provider_reference: Optional[str] = None
    booking_reference: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MutationDecision:
    strategy: MutationStrategy
    reason: str
    notes: list[str] = field(default_factory=list)


def determine_mutation_strategy(
    resolved_appointment: Optional[AppointmentCandidate],
    requested_action: str,
    context: AppointmentMutationContext,
) -> MutationDecision:
    if requested_action in {"confirm", "keep"}:
        return MutationDecision(
            strategy="no_mutation",
            reason="confirm_existing_requires_no_provider_mutation",
            notes=["Existing appointment confirmation should not create or replace calendar events."],
        )

    if resolved_appointment is None:
        return MutationDecision(
            strategy="abort_due_to_risk",
            reason="resolved_target_missing",
            notes=["No resolved appointment target was available for mutation."],
        )

    booking_reference = resolved_appointment.booking_reference or context.booking_reference
    provider_reference = resolved_appointment.provider_event_ref or context.current_provider_reference

    if requested_action == "cancel":
        if not booking_reference or not provider_reference:
            return MutationDecision(
                strategy="abort_due_to_risk",
                reason="cancel_requires_booking_and_provider_reference",
                notes=["Cancellation requires both booking_reference and provider_event_ref."],
            )
        return MutationDecision(
            strategy="patch_existing",
            reason="cancel_existing_direct_target",
            notes=["Cancellation operates directly on the resolved existing appointment."],
        )

    if requested_action == "reschedule":
        if not booking_reference:
            return MutationDecision(
                strategy="abort_due_to_risk",
                reason="reschedule_requires_booking_reference",
                notes=["Reschedule needs a stable booking_reference before mutation."],
            )
        if context.force_replace_existing or context.provider_requires_replace:
            if not context.has_new_schedule:
                return MutationDecision(
                    strategy="abort_due_to_risk",
                    reason="replace_requires_new_schedule",
                    notes=["Replace strategy was requested but no new schedule payload was supplied."],
                )
            return MutationDecision(
                strategy="replace_existing",
                reason="replace_explicitly_required",
                notes=["Replacement was explicitly requested or required by provider/business rules."],
            )
        if provider_reference and context.has_new_schedule:
            return MutationDecision(
                strategy="patch_existing",
                reason="provider_reference_valid_for_patch",
                notes=["Reschedule defaults to patch/update when a mutable provider reference is available."],
            )
        return MutationDecision(
            strategy="abort_due_to_risk",
            reason="patch_requires_provider_reference",
            notes=["Patch/update was not safe because provider_event_ref was missing and replace was not explicitly allowed."],
        )

    return MutationDecision(
        strategy="abort_due_to_risk",
        reason="unsupported_action_for_mutation_policy",
        notes=[f"Unsupported mutation action '{requested_action}' reached mutation policy."],
    )
