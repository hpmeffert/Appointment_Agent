from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_resolution import (
    AppointmentCandidate,
    AppointmentResolutionContext,
    AppointmentResolutionResult,
    ExistingBookingResolver,
)


def test_resolution_context_supports_button_and_free_text_hints() -> None:
    context = AppointmentResolutionContext(
        booking_reference="book-123",
        correlation_id="corr-123",
        customer_phone="+491701234567",
        requested_action="reschedule",
        requested_datetime_hint="next Tuesday morning",
        raw_input_text="Can I move this to next Tuesday?",
        metadata={"source": "chat"},
    )

    assert context.booking_reference == "book-123"
    assert context.requested_datetime_hint == "next Tuesday morning"
    assert context.metadata["source"] == "chat"


def test_resolution_candidate_keeps_source_and_match_explanation() -> None:
    candidate = AppointmentCandidate(
        appointment_id="apt-1",
        booking_reference="book-1",
        provider_event_ref="provider-1",
        source="booking_store",
        source_trust_level="HIGH",
        match_basis=["booking_reference", "provider_event_ref"],
        match_score=1.0,
    )

    assert candidate.source == "booking_store"
    assert candidate.source_trust_level == "HIGH"
    assert candidate.match_basis == ["booking_reference", "provider_event_ref"]


def test_resolution_result_contract_supports_no_match() -> None:
    result = AppointmentResolutionResult(
        resolution_status="no_match",
        clarification_required=False,
        clarification_reason="no_candidates",
        notes=["No candidates available."],
    )

    assert result.resolution_status == "no_match"
    assert result.selected is None
    assert result.notes == ["No candidates available."]


def test_finalize_result_returns_no_match_for_zero_candidates() -> None:
    resolver = ExistingBookingResolver()

    result = resolver._finalize_result([])

    assert result.resolution_status == "no_match"
    assert result.selected is None
    assert result.clarification_required is False
    assert result.clarification_reason == "no_candidates"


def test_finalize_result_returns_single_match_for_high_trust_candidate() -> None:
    resolver = ExistingBookingResolver()
    candidate = AppointmentCandidate(
        booking_reference="book-1",
        source="journey_store",
        source_trust_level="HIGH",
        match_basis=["booking_reference"],
    )

    result = resolver._finalize_result([candidate])

    assert result.resolution_status == "single_match"
    assert result.selected == candidate
    assert result.clarification_required is False
    assert result.match_basis == ["booking_reference"]


def test_finalize_result_requires_clarification_for_low_trust_single_candidate() -> None:
    resolver = ExistingBookingResolver()
    candidate = AppointmentCandidate(
        booking_reference="book-weak",
        source="heuristic_scan",
        source_trust_level="LOW",
        match_basis=["customer_name", "future_time_window"],
    )

    result = resolver._finalize_result([candidate])

    assert result.resolution_status == "single_match"
    assert result.selected == candidate
    assert result.clarification_required is True
    assert result.clarification_reason == "low_trust_single_candidate"


def test_finalize_result_returns_multiple_matches_for_many_candidates() -> None:
    resolver = ExistingBookingResolver()
    first = AppointmentCandidate(
        booking_reference="book-1",
        source="booking_store",
        source_trust_level="HIGH",
        match_basis=["contact_id"],
    )
    second = AppointmentCandidate(
        booking_reference="book-2",
        source="calendar_records",
        source_trust_level="MEDIUM",
        match_basis=["contact_id", "future_window"],
    )

    result = resolver._finalize_result([first, second])

    assert result.resolution_status == "multiple_matches"
    assert result.selected is None
    assert result.clarification_required is True
    assert result.clarification_reason == "multiple_candidates"
    assert result.match_basis == ["contact_id", "future_window"]


def test_resolve_uses_empty_stage_skeleton_without_runtime_side_effects() -> None:
    resolver = ExistingBookingResolver()

    result = resolver.resolve(AppointmentResolutionContext(booking_reference="book-1"))

    assert result.resolution_status == "no_match"
    assert result.selected is None
