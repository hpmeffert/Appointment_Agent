from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from appointment_agent_shared.repositories import LekabConfigRepository
from appointment_agent_shared.shared_settings_store import SharedSettingsStoreService

from lekab_adapter.v1_2_1.lekab_adapter.service import LekabMessagingService


logger = logging.getLogger("appointment_agent.lekab.rcs")


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
        "webhook_api_key",
    }

    def __init__(self, session: Session, *, mock_mode: bool = True) -> None:
        super().__init__(session, mock_mode=mock_mode)
        self.configs = LekabConfigRepository(session)
        self.shared_settings = SharedSettingsStoreService(session)

    def _sync_shared_settings(
        self,
        *,
        values: dict[str, Any],
        secrets: dict[str, Any],
        readiness: dict[str, Any],
        extra_status: dict[str, Any] | None = None,
    ) -> None:
        status_payload = {"readiness": deepcopy(readiness), **deepcopy(extra_status or {})}
        self.shared_settings.merge_namespace(
            "lekab",
            deepcopy(values),
            secret_values=deepcopy(secrets),
            status_values=status_payload,
        )

    def get_rcs_settings(self, *, trace_id: str | None = None) -> dict[str, Any]:
        record = self.configs.get()
        if record is None:
            saved_config = self._default_config()
            saved_secrets = {}
            saved_status = {}
        else:
            saved_config = self._normalized_config_values(record.config_payload or {})
            saved_secrets = deepcopy(record.secret_payload or {})
            saved_status = deepcopy(record.status_payload or {})

        readiness = self._calculate_readiness(saved_config, saved_secrets)
        return {
            "version": "v1.2.1-patch4",
            "settings": self._build_settings_response(saved_config, saved_secrets, readiness),
            "readiness": readiness,
            "connection_diagnostics": self._build_connection_diagnostics(saved_config, saved_status, readiness),
            "storage_mode": "local_sqlite_config_store",
            "trace_id": trace_id,
        }

    def _normalized_config_values(self, stored_values: dict[str, Any]) -> dict[str, Any]:
        """Merge stored values onto the current defaults.

        Older saved LEKAB settings may predate newly introduced fields such as
        `test_recipient_address`. Without this merge, reading an old config
        would silently drop fresh defaults and make new readiness checks fail.
        By layering stored values on top of defaults, existing operators keep
        their saved settings while newly added fields get sensible defaults.
        """

        return {**self._default_config(), **deepcopy(stored_values)}

    def save_rcs_settings(self, payload: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        record = self.configs.get()
        current = self.get_rcs_settings(trace_id=trace_id)["settings"]["values"]
        current_secrets = self._extract_secret_state(record)
        current_status = deepcopy(record.status_payload or {}) if record is not None else {}

        normalized_payload = self._normalize_webhook_site_settings_payload(payload)
        merged_values = {**current, **normalized_payload}
        updated_secret_fields = {field_id for field_id in self.SECRET_FIELDS if field_id in normalized_payload and bool(normalized_payload.get(field_id))}

        # When operators switch auth strategy we treat the newly submitted
        # credential family as authoritative instead of blending it with
        # previously stored secrets from another mode.
        if {"auth_client_secret", "auth_password"} & updated_secret_fields:
            current_secrets.pop("rime_api_key", None)
        if "rime_api_key" in updated_secret_fields:
            current_secrets.pop("auth_client_secret", None)
            current_secrets.pop("auth_password", None)

        # Secret fields are persisted only when the operator deliberately sends a
        # non-empty value. Blank values mean "keep existing secret" instead of
        # accidentally deleting credentials during an unrelated save.
        for secret_field in self.SECRET_FIELDS:
            if secret_field in normalized_payload:
                secret_value = normalized_payload.get(secret_field)
                if secret_value:
                    current_secrets[secret_field] = secret_value
            merged_values.pop(secret_field, None)

        readiness = self._calculate_readiness(merged_values, current_secrets)
        self.configs.save(
            config_payload=merged_values,
            secret_payload=current_secrets,
            status_payload=self._merge_status_payload(current_status, readiness=readiness),
        )
        self._sync_shared_settings(values=merged_values, secrets=current_secrets, readiness=readiness)
        self._log_rcs_event(
            "settings_saved",
            trace_id=trace_id,
            readiness=readiness,
            payload={
                "updated_fields": sorted(payload.keys()),
                "normalized_fields": sorted(normalized_payload.keys()),
                "secret_fields_updated": sorted(updated_secret_fields),
                "config_summary": self._config_summary(merged_values, current_secrets),
            },
        )
        response = self.get_rcs_settings(trace_id=trace_id)
        response["save_result"] = {
            "success": True,
            "message": "RCS configuration saved successfully",
        }
        return response

    def validate_rcs_settings(self, *, trace_id: str | None = None) -> dict[str, Any]:
        response = self.get_rcs_settings(trace_id=trace_id)
        readiness = response["readiness"]
        result = {
            "success": readiness["ready"],
            "readiness": readiness,
            "connection_diagnostics": response["connection_diagnostics"],
            "message": readiness["headline"],
            "trace_id": trace_id,
        }
        self._log_rcs_event(
            "settings_validated",
            trace_id=trace_id,
            readiness=readiness,
            payload={
                "result": "ready" if readiness["ready"] else "not_ready",
                "config_summary": self._config_summary(response["settings"]["values"], self._extract_secret_state(self.configs.get())),
            },
        )
        return result

    def fetch_latest_callback(self, *, trace_id: str | None = None) -> dict[str, Any]:
        record = self.configs.get()
        response = self.get_rcs_settings(trace_id=trace_id)
        values = response["settings"]["values"]
        readiness = response["readiness"]
        secrets = self._extract_secret_state(record)
        current_status = deepcopy(record.status_payload or {}) if record is not None else {}
        resolved_url = self._resolve_webhook_latest_request_url(values)
        api_key_present = bool(secrets.get("webhook_api_key"))
        webhook_site_public_fetch = "webhook.site/token/" in str(values.get("webhook_fetch_url") or "").strip()

        if not resolved_url or (not api_key_present and not webhook_site_public_fetch):
            result = {
                "success": False,
                "message": "Webhook callback fetch is not ready. Please set webhook_fetch_url and, if required by the endpoint, webhook_api_key.",
                "trace_id": trace_id,
                "webhook_fetch_url": values.get("webhook_fetch_url"),
                "resolved_latest_request_url": resolved_url,
                "api_key_present": api_key_present,
                "steps": [
                    {"step": "fetch_config_check", "status": "failed", "detail": "Missing webhook_fetch_url or required webhook_api_key"},
                    {"step": "resolved_latest_request_url", "status": "done", "detail": resolved_url or "not_available"},
                ],
            }
            self.configs.save(
                config_payload=deepcopy(values),
                secret_payload=secrets,
                status_payload=self._merge_status_payload(
                    current_status,
                    readiness=readiness,
                    last_callback_fetch=self._build_last_callback_fetch(result),
                ),
            )
            self._sync_shared_settings(
                values=values,
                secrets=secrets,
                readiness=readiness,
                extra_status={"last_callback_fetch": self._build_last_callback_fetch(result)},
            )
            result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
            self._log_rcs_event(
                "callback_fetch_failed",
                trace_id=trace_id,
                readiness=readiness,
                payload={
                    "webhook_fetch_url": values.get("webhook_fetch_url"),
                    "resolved_latest_request_url": resolved_url,
                    "api_key_present": api_key_present,
                    "steps": result["steps"] if self._verbose_connection_logging_enabled(values) else [],
                },
            )
            return result

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Trace-Id": trace_id or "",
        }
        if api_key_present:
            headers["Api-Key"] = secrets["webhook_api_key"]
        try:
            with httpx.Client(timeout=10.0) as client:
                api_response = client.get(resolved_url, headers=headers)
            response_excerpt = api_response.text[:500]
            try:
                raw_response_json = api_response.json()
            except ValueError:
                raw_response_json = None
            response_json = self._select_webhook_request_payload(raw_response_json)
            callback_summary = self._summarize_webhook_callback(response_json)
            result = {
                "success": 200 <= api_response.status_code < 300,
                "message": (
                    "Latest webhook callback fetched successfully"
                    if 200 <= api_response.status_code < 300
                    else f"Webhook callback fetch failed with status {api_response.status_code}"
                ),
                "trace_id": trace_id,
                "webhook_fetch_url": values.get("webhook_fetch_url"),
                "resolved_latest_request_url": resolved_url,
                "api_key_present": True,
                "provider_status_code": api_response.status_code,
                "response_excerpt": response_excerpt,
                "response_json": response_json,
                "raw_fetch_response_json": raw_response_json,
                "parsed_content_json": callback_summary.get("parsed_content_json"),
                "normalized_event_type": callback_summary.get("normalized_event_type"),
                "reply_intent": callback_summary.get("reply_intent"),
                "reply_datetime_candidates": callback_summary.get("reply_datetime_candidates"),
                "callback_transport": callback_summary.get("callback_transport"),
                "callback_source_method": callback_summary.get("callback_source_method"),
                "request_preview": {
                    "method": "GET",
                    "url": resolved_url,
                    "headers": {
                        "Accept": headers["Accept"],
                        "Content-Type": headers["Content-Type"],
                        "Api-Key": "********" if headers.get("Api-Key") else None,
                        "X-Trace-Id": headers["X-Trace-Id"],
                    },
                },
                "steps": [
                    {"step": "fetch_config_check", "status": "ok", "detail": "Webhook.site fetch configuration is complete"},
                    {"step": "resolved_latest_request_url", "status": "done", "detail": resolved_url},
                    {"step": "webhook_api_request", "status": "done", "detail": f"GET {resolved_url}"},
                    {"step": "webhook_api_response", "status": "done", "detail": f"HTTP {api_response.status_code}"},
                    {"step": "callback_parse", "status": "done", "detail": callback_summary.get("normalized_event_type", "message.unknown")},
                ],
            }
        except httpx.HTTPError as exc:
            result = {
                "success": False,
                "message": f"Webhook callback fetch failed: {exc.__class__.__name__}",
                "trace_id": trace_id,
                "webhook_fetch_url": values.get("webhook_fetch_url"),
                "resolved_latest_request_url": resolved_url,
                "api_key_present": True,
                "provider_status_code": 0,
                "response_excerpt": f"http_error:{exc.__class__.__name__}:{str(exc)[:240]}",
                "response_json": None,
                "request_preview": {
                    "method": "GET",
                    "url": resolved_url,
                    "headers": {
                        "Accept": headers["Accept"],
                        "Content-Type": headers["Content-Type"],
                        "Api-Key": "********" if headers.get("Api-Key") else None,
                        "X-Trace-Id": headers["X-Trace-Id"],
                    },
                },
                "steps": [
                    {"step": "fetch_config_check", "status": "ok", "detail": "Webhook.site fetch configuration is complete"},
                    {"step": "resolved_latest_request_url", "status": "done", "detail": resolved_url},
                    {"step": "webhook_api_request", "status": "done", "detail": f"GET {resolved_url}"},
                    {"step": "webhook_api_response", "status": "failed", "detail": f"{exc.__class__.__name__}: {str(exc)[:180]}"},
                ],
            }

        self.configs.save(
            config_payload=deepcopy(values),
            secret_payload=secrets,
            status_payload=self._merge_status_payload(
                current_status,
                readiness=readiness,
                last_callback_fetch=self._build_last_callback_fetch(result),
            ),
        )
        self._sync_shared_settings(
            values=values,
            secrets=secrets,
            readiness=readiness,
            extra_status={"last_callback_fetch": self._build_last_callback_fetch(result)},
        )
        if result["success"]:
            self._store_callback_message(values=values, trace_id=trace_id, result=result)
        result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
        self._log_rcs_event(
            "callback_fetch_succeeded" if result["success"] else "callback_fetch_failed",
            trace_id=trace_id,
            readiness=readiness,
            payload={
                "webhook_fetch_url": values.get("webhook_fetch_url"),
                "resolved_latest_request_url": resolved_url,
                "provider_status_code": result.get("provider_status_code"),
                "request_preview": result.get("request_preview"),
                "response_excerpt": result.get("response_excerpt"),
                "steps": result.get("steps") if self._verbose_connection_logging_enabled(values) else [],
            },
        )
        return result

    def test_rcs_connection(self, *, trace_id: str | None = None) -> dict[str, Any]:
        record = self.configs.get()
        response = self.get_rcs_settings(trace_id=trace_id)
        readiness = response["readiness"]
        secrets = self._extract_secret_state(record)
        current_status = deepcopy(record.status_payload or {}) if record is not None else {}
        config_summary = self._config_summary(response["settings"]["values"], secrets)
        auth_mode = readiness.get("auth_mode", "unknown")
        provider_endpoint = readiness.get("provider_endpoint")
        effective_mock_mode = self._mock_connection_mode_enabled(response["settings"]["values"])
        if not readiness["ready"]:
            steps = [
                {"step": "readiness_check", "status": "failed", "detail": readiness["headline"]},
                {"step": "auth_mode_selection", "status": "done", "detail": auth_mode},
            ]
            result = {
                "success": False,
                "message": readiness["headline"],
                "readiness": readiness,
                "trace_id": trace_id,
                "auth_mode": auth_mode,
                "provider_endpoint": provider_endpoint,
                "provider_request_sent": False,
                "steps": steps,
            }
            self.configs.save(
                config_payload=deepcopy(response["settings"]["values"]),
                secret_payload=secrets,
                status_payload=self._merge_status_payload(
                    current_status,
                    readiness=readiness,
                    last_connection_test=self._build_last_connection_test(result),
                ),
            )
            self._sync_shared_settings(
                values=response["settings"]["values"],
                secrets=secrets,
                readiness=readiness,
                extra_status={"last_connection_test": self._build_last_connection_test(result)},
            )
            result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
            self._log_rcs_event(
                "test_connection_failed",
                trace_id=trace_id,
                readiness=readiness,
                payload={
                    "mode": "mock_connection_test" if effective_mock_mode else "provider_connection_test",
                    "config_summary": config_summary,
                    "reason": "configuration_incomplete_or_rcs_disabled",
                    "provider_request_sent": False,
                    "steps": steps if self._verbose_connection_logging_enabled(response["settings"]["values"]) else [],
                },
            )
            return result
        if effective_mock_mode:
            steps = [
                {"step": "readiness_check", "status": "ok", "detail": readiness["headline"]},
                {"step": "auth_mode_selection", "status": "done", "detail": auth_mode},
                {"step": "provider_request", "status": "skipped", "detail": "Mock mode enabled, no provider POST sent"},
            ]
            result = {
                "success": True,
                "message": "LEKAB adapter ready for test messaging (mock mode, no provider POST sent)",
                "mode": "mock_connection_test",
                "readiness": readiness,
                "trace_id": trace_id,
                "auth_mode": auth_mode,
                "provider_endpoint": provider_endpoint,
                "provider_request_sent": False,
                "steps": steps,
            }
            self.configs.save(
                config_payload=deepcopy(response["settings"]["values"]),
                secret_payload=secrets,
                status_payload=self._merge_status_payload(
                    current_status,
                    readiness=readiness,
                    last_connection_test=self._build_last_connection_test(result),
                ),
            )
            self._sync_shared_settings(
                values=response["settings"]["values"],
                secrets=secrets,
                readiness=readiness,
                extra_status={"last_connection_test": self._build_last_connection_test(result)},
            )
            result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
            self._log_rcs_event(
                "test_connection_succeeded",
                trace_id=trace_id,
                readiness=readiness,
                payload={
                    "mode": result["mode"],
                    "auth_mode": auth_mode,
                    "provider_endpoint": provider_endpoint,
                    "provider_request_sent": False,
                    "config_summary": config_summary,
                    "steps": steps if self._verbose_connection_logging_enabled(response["settings"]["values"]) else [],
                },
            )
            return result

        if not self._provider_test_post_supported(auth_mode):
            steps = [
                {"step": "readiness_check", "status": "ok", "detail": readiness["headline"]},
                {"step": "auth_mode_selection", "status": "done", "detail": auth_mode},
                {
                    "step": "provider_auth_handoff",
                    "status": "failed",
                    "detail": "OAuth/password mode is configured, but Patch 7 blocks unauthenticated provider POST tests until token handoff is implemented safely.",
                },
            ]
            result = {
                "success": False,
                "message": "OAuth/password configuration is present, but provider POST testing is blocked until safe token handoff is available. Use mock mode or configure a RIME API key.",
                "mode": "provider_connection_test",
                "readiness": readiness,
                "trace_id": trace_id,
                "auth_mode": auth_mode,
                "provider_endpoint": provider_endpoint,
                "provider_request_sent": False,
                "provider_status_code": None,
                "provider_response_excerpt": "",
                "provider_request_preview": {
                    "method": "POST",
                    "url": provider_endpoint,
                    "headers": {
                        "Content-Type": "application/json",
                        "X-Trace-Id": trace_id or "",
                    },
                    "json": {},
                },
                "steps": steps,
            }
            self.configs.save(
                config_payload=deepcopy(response["settings"]["values"]),
                secret_payload=secrets,
                status_payload=self._merge_status_payload(
                    current_status,
                    readiness=readiness,
                    last_connection_test=self._build_last_connection_test(result),
                ),
            )
            self._sync_shared_settings(
                values=response["settings"]["values"],
                secrets=secrets,
                readiness=readiness,
                extra_status={"last_connection_test": self._build_last_connection_test(result)},
            )
            result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
            self._log_rcs_event(
                "test_connection_failed",
                trace_id=trace_id,
                readiness=readiness,
                payload={
                    "mode": result["mode"],
                    "auth_mode": auth_mode,
                    "provider_endpoint": provider_endpoint,
                    "provider_request_sent": False,
                    "config_summary": config_summary,
                    "reason": "provider_post_blocked_without_safe_token_handoff",
                    "steps": steps if self._verbose_connection_logging_enabled(response["settings"]["values"]) else [],
                },
            )
            return result

        provider_result = self._send_provider_test_post(
            values=response["settings"]["values"],
            secrets=secrets,
            trace_id=trace_id,
            auth_mode=auth_mode,
        )
        success = 200 <= provider_result["provider_status_code"] < 300
        result = {
            "success": success,
            "message": (
                "LEKAB provider test POST accepted"
                if success
                else (
                    "LEKAB provider test POST failed with status 401. Check the configured credentials or auth mode."
                    if provider_result["provider_status_code"] == 401
                    else f"LEKAB provider test POST failed with status {provider_result['provider_status_code']}"
                )
            ),
            "mode": "provider_connection_test",
            "readiness": readiness,
            "trace_id": trace_id,
            "auth_mode": auth_mode,
            "provider_endpoint": provider_endpoint,
            "provider_request_sent": True,
            "provider_status_code": provider_result["provider_status_code"],
            "provider_response_excerpt": provider_result["provider_response_excerpt"],
            "provider_request_preview": provider_result["provider_request_preview"],
            "steps": provider_result["steps"],
        }
        self.configs.save(
            config_payload=deepcopy(response["settings"]["values"]),
            secret_payload=secrets,
            status_payload=self._merge_status_payload(
                current_status,
                readiness=readiness,
                last_connection_test=self._build_last_connection_test(result),
            ),
        )
        self._sync_shared_settings(
            values=response["settings"]["values"],
            secrets=secrets,
            readiness=readiness,
            extra_status={"last_connection_test": self._build_last_connection_test(result)},
        )
        self._store_outbound_test_connection_message(
            values=response["settings"]["values"],
            readiness=readiness,
            trace_id=trace_id,
            result=result,
        )
        result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
        self._log_rcs_event(
            "test_connection_succeeded" if result["success"] else "test_connection_failed",
            trace_id=trace_id,
            readiness=readiness,
            payload={
                "mode": result["mode"],
                "auth_mode": auth_mode,
                "provider_endpoint": provider_endpoint,
                "provider_request_sent": True,
                "provider_status_code": provider_result["provider_status_code"],
                "provider_response_excerpt": provider_result["provider_response_excerpt"],
                "config_summary": config_summary,
                "steps": provider_result["steps"] if self._verbose_connection_logging_enabled(response["settings"]["values"]) else [],
            },
        )
        return result

    def configure_provider_callback_urls(self, *, trace_id: str | None = None) -> dict[str, Any]:
        record = self.configs.get()
        response = self.get_rcs_settings(trace_id=trace_id)
        readiness = response["readiness"]
        values = response["settings"]["values"]
        secrets = self._extract_secret_state(record)
        current_status = deepcopy(record.status_payload or {}) if record is not None else {}
        result = self._configure_provider_callback_urls(
            values=values,
            secrets=secrets,
            trace_id=trace_id,
            readiness=readiness,
        )
        self.configs.save(
            config_payload=deepcopy(values),
            secret_payload=secrets,
            status_payload=self._merge_status_payload(
                current_status,
                readiness=readiness,
                last_seturl=result,
            ),
        )
        self._sync_shared_settings(
            values=values,
            secrets=secrets,
            readiness=readiness,
            extra_status={"last_seturl": result},
        )
        result["connection_diagnostics"] = self.get_rcs_settings(trace_id=trace_id)["connection_diagnostics"]
        return result

    def send_message(
        self,
        *,
        channel: str,
        tenant_id: str,
        correlation_id: str,
        phone_number: str,
        body: str,
        customer_id: str | None = None,
        contact_reference: str | None = None,
        journey_id: str | None = None,
        booking_reference: str | None = None,
        message_type: str = "text",
        actions: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        record = self.configs.get()
        values = self._normalized_config_values(record.config_payload or {}) if record is not None else self._default_config()
        secrets = self._extract_secret_state(record)
        readiness = self._calculate_readiness(values, secrets)
        effective_mock_mode = self._mock_connection_mode_enabled(values)
        resolved_contact = None
        if not customer_id and not contact_reference:
            resolved_contact = self.resolve_contact(tenant_id=tenant_id, phone_number=phone_number)
            customer_id = resolved_contact["customer_id"] or customer_id
            contact_reference = resolved_contact["contact_reference"] or contact_reference

        outbound_actions = actions or []
        provider_message_id = f"{channel.lower()}-{uuid4().hex[:14]}"
        provider_job_id = f"lekab-job-{uuid4().hex[:10]}"
        provider_payload = {
            "provider_path": "rime_send" if channel == "RCS" else "sms_send",
            "channel": channel,
            "recipient": phone_number,
            "body": body,
            "actions": deepcopy(outbound_actions),
            "mock_mode": effective_mock_mode,
        }
        status = "accepted" if effective_mock_mode else "submitted"
        if channel == "RCS" and not effective_mock_mode:
            if not readiness["ready"] or readiness.get("auth_mode") != "rime_api_key":
                status = "failed"
                provider_payload["provider_error"] = "real_send_blocked_configuration_not_ready"
            else:
                seturl_result = self._configure_provider_callback_urls(
                    values=values,
                    secrets=secrets,
                    trace_id=correlation_id,
                    readiness=readiness,
                )
                provider_payload["seturl"] = deepcopy(seturl_result)
                if not seturl_result.get("success"):
                    callback_url = str(values.get("callback_url") or "").strip()
                    webhook_fetch_url = str(values.get("webhook_fetch_url") or "").strip()
                    best_effort_webhook_mode = "webhook.site" in callback_url and bool(webhook_fetch_url)
                    if best_effort_webhook_mode:
                        provider_payload["provider_warning"] = "seturl_failed_best_effort_send_enabled"
                    else:
                        status = "failed"
                        provider_payload["provider_error"] = "seturl_failed"
                if status != "failed":
                    provider_result = self._send_provider_message_post(
                        values=values,
                        secrets=secrets,
                        trace_id=correlation_id,
                        channel=channel,
                        phone_number=phone_number,
                        body=body,
                        actions=outbound_actions,
                    )
                    provider_message_id = provider_result.get("provider_message_id") or provider_message_id
                    provider_job_id = provider_result.get("provider_job_id") or provider_job_id
                    provider_payload.update(deepcopy(provider_result))
                    status = "submitted" if 200 <= provider_result.get("provider_status_code", 0) < 300 else "failed"

        normalized = self._build_normalized_message(
            message_id=f"msg-{uuid4().hex[:12]}",
            provider_message_id=provider_message_id,
            provider_job_id=provider_job_id,
            channel=channel,
            direction="outbound",
            status=status,
            customer_id=customer_id,
            contact_reference=contact_reference,
            phone_number=phone_number,
            journey_id=journey_id,
            booking_reference=booking_reference,
            message_type=message_type,
            body=body,
            actions=outbound_actions,
            metadata={
                "provider_path": "rime_send" if channel == "RCS" else "sms_send",
                "contact_resolution": resolved_contact,
                **(metadata or {}),
            },
            provider_payload=provider_payload,
            correlation_ref=correlation_id,
        )
        self._store_message(normalized)
        self._publish_event(
            event_type="lekab.message.outbound.accepted" if status != "failed" else "lekab.message.outbound.failed",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=normalized.model_dump(mode="json"),
        )
        return normalized

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
            "test_recipient_address": "491705707716",
            "callback_url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
            "receipt_callback_url": "https://webhook.site/0afb4569-94b5-49cd-970c-556d3e92d5c6",
            "webhook_fetch_url": "https://webhook.site/token/0afb4569-94b5-49cd-970c-556d3e92d5c6",
            "channel_priority": "RCS_FIRST",
            "sms_fallback_enabled": True,
            "sms_enabled": True,
            "sms_sender_name": "APPT",
            "sms_length_mode": "auto_split",
            "default_language": "en",
            "addressbook_enabled": True,
            "contact_lookup_mode": "phone_first",
            "phone_normalization_mode": "E164",
            "mock_connection_mode": self.mock_mode,
            "verbose_connection_logging": True,
        }

    def _extract_secret_state(self, record) -> dict[str, str]:
        if record is None:
            return {}
        return deepcopy(record.secret_payload or {})

    def _config_summary(self, values: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
        """Return a log-safe configuration summary.

        The operator needs logs that explain *what kind* of configuration was
        used, but we must never print secrets or full credential payloads. This
        summary keeps just the fields that help diagnose a connection attempt.
        """

        return {
            "workspace_id": values.get("workspace_id"),
            "environment_name": values.get("environment_name"),
            "messaging_environment": values.get("messaging_environment"),
            "verbose_connection_logging": self._verbose_connection_logging_enabled(values),
            "channel_priority": values.get("channel_priority"),
            "rcs_enabled": bool(values.get("rcs_enabled")),
            "sms_fallback_enabled": bool(values.get("sms_fallback_enabled")),
            "callback_url": values.get("callback_url"),
            "webhook_fetch_url": values.get("webhook_fetch_url"),
            "auth_base_url": values.get("auth_base_url"),
            "dispatch_base_url": values.get("dispatch_base_url"),
            "rime_base_url": values.get("rime_base_url"),
            "auth_mode": self._determine_auth_mode(values, secrets),
            "saved_secret_fields": sorted(field_id for field_id, secret_value in secrets.items() if bool(secret_value)),
        }

    def _verbose_connection_logging_enabled(self, values: dict[str, Any]) -> bool:
        return bool(values.get("verbose_connection_logging", True))

    def _mock_connection_mode_enabled(self, values: dict[str, Any]) -> bool:
        return bool(values.get("mock_connection_mode", self.mock_mode))

    def _resolve_webhook_latest_request_url(self, values: dict[str, Any]) -> str | None:
        configured = (values.get("webhook_fetch_url") or "").strip()
        callback_url = (values.get("callback_url") or "").strip()
        token_id = self._extract_webhook_site_token(configured) or self._extract_webhook_site_token(callback_url)
        if token_id:
            return f"https://webhook.site/token/{token_id}/requests?sorting=newest&per_page=25"
        candidate = configured or callback_url
        if not candidate:
            return None
        if "/token/" in candidate and candidate.endswith("/request/latest"):
            return candidate
        if "/token/" in candidate:
            return candidate.rstrip("/") + "/request/latest"
        match = re.match(r"^https://webhook\.site/([0-9a-fA-F-]{36})/?$", candidate)
        if match:
            return f"https://webhook.site/token/{match.group(1)}/request/latest"
        return None

    def _resolve_receipt_callback_url(self, values: dict[str, Any]) -> str:
        callback_url = str(values.get("callback_url") or "").strip()
        receipt_url = str(values.get("receipt_callback_url") or "").strip()
        if "webhook.site" in callback_url and (not receipt_url or "demo.example.test" in receipt_url):
            return callback_url
        return receipt_url or callback_url

    def _extract_webhook_site_token(self, candidate: str | None) -> str | None:
        value = str(candidate or "").strip()
        token_match = re.match(r"^https://webhook\.site/token/([0-9a-fA-F-]{36})(?:/.*)?$", value)
        if token_match:
            return token_match.group(1)
        capture_match = re.match(r"^https://webhook\.site/([0-9a-fA-F-]{36})/?$", value)
        if capture_match:
            return capture_match.group(1)
        return None

    def _normalize_webhook_site_settings_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = deepcopy(payload)
        callback_token = self._extract_webhook_site_token(normalized.get("callback_url"))
        fetch_token = self._extract_webhook_site_token(normalized.get("webhook_fetch_url"))
        receipt_token = self._extract_webhook_site_token(normalized.get("receipt_callback_url"))
        token_id = callback_token or fetch_token or receipt_token
        if not token_id:
            return normalized

        capture_url = f"https://webhook.site/{token_id}"
        fetch_url = f"https://webhook.site/token/{token_id}"
        normalized["callback_url"] = capture_url
        if str(normalized.get("receipt_callback_url") or "").strip():
            normalized["receipt_callback_url"] = capture_url
        else:
            normalized.setdefault("receipt_callback_url", capture_url)
        if str(normalized.get("webhook_fetch_url") or "").strip():
            normalized["webhook_fetch_url"] = fetch_url
        else:
            normalized.setdefault("webhook_fetch_url", fetch_url)
        return normalized

    def _select_webhook_request_payload(self, response_json: Any) -> dict[str, Any] | None:
        if isinstance(response_json, dict) and isinstance(response_json.get("uuid"), str):
            return response_json
        request_items: list[dict[str, Any]] = []
        if isinstance(response_json, dict):
            for key in ("data", "requests"):
                items = response_json.get(key)
                if isinstance(items, list):
                    request_items = [item for item in items if isinstance(item, dict)]
                    break
        elif isinstance(response_json, list):
            request_items = [item for item in response_json if isinstance(item, dict)]
        if not request_items:
            return response_json if isinstance(response_json, dict) else None

        def _score(item: dict[str, Any]) -> tuple[int, int]:
            parsed_payload = self._extract_webhook_request_payload(item)
            has_reply_signal = any(
                parsed_payload.get(key)
                for key in ("reply", "button", "selectedSuggestion", "selected_suggestion", "suggestionReply", "buttonReply", "postbackData", "postback_data")
            )
            status_value = str(parsed_payload.get("status") or "").strip().upper()
            reply_text = self._extract_reply_body_text(parsed_payload)
            score = 0
            if has_reply_signal or reply_text:
                score += 3
            if status_value not in {"", "DELIVERED", "READ", "FAILED", "UNDELIVERABLE", "REJECTED"}:
                score += 2
            created = str(item.get("created_at") or "")
            return (score, 1 if created else 0)

        request_items.sort(key=_score, reverse=True)
        return request_items[0]

    def _resolve_seturl_endpoint(self, values: dict[str, Any]) -> str | None:
        base_url = str(values.get("rime_base_url") or "").strip()
        if not base_url:
            return None
        if base_url.endswith("/send"):
            return f"{base_url[:-5]}/seturl"
        return f"{base_url.rstrip('/')}/seturl"

    def _build_rime_headers(self, *, secrets: dict[str, str], trace_id: str | None, auth_mode: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": trace_id or "",
        }
        if auth_mode == "rime_api_key" and secrets.get("rime_api_key"):
            headers["X-API-Key"] = secrets["rime_api_key"]
        return headers

    def _build_rime_send_payload(
        self,
        *,
        channel: str,
        phone_number: str,
        body: str,
        actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "channels": channel,
            "address": phone_number,
            "richMessage": {
                "text": body,
            },
        }
        if actions:
            payload["richMessage"]["suggestions"] = [
                {
                    "reply": {
                        "text": str(item.get("label") or item.get("value") or ""),
                        "postbackData": str(item.get("value") or item.get("action_id") or item.get("label") or ""),
                    }
                }
                for item in actions
            ]
        return payload

    def _configure_provider_callback_urls(
        self,
        *,
        values: dict[str, Any],
        secrets: dict[str, str],
        trace_id: str | None,
        readiness: dict[str, Any],
    ) -> dict[str, Any]:
        incoming_url = str(values.get("callback_url") or "").strip()
        receipt_url = self._resolve_receipt_callback_url(values)
        endpoint = self._resolve_seturl_endpoint(values)
        auth_mode = readiness.get("auth_mode", "unknown")
        headers = self._build_rime_headers(secrets=secrets, trace_id=trace_id, auth_mode=auth_mode)
        request_payload = {
            "channels": "RCS",
            "receipttype": "JSON",
            "receipturl": receipt_url,
            "incomingtype": "JSON",
            "incomingurl": incoming_url,
        }
        if not endpoint or not incoming_url or not receipt_url:
            return {
                "success": False,
                "message": "RIME callback URL configuration is incomplete.",
                "trace_id": trace_id,
                "seturl_endpoint": endpoint,
                "incoming_url": incoming_url,
                "receipt_url": receipt_url,
                "provider_status_code": None,
                "request_preview": {"method": "POST", "url": endpoint, "json": request_payload},
            }
        try:
            logger.info(
                "SetURL Payload: %s",
                {
                    "method": "POST",
                    "url": endpoint,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": request_payload,
                },
            )
            with httpx.Client(timeout=10.0) as client:
                response = client.post(endpoint, headers=headers, json=request_payload)
            logger.info("SetURL Response: %s", response.text[:1000])
            return {
                "success": 200 <= response.status_code < 300,
                "message": "RIME callback URLs configured." if 200 <= response.status_code < 300 else f"RIME /seturl failed with status {response.status_code}",
                "trace_id": trace_id,
                "seturl_endpoint": endpoint,
                "incoming_url": incoming_url,
                "receipt_url": receipt_url,
                "provider_status_code": response.status_code,
                "provider_response_excerpt": response.text[:300],
                "request_preview": {
                    "method": "POST",
                    "url": endpoint,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": request_payload,
                },
            }
        except httpx.HTTPError as exc:
            return {
                "success": False,
                "message": f"RIME /seturl failed: {exc.__class__.__name__}",
                "trace_id": trace_id,
                "seturl_endpoint": endpoint,
                "incoming_url": incoming_url,
                "receipt_url": receipt_url,
                "provider_status_code": 0,
                "provider_response_excerpt": f"http_error:{exc.__class__.__name__}:{str(exc)[:240]}",
                "request_preview": {
                    "method": "POST",
                    "url": endpoint,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": request_payload,
                },
            }

    def _safe_json_loads(self, raw_value: Any) -> Any:
        if not isinstance(raw_value, str):
            return raw_value
        stripped = raw_value.strip()
        if not stripped or stripped[0] not in {'{', '[', '"'}:
            return raw_value
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value

    def _extract_webhook_request_payload(self, response_json: Any) -> dict[str, Any]:
        payload = response_json if isinstance(response_json, dict) else {}
        extracted: dict[str, Any] = {}
        content = self._safe_json_loads(payload.get("content"))
        if isinstance(content, dict):
            extracted.update(content)
        elif isinstance(content, str):
            content_text = content.strip()
            if content_text:
                parsed_form = parse_qs(content_text, keep_blank_values=True)
                if parsed_form:
                    for key, values in parsed_form.items():
                        extracted[key] = values[-1] if values else ""

        query_payload = payload.get("query")
        if isinstance(query_payload, dict):
            for key, value in query_payload.items():
                if isinstance(value, list):
                    candidate_value = value[-1] if value else ""
                else:
                    candidate_value = value
                extracted[key] = self._safe_json_loads(candidate_value)
        request_url = str(payload.get("url") or "").strip()
        if request_url:
            parsed_url = urlparse(request_url)
            parsed_query = parse_qs(parsed_url.query, keep_blank_values=True)
            for key, values in parsed_query.items():
                extracted.setdefault(key, self._safe_json_loads(values[-1] if values else ""))
        return extracted

    def _extract_datetime_candidates(self, text: str) -> list[str]:
        matches = re.findall(
            r"\b(?:\d{1,2}[.:]\d{2}|\d{1,2}\.\d{1,2}\.\d{2,4}|\d{4}-\d{2}-\d{2})\b",
            text,
            flags=re.IGNORECASE,
        )
        return sorted(dict.fromkeys(matches))

    def _classify_reply_intent(self, text: str) -> dict[str, Any]:
        normalized = (text or "").strip().lower()
        candidates = self._extract_datetime_candidates(text or "")
        if any(token in normalized for token in ("cancel", "storn", "absagen", "abbrechen")):
            return {"reply_intent": "cancel", "normalized_event_type": "message.reply_received", "reply_datetime_candidates": candidates}
        if any(token in normalized for token in ("reschedule", "verschieb", "anderer termin", "neuer termin", "umplan")):
            return {"reply_intent": "reschedule", "normalized_event_type": "message.reply_received", "reply_datetime_candidates": candidates}
        if candidates:
            return {"reply_intent": "datetime_proposal", "normalized_event_type": "message.reply_received", "reply_datetime_candidates": candidates}
        return {"reply_intent": "free_text", "normalized_event_type": "message.reply_received", "reply_datetime_candidates": candidates}

    def _summarize_webhook_callback(self, response_json: Any) -> dict[str, Any]:
        payload = response_json if isinstance(response_json, dict) else {}
        parsed_content = self._safe_json_loads(payload.get("content"))
        parsed_content_json = parsed_content if isinstance(parsed_content, dict) else None
        status_value = str((parsed_content_json or {}).get("status") or "").strip().upper()
        body_text = (
            (parsed_content_json or {}).get("text")
            or (parsed_content_json or {}).get("body")
            or (parsed_content_json or {}).get("message")
            or ""
        )
        if status_value == "DELIVERED":
            normalized_event_type = "message.delivered"
            reply_intent = None
            datetime_candidates: list[str] = []
        elif status_value in {"FAILED", "UNDELIVERABLE", "REJECTED"}:
            normalized_event_type = "message.failed"
            reply_intent = None
            datetime_candidates = []
        elif body_text:
            reply_info = self._classify_reply_intent(body_text)
            normalized_event_type = reply_info["normalized_event_type"]
            reply_intent = reply_info["reply_intent"]
            datetime_candidates = reply_info["reply_datetime_candidates"]
        else:
            normalized_event_type = "message.unknown"
            reply_intent = None
            datetime_candidates = []
        return {
            "parsed_content_json": parsed_content_json,
            "normalized_event_type": normalized_event_type,
            "reply_intent": reply_intent,
            "reply_datetime_candidates": datetime_candidates,
            "channel": (parsed_content_json or {}).get("channel") or "RCS",
            "from": (parsed_content_json or {}).get("from"),
            "to": (parsed_content_json or {}).get("to"),
            "provider_message_id": (parsed_content_json or {}).get("id"),
            "status": status_value.lower() if status_value else "received",
            "body_text": body_text if body_text else status_value or payload.get("content") or "",
            "provider_timestamp": (parsed_content_json or {}).get("time"),
        }

    def _send_provider_message_post(
        self,
        *,
        values: dict[str, Any],
        secrets: dict[str, str],
        trace_id: str | None,
        channel: str,
        phone_number: str,
        body: str,
        actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        auth_mode = self._determine_auth_mode(values, secrets)
        endpoint = str(values.get("rime_base_url") or "").strip()
        headers = self._build_rime_headers(secrets=secrets, trace_id=trace_id, auth_mode=auth_mode)
        payload = self._build_rime_send_payload(channel=channel, phone_number=phone_number, body=body, actions=actions)
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(endpoint, headers=headers, json=payload)
            return {
                "provider_status_code": response.status_code,
                "provider_response_excerpt": response.text[:300],
                "provider_request_preview": {
                    "method": "POST",
                    "url": endpoint,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": payload,
                },
            }
        except httpx.HTTPError as exc:
            return {
                "provider_status_code": 0,
                "provider_response_excerpt": f"http_error:{exc.__class__.__name__}:{str(exc)[:240]}",
                "provider_request_preview": {
                    "method": "POST",
                    "url": endpoint,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": payload,
                },
            }

    def _store_outbound_test_connection_message(
        self,
        *,
        values: dict[str, Any],
        readiness: dict[str, Any],
        trace_id: str | None,
        result: dict[str, Any],
    ) -> None:
        preview = result.get("provider_request_preview") or {}
        payload_json = preview.get("json") or {}
        body_text = ((payload_json.get("richMessage") or {}).get("text") or "Appointment Agent LEKAB RIME connection test").strip()
        status = "accepted" if result.get("success") else "failed"
        message = self._build_normalized_message(
            message_id=f"msg-out-{(trace_id or uuid4().hex)[:24]}",
            provider_message_id=result.get("trace_id"),
            provider_job_id=result.get("trace_id"),
            channel=str(payload_json.get("channels") or "RCS"),
            direction="outbound",
            status=status,
            customer_id=None,
            contact_reference=None,
            phone_number=payload_json.get("address") or values.get("test_recipient_address"),
            journey_id=None,
            booking_reference=None,
            message_type="text",
            body=body_text,
            actions=[],
            metadata={
                "source": "rcs_test_connection",
                "trace_id": trace_id,
                "normalized_event_type": "message.outbound_submitted" if result.get("success") else "message.outbound_failed",
                "provider_endpoint": readiness.get("provider_endpoint"),
            },
            provider_payload={
                "request_preview": preview,
                "response_excerpt": result.get("provider_response_excerpt"),
                "provider_status_code": result.get("provider_status_code"),
            },
        )
        self._store_message(message)

    def _store_callback_message(self, *, values: dict[str, Any], trace_id: str | None, result: dict[str, Any]) -> None:
        response_json = result.get("response_json") if isinstance(result.get("response_json"), dict) else {}
        summary = self._summarize_webhook_callback(response_json)
        callback_uuid = response_json.get("uuid") or f"callback-{uuid4().hex[:12]}"
        message = self._build_normalized_message(
            message_id=f"msg-in-{callback_uuid}",
            provider_message_id=summary.get("provider_message_id") or callback_uuid,
            provider_job_id=None,
            channel=str(summary.get("channel") or "RCS"),
            direction="inbound",
            status=str(summary.get("status") or "received"),
            customer_id=None,
            contact_reference=None,
            phone_number=summary.get("to"),
            journey_id=None,
            booking_reference=None,
            message_type="status" if summary.get("normalized_event_type") in {"message.delivered", "message.failed"} else "reply",
            body=str(summary.get("body_text") or ""),
            actions=[],
            metadata={
                "source": "webhook_site_callback_fetch",
                "trace_id": trace_id,
                "normalized_event_type": summary.get("normalized_event_type"),
                "reply_intent": summary.get("reply_intent"),
                "reply_datetime_candidates": summary.get("reply_datetime_candidates"),
                "provider_timestamp": summary.get("provider_timestamp"),
                "webhook_fetch_url": values.get("webhook_fetch_url"),
            },
            provider_payload={
                "webhook_json": response_json,
                "parsed_content_json": summary.get("parsed_content_json"),
                "request_preview": result.get("request_preview"),
            },
        )
        self._store_message(message)

    def _merge_status_payload(
        self,
        current_status: dict[str, Any],
        *,
        readiness: dict[str, Any],
        last_connection_test: dict[str, Any] | None = None,
        last_callback_fetch: dict[str, Any] | None = None,
        last_seturl: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        merged = deepcopy(current_status)
        merged["readiness"] = readiness
        if last_connection_test is not None:
            merged["last_connection_test"] = last_connection_test
        if last_callback_fetch is not None:
            merged["last_callback_fetch"] = last_callback_fetch
        if last_seturl is not None:
            merged["last_seturl"] = last_seturl
        return merged

    def _build_last_connection_test(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": result.get("success", False),
            "message": result.get("message"),
            "mode": result.get("mode"),
            "trace_id": result.get("trace_id"),
            "auth_mode": result.get("auth_mode"),
            "provider_endpoint": result.get("provider_endpoint"),
            "provider_request_sent": result.get("provider_request_sent", False),
            "provider_status_code": result.get("provider_status_code"),
            "provider_response_excerpt": result.get("provider_response_excerpt"),
            "provider_request_preview": result.get("provider_request_preview"),
            "steps": deepcopy(result.get("steps") or []),
            "tested_at_utc": datetime.utcnow().isoformat() + "Z",
        }

    def _build_last_callback_fetch(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": result.get("success", False),
            "message": result.get("message"),
            "trace_id": result.get("trace_id"),
            "webhook_fetch_url": result.get("webhook_fetch_url"),
            "resolved_latest_request_url": result.get("resolved_latest_request_url"),
            "api_key_present": result.get("api_key_present", False),
            "provider_status_code": result.get("provider_status_code"),
            "response_excerpt": result.get("response_excerpt"),
            "response_json": deepcopy(result.get("response_json")),
            "request_preview": deepcopy(result.get("request_preview")),
            "steps": deepcopy(result.get("steps") or []),
            "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
        }

    def _build_connection_diagnostics(
        self,
        values: dict[str, Any],
        status_payload: dict[str, Any],
        readiness: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "mock_mode": self._mock_connection_mode_enabled(values),
            "provider_post_enabled": not self._mock_connection_mode_enabled(values),
            "verbose_connection_logging": self._verbose_connection_logging_enabled(values),
            "auth_mode": readiness.get("auth_mode"),
            "config_ready": readiness.get("config_ready"),
            "auth_ready": readiness.get("auth_ready"),
            "provider_test_supported": readiness.get("provider_test_supported"),
            "provider_endpoint": readiness.get("provider_endpoint"),
            "webhook_fetch_url": values.get("webhook_fetch_url"),
            "resolved_latest_request_url": self._resolve_webhook_latest_request_url(values),
            "last_connection_test": deepcopy(status_payload.get("last_connection_test") or {}),
            "last_callback_fetch": deepcopy(status_payload.get("last_callback_fetch") or {}),
        }

    def _determine_auth_mode(self, values: dict[str, Any], secrets: dict[str, str]) -> str:
        if secrets.get("rime_api_key"):
            return "rime_api_key"
        if secrets.get("auth_client_secret") and secrets.get("auth_password"):
            return "oauth_password"
        return "incomplete"

    def _provider_test_post_supported(self, auth_mode: str) -> bool:
        return auth_mode == "rime_api_key"

    def _send_provider_test_post(
        self,
        *,
        values: dict[str, Any],
        secrets: dict[str, str],
        trace_id: str | None,
        auth_mode: str,
    ) -> dict[str, Any]:
        """Send one real POST to the configured RIME endpoint.

        The exact downstream schema may evolve, so this probe keeps the payload
        intentionally small and explicit. Its main purpose is to confirm that
        the configured endpoint is reachable and that the stored credentials are
        accepted by the provider-facing HTTP call.
        """

        rime_base_url = (values.get("rime_base_url") or "").strip()
        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": trace_id or "",
        }
        # RIME expects the API key in `X-API-Key`, not in an OAuth-style
        # Authorization header. We keep the auth mode label as `rime_api_key`
        # so the UI and diagnostics stay understandable for operators.
        if auth_mode == "rime_api_key" and secrets.get("rime_api_key"):
            headers["X-API-Key"] = secrets["rime_api_key"]

        payload = {
            "channels": "RCS",
            "address": (values.get("test_recipient_address") or "").strip(),
            "richMessage": {
                "text": "Appointment Agent LEKAB RIME connection test",
            },
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(rime_base_url, headers=headers, json=payload)
            excerpt = response.text[:300]
            response_step_detail = f"HTTP {response.status_code}"
            if response.status_code == 401:
                response_step_detail = "HTTP 401 - provider rejected the configured credentials"
            return {
                "provider_status_code": response.status_code,
                "provider_response_excerpt": excerpt,
                "provider_request_preview": {
                    "method": "POST",
                    "url": rime_base_url,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": payload,
                },
                "steps": [
                    {"step": "readiness_check", "status": "ok", "detail": "Adapter settings are ready"},
                    {"step": "auth_mode_selection", "status": "done", "detail": auth_mode},
                    {"step": "payload_mapping", "status": "done", "detail": "Mapped test payload to LEKAB /send schema"},
                    {"step": "provider_request_build", "status": "done", "detail": f"POST {rime_base_url}"},
                    {
                        "step": "provider_response",
                        "status": "done" if response.status_code != 401 else "failed",
                        "detail": response_step_detail,
                    },
                ],
            }
        except httpx.HTTPError as exc:
            return {
                "provider_status_code": 0,
                "provider_response_excerpt": f"http_error:{exc.__class__.__name__}:{str(exc)[:240]}",
                "provider_request_preview": {
                    "method": "POST",
                    "url": rime_base_url,
                    "headers": {
                        "Content-Type": headers.get("Content-Type"),
                        "X-Trace-Id": headers.get("X-Trace-Id"),
                        "X-API-Key": "********" if headers.get("X-API-Key") else None,
                    },
                    "json": payload,
                },
                "steps": [
                    {"step": "readiness_check", "status": "ok", "detail": "Adapter settings are ready"},
                    {"step": "auth_mode_selection", "status": "done", "detail": auth_mode},
                    {"step": "payload_mapping", "status": "done", "detail": "Mapped test payload to LEKAB /send schema"},
                    {"step": "provider_request_build", "status": "done", "detail": f"POST {rime_base_url}"},
                    {"step": "provider_response", "status": "failed", "detail": f"{exc.__class__.__name__}: {str(exc)[:180]}"},
                ],
            }

    def _log_rcs_event(
        self,
        event_name: str,
        *,
        trace_id: str | None,
        readiness: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        """Write one structured, secret-safe LEKAB log line.

        Docker users mostly inspect stdout logs. We therefore emit one compact
        JSON-like dict per important action so they can correlate UI actions,
        API responses, and provider-readiness checks by `trace_id`.
        """

        verbose_enabled = payload.get("config_summary", {}).get("verbose_connection_logging", True)
        if not verbose_enabled:
            payload = {
                key: value
                for key, value in payload.items()
                if key not in {"steps", "provider_response_excerpt", "provider_request_preview"}
            }
        log_payload = {
            "component": "lekab_rcs_settings",
            "event": event_name,
            "trace_id": trace_id,
            "ready": readiness["ready"],
            "headline": readiness["headline"],
            "missing_fields": readiness["missing_fields"],
            "warnings": readiness["warnings"],
            "active_channel_mode": readiness["active_channel_mode"],
            **payload,
        }

        if readiness["ready"]:
            logger.info("LEKAB RCS event: %s", log_payload)
        else:
            logger.warning("LEKAB RCS event: %s", log_payload)

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
                        self._field("test_recipient_address", values, required=False),
                        self._field("callback_url", values, required=True),
                        self._field("webhook_fetch_url", values, required=False),
                        self._field("channel_priority", values, required=True, field_type="select", options=["RCS_FIRST", "SMS_FIRST"]),
                        self._field("sms_fallback_enabled", values, field_type="toggle", required=True),
                        self._secret_field("rime_api_key", secrets, required=False, state="planned"),
                        self._secret_field("webhook_api_key", secrets, required=False, state="active"),
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
                    "id": "connection_diagnostics",
                    "title": "Connection Diagnostics",
                    "state": "active",
                    "fields": [
                        self._field("mock_connection_mode", values, field_type="toggle", required=True),
                        self._field("verbose_connection_logging", values, field_type="toggle", required=True),
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
            "callback_url": "Inbound callback URL that LEKAB would call for replies or delivery status updates. In this demo it points to a Webhook.site URL so we can inspect incoming messages safely.",
            "webhook_fetch_url": "Webhook.site API URL used to fetch the latest callback. If you enter a token URL like https://webhook.site/token/UUID, the adapter automatically reads from /request/latest.",
            "test_recipient_address": "Phone number used for a real LEKAB /send test POST. Use international format with country code, for example 491705707716. This becomes the `address` field in the RIME JSON body.",
            "channel_priority": "Defines which channel is attempted first. RCS_FIRST tries rich messaging before SMS. SMS_FIRST reverses that order.",
            "sms_sender_name": "Originator name shown on SMS where the provider and country allow branded senders.",
            "sms_length_mode": "Choose whether long texts split automatically into several SMS parts or should be truncated later by policy.",
            "default_language": "Default template language used when the journey does not provide a more specific language.",
            "contact_lookup_mode": "Controls how phone or email based contact resolution is attempted before sending.",
            "phone_normalization_mode": "Defines the phone number formatting style before lookup or send. E164 is best for provider-neutral handling.",
            "default_template_context": "Template family or business context used when the adapter chooses the message text.",
            "mock_connection_mode": "Turn provider POST testing on or off directly in the UI. True means mock mode with no real RIME POST. False means the test connection may send a real POST to the configured RIME endpoint.",
            "verbose_connection_logging": "Turn detailed connection logging on or off. When it is on, the backend logs every test step, endpoint, trace id, and provider response excerpt. Secrets stay masked.",
        }
        return mapping.get(field_id, "This field is part of the LEKAB messaging setup.")

    def _calculate_readiness(self, values: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
        # Readiness is intentionally simple: the cockpit needs a clear yes/no
        # onboarding signal instead of a hidden provider-specific matrix.
        common_required_pairs = [
            ("environment_name", values.get("environment_name")),
            ("workspace_id", values.get("workspace_id")),
            ("rime_base_url", values.get("rime_base_url")),
            ("callback_url", values.get("callback_url")),
        ]
        missing = [field_id for field_id, value in common_required_pairs if not value]
        auth_mode = self._determine_auth_mode(values, secrets)
        if auth_mode == "oauth_password":
            oauth_required_pairs = [
                ("auth_base_url", values.get("auth_base_url")),
                ("auth_client_id", values.get("auth_client_id")),
                ("auth_username", values.get("auth_username")),
                ("dispatch_base_url", values.get("dispatch_base_url")),
                ("sms_base_url", values.get("sms_base_url")),
                ("auth_client_secret", secrets.get("auth_client_secret")),
                ("auth_password", secrets.get("auth_password")),
            ]
            missing.extend(field_id for field_id, value in oauth_required_pairs if not value and field_id not in missing)
        elif auth_mode == "rime_api_key":
            if not values.get("rime_base_url") and "rime_base_url" not in missing:
                missing.append("rime_base_url")
            if (
                not self._mock_connection_mode_enabled(values)
                and not values.get("test_recipient_address")
                and "test_recipient_address" not in missing
            ):
                missing.append("test_recipient_address")
        else:
            missing.extend(field_id for field_id in ("rime_api_key",) if field_id not in missing)
        warnings: list[str] = []
        if values.get("sms_fallback_enabled"):
            warnings.append("SMS fallback is enabled")
        if values.get("messaging_environment") == "production":
            warnings.append("Production mode is selected")
        ready = not missing and bool(values.get("rcs_enabled"))
        provider_test_supported = self._provider_test_post_supported(auth_mode) or self._mock_connection_mode_enabled(values)
        headline = (
            (
                "LEKAB adapter ready for direct RIME test messaging"
                if auth_mode == "rime_api_key"
                else "LEKAB adapter configured for OAuth/password messaging, but direct provider POST tests are blocked until safe token handoff is implemented"
            )
            if ready
            else f"Configuration incomplete: {', '.join(missing[:3])}" if missing else "RCS is disabled"
        )
        return {
            "ready": ready,
            "headline": headline,
            "missing_fields": missing,
            "warnings": warnings,
            "active_channel_mode": values.get("channel_priority", "RCS_FIRST"),
            "auth_mode": auth_mode,
            "provider_endpoint": values.get("rime_base_url"),
            "config_ready": not bool(missing),
            "auth_ready": auth_mode in {"rime_api_key", "oauth_password"},
            "provider_test_supported": provider_test_supported,
        }
