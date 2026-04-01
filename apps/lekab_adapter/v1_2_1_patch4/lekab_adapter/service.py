from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from appointment_agent_shared.repositories import LekabConfigRepository

from lekab_adapter.v1_2_1.lekab_adapter.service import LekabMessagingService


class LekabMessagingSettingsService(LekabMessagingService):
    """Patch4 keeps the settings backend stable for the guided demo line.

    The base adapter already normalizes message traffic. This patch adds the
    operator-facing configuration layer for RCS/SMS so the cockpit can save,
    reload, validate, and present readiness without exposing raw secrets.
    Patch2 mainly deepens helper text and onboarding value so new teammates can
    understand why each parameter exists and what it changes in runtime.
    """

    SECRET_FIELDS = {
        "auth_client_secret",
        "auth_password",
        "sms_sender_secret",
        "addressbook_api_key",
        "dispatch_api_key",
        "rime_api_key",
        "sms_api_key",
    }

    def __init__(self, session: Session, *, mock_mode: bool = True) -> None:
        super().__init__(session, mock_mode=mock_mode)
        self.configs = LekabConfigRepository(session)

    def get_rcs_settings(self) -> dict[str, Any]:
        record = self.configs.get()
        if record is None:
            saved_config = self._default_config()
            saved_secrets = {}
        else:
            saved_config = deepcopy(record.config_payload or {})
            saved_secrets = deepcopy(record.secret_payload or {})

        readiness = self._calculate_readiness(saved_config, saved_secrets)
        return {
            "version": "v1.2.1-patch4",
            "settings": self._build_settings_response(saved_config, saved_secrets, readiness),
            "readiness": readiness,
            "storage_mode": "local_sqlite_config_store",
        }

    def save_rcs_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get_rcs_settings()["settings"]["values"]
        current_secrets = self._extract_secret_state(self.configs.get())

        merged_values = {**current, **payload}

        # Secret fields are persisted only when the operator deliberately sends a
        # non-empty value. Blank values mean "keep existing secret" instead of
        # accidentally deleting credentials during an unrelated save.
        for secret_field in self.SECRET_FIELDS:
            if secret_field in payload:
                secret_value = payload.get(secret_field)
                if secret_value:
                    current_secrets[secret_field] = secret_value
            merged_values.pop(secret_field, None)

        readiness = self._calculate_readiness(merged_values, current_secrets)
        self.configs.save(
            config_payload=merged_values,
            secret_payload=current_secrets,
            status_payload=readiness,
        )
        response = self.get_rcs_settings()
        response["save_result"] = {
            "success": True,
            "message": "RCS configuration saved successfully",
        }
        return response

    def validate_rcs_settings(self) -> dict[str, Any]:
        response = self.get_rcs_settings()
        readiness = response["readiness"]
        return {
            "success": readiness["ready"],
            "readiness": readiness,
            "message": readiness["headline"],
        }

    def test_rcs_connection(self) -> dict[str, Any]:
        readiness = self.get_rcs_settings()["readiness"]
        if not readiness["ready"]:
            return {
                "success": False,
                "message": readiness["headline"],
                "readiness": readiness,
            }
        return {
            "success": True,
            "message": "LEKAB adapter ready for test messaging",
            "mode": "mock_connection_test" if self.mock_mode else "provider_connection_test",
            "readiness": readiness,
        }

    def _default_config(self) -> dict[str, Any]:
        return {
            "environment_name": "Demo",
            "workspace_id": "appointment-agent-demo",
            "messaging_environment": "test",
            "auth_base_url": "https://auth.example.test",
            "auth_client_id": "appointment-agent-demo-client",
            "auth_username": "demo-operator",
            "token_endpoint": "/oauth/token",
            "revoke_endpoint": "/oauth/revoke",
            "dispatch_base_url": "https://dispatch.example.test",
            "rime_base_url": "https://rime.example.test",
            "sms_base_url": "https://sms.example.test",
            "addressbook_base_url": "https://addressbook.example.test",
            "rcs_enabled": True,
            "rcs_sender_profile": "Appointment Agent",
            "default_template_context": "appointment_journey",
            "callback_url": "https://demo.example.test/api/lekab/v1.2.1/messages/inbound",
            "channel_priority": "RCS_FIRST",
            "sms_fallback_enabled": True,
            "sms_enabled": True,
            "sms_sender_name": "APPT",
            "sms_length_mode": "auto_split",
            "default_language": "en",
            "addressbook_enabled": True,
            "contact_lookup_mode": "phone_first",
            "phone_normalization_mode": "E164",
        }

    def _extract_secret_state(self, record) -> dict[str, str]:
        if record is None:
            return {}
        return deepcopy(record.secret_payload or {})

    def _build_settings_response(self, values: dict[str, Any], secrets: dict[str, str], readiness: dict[str, Any]) -> dict[str, Any]:
        return {
            "values": values,
            "sections": [
                {
                    "id": "environment",
                    "title": "Environment / Workspace",
                    "state": "active",
                    "fields": [
                        self._field("environment_name", values, required=True),
                        self._field("workspace_id", values, required=True),
                        self._field("messaging_environment", values, required=True, field_type="select", options=["test", "production"]),
                        self._field("dispatch_base_url", values, required=True),
                        self._field("rime_base_url", values, required=True),
                        self._field("sms_base_url", values, required=True),
                        self._field("addressbook_base_url", values, required=True),
                    ],
                },
                {
                    "id": "authentication",
                    "title": "Authentication",
                    "state": "active",
                    "fields": [
                        self._field("auth_base_url", values, required=True),
                        self._field("auth_client_id", values, required=True),
                        self._secret_field("auth_client_secret", secrets, required=True),
                        self._field("auth_username", values, required=True),
                        self._secret_field("auth_password", secrets, required=True),
                        self._field("token_endpoint", values, required=True),
                        self._field("revoke_endpoint", values, required=False),
                    ],
                },
                {
                    "id": "rcs",
                    "title": "RCS / Messaging",
                    "state": "active",
                    "fields": [
                        self._field("rcs_enabled", values, field_type="toggle", required=True),
                        self._field("rcs_sender_profile", values, required=True),
                        self._field("default_template_context", values, required=False),
                        self._field("callback_url", values, required=True),
                        self._field("channel_priority", values, required=True, field_type="select", options=["RCS_FIRST", "SMS_FIRST"]),
                        self._field("sms_fallback_enabled", values, field_type="toggle", required=True),
                        self._secret_field("rime_api_key", secrets, required=False, state="planned"),
                    ],
                },
                {
                    "id": "sms",
                    "title": "SMS",
                    "state": "active",
                    "fields": [
                        self._field("sms_enabled", values, field_type="toggle", required=True),
                        self._field("sms_sender_name", values, required=True),
                        self._field("sms_length_mode", values, required=True, field_type="select", options=["auto_split", "truncate"]),
                        self._field("default_language", values, required=False),
                        self._secret_field("sms_api_key", secrets, required=False, state="planned"),
                    ],
                },
                {
                    "id": "addressbook",
                    "title": "Addressbook / Contact Resolution",
                    "state": "active",
                    "fields": [
                        self._field("addressbook_enabled", values, field_type="toggle", required=True),
                        self._field("contact_lookup_mode", values, required=True, field_type="select", options=["phone_first", "phone_then_email"]),
                        self._field("phone_normalization_mode", values, required=True, field_type="select", options=["E164", "national"]),
                        self._secret_field("addressbook_api_key", secrets, required=False, state="planned"),
                    ],
                },
                {
                    "id": "diagnostics",
                    "title": "Diagnostics / Status",
                    "state": "informational",
                    "fields": [
                        {
                            "id": "adapter_ready",
                            "label": "Adapter readiness",
                            "value": "ready" if readiness["ready"] else "not_ready",
                            "helper_text": readiness["headline"],
                            "required": False,
                            "type": "status",
                            "state": "active",
                        },
                        {
                            "id": "missing_fields",
                            "label": "Missing fields",
                            "value": ", ".join(readiness["missing_fields"]) if readiness["missing_fields"] else "none",
                            "helper_text": "These fields block test messaging when they are empty.",
                            "required": False,
                            "type": "status",
                            "state": "informational",
                        },
                    ],
                },
            ],
        }

    def _field(
        self,
        field_id: str,
        values: dict[str, Any],
        *,
        required: bool,
        field_type: str = "text",
        options: list[str] | None = None,
        state: str = "active",
    ) -> dict[str, Any]:
        return {
            "id": field_id,
            "label": field_id.replace("_", " ").title(),
            "value": values.get(field_id),
            "required": required,
            "type": field_type,
            "options": options or [],
            "state": state,
            "helper_text": self._helper_text(field_id),
        }

    def _secret_field(self, field_id: str, secrets: dict[str, str], *, required: bool, state: str = "active") -> dict[str, Any]:
        secret_present = bool(secrets.get(field_id))
        return {
            "id": field_id,
            "label": field_id.replace("_", " ").title(),
            "value": "********" if secret_present else "",
            "required": required,
            "type": "password",
            "options": [],
            "state": state,
            "has_saved_secret": secret_present,
            "helper_text": "Leave blank to keep the saved secret. A new value replaces the stored secret.",
        }

    def _helper_text(self, field_id: str) -> str:
        mapping = {
            "environment_name": "Human-friendly environment label, for example Demo EU or Customer Pilot. Operators mainly see this in the cockpit, not customers.",
            "workspace_id": "Technical LEKAB workspace or tenant id. This decides which provider space receives outbound traffic.",
            "messaging_environment": "Use test for demos and internal checks. Use production only when the real rollout is approved, because the adapter then targets live messaging infrastructure.",
            "auth_base_url": "Base URL for LEKAB authentication requests. Example: https://auth.example.test",
            "auth_client_id": "Technical client or application id used during LEKAB authentication. Example: appointment-agent-demo-client",
            "auth_username": "Technical user name for the messaging environment. This is usually an operator or service account, not a customer identity.",
            "token_endpoint": "Relative endpoint path used to request new access tokens, for example /oauth/token",
            "dispatch_base_url": "Base URL for workflow dispatch operations. This affects where outbound workflow triggers are sent.",
            "rime_base_url": "Base URL for rich messaging or RCS-style requests. If this is wrong, RCS traffic cannot be prepared correctly.",
            "sms_base_url": "Base URL for SMS requests. This becomes important when SMS fallback is enabled.",
            "addressbook_base_url": "Base URL for addressbook lookups or future sync actions. It affects contact resolution before outbound messages are sent.",
            "rcs_sender_profile": "Visible RCS sender or agent profile name that the customer should recognize.",
            "callback_url": "Inbound callback URL that LEKAB would call for replies or delivery status updates. Example: https://demo.example.test/api/lekab/v1.2.1/messages/inbound",
            "channel_priority": "Defines which channel is attempted first. RCS_FIRST tries rich messaging before SMS. SMS_FIRST reverses that order.",
            "sms_sender_name": "Originator name shown on SMS where the provider and country allow branded senders.",
            "sms_length_mode": "Choose whether long texts split automatically into several SMS parts or should be truncated later by policy.",
            "default_language": "Default template language used when the journey does not provide a more specific language.",
            "contact_lookup_mode": "Controls how phone or email based contact resolution is attempted before sending.",
            "phone_normalization_mode": "Defines the phone number formatting style before lookup or send. E164 is best for provider-neutral handling.",
            "default_template_context": "Template family or business context used when the adapter chooses the message text.",
        }
        return mapping.get(field_id, "This field is part of the LEKAB messaging setup.")

    def _calculate_readiness(self, values: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
        # Readiness is intentionally simple: the cockpit needs a clear yes/no
        # onboarding signal instead of a hidden provider-specific matrix.
        required_pairs = [
            ("environment_name", values.get("environment_name")),
            ("workspace_id", values.get("workspace_id")),
            ("auth_base_url", values.get("auth_base_url")),
            ("auth_client_id", values.get("auth_client_id")),
            ("auth_username", values.get("auth_username")),
            ("dispatch_base_url", values.get("dispatch_base_url")),
            ("rime_base_url", values.get("rime_base_url")),
            ("sms_base_url", values.get("sms_base_url")),
            ("callback_url", values.get("callback_url")),
            ("auth_client_secret", secrets.get("auth_client_secret")),
            ("auth_password", secrets.get("auth_password")),
        ]
        missing = [field_id for field_id, value in required_pairs if not value]
        warnings: list[str] = []
        if values.get("sms_fallback_enabled"):
            warnings.append("SMS fallback is enabled")
        if values.get("messaging_environment") == "production":
            warnings.append("Production mode is selected")
        ready = not missing and bool(values.get("rcs_enabled"))
        headline = (
            "LEKAB adapter ready for test messaging"
            if ready
            else f"Configuration incomplete: {', '.join(missing[:3])}" if missing else "RCS is disabled"
        )
        return {
            "ready": ready,
            "headline": headline,
            "missing_fields": missing,
            "warnings": warnings,
            "active_channel_mode": values.get("channel_priority", "RCS_FIRST"),
        }
