from __future__ import annotations

from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_mutation_policy import (
    AppointmentMutationContext,
    MutationDecision,
    determine_mutation_strategy,
)
from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_resolution import AppointmentCandidate


def _candidate() -> AppointmentCandidate:
    return AppointmentCandidate(
        appointment_id="apt-123",
        booking_reference="book-123",
        provider_event_ref="provider-123",
        correlation_id="corr-123",
        customer_name="Hans-Peter",
        appointment_type="dentist",
        address_id="addr-123",
        status="BOOKED",
        source="journey_store",
        source_trust_level="HIGH",
        match_basis=["booking_reference"],
    )


def test_mutation_policy_prefers_patch_for_reschedule_when_provider_reference_is_valid() -> None:
    decision = determine_mutation_strategy(
        _candidate(),
        "reschedule",
        AppointmentMutationContext(
            requested_action="reschedule",
            has_new_schedule=True,
            current_provider_reference="provider-123",
            booking_reference="book-123",
        ),
    )

    assert decision.strategy == "patch_existing"
    assert decision.reason == "provider_reference_valid_for_patch"


def test_mutation_policy_uses_replace_when_explicitly_required() -> None:
    decision = determine_mutation_strategy(
        _candidate(),
        "reschedule",
        AppointmentMutationContext(
            requested_action="reschedule",
            has_new_schedule=True,
            force_replace_existing=True,
            current_provider_reference="provider-123",
            booking_reference="book-123",
        ),
    )

    assert decision.strategy == "replace_existing"
    assert decision.reason == "replace_explicitly_required"


def test_mutation_policy_returns_no_mutation_for_confirm_existing() -> None:
    decision = determine_mutation_strategy(
        _candidate(),
        "keep",
        AppointmentMutationContext(
            requested_action="keep",
            booking_reference="book-123",
            current_provider_reference="provider-123",
        ),
    )

    assert decision.strategy == "no_mutation"
    assert decision.reason == "confirm_existing_requires_no_provider_mutation"


def test_mutation_policy_aborts_when_required_identifiers_are_missing() -> None:
    candidate = _candidate()
    candidate.provider_event_ref = None
    decision = determine_mutation_strategy(
        candidate,
        "cancel",
        AppointmentMutationContext(
            requested_action="cancel",
            booking_reference="book-123",
            current_provider_reference=None,
        ),
    )

    assert decision.strategy == "abort_due_to_risk"
    assert decision.reason == "cancel_requires_booking_and_provider_reference"


def test_mutation_policy_notes_explain_strategy() -> None:
    decision = determine_mutation_strategy(
        _candidate(),
        "reschedule",
        AppointmentMutationContext(
            requested_action="reschedule",
            has_new_schedule=True,
            force_replace_existing=True,
            current_provider_reference="provider-123",
            booking_reference="book-123",
        ),
    )

    assert isinstance(decision, MutationDecision)
    assert decision.notes
