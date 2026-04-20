from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_lekab_v121_send_inbound_status_and_monitor() -> None:
    client = TestClient(app)

    outbound = client.post(
        "/api/lekab/v1.2.1/messages/send/rcs",
        json={
            "tenant_id": "demo",
            "correlation_id": "corr-v121-1",
            "phone_number": "+491701234567",
            "body": "Please choose one appointment slot.",
            "journey_id": "journey-v121-1",
            "booking_reference": "booking-v121-1",
            "actions": [
                {"action_id": "keep", "label": "Keep", "value": "keep", "action_type": "reply"},
            ],
        },
    )
    assert outbound.status_code == 200
    outbound_payload = outbound.json()
    assert outbound_payload["channel"] == "RCS"
    assert outbound_payload["direction"] == "outbound"
    assert outbound_payload["message_id"]
    assert outbound_payload["provider_message_id"]
    assert outbound_payload["actions"][0]["value"] == "keep"

    inbound = client.post(
        "/api/lekab/v1.2.1/messages/inbound",
        json={
            "tenant_id": "demo",
            "correlation_id": "corr-v121-2",
            "phone_number": "+491701234567",
            "body": "Keep the appointment.",
            "channel": "RCS",
            "journey_id": "journey-v121-1",
            "booking_reference": "booking-v121-1",
        },
    )
    assert inbound.status_code == 200
    assert inbound.json()["direction"] == "inbound"
    assert inbound.json()["status"] == "received"

    status_update = client.post(
        "/api/lekab/v1.2.1/messages/status",
        json={
            "tenant_id": "demo",
            "correlation_id": "corr-v121-3",
            "message_id": outbound_payload["message_id"],
            "status": "delivered",
            "provider_payload": {"delivery_status": "delivered"},
        },
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "delivered"

    listing = client.get("/api/lekab/v1.2.1/messages?journey_id=journey-v121-1")
    assert listing.status_code == 200
    listed_messages = listing.json()["messages"]
    assert any(message["direction"] == "outbound" for message in listed_messages)
    assert any(message["direction"] == "inbound" for message in listed_messages)

    detail = client.get(f"/api/lekab/v1.2.1/messages/{outbound_payload['message_id']}")
    assert detail.status_code == 200
    assert detail.json()["provider"] == "lekab"
    assert detail.json()["journey_id"] == "journey-v121-1"

    monitor = client.get("/api/lekab/v1.2.1/monitor")
    assert monitor.status_code == 200
    monitor_payload = monitor.json()
    assert "summary_cards" in monitor_payload
    assert "report_cards" in monitor_payload
    assert monitor_payload["messages"][0]["message_id"]


def test_lekab_v121_help_and_addressbook_lookup() -> None:
    client = TestClient(app)

    help_response = client.get("/api/lekab/v1.2.1/help")
    assert help_response.status_code == 200
    assert "rcs_send" in help_response.json()["adapter_features"]
    assert "RimeRESTWebService" in help_response.json()["doc_basis"]

    lookup = client.post(
        "/api/lekab/v1.2.1/addressbook/resolve",
        params={"tenant_id": "demo", "phone_number": "+491701234567"},
    )
    assert lookup.status_code == 200
    assert lookup.json()["source"] == "lekab_addressbook_abstraction"
