from fastapi.testclient import TestClient

from address_database.v1_3_9.address_database.service import AddressDatabaseService, AddressInput
from appointment_agent_shared.db import SessionLocal
from google_adapter.v1_3_6.google_adapter.app import app


def test_google_v136_linkage_demo_exposes_source_normalized_view_and_stories() -> None:
    client = TestClient(app)
    response = client.get("/api/google/v1.3.6/linkage/demo", params={"appointment_type": "dentist"})

    assert response.status_code == 200
    body = response.json()

    assert body["version"] == "v1.3.6"
    assert body["appointment_source"]["provider"] == "google"
    assert body["appointment_source"]["sync_status"] == "synced"
    assert body["normalized_appointment"]["appointment_type"] == "dentist"
    assert body["normalized_appointment"]["booking_reference"] == "booking-gdemo-dentist-001"
    assert body["normalized_appointment"]["reminder_relevant_fields"]["policy_key"] == "google-linkage-demo"
    assert body["normalized_appointment"]["reminder_relevant_fields"]["reminder_offsets_hours"] == [24, 2]

    stories = {story["story_key"]: story for story in body["stories"]}
    assert set(stories) == {"new_appointment", "reschedule", "cancel"}
    assert stories["reschedule"]["changes"]["google_event_id_after"].endswith("-rescheduled")
    assert stories["cancel"]["changes"]["normalized_status_after"] == "cancelled"


def test_google_v136_linkage_help_lists_visible_demo_features() -> None:
    client = TestClient(app)
    response = client.get("/api/google/v1.3.6/linkage/help")

    assert response.status_code == 200
    body = response.json()

    assert body["version"] == "v1.3.6"
    assert "appointment_source_visibility" in body["features"]
    assert "/linkage/demo" in body["endpoints"]


def test_google_v136_linkage_demo_uses_selected_address_context_when_provided() -> None:
    session = SessionLocal()
    try:
        AddressDatabaseService(session).save_address(
            AddressInput(
                address_id="addr-demo-001",
                display_name="Anna Berger",
                city="Berlin",
                phone="491705707716",
                email="anna.berger@example.com",
                preferred_channel="rcs_sms",
                correlation_ref="corr-addr-demo-001",
            )
        )
    finally:
        session.close()
    client = TestClient(app)
    response = client.get(
        "/api/google/v1.3.6/linkage/demo",
        params={"appointment_type": "dentist", "address_id": "addr-demo-001"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["normalized_appointment"]["address_id"] == "addr-demo-001"
    assert body["normalized_appointment"]["customer_name"] == "Anna Berger"
    assert body["normalized_appointment"]["customer_contact"] == "491705707716"
    assert body["normalized_appointment"]["correlation_ref"] == "corr-addr-demo-001"
    assert body["normalized_appointment"]["reminder_relevant_fields"]["selected_address_id"] == "addr-demo-001"
