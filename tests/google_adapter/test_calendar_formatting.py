from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from appointment_agent_shared.db import SessionLocal

from google_adapter.v1_1_0_patch8a.google_adapter.service import GoogleBookingCreateRequest, GoogleBookingRescheduleRequest
from google_adapter.v1_3_6.google_adapter.service import GoogleAdapterServiceV136


def test_calendar_event_format() -> None:
    with SessionLocal() as session:
        service = GoogleAdapterServiceV136(session)
        event = service.build_calendar_event(
            {
                "appointment_type": "dentist",
                "customer_name": "Anna Berger",
                "address_lines": ["Anna Berger", "Berlin, Musterstrasse 12"],
                "context_label": "Rescheduled appointment confirmed",
                "date_label": "20 Apr 2026",
                "time_label": "11:30",
                "correlation_id": "corr-anna-001",
                "booking_reference": "book-anna-001",
                "appointment_id": "appt-anna-001",
                "address_id": "addr-anna-001",
                "linked_contact_reference_id": "contact-anna-001",
            }
        )

    assert event["summary"] == "Dentist Appointment – Anna Berger"
    assert "Address:" in event["description"]
    assert "Berlin, Musterstrasse 12" in event["description"]
    assert "Context:" in event["description"]
    assert event["metadata"]["correlation_id"] == "corr-anna-001"
    assert event["metadata"]["booking_reference"] == "book-anna-001"
    assert event["metadata"]["appointment_id"] == "appt-anna-001"
    assert event["metadata"]["address_id"] == "addr-anna-001"


def test_extract_customer_name_prefers_linked_address_fields() -> None:
    with SessionLocal() as session:
        service = GoogleAdapterServiceV136(session)

        assert (
            service.extract_customer_name(
                {
                    "linked_address_name": "Anna Berger",
                    "customer_name": "Checkup",
                    "linked_address_full_details": "Wrong Name | Berlin",
                }
            )
            == "Anna Berger"
        )
        assert (
            service.extract_customer_name(
                {
                    "linked_address_full_details": "Anna Berger | Berlin, Musterstrasse 12",
                }
            )
            == "Anna Berger"
        )


def test_v136_booking_create_and_reschedule_use_selected_address_metadata(monkeypatch) -> None:
    captured_events: list[dict] = []

    def _create_demo_event(**kwargs):
        captured_events.append(kwargs)
        booking_reference = kwargs["metadata"]["appointment_agent_booking_reference"]
        return SimpleNamespace(
            provider_reference=f"provider-{booking_reference}",
            event_id=f"event-{booking_reference}",
            html_link="https://calendar.google.test/event",
        )

    with SessionLocal() as session:
        service = GoogleAdapterServiceV136(session)
        monkeypatch.setattr(
            service,
            "_require_supported_mode",
            lambda mode: SimpleNamespace(mode="test", live_calendar_writes=True),
        )
        monkeypatch.setattr(
            service,
            "check_availability_patch8",
            lambda request: SimpleNamespace(
                slot_available=True,
                google_source="live",
                message="Selected slot is available.",
                selected_slot={},
                alternative_slots=[],
                technical_reason=None,
            ),
        )
        monkeypatch.setattr(service.gateway, "create_demo_event", _create_demo_event)
        monkeypatch.setattr(service.gateway, "get_event", lambda provider_reference: {"id": provider_reference})
        monkeypatch.setattr(service.gateway, "delete_event", lambda provider_reference: None)

        start_time = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=14)
        end_time = start_time + timedelta(minutes=45)
        create_result = service.create_booking_patch8(
            GoogleBookingCreateRequest(
                mode="test",
                slot_id="slot-anna-001",
                start_time=start_time,
                end_time=end_time,
                label="Tue, 05 May, 11:30",
                appointment_type="dentist",
                customer_name="Anna Berger",
                customer_email="anna.berger@example.com",
                customer_mobile="491705707716",
                booking_reference="book-anna-001",
                correlation_id="corr-anna-001",
                appointment_id="appt-anna-001",
                address_id="addr-anna-001",
                linked_contact_reference_id="contact-anna-001",
                linked_address_full_details="Anna Berger | Berlin, Musterstrasse 12",
                context_label="Rescheduled appointment confirmed",
            )
        )

        reschedule_result = service.reschedule_booking_patch8(
            GoogleBookingRescheduleRequest(
                mode="test",
                booking_reference="book-anna-001",
                provider_reference=create_result.provider_reference,
                slot_id="slot-anna-002",
                start_time=start_time + timedelta(days=1),
                end_time=end_time + timedelta(days=1),
                label="Wed, 06 May, 09:00",
                appointment_type="dentist",
                customer_name="Anna Berger",
                customer_email="anna.berger@example.com",
                customer_mobile="491705707716",
                correlation_id="corr-anna-001",
                appointment_id="appt-anna-001",
                address_id="addr-anna-001",
                linked_contact_reference_id="contact-anna-001",
                linked_address_full_details="Anna Berger | Berlin, Musterstrasse 12",
                context_label="Rescheduled appointment confirmed",
            )
        )

    assert create_result.success is True
    assert reschedule_result.success is True
    assert captured_events[0]["title"] == "Dentist Appointment – Anna Berger"
    assert "Address:" in captured_events[0]["description"]
    assert "Rescheduled appointment confirmed" in captured_events[0]["description"]
    assert captured_events[0]["metadata"]["appointment_agent_correlation_ref"] == "corr-anna-001"
    assert captured_events[0]["metadata"]["appointment_agent_booking_reference"] == "book-anna-001"
    assert captured_events[0]["metadata"]["appointment_agent_appointment_id"] == "appt-anna-001"
    assert captured_events[0]["metadata"]["appointment_agent_address_id"] == "addr-anna-001"
    assert captured_events[1]["title"] == "Dentist Appointment – Anna Berger"
    assert captured_events[1]["metadata"]["appointment_agent_contact_id"] == "contact-anna-001"


