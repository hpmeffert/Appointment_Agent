from appointment_agent_shared.commands import LaunchAppointmentWorkflowCommand, ResolveCustomerCommand, SearchSlotsCommand
from appointment_agent_shared.enums import ErrorCategory, JourneyState
from appointment_agent_shared.events import CommandEnvelope, EventEnvelope
from appointment_agent_shared.ids import new_id
from appointment_agent_shared.models import AppointmentJourney, CandidateSlot, CustomerProfile
from appointment_agent_shared.validators import require_non_empty, validate_iso_datetime


def test_event_and_command_envelopes_serialize() -> None:
    event = EventEnvelope(
        event_type="appointment.search.requested",
        correlation_id="corr-1",
        trace_id="trace-1",
        tenant_id="demo",
        journey_id="journey-1",
        payload={"service_type": "consultation"},
    )
    command = CommandEnvelope(
        command_type="appointment.booking.create.requested",
        correlation_id="corr-1",
        trace_id="trace-1",
        tenant_id="demo",
        journey_id="journey-1",
        payload={"slot_id": "slot-1"},
    )

    assert event.model_dump()["journey_id"] == "journey-1"
    assert command.model_dump()["idempotency_key"].startswith("idem_")


def test_enum_stability() -> None:
    assert JourneyState.REMINDER_PENDING.value == "REMINDER_PENDING"
    assert ErrorCategory.DUPLICATE.value == "DUPLICATE"


def test_iso_datetime_validation() -> None:
    validate_iso_datetime("2026-03-27T12:00:00Z", "timestamp")


def test_empty_field_validation() -> None:
    try:
        require_non_empty("   ", "job_name")
    except ValueError as exc:
        assert "job_name" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_model_instantiation() -> None:
    journey = AppointmentJourney(journey_id="journey-1", tenant_id="demo", correlation_id="corr-1")
    customer = CustomerProfile(customer_id="C-1", mobile_number="+49123")
    slot = CandidateSlot(
        slot_id="slot-1",
        start_time="2026-03-27T10:00:00Z",
        end_time="2026-03-27T10:30:00Z",
        timezone="Europe/Berlin",
    )

    assert journey.current_state == JourneyState.NEW
    assert customer.customer_id == "C-1"
    assert slot.slot_id == "slot-1"


def test_command_instantiation() -> None:
    search = SearchSlotsCommand(
        tenant_id="demo",
        journey_id="journey-1",
        customer_id="C-1",
        service_type="consultation",
        duration_minutes=30,
        date_window_start="2026-03-27T00:00:00Z",
        date_window_end="2026-03-28T00:00:00Z",
        timezone="Europe/Berlin",
    )
    workflow = LaunchAppointmentWorkflowCommand(
        tenant_id="demo",
        correlation_id="corr-1",
        job_name="Appointment Confirmation",
        message_text="Confirmed",
        recipient_phone_numbers=["+49123"],
    )
    resolve = ResolveCustomerCommand(tenant_id="demo", phone="+49123")

    assert search.journey_id == "journey-1"
    assert workflow.to_numbers == ["+49123"]
    assert resolve.phone == "+49123"


def test_id_helper_behavior() -> None:
    identifier = new_id("journey")
    assert identifier.startswith("journey_")
