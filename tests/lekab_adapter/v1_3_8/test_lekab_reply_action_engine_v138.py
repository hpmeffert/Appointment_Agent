import json
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.main import app
from appointment_agent_shared.models import MessageRecord
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.repositories import CallbackRepository, JourneyRepository, MessageRepository
from demo_monitoring_ui.v1_3_9.demo_monitoring_ui.scenario_context import DemoScenarioContextUpdate
from lekab_adapter.v1_3_8.lekab_adapter.service import LekabReplyActionService


def _save_ready_settings(client: TestClient) -> None:
    response = client.post(
        "/api/lekab/v1.3.8/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-v138-demo",
                "environment_name": "Reply Engine Demo",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "webhook_fetch_url": "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "rime_api_key": "real-rime-key",
                "webhook_api_key": "real-webhook-key",
                "test_recipient_address": "491705707716",
            }
        },
    )
    assert response.status_code == 200


def _create_booked_journey(client: TestClient) -> tuple[str, str, str]:
    suffix = uuid4().hex[:8]
    journey_id = f"journey-v138-callback-{suffix}"
    correlation_id = f"corr-v138-callback-{suffix}"
    start = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-LEKAB-138",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
        },
    )
    assert start.status_code == 200
    slot_id = start.json()["slot_options"][0]["slot_id"]
    selected = client.post(
        "/api/orchestrator/v1.0.1/journeys/select",
        json={"journey_id": journey_id, "tenant_id": "demo", "correlation_id": correlation_id, "slot_id": slot_id},
    )
    assert selected.status_code == 200
    confirmed = client.post(
        "/api/orchestrator/v1.0.1/journeys/confirm",
        json={
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "booking": {
                "tenant_id": "demo",
                "journey_id": journey_id,
                "customer_id": "C-LEKAB-138",
                "slot_id": slot_id,
                "calendar_target": "advisor@example.com",
                "title": "Consultation",
                "description": "Initial booking",
                "timezone": "Europe/Berlin",
            },
            "dispatch": {
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "job_name": "Appointment Confirmation",
                "message": "Confirmed",
                "to_numbers": ["+49123"],
            },
        },
    )
    assert confirmed.status_code == 200
    reminder = client.post(
        "/api/orchestrator/v1.0.1/journeys/remind",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "to_numbers": ["+49123"],
        },
    )
    assert reminder.status_code == 200
    return journey_id, correlation_id, slot_id