def test_v136_reschedule_uses_request_timezone_for_google_event_and_description(monkeypatch) -> None:
    captured_events: list[dict] = []

    def _create_demo_event(**kwargs):
        captured_events.append(kwargs)
        booking_reference = kwargs["metadata"]["appointment_agent_booking_reference"]
        return SimpleNamespace(
            provider_reference=f"provider-{booking_reference}",
            event_id=f"event-{booking_reference}",
            html_link="https://calendar.google.test/event",
        )

    with SessionLocal() as session:
        service = GoogleAdapterServiceV136(session)
        monkeypatch.setattr(
            service,
            "_require_supported_mode",
            lambda mode: SimpleNamespace(mode="test", live_calendar_writes=True),
        )
        monkeypatch.setattr(
            service,
            "check_availability_patch8",
            lambda request: SimpleNamespace(
                slot_available=True,
                google_source="live",
                message="Selected slot is available.",
                selected_slot={},
                alternative_slots=[],
                technical_reason=None,
            ),
        )
        monkeypatch.setattr(service.gateway, "create_demo_event", _create_demo_event)
        monkeypatch.setattr(service.gateway, "get_event", lambda provider_reference: {"id": provider_reference})
        monkeypatch.setattr(service.gateway, "delete_event", lambda provider_reference: None)

        berlin = ZoneInfo("Europe/Berlin")
        start_time = datetime(2026, 4, 21, 14, 0, tzinfo=berlin)
        end_time = start_time + timedelta(minutes=30)
        service.create_booking_patch8(
            GoogleBookingCreateRequest(
                mode="test",
                slot_id="slot-berlin-001",
                start_time=start_time,
                end_time=end_time,
                label="Tue, 21 Apr, 14:00",
                appointment_type="dentist",
                customer_name="Hans-Peter",
                customer_email="hans@example.com",
                customer_mobile="491705707716",
                booking_reference="book-berlin-001",
                correlation_id="corr-berlin-001",
                appointment_id="appt-berlin-001",
                address_id="addr-berlin-001",
                linked_contact_reference_id="contact-berlin-001",
                linked_address_full_details="Hans-Peter | Rochusstrasse 47 | 47975 Düsseldorf",
                context_label="Rescheduled appointment confirmed",
                timezone="Europe/Berlin",
            )
        )

    assert captured_events[0]["timezone_name"] == "Europe/Berlin"
    assert captured_events[0]["start_time"].hour == 14
    assert "Time: 14:00" in captured_events[0]["description"]
    assert "Rochusstrasse 47" in captured_events[0]["description"]


def test_v136_demo_generate_uses_linked_address_name_over_subtype() -> None:
    from fastapi.testclient import TestClient
    from appointment_agent_shared.main import app

    client = TestClient(app)
    response = client.post(
        "/api/google/v1.3.6/demo-calendar/generate",
        json={
            "mode": "simulation",
            "from_date": "2026-05-05",
            "to_date": "2026-05-06",
            "appointment_type": "dentist",
            "count": 1,
            "linked_address_id": "addr-anna-001",
            "linked_address_name": "Anna Berger",
            "linked_contact_reference_id": "contact-anna-001",
            "linked_address_full_details": "Anna Berger | Berlin, Musterstrasse 12",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["title"] == "Dentist Appointment – Anna Berger"
