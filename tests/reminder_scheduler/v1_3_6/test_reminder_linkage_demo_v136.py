from fastapi.testclient import TestClient

from reminder_scheduler.v1_3_6.reminder_scheduler.app import app


def test_reminder_v136_linkage_demo_builds_preview_from_google_linkage() -> None:
    client = TestClient(app)
    response = client.get("/api/reminders/v1.3.6/linkage/demo", params={"appointment_type": "wallbox"})

    assert response.status_code == 200
    body = response.json()

    assert body["version"] == "v1.3.6"
    assert body["appointment_source"]["provider"] == "google"
    assert body["normalized_appointment"]["appointment_type"] == "wallbox"
    assert body["reminder_policy"]["reminder_count"] == 2
    assert body["reminder_validation"] == []
    assert len(body["reminder_preview"]) == 2
    assert all(item["status"] == "planned" for item in body["reminder_preview"])
    assert len(body["reminder_jobs"]) == 2
    assert body["reminder_relevant_fields"]["reminder_channels"] == ["email", "voice"]

    stories = {story["story_key"]: story for story in body["stories"]}
    assert set(stories) == {"new_appointment", "reschedule", "cancel"}
    assert stories["cancel"]["reminder_state"] == "cancelled"


def test_reminder_v136_linkage_help_lists_visible_demo_features() -> None:
    client = TestClient(app)
    response = client.get("/api/reminders/v1.3.6/linkage/help")

    assert response.status_code == 200
    body = response.json()

    assert body["version"] == "v1.3.6"
    assert "google_linked_appointment_source" in body["features"]
    assert "/linkage/reminder-preview" in body["endpoints"]
