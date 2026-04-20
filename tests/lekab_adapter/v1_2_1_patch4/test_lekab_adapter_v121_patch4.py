import json

from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_lekab_v121_patch4_settings_route_is_available() -> None:
    client = TestClient(app)

    response = client.get("/api/lekab/v1.2.1-patch4/settings/rcs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1.2.1-patch4"
    assert payload["storage_mode"] == "local_sqlite_config_store"
    assert payload["trace_id"].startswith("lekab-rcs-")
    assert "connection_diagnostics" in payload
    assert isinstance(payload["connection_diagnostics"]["mock_mode"], bool)
    assert isinstance(payload["connection_diagnostics"]["verbose_connection_logging"], bool)
    assert "callback_url" in payload["settings"]["values"]
    assert "webhook_fetch_url" in payload["settings"]["values"]
    assert payload["settings"]["values"]["test_recipient_address"]
    rcs_section = next(section for section in payload["settings"]["sections"] if section["id"] == "rcs")
    rcs_field_ids = [field["id"] for field in rcs_section["fields"]]
    assert "test_recipient_address" in rcs_field_ids


def test_lekab_v121_patch4_test_connection_returns_trace_id_and_safe_logs(caplog) -> None:
    client = TestClient(app)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "environment_name": "Patch4 Demo",
                "workspace_id": "lekab-patch4-demo",
                "messaging_environment": "test",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "test_recipient_address": "46701234567",
                "rcs_enabled": True,
                "sms_fallback_enabled": True,
                "channel_priority": "RCS_FIRST",
                "mock_connection_mode": True,
                "rime_api_key": "super-secret-rime-key",
            }
        },
        headers={"x-trace-id": "trace-save-123"},
    )
    assert save_response.status_code == 200
    assert save_response.json()["trace_id"] == "trace-save-123"

    with caplog.at_level("INFO", logger="appointment_agent.lekab.rcs"):
        response = client.post(
            "/api/lekab/v1.2.1-patch4/settings/rcs/test-connection",
            headers={"x-trace-id": "trace-test-456"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["trace_id"] == "trace-test-456"
    assert payload["mode"] == "mock_connection_test"
    assert payload["auth_mode"] == "rime_api_key"
    assert payload["provider_endpoint"] == "https://secure.lekab.com/rime/send"
    assert payload["connection_diagnostics"]["last_connection_test"]["trace_id"] == "trace-test-456"
    assert payload["connection_diagnostics"]["last_connection_test"]["provider_request_sent"] is False
    log_text = "\n".join(caplog.messages)
    assert "trace-test-456" in log_text
    assert "test_connection_succeeded" in log_text
    assert "super-secret-rime-key" not in log_text
    assert "provider_request_sent" in log_text


def test_lekab_v121_patch4_mock_mode_can_be_switched_in_ui_settings() -> None:
    client = TestClient(app)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-live-check",
                "environment_name": "Live Check",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "test_recipient_address": "46701234567",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "verbose_connection_logging": False,
                "rime_api_key": "live-rime-key",
            }
        },
    )
    assert save_response.status_code == 200

    reloaded = client.get("/api/lekab/v1.2.1-patch4/settings/rcs")
    assert reloaded.status_code == 200
    payload = reloaded.json()
    assert payload["connection_diagnostics"]["mock_mode"] is False
    assert payload["connection_diagnostics"]["provider_post_enabled"] is True
    assert payload["connection_diagnostics"]["verbose_connection_logging"] is False