def test_lekab_v138_settings_route_is_available() -> None:
    client = TestClient(app)
    response = client.get("/api/lekab/v1.3.8/settings/rcs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1.3.8"
    assert payload["settings"]["values"]["test_recipient_address"] == "491705707716"


def test_lekab_v138_fetch_latest_callback_maps_next_week_to_action(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    event_bus.events.clear()

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": "reply-next-week",
                "content": json.dumps(
                    {
                        "id": "reply-2",
                        "time": "2026-04-09T10:00:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "text": "next week works for me",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)
    monkeypatch.setattr(
        "lekab_adapter.v1_3_8.lekab_adapter.service.LekabReplyActionService._load_dynamic_slots_for_range",
        lambda self, from_date_value, to_date_value, appointment_type: [
            {
                "slot_id": "google-slot-1",
                "start": "2026-04-27T09:00:00+00:00",
                "end": "2026-04-27T09:30:00+00:00",
                "label": "Mon, 27 Apr, 09:00",
                "available": True,
                "calendar_provider": "google",
            },
            {
                "slot_id": "google-slot-2",
                "start": "2026-04-27T11:30:00+00:00",
                "end": "2026-04-27T12:00:00+00:00",
                "label": "Mon, 27 Apr, 11:30",
                "available": True,
                "calendar_provider": "google",
            },
        ],
    )

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_event_type"] == "message.reply_received"
    assert payload["reply_intent"] == "appointment_next_week"
    assert payload["action_candidate"]["action_type"] == "appointment.find_slot_next_week_requested"
    assert payload["interpretation_state"] == "safe"
    assert payload["resolved_action"]["action_type"] == "appointment.find_slot_next_week_requested"
    assert payload["resolved_action"]["resolution_state"] in {"safe", "review"}
    assert any(event.event_type == "CommunicationReplyNormalized" for event in event_bus.events)
    assert any(event.event_type == "AppointmentActionRequested" for event in event_bus.events)
    assert any(event.event_type == "AppointmentActionResolved" for event in event_bus.events)
    assert any(event.event_type in {"AppointmentActionReviewRequired", "AppointmentActionExecutionRequested"} for event in event_bus.events)


def test_lekab_v138_seturl_route_uses_runtime_callback_urls(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    client.post(
        "/api/lekab/v1.3.8/settings/rcs",
        json={
            "values": {
                "callback_url": "https://demo.example.test/api/lekab/callback/incoming",
                "receipt_callback_url": "https://demo.example.test/api/lekab/callback/receipt",
            }
        },
    )

    captured = {}

    class DummyResponse:
        status_code = 200
        text = '{"configured": true}'

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/seturl")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["incoming_url"] == "https://demo.example.test/api/lekab/callback/incoming"
    assert payload["receipt_url"] == "https://demo.example.test/api/lekab/callback/receipt"
    assert captured["url"].endswith("/seturl")
    assert captured["json"]["channels"] == "RCS"
    assert captured["json"]["incomingtype"] == "JSON"
    assert captured["json"]["receipttype"] == "JSON"
    assert captured["json"]["incomingurl"] == "https://demo.example.test/api/lekab/callback/incoming"
    assert captured["json"]["receipturl"] == "https://demo.example.test/api/lekab/callback/receipt"


def test_lekab_v138_fetch_latest_callback_maps_slot_label_to_safe_action(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": "reply-slot-safe",
                "content": json.dumps(
                    {
                        "id": "reply-3",
                        "time": "2026-04-09T10:30:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "text": "05 May, 16:00",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply_intent"] == "slot_selection"
    assert payload["action_candidate"]["action_type"] == "appointment.slot_selected"
    assert payload["interpretation_state"] == "safe"
    assert "16:00" in payload["reply_datetime_candidates"]


def test_lekab_v138_fetch_latest_callback_maps_this_week_to_action(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": "reply-this-week",
                "content": json.dumps(
                    {
                        "id": "reply-5",
                        "time": "2026-04-09T12:00:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "text": "this week",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply_intent"] == "appointment_this_week"
    assert payload["action_candidate"]["action_type"] == "appointment.find_slot_this_week_requested"


def test_lekab_v138_fetch_latest_callback_maps_this_month_to_action(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": "reply-this-month",
                "content": json.dumps(
                    {
                        "id": "reply-6",
                        "time": "2026-04-09T12:30:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "text": "this month",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply_intent"] == "appointment_this_month"
    assert payload["action_candidate"]["action_type"] == "appointment.find_slot_this_month_requested"


def test_lekab_v138_fetch_latest_callback_maps_ordinal_slot_to_ambiguous_action(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    callback_uuid = f"reply-slot-ordinal-{uuid4().hex[:8]}"

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": callback_uuid,
                "content": json.dumps(
                    {
                        "id": "reply-4",
                        "time": "2026-04-09T11:00:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "text": "the first one",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply_intent"] == "slot_selection"
    assert payload["action_candidate"]["action_type"] == "appointment.slot_selected"
    assert payload["interpretation_state"] == "ambiguous"
    assert payload["action_candidate"]["parameters"]["ordinal_index"] == 1

    monitor = client.get("/api/lekab/v1.3.8/monitor").json()
    latest = next(message for message in monitor["messages"] if message["message_id"] == f"msg-in-{callback_uuid}")
    assert latest["metadata"]["action_type"] == "appointment.slot_selected"
    assert latest["metadata"]["interpretation_state"] == "ambiguous"


def test_lekab_v138_fetch_latest_callback_resolves_address_and_appointment_context(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    callback_uuid = f"reply-linked-context-{uuid4().hex[:8]}"

    created = client.post(
        "/api/addresses/v1.3.9",
        json={
            "address_id": "addr-linked-001",
            "display_name": "Anna Berger",
            "city": "Berlin",
            "phone": "491705707716",
            "correlation_ref": "corr-addr-linked-001",
        },
    )
    assert created.status_code == 200

    linked = client.post(
        "/api/addresses/v1.3.9/link-to-appointment",
        json={
            "address_id": "addr-linked-001",
            "appointment_external_id": "appt-linked-001",
            "booking_reference": "book-linked-001",
            "calendar_ref": "gcal-linked-001",
            "correlation_ref": "corr-addr-linked-001",
        },
    )
    assert linked.status_code == 200

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": callback_uuid,
                "content": json.dumps(
                    {
                        "id": "reply-5",
                        "time": "2026-04-09T11:30:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "status": "DELIVERED",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["address_id"] == "addr-linked-001"
    assert payload["appointment_id"] == "appt-linked-001"
    assert payload["correlation_ref"] == "corr-addr-linked-001"
    assert payload["resolved_action"] == {}

    monitor = client.get("/api/lekab/v1.3.8/monitor").json()
    latest = next(message for message in monitor["messages"] if message["message_id"] == f"msg-in-{callback_uuid}")
    assert latest["address_id"] == "addr-linked-001"
    assert latest["appointment_id"] == "appt-linked-001"


def test_lekab_v138_fetch_latest_callback_resolves_safe_cancel_to_execution_request(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    event_bus.events.clear()

    created = client.post(
        "/api/addresses/v1.3.9",
        json={
            "address_id": "addr-safe-001",
            "display_name": "Safe Cancel",
            "city": "Berlin",
            "phone": "491705707716",
            "correlation_ref": "corr-safe-001",
        },
    )
    assert created.status_code == 200
    linked = client.post(
        "/api/addresses/v1.3.9/link-to-appointment",
        json={
            "address_id": "addr-safe-001",
            "appointment_external_id": "appt-safe-001",
            "booking_reference": "book-safe-001",
            "calendar_ref": "gcal-safe-001",
            "correlation_ref": "corr-safe-001",
        },
    )
    assert linked.status_code == 200

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": "reply-safe-cancel",
                "content": json.dumps(
                    {
                        "id": "reply-6",
                        "time": "2026-04-09T12:00:00Z",
                        "channel": "RCS",
                        "from": "customer",
                        "to": "491705707716",
                        "text": "cancel please",
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["resolved_action"]["action_type"] == "appointment.cancel_requested"
    assert payload["resolved_action"]["resolution_state"] == "safe"
    assert payload["resolved_action"]["execution_requested"] is True
    assert any(event.event_type == "AppointmentActionExecutionRequested" for event in event_bus.events)


def test_lekab_v138_real_callback_route_updates_journey_context_and_deduplicates() -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-callback-001",
            "booking_reference": "book-real-callback-001",
            "correlation_ref": correlation_id,
            "current_step": "awaiting_customer_reply",
            "status": "reminder_pending",
        },
    )
    assert context_updated.status_code == 200

    event_id = f"evt-real-confirm-{uuid4().hex[:8]}"
    callback_payload = {
        "event_id": event_id,
        "event": "INCOMING",
        "incoming_type": "RESPONSE",
        "incoming_data": "confirm_appointment",
        "correlation_id": correlation_id,
        "appointment_id": "appt-real-callback-001",
        "booking_reference": "book-real-callback-001",
        "address_id": "addr-demo-001",
        "from": "491705707716",
    }
    accepted = client.post("/api/lekab/callback", json=callback_payload)
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True

    duplicate = client.post("/api/lekab/callback", json=callback_payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["accepted"] is True

    deadline = time.time() + 1.0
    final_state = None
    inbound = None
    while time.time() < deadline:
        session = SessionLocal()
        try:
            journeys = JourneyRepository(session)
            callbacks = CallbackRepository(session)
            messages = MessageRepository(session)

            journey = journeys.get(journey_id)
            inbound = messages.get(f"msg-in-{event_id}")
            if journey is not None:
                final_state = journey.current_state
            if final_state == "BOOKED" and callbacks.exists(event_id) and inbound is not None:
                break
        finally:
            session.close()
        time.sleep(0.05)

    assert final_state == "BOOKED"
    assert inbound is not None
    assert inbound.message_type == "reply_button"
    assert inbound.correlation_ref == correlation_id
    assert inbound.metadata_payload["resolved_action"] == "keep"

    context = client.get("/api/demo-monitoring/v1.3.9/scenario-context").json()
    assert context["mode"] == "real"
    assert context["current_step"] == "confirmation_complete"
    assert context["status"] == "confirmed"
    assert context["metadata"]["real_callback"]["selected_action"] == "keep"
    assert context["metadata"]["customer_journey_message"]["text"] == "Your appointment is confirmed."

    payload = client.get("/api/demo-monitoring/v1.3.9/payload?lang=en").json()
    assert payload["messages_customer_journey"]["mode"] == "real"
    assert payload["messages_customer_journey"]["selected_action"] == "keep"
    assert any(item.get("selected") for item in payload["messages_customer_journey"]["suggestion_buttons"])
    assert any(item.get("selected") for item in payload["messages_customer_journey"]["real_channel_payload"]["suggestions"])


def test_lekab_v138_real_callback_route_accepts_get_query_payload() -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-callback-get-001",
            "booking_reference": "book-real-callback-get-001",
            "correlation_ref": correlation_id,
            "current_step": "awaiting_customer_reply",
            "status": "reminder_pending",
        },
    )
    assert context_updated.status_code == 200

    event_id = f"evt-real-reschedule-get-{uuid4().hex[:8]}"
    accepted = client.get(
        f"/api/lekab/callback?event_id={event_id}&event=INCOMING&incoming_type=GET&incoming_data=reschedule_appointment"
        f"&correlation_id={correlation_id}&appointment_id=appt-real-callback-get-001&booking_reference=book-real-callback-get-001"
        "&address_id=addr-demo-001&from=491705707716&reply_label=Reschedule&callback_transport=get"
    )
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True

    deadline = time.time() + 1.0
    inbound = None
    while time.time() < deadline:
        session = SessionLocal()
        try:
            messages = MessageRepository(session)
            inbound = messages.get(f"msg-in-{event_id}")
            if inbound is not None:
                break
        finally:
            session.close()
        time.sleep(0.05)

    assert inbound is not None
    assert inbound.metadata_payload["resolved_action"] == "reschedule"

    context = client.get("/api/demo-monitoring/v1.3.9/scenario-context").json()
    assert context["mode"] == "real"
    assert context["current_step"] == "reschedule_requested"
    assert context["status"] == "action_requested"
    assert context["metadata"]["real_callback"]["selected_action"] == "reschedule"
    assert context["metadata"]["customer_journey_message"]["text"] == "Choose the preferred scheduling window."
    assert context["metadata"]["customer_journey_message"]["real_channel_payload"]["suggestions"]


def test_lekab_v138_fetch_latest_callback_bridges_webhook_reply_into_demo_context(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    callback_uuid = f"reply-fetch-bridge-confirm-{uuid4().hex[:8]}"

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-manual-fetch-001",
            "booking_reference": "book-manual-fetch-001",
            "correlation_ref": "corr-addr-demo-001",
            "current_step": "awaiting_customer_reply",
            "status": "reminder_pending",
        },
    )
    assert context_updated.status_code == 200

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "uuid": callback_uuid,
                "content": json.dumps(
                    {
                        "id": callback_uuid,
                        "time": "2026-04-09T12:00:00Z",
                        "channel": "RCS",
                        "from": "491705707716",
                        "to": "491705707716",
                        "selectedSuggestion": {"value": "confirm_appointment", "label": "Confirm"},
                    }
                ),
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["real_callback_bridge"]["accepted"] is True
    assert payload["real_callback_bridge"].get("resolved_action") in {None, "keep"}

    context = client.get("/api/demo-monitoring/v1.3.9/scenario-context").json()
    assert context["mode"] == "real"
    assert context["current_step"] == "confirmation_complete"
    assert context["status"] == "confirmed"
    assert context["metadata"]["real_callback"]["selected_action"] == "keep"


def test_lekab_v138_fetch_latest_callback_uses_requests_feed_and_bridges_selected_suggestion(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    callback_uuid = f"reply-fetch-bridge-reschedule-{uuid4().hex[:8]}"

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-manual-fetch-002",
            "booking_reference": "book-manual-fetch-002",
            "correlation_ref": "corr-addr-demo-001",
            "current_step": "awaiting_customer_reply",
            "status": "reminder_pending",
        },
    )
    assert context_updated.status_code == 200

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "data": [
                    {
                        "uuid": "status-record-1",
                        "created_at": "2026-04-09 11:59:00",
                        "method": "POST",
                        "url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                        "content": json.dumps({"status": "READ", "to": "491705707716"}),
                    },
                    {
                        "uuid": callback_uuid,
                        "created_at": "2026-04-09 12:00:00",
                        "method": "GET",
                        "url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6?correlation_id=corr-addr-demo-001&from=491705707716",
                        "query": {
                            "correlation_id": "corr-addr-demo-001",
                            "from": "491705707716",
                            "selectedSuggestion": json.dumps({"value": "reschedule_appointment", "label": "Reschedule"}),
                        },
                        "content": "",
                    },
                ]
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_preview"]["url"].endswith("/requests?sorting=newest&per_page=25")
    assert payload["callback_source_method"] == "GET"
    assert payload["callback_transport"] == "get"
    assert payload["real_callback_bridge"]["accepted"] is True
    assert payload["real_callback_bridge"]["normalized_callback"]["reply_payload"] == "reschedule_appointment"
    assert payload["real_callback_bridge"]["normalized_callback"]["reply_label"] == "Reschedule"

    context = client.get("/api/demo-monitoring/v1.3.9/scenario-context").json()
    assert context["mode"] == "real"
    assert context["current_step"] == "reschedule_requested"
    assert context["status"] == "action_requested"
    assert context["metadata"]["real_callback"]["selected_action"] == "reschedule"
    assert context["metadata"]["customer_journey_message"]["text"] == "Choose the preferred scheduling window."


def test_lekab_v138_fetch_latest_callback_processes_unseen_next_week_and_sends_date_follow_up(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    confirm_uuid = f"confirm-{uuid4().hex[:8]}"

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-manual-fetch-003",
            "booking_reference": "book-manual-fetch-003",
            "correlation_ref": "corr-addr-demo-001",
            "current_step": "reschedule_requested",
            "status": "action_requested",
        },
    )
    assert context_updated.status_code == 200

    class DummyResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "data": [
                    {
                        "uuid": "status-read-1",
                        "created_at": "2026-04-09 11:59:00",
                        "sorting": 1,
                        "method": "POST",
                        "url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                        "content": json.dumps({"status": "READ", "to": "491705707716"}),
                    },
                    {
                        "uuid": f"next-week-{uuid4().hex[:8]}",
                        "created_at": "2026-04-09 12:00:00",
                        "sorting": 2,
                        "method": "POST",
                        "url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                        "content": json.dumps(
                            {
                                "id": "reply-next-week",
                                "time": "2026-04-09T12:00:00Z",
                                "channel": "RCS",
                                "from": "491705707716",
                                "to": "d_sselvolt_meldungen_4nht5tub_agent",
                                "type": "REPLY",
                                "text": "next_week",
                                "buttontext": "Next week",
                            }
                        ),
                    },
                    {
                        "uuid": confirm_uuid,
                        "created_at": "2026-04-09 12:00:30",
                        "sorting": 3,
                        "method": "POST",
                        "url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                        "content": json.dumps(
                            {
                                "id": "reply-confirm",
                                "time": "2026-04-09T12:00:30Z",
                                "channel": "RCS",
                                "from": "491705707716",
                                "to": "d_sselvolt_meldungen_4nht5tub_agent",
                                "type": "REPLY",
                                "text": "confirm",
                                "buttontext": "Confirm",
                            }
                        ),
                    },
                ]
            }

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers=None):
            return DummyResponse()

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    session = SessionLocal()
    try:
        CallbackRepository(session).record(
            event_id=confirm_uuid,
            event_type="INCOMING",
            correlation_id="corr-addr-demo-001",
            payload={"source": "test-preprocessed-confirm"},
            is_duplicate=False,
        )
    finally:
        session.close()

    response = client.post("/api/lekab/v1.3.8/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    processed_callbacks = payload.get("processed_callbacks") or []
    bridge_source = processed_callbacks[-1]["bridge_result"] if processed_callbacks else payload["real_callback_bridge"]
    callback_source = processed_callbacks[-1]["callback_payload"] if processed_callbacks else None
    if callback_source is not None:
        assert callback_source["incoming_data"] == "next_week"
    assert bridge_source["accepted"] is True
    assert bridge_source["normalized_callback"]["reply_payload"] == "next_week"

    context = client.get("/api/demo-monitoring/v1.3.9/scenario-context").json()
    assert context["mode"] == "real"
    assert context["current_step"] == "relative_choice_complete"
    assert context["status"] == "awaiting_date_choice"
    assert context["metadata"]["real_callback"]["selected_action"] == "next_week"
    assert context["metadata"]["customer_journey_message"]["text"] == "Choose one of the proposed dates."


def test_lekab_v138_next_week_real_callback_with_existing_journey_sends_date_follow_up(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    _journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-next-week",
            "booking_reference": "book-real-next-week",
            "correlation_ref": correlation_id,
            "current_step": "reschedule_requested",
            "status": "action_requested",
        },
    )
    assert context_updated.status_code == 200

    class DummyResponse:
        status_code = 200
        text = '{"resultText":"At least one message sent OK","sent":[{"id":"provider-follow-up-1","result":"OK"}]}'

        def json(self):
            return {"resultText": "At least one message sent OK", "sent": [{"id": "provider-follow-up-1", "result": "OK"}]}

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    session = SessionLocal()
    try:
        service = LekabReplyActionService(session, mock_mode=False)
        result = service.process_provider_callback(
            {
                "event_id": f"next-week-journey-{uuid4().hex[:8]}",
                "event": "INCOMING",
                "incoming_type": "POST",
                "incoming_data": "next_week",
                "correlation_id": correlation_id,
                "correlation_ref": correlation_id,
                "phone_number": "491705707716",
                "from": "491705707716",
                "reply_label": "Next week",
                "callback_transport": "post",
                "received_at": "2026-04-20T08:27:30Z",
                "source": "test",
            }
        )
        assert result["accepted"] is True
        assert result["follow_up_message"]["text"] == "Choose one of the proposed dates."
    finally:
        session.close()


def test_lekab_v138_next_week_real_callback_uses_dynamic_google_dates(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    _journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-dynamic-next-week",
            "booking_reference": "book-real-dynamic-next-week",
            "correlation_ref": correlation_id,
            "current_step": "reschedule_requested",
            "status": "action_requested",
        },
    )
    assert context_updated.status_code == 200

    class DummyResponse:
        status_code = 200
        text = '{"resultText":"At least one message sent OK","sent":[{"id":"provider-follow-up-dynamic","result":"OK"}]}'

        def json(self):
            return {"resultText": "At least one message sent OK", "sent": [{"id": "provider-follow-up-dynamic", "result": "OK"}]}

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)
    monkeypatch.setattr(
        "lekab_adapter.v1_3_8.lekab_adapter.service.LekabReplyActionService._load_dynamic_slots",
        lambda self, relative_action, appointment_type: [
            {
                "slot_id": "google-slot-1",
                "start": "2026-04-27T09:00:00+00:00",
                "end": "2026-04-27T09:30:00+00:00",
                "label": "Mon, 27 Apr, 09:00",
                "available": True,
                "calendar_provider": "google",
            },
            {
                "slot_id": "google-slot-2",
                "start": "2026-04-29T11:30:00+00:00",
                "end": "2026-04-29T12:00:00+00:00",
                "label": "Wed, 29 Apr, 11:30",
                "available": True,
                "calendar_provider": "google",
            },
        ],
    )

    session = SessionLocal()
    try:
        service = LekabReplyActionService(session, mock_mode=False)
        result = service.process_provider_callback(
            {
                "event_id": f"next-week-dynamic-{uuid4().hex[:8]}",
                "event": "INCOMING",
                "incoming_type": "POST",
                "incoming_data": "next_week",
                "correlation_id": correlation_id,
                "correlation_ref": correlation_id,
                "phone_number": "491705707716",
                "from": "491705707716",
                "reply_label": "Next week",
                "callback_transport": "post",
                "received_at": "2026-04-20T09:00:00Z",
                "source": "test",
            }
        )
    finally:
        session.close()

    follow_up = result["follow_up_message"]
    values = [item["value"] for item in follow_up["actions"]]
    labels = [item["label"] for item in follow_up["actions"]]
    assert "date_2026-04-27" in values
    assert "date_2026-04-29" in values
    assert "date_05_may" not in values
    assert "27 Apr" in labels
    assert "29 Apr" in labels


def test_lekab_v138_dynamic_date_callback_returns_dynamic_time_buttons(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    _journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    context_updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-dynamic-date",
            "booking_reference": "book-real-dynamic-date",
            "correlation_ref": correlation_id,
            "current_step": "relative_choice_complete",
            "status": "awaiting_date_choice",
            "metadata": {
                "dynamic_grouped_slots": {
                    "2026-04-27": [
                        {
                            "slot_id": "google-slot-1",
                            "start": "2026-04-27T09:00:00+00:00",
                            "end": "2026-04-27T09:30:00+00:00",
                            "label": "Mon, 27 Apr, 09:00",
                            "available": True,
                            "calendar_provider": "google",
                        },
                        {
                            "slot_id": "google-slot-2",
                            "start": "2026-04-27T11:30:00+00:00",
                            "end": "2026-04-27T12:00:00+00:00",
                            "label": "Mon, 27 Apr, 11:30",
                            "available": True,
                            "calendar_provider": "google",
                        },
                    ]
                }
            },
        },
    )
    assert context_updated.status_code == 200

    class DummyResponse:
        status_code = 200
        text = '{"resultText":"At least one message sent OK","sent":[{"id":"provider-follow-up-time","result":"OK"}]}'

        def json(self):
            return {"resultText": "At least one message sent OK", "sent": [{"id": "provider-follow-up-time", "result": "OK"}]}

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    session = SessionLocal()
    try:
        service = LekabReplyActionService(session, mock_mode=False)
        result = service.process_provider_callback(
            {
                "event_id": f"date-dynamic-{uuid4().hex[:8]}",
                "event": "INCOMING",
                "incoming_type": "POST",
                "incoming_data": "date_2026-04-27",
                "correlation_id": correlation_id,
                "correlation_ref": correlation_id,
                "phone_number": "491705707716",
                "from": "491705707716",
                "reply_label": "27 Apr",
                "callback_transport": "post",
                "received_at": "2026-04-20T09:10:00Z",
                "source": "test",
            }
        )
    finally:
        session.close()

    follow_up = result["follow_up_message"]
    values = [item["value"] for item in follow_up["actions"]]
    assert all(value.startswith("time_2026-04-27") for value in values)
    assert len(values) >= 2
    assert "time_0900" not in values


def test_lekab_v138_time_selection_returns_confirmation_buttons(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    setup_session = SessionLocal()
    try:
        JourneyRepository(setup_session).mark_state(journey_id, JourneyState.RESCHEDULE_FLOW.value)
    finally:
        setup_session.close()
    client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-time-confirm",
            "booking_reference": "book-real-time-confirm",
            "correlation_ref": correlation_id,
            "current_step": "date_choice_complete",
            "status": "awaiting_time_choice",
        },
    )

    class DummyResponse:
        status_code = 200
        text = '{"resultText":"At least one message sent OK","sent":[{"id":"provider-follow-up-2","result":"OK"}]}'

        def json(self):
            return {"resultText": "At least one message sent OK", "sent": [{"id": "provider-follow-up-2", "result": "OK"}]}

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    session = SessionLocal()
    try:
        service = LekabReplyActionService(session, mock_mode=False)
        service.contexts.save_context(
            DemoScenarioContextUpdate(
                metadata={
                    **service.contexts.get_context().metadata,
                    "pending_slot": {"date_token": "date_06_may", "date_label": "06 May"},
                }
            )
        )
        result = service.process_provider_callback(
            {
                "event_id": f"time-select-{uuid4().hex[:8]}",
                "event": "INCOMING",
                "incoming_type": "POST",
                "incoming_data": "time_1130",
                "correlation_id": correlation_id,
                "correlation_ref": correlation_id,
                "phone_number": "491705707716",
                "from": "491705707716",
                "reply_label": "11:30",
                "callback_transport": "post",
                "received_at": "2026-04-20T09:30:00Z",
                "source": "test",
            }
        )
        follow_up = result["follow_up_message"]
        assert "Confirm" in [item["label"] for item in follow_up["actions"]]
        assert follow_up["selected_button"] == "time_1130"
        assert "06 May, 11:30" in follow_up["text"]
    finally:
        session.close()


def test_lekab_v138_confirm_after_time_selection_commits_google_booking(monkeypatch) -> None:
    client = TestClient(app)
    _save_ready_settings(client)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)
    session = SessionLocal()
    try:
        journeys = JourneyRepository(session)
        journeys.store_selected_slot(
            journey_id,
            {
                "slot_id": "date_06_may_time_1130",
                "date_token": "date_06_may",
                "time_token": "time_1130",
                "date_label": "06 May",
                "time_label": "11:30",
                "label": "06 May, 11:30",
                "start": "2026-05-06T11:30:00",
                "end": "2026-05-06T12:00:00",
            },
        )
        journeys.mark_state(journey_id, JourneyState.WAITING_FOR_CONFIRMATION.value)
    finally:
        session.close()

    client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "appointment_id": "appt-real-google-confirm",
            "booking_reference": "book-real-google-confirm",
            "correlation_ref": correlation_id,
            "current_step": "slot_selected",
            "status": "awaiting_confirmation",
        },
    )

    def fake_mode_status(_mode):
        class Status:
            live_calendar_writes = True

        return Status()

    captured_request = {}

    def fake_reschedule(self, request):
        captured_request["booking_reference"] = request.booking_reference
        captured_request["correlation_id"] = request.correlation_id
        captured_request["appointment_id"] = request.appointment_id
        captured_request["address_id"] = request.address_id
        captured_request["customer_name"] = request.customer_name
        captured_request["linked_contact_reference_id"] = request.linked_contact_reference_id
        captured_request["linked_address_full_details"] = request.linked_address_full_details
        captured_request["timezone"] = request.timezone
        return type(
            "Result",
            (),
            {
                "model_dump": lambda self, mode="json": {
                    "success": True,
                    "action": "reschedule",
                    "mode": request.mode,
                    "google_source": "live",
                    "booking_reference": request.booking_reference,
                    "provider_reference": "google-live-ref-1",
                    "message": "Booking rescheduled successfully.",
                    "status": "rescheduled",
                    "selected_slot": {"slot_id": request.slot_id, "label": request.label},
                }
            },
        )()

    monkeypatch.setattr("lekab_adapter.v1_3_8.lekab_adapter.service.GoogleAdapterServiceV136.get_mode_status", fake_mode_status)
    monkeypatch.setattr("lekab_adapter.v1_3_8.lekab_adapter.service.GoogleAdapterServiceV136.reschedule_booking_patch8", fake_reschedule)

    session = SessionLocal()
    try:
        service = LekabReplyActionService(session, mock_mode=False)
        result = service.process_provider_callback(
            {
                "event_id": f"confirm-slot-{uuid4().hex[:8]}",
                "event": "INCOMING",
                "incoming_type": "POST",
                "incoming_data": "confirm_appointment",
                "correlation_id": correlation_id,
                "correlation_ref": correlation_id,
                "phone_number": "491705707716",
                "from": "491705707716",
                "reply_label": "Confirm",
                "callback_transport": "post",
                "received_at": "2026-04-20T09:45:00Z",
                "source": "test",
            }
        )
        assert result["google_booking_result"]["success"] is True
        assert result["google_booking_result"]["google_source"] == "live"
        assert result["follow_up_message"]["text"] == "Your appointment is confirmed and synced to Google Calendar."
    finally:
        session.close()

    assert captured_request["booking_reference"]
    assert captured_request["correlation_id"] == correlation_id
    assert captured_request["appointment_id"]
    assert captured_request["address_id"] == "addr-demo-001"
    assert captured_request["customer_name"] == "Anna Berger"
    assert captured_request["linked_contact_reference_id"] == "addr-demo-001"
    assert "Anna Berger" in captured_request["linked_address_full_details"]
    assert "Berlin" in captured_request["linked_address_full_details"]
    assert captured_request["timezone"] == "Europe/Berlin"

    context = client.get("/api/demo-monitoring/v1.3.9/scenario-context").json()
    assert context["current_step"] == "confirmation_complete"
    assert context["status"] == "confirmed"
    assert context["metadata"]["real_callback"]["selected_action"] == "keep"
    assert context["metadata"]["real_callback"]["google_booking_result"]["success"] is True
    assert context["metadata"]["customer_journey_message"]["text"] == "Your appointment is confirmed and synced to Google Calendar."

    session = SessionLocal()
    try:
        outbound_rows = (
            session.query(MessageRecord)
            .filter(
                MessageRecord.correlation_ref == correlation_id,
                MessageRecord.body == "Your appointment is confirmed and synced to Google Calendar.",
            )
            .all()
        )
        assert outbound_rows
    finally:
        session.close()
