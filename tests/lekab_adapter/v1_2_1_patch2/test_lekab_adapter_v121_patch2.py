from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_lekab_v121_patch2_rcs_settings_are_documented_and_masked() -> None:
    client = TestClient(app)

    saved = client.post(
        "/api/lekab/v1.2.1-patch2/settings/rcs",
        json={
            "values": {
                "environment_name": "Onboarding Demo",
                "workspace_id": "lekab-onboarding",
                "messaging_environment": "test",
                "auth_base_url": "https://auth.demo.example.test",
                "auth_client_id": "demo-client",
                "auth_client_secret": "very-secret-client",
                "auth_username": "demo-operator",
                "auth_password": "very-secret-password",
                "dispatch_base_url": "https://dispatch.demo.example.test",
                "rime_base_url": "https://rime.demo.example.test",
                "sms_base_url": "https://sms.demo.example.test",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "rcs_enabled": True,
                "sms_fallback_enabled": True,
            }
        },
    )
    assert saved.status_code == 200
    assert saved.json()["version"] == "v1.2.1-patch2"

    reloaded = client.get("/api/lekab/v1.2.1-patch2/settings/rcs")
    assert reloaded.status_code == 200
    payload = reloaded.json()
    auth_section = next(section for section in payload["settings"]["sections"] if section["id"] == "authentication")
    client_secret_field = next(field for field in auth_section["fields"] if field["id"] == "auth_client_secret")
    env_section = next(section for section in payload["settings"]["sections"] if section["id"] == "environment")
    environment_name_field = next(field for field in env_section["fields"] if field["id"] == "environment_name")

    assert client_secret_field["value"] == "********"
    assert client_secret_field["has_saved_secret"] is True
    assert "leave blank" in client_secret_field["helper_text"].lower()
    assert "human-friendly environment label" in environment_name_field["helper_text"].lower()

    validation = client.post("/api/lekab/v1.2.1-patch2/settings/rcs/validate")
    assert validation.status_code == 200
    assert validation.json()["readiness"]["ready"] is True