def test_lekab_v121_patch4_provider_post_uses_x_api_key_header(monkeypatch) -> None:
    client = TestClient(app)
    captured: dict[str, object] = {}

    class DummyResponse:
        status_code = 202
        text = '{"status":"accepted"}'

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers or {}
            captured["json"] = json or {}
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-provider-check",
                "environment_name": "Provider Check",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "test_recipient_address": "46701234567",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "verbose_connection_logging": True,
                "rime_api_key": "real-rime-key",
            }
        },
        headers={"x-trace-id": "trace-provider-save"},
    )
    assert save_response.status_code == 200

    response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs/test-connection",
        headers={"x-trace-id": "trace-provider-test"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["mode"] == "provider_connection_test"
    assert payload["provider_request_sent"] is True
    assert captured["url"] == "https://secure.lekab.com/rime/send"
    assert captured["headers"]["X-API-Key"] == "real-rime-key"
    assert "Authorization" not in captured["headers"]
    assert captured["json"]["channels"] == "RCS"
    assert captured["json"]["address"] == "46701234567"
    assert captured["json"]["richMessage"]["text"] == "Appointment Agent LEKAB RIME connection test"
    assert "callback_url" not in captured["json"]
    preview_headers = payload["provider_request_preview"]["headers"]
    assert preview_headers["X-API-Key"] == "********"
    assert "Authorization" not in preview_headers
    assert payload["provider_status_code"] == 202
    assert payload["provider_response_excerpt"] == '{"status":"accepted"}'


def test_lekab_v121_patch4_old_saved_config_gets_default_test_recipient_address() -> None:
    client = TestClient(app)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "legacy-config-check",
                "environment_name": "Legacy Config",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "rime_api_key": "legacy-rime-key",
                "test_recipient_address": "491705707716",
            }
        },
    )
    assert save_response.status_code == 200

    # Simulate an older persisted record that predates the new field by saving
    # again without it. The service should still inject the new default on read.
    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "legacy-config-check",
                "environment_name": "Legacy Config",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "rcs_enabled": True,
                "mock_connection_mode": False,
            }
        },
    )
    assert save_response.status_code == 200

    payload = client.get("/api/lekab/v1.2.1-patch4/settings/rcs").json()
    assert payload["settings"]["values"]["test_recipient_address"] == "491705707716"


def test_lekab_v121_patch4_normalizes_webhook_site_capture_and_fetch_urls() -> None:
    client = TestClient(app)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "callback_url": "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "receipt_callback_url": "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "webhook_fetch_url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
            }
        },
    )
    assert save_response.status_code == 200
    values = save_response.json()["settings"]["values"]
    assert values["callback_url"] == "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6"
    assert values["receipt_callback_url"] == "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6"
    assert values["webhook_fetch_url"] == "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6"


def test_lekab_v121_patch4_oauth_mode_blocks_unsafe_provider_post(monkeypatch) -> None:
    client = TestClient(app)

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("Provider POST must not run in oauth_password mode without safe token handoff")

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-oauth-check",
                "environment_name": "OAuth Check",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "auth_client_secret": "oauth-secret",
                "auth_password": "oauth-password",
            }
        },
    )
    assert save_response.status_code == 200

    response = client.post("/api/lekab/v1.2.1-patch4/settings/rcs/test-connection")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["auth_mode"] == "oauth_password"
    assert payload["provider_request_sent"] is False
    assert "token handoff" in payload["message"]
    assert payload["connection_diagnostics"]["provider_test_supported"] is False


def test_lekab_v121_patch4_provider_401_returns_actionable_diagnostics(monkeypatch) -> None:
    client = TestClient(app)

    class DummyResponse:
        status_code = 401
        text = '{"message":"unauthorized"}'

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

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-401-check",
                "environment_name": "401 Check",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://demo.example.test/api/lekab/inbound",
                "test_recipient_address": "46701234567",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "rime_api_key": "bad-rime-key",
            }
        },
    )
    assert save_response.status_code == 200

    response = client.post("/api/lekab/v1.2.1-patch4/settings/rcs/test-connection")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["provider_status_code"] == 401
    assert "status 401" in payload["message"]
    assert "credentials" in payload["message"]
    assert any(step["step"] == "provider_response" and step["status"] == "failed" for step in payload["steps"])


