from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_google_v110_patch6_prepare_preview_accepts_date_range_and_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch6/demo-calendar/prepare-preview",
        json={
            "mode": "simulation",
            "from_date": "2026-03-29",
            "to_date": "2026-04-02",
            "appointment_type": "wallbox",
            "count": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "prepare"
    assert body["preview_only"] is True
    assert body["appointment_type"] == "wallbox"
    assert body["from_date"] == "2026-03-29"
    assert body["to_date"] == "2026-04-02"
    assert body["generated_count"] == 3


def test_google_v110_patch6_generate_uses_appointment_type_titles() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch6/demo-calendar/generate",
        json={
            "mode": "simulation",
            "from_date": "2026-03-29",
            "to_date": "2026-04-03",
            "appointment_type": "gas_meter",
            "count": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["appointment_type"] == "gas_meter"
    assert body["generated_count"] == 2
    assert "Gas" in body["items"][0]["title"]


def test_google_v110_patch6_rejects_invalid_date_range() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch6/demo-calendar/generate",
        json={
            "mode": "simulation",
            "from_date": "2026-04-05",
            "to_date": "2026-04-01",
            "appointment_type": "water_meter",
            "count": 2,
        },
    )

    assert response.status_code == 422
