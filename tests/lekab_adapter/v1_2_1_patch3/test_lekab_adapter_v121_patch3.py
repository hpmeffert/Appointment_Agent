from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_lekab_v121_patch3_settings_route_is_available() -> None:
    client = TestClient(app)

    response = client.get("/api/lekab/v1.2.1-patch3/settings/rcs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1.2.1-patch3"
    assert payload["storage_mode"] == "local_sqlite_config_store"
