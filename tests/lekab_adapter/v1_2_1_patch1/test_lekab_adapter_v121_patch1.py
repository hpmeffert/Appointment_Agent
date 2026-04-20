from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_lekab_v121_patch1_rcs_settings_save_reload_and_validate() -> None:
    client = TestClient(app)

    initial = client.get("/api/lekab/v1.2.1-patch1/settings/rcs")
    assert initial.status_code == 200
    initial_payload = initial.json()
    assert initial_payload["version"] == "v1.2.1-patch1"
    assert initial_payload["settings"]["sections"][0]["title"] == "Environment / Workspace"

    saved = client.post(
        "/api/lekab/v1.2.1-patch1/settings/rcs",
        json={
            "values": {
                "environment_name": "PreSales",
                "workspace_id": "lekab-sales-eu",
                "messaging_environment": "test",
                "auth_base_url": "https://auth.sales.example.test",
                "auth_client_id": "sales-client",
                "auth_client_secret": "super-secret-client",
                "auth_username": "sales-operator",
                "auth_password": "very-secret-password",
                "dispatch_base_url": "https://dispatch.sales.example.test",
                "rime_base_url": "https://rime.sales.example.test",
                "sms_base_url": "https://sms.sales.example.test",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "rcs_enabled": True,
                "sms_fallback_enabled": True,
            }
        },
    )
    assert saved.status_code == 200
    saved_payload = saved.json()
    assert saved_payload["save_result"]["success"] is True
    assert saved_payload["settings"]["values"]["environment_name"] == "PreSales"

    reloaded = client.get("/api/lekab/v1.2.1-patch1/settings/rcs")
    assert reloaded.status_code == 200
    reloaded_payload = reloaded.json()
    auth_section = next(section for section in reloaded_payload["settings"]["sections"] if section["id"] == "authentication")
    secret_field = next(field for field in auth_section["fields"] if field["id"] == "auth_client_secret")
    assert secret_field["value"] == "********"
    assert secret_field["has_saved_secret"] is True
    assert reloaded_payload["settings"]["values"]["workspace_id"] == "lekab-sales-eu"

    validation = client.post("/api/lekab/v1.2.1-patch1/settings/rcs/validate")
    assert validation.status_code == 200
    assert validation.json()["readiness"]["ready"] is True

    connection = client.post("/api/lekab/v1.2.1-patch1/settings/rcs/test-connection")
    assert connection.status_code == 200
    assert connection.json()["success"] is True
    assert "ready for test messaging" in connection.json()["message"]