def test_lekab_v121_patch4_fetch_latest_callback_uses_webhook_api_key(monkeypatch) -> None:
    client = TestClient(app)
    captured: dict[str, object] = {}

    class DummyResponse:
        status_code = 200
        text = '{"uuid":"latest-request","content":"{\\"id\\":\\"reply-1\\",\\"time\\":\\"2026-04-09T08:00:00Z\\",\\"channel\\":\\"RCS\\",\\"from\\":\\"agent\\",\\"to\\":\\"491705707716\\",\\"status\\":\\"DELIVERED\\"}"}'

        def json(self):
            return {
                "uuid": "latest-request",
                "content": json.dumps(
                    {
                        "id": "reply-1",
                        "time": "2026-04-09T08:00:00Z",
                        "channel": "RCS",
                        "from": "agent",
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
            captured["url"] = url
            captured["headers"] = headers or {}
            return DummyResponse()

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-callback-check",
                "environment_name": "Callback Check",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "webhook_fetch_url": "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "rime_api_key": "real-rime-key",
                "webhook_api_key": "real-webhook-key",
            }
        },
        headers={"x-trace-id": "trace-callback-save"},
    )
    assert save_response.status_code == 200

    response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs/fetch-latest-callback",
        headers={"x-trace-id": "trace-callback-fetch"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert captured["url"] == "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6/requests?sorting=newest&per_page=25"
    assert captured["headers"]["Api-Key"] == "real-webhook-key"
    assert captured["headers"]["Accept"] == "application/json"
    assert payload["request_preview"]["headers"]["Api-Key"] == "********"
    assert payload["response_json"]["uuid"] == "latest-request"
    assert payload["normalized_event_type"] == "message.delivered"
    assert payload["provider_status_code"] == 200


def test_lekab_v121_patch4_fetch_latest_callback_detects_cancel_reply(monkeypatch) -> None:
    client = TestClient(app)

    class DummyResponse:
        status_code = 200
        text = '{"uuid":"reply-request","content":"{\\"id\\":\\"reply-1\\",\\"time\\":\\"2026-04-09T08:00:00Z\\",\\"channel\\":\\"RCS\\",\\"from\\":\\"agent\\",\\"to\\":\\"491705707716\\",\\"text\\":\\"Please cancel the appointment on 2026-04-10 at 14:30\\"}"}'

        def json(self):
            return {
                "uuid": "reply-request",
                "content": json.dumps(
                    {
                        "id": "reply-1",
                        "time": "2026-04-09T08:00:00Z",
                        "channel": "RCS",
                        "from": "agent",
                        "to": "491705707716",
                        "text": "Please cancel the appointment on 2026-04-10 at 14:30",
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

    monkeypatch.setattr("lekab_adapter.v1_2_1_patch4.lekab_adapter.service.httpx.Client", DummyClient)

    save_response = client.post(
        "/api/lekab/v1.2.1-patch4/settings/rcs",
        json={
            "values": {
                "workspace_id": "lekab-reply-check",
                "environment_name": "Reply Check",
                "rime_base_url": "https://secure.lekab.com/rime/send",
                "callback_url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "webhook_fetch_url": "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6",
                "rcs_enabled": True,
                "mock_connection_mode": False,
                "rime_api_key": "real-rime-key",
                "webhook_api_key": "real-webhook-key",
            }
        },
    )
    assert save_response.status_code == 200

    response = client.post("/api/lekab/v1.2.1-patch4/settings/rcs/fetch-latest-callback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_event_type"] == "message.reply_received"
    assert payload["reply_intent"] == "cancel"
    assert "2026-04-10" in payload["reply_datetime_candidates"]
    assert "14:30" in payload["reply_datetime_candidates"]


def test_lekab_v121_patch4_monitor_report_cards_show_communication_history_labels() -> None:
    client = TestClient(app)

    payload = client.get("/api/lekab/v1.2.1-patch4/monitor").json()

    titles = [card["title"] for card in payload["report_cards"]]
    assert "Communication History" in titles
    assert "Delivery And Replies" in titles
    assert "Routing And Context" in titles
    assert "submitted" in payload["filters"]["statuses"]
