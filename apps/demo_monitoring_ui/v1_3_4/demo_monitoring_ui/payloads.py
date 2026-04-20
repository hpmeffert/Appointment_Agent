from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone


def _sample_delivery_example(lang: str) -> dict:
    appointment_start = datetime(2026, 4, 20, 10, 0, tzinfo=timezone(timedelta(hours=2)))
    return {
        "delivery_id": "delivery-demo-1001",
        "title": "Reminder delivery pilot" if lang == "en" else "Reminder delivery pilot",
        "customer_name": "Anna Demo" if lang == "en" else "Anna Demo",
        "timezone": "Europe/Berlin",
        "start_at": appointment_start.isoformat(),
        "display_date": "2026-04-20",
        "display_time": "10:00",
        "recipient_email": "anna.demo@example.com",
        "recipient_phone": "+49 170 1234567",
        "message_length_chars": 142,
        "message_text": (
            "Your appointment is tomorrow at 10:00. Please reply if you need help."
            if lang == "en"
            else "Your appointment is tomorrow at 10:00. Please reply if you need help."
        ),
    }


def _default_delivery_setup(lang: str) -> dict:
    return {
        "enabled": True,
        "delivery_mode": "priority_order",
        "primary_channel": "rcs_sms",
        "allow_fallback_channels": True,
        "validate_recipient": True,
        "validate_channel": True,
        "max_retry_count": 2,
        "delivery_window_minutes": 20,
        "message_length_limit": 160,
        "result_retention_days": 30,
        "channel_email_enabled": True,
        "channel_voice_enabled": False,
        "channel_rcs_sms_enabled": True,
        "labels": {
            "enabled": "Enabled" if lang == "en" else "Enabled",
            "delivery_mode": "Delivery mode" if lang == "en" else "Delivery mode",
            "primary_channel": "Primary channel" if lang == "en" else "Primary channel",
            "allow_fallback": "Allow fallback channels" if lang == "en" else "Allow fallback channels",
            "validate_recipient": "Validate recipient" if lang == "en" else "Validate recipient",
            "validate_channel": "Validate channel" if lang == "en" else "Validate channel",
            "max_retry_count": "Max retry count" if lang == "en" else "Max retry count",
            "delivery_window_minutes": "Delivery window minutes" if lang == "en" else "Delivery window minutes",
            "message_length_limit": "Message length limit" if lang == "en" else "Message length limit",
            "result_retention_days": "Result retention days" if lang == "en" else "Result retention days",
            "channel_email": "Email channel" if lang == "en" else "Email channel",
            "channel_voice": "Voice channel" if lang == "en" else "Voice channel",
            "channel_rcs_sms": "RCS/SMS channel" if lang == "en" else "RCS/SMS channel",
        },
    }


def _delivery_channels(lang: str) -> list[dict]:
    return [
        {
            "id": "rcs_sms",
            "label": "RCS / SMS",
            "enabled": True,
            "status": "ready",
            "note": (
                "Primary delivery path for fast reminders."
                if lang == "en"
                else "Primary delivery path for fast reminders."
            ),
        },
        {
            "id": "email",
            "label": "Email",
            "enabled": True,
            "status": "fallback",
            "note": (
                "Fallback path when the primary channel is not available."
                if lang == "en"
                else "Fallback path when the primary channel is not available."
            ),
        },
        {
            "id": "voice",
            "label": "Voice",
            "enabled": False,
            "status": "disabled",
            "note": (
                "Kept off for this demo so the operator can focus on the main flow."
                if lang == "en"
                else "Kept off for this demo so the operator can focus on the main flow."
            ),
        },
    ]


def _validation_outcomes(lang: str) -> list[dict]:
    return [
        {
            "id": "passed",
            "title": "Validation passed" if lang == "en" else "Validation passed",
            "state": "ok",
            "body": (
                "The delivery settings are ready and the main channel is available."
                if lang == "en"
                else "The delivery settings are ready and the main channel is available."
            ),
        },
        {
            "id": "warning",
            "title": "Validation warning" if lang == "en" else "Validation warning",
            "state": "warn",
            "body": (
                "The cockpit can warn when a fallback channel is used or when retries are low."
                if lang == "en"
                else "The cockpit can warn when a fallback channel is used or when retries are low."
            ),
        },
        {
            "id": "blocked",
            "title": "Validation blocked" if lang == "en" else "Validation blocked",
            "state": "danger",
            "body": (
                "The cockpit blocks delivery when no channel is active or the message is too long."
                if lang == "en"
                else "The cockpit blocks delivery when no channel is active or the message is too long."
            ),
        },
    ]


def _demo_stories(lang: str) -> list[dict]:
    return [
        {
            "id": "primary-channel",
            "title": "Story 1: Primary channel works" if lang == "en" else "Story 1: Primary channel works",
            "business_value": (
                "RCS/SMS is active, validation passes, and the message is delivered on the first try."
                if lang == "en"
                else "RCS/SMS is active, validation passes, and the message is delivered on the first try."
            ),
            "wow_effect": (
                "The operator sees one clear path from settings to result."
                if lang == "en"
                else "The operator sees one clear path from settings to result."
            ),
        },
        {
            "id": "validation-block",
            "title": "Story 2: Validation blocks a bad target" if lang == "en" else "Story 2: Validation blocks a bad target",
            "business_value": (
                "A too long message or a missing channel is caught before delivery starts."
                if lang == "en"
                else "A too long message or a missing channel is caught before delivery starts."
            ),
            "wow_effect": (
                "The cockpit explains the block in plain words."
                if lang == "en"
                else "The cockpit explains the block in plain words."
            ),
        },
        {
            "id": "fallback-channel",
            "title": "Story 3: Fallback saves the delivery" if lang == "en" else "Story 3: Fallback saves the delivery",
            "business_value": (
                "When the primary channel is not ready, the fallback channel takes over."
                if lang == "en"
                else "When the primary channel is not ready, the fallback channel takes over."
            ),
            "wow_effect": (
                "The operator sees why the result switched from one channel to another."
                if lang == "en"
                else "The operator sees why the result switched from one channel to another."
            ),
        },
    ]


def _delivery_results(lang: str) -> list[dict]:
    return [
        {
            "result_id": "result-001",
            "channel": "rcs_sms",
            "status": "sent",
            "timestamp": "2026-04-20T08:30:00+02:00",
            "reason": (
                "Primary channel delivered the reminder."
                if lang == "en"
                else "Primary channel delivered the reminder."
            ),
        },
        {
            "result_id": "result-002",
            "channel": "email",
            "status": "fallback_sent",
            "timestamp": "2026-04-20T08:32:00+02:00",
            "reason": (
                "Fallback channel was used because the primary path was busy."
                if lang == "en"
                else "Fallback channel was used because the primary path was busy."
            ),
        },
        {
            "result_id": "result-003",
            "channel": "rcs_sms",
            "status": "blocked",
            "timestamp": "2026-04-20T08:35:00+02:00",
            "reason": (
                "Delivery was blocked because the message was too long."
                if lang == "en"
                else "Delivery was blocked because the message was too long."
            ),
        },
        {
            "result_id": "result-004",
            "channel": "voice",
            "status": "retrying",
            "timestamp": "2026-04-20T08:37:00+02:00",
            "reason": (
                "A retry is in progress after a temporary provider issue."
                if lang == "en"
                else "A retry is in progress after a temporary provider issue."
            ),
        },
        {
            "result_id": "result-005",
            "channel": "email",
            "status": "failed",
            "timestamp": "2026-04-20T08:40:00+02:00",
            "reason": (
                "The provider returned an error and no fallback was left."
                if lang == "en"
                else "The provider returned an error and no fallback was left."
            ),
        },
        {
            "result_id": "result-006",
            "channel": "rcs_sms",
            "status": "skipped",
            "timestamp": "2026-04-20T08:42:00+02:00",
            "reason": (
                "The delivery was skipped because the channel was disabled in the example."
                if lang == "en"
                else "The delivery was skipped because the channel was disabled in the example."
            ),
        },
    ]


def build_v134_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    doc_lang = "de" if language == "de" else "en"
    payload = {
        "version": "v1.3.4",
        "ui_meta": {
            "tagline": (
                "Reminder delivery cockpit with channels, validation outcomes, and delivery results."
                if language == "en"
                else "Reminder delivery cockpit with channels, validation outcomes, and delivery results."
            ),
            "accent": "amber",
            "role": "admin-console",
        },
        "pages": [
            {"id": "dashboard", "label": "Dashboard"},
            {"id": "setup", "label": "Delivery" if language == "en" else "Delivery"},
            {"id": "preview", "label": "Validation" if language == "en" else "Validation"},
            {"id": "jobs", "label": "Results" if language == "en" else "Results"},
            {"id": "lifecycle", "label": "Channels" if language == "en" else "Channels"},
            {"id": "sync", "label": "Operator" if language == "en" else "Operator"},
            {"id": "help", "label": "Help" if language == "en" else "Help"},
        ],
        "delivery_setup": _default_delivery_setup(language),
        "delivery_example": _sample_delivery_example(language),
        "delivery_overview": {
            "title": "How delivery works" if language == "en" else "How delivery works",
            "subtitle": (
                "The operator chooses a channel, checks the validation outcome, and reads the result before anything leaves the system."
                if language == "en"
                else "The operator chooses a channel, checks the validation outcome, and reads the result before anything leaves the system."
            ),
            "cards": [
                {
                    "title": "Delivery channels" if language == "en" else "Delivery channels",
                    "body": (
                        "RCS/SMS is the main path, email is the fallback, and voice stays off in this demo."
                        if language == "en"
                        else "RCS/SMS is the main path, email is the fallback, and voice stays off in this demo."
                    ),
                },
                {
                    "title": "Validation" if language == "en" else "Validation",
                    "body": (
                        "The cockpit checks the target, the message size, the retry policy, and the active channel."
                        if language == "en"
                        else "The cockpit checks the target, the message size, the retry policy, and the active channel."
                    ),
                },
                {
                    "title": "Delivery results" if language == "en" else "Delivery results",
                    "body": (
                        "Sent, fallback_sent, blocked, retrying, failed, and skipped stay visible for the operator."
                        if language == "en"
                        else "Sent, fallback_sent, blocked, retrying, failed, and skipped stay visible for the operator."
                    ),
                },
                {
                    "title": "Operator summary" if language == "en" else "Operator summary",
                    "body": (
                        "The cockpit explains what happened in simple words so a new colleague can follow it."
                        if language == "en"
                        else "The cockpit explains what happened in simple words so a new colleague can follow it."
                    ),
                },
            ],
        },
        "validation_rules": [
            "Delivery must be enabled",
            "At least one channel must be active",
            "The primary channel must be active or a fallback must be allowed",
            "Retry count must stay between 0 and 3",
            "The delivery window must stay positive",
            "The message must fit into the configured message length limit",
        ],
        "validation_outcomes": _validation_outcomes(language),
        "demo_stories": _demo_stories(language),
        "delivery_channels": _delivery_channels(language),
        "delivery_results": _delivery_results(language),
        "result_overview": {
            "sent": 1,
            "fallback_sent": 1,
            "blocked": 1,
            "retrying": 1,
            "failed": 1,
            "skipped": 1,
        },
        "operator_summary": {
            "title": "What the operator should notice" if language == "en" else "What the operator should notice",
            "subtitle": (
                "The controls are simple: pick a channel, check the validation outcome, and read the result."
                if language == "en"
                else "The controls are simple: pick a channel, check the validation outcome, and read the result."
            ),
            "bullets": [
                (
                    "Channel choice decides where the reminder goes first."
                    if language == "en"
                    else "Channel choice decides where the reminder goes first."
                ),
                (
                    "Validation tells the operator if delivery is ready or blocked."
                    if language == "en"
                    else "Validation tells the operator if delivery is ready or blocked."
                ),
                (
                    "Results stay visible so the team can explain what happened."
                    if language == "en"
                    else "Results stay visible so the team can explain what happened."
                ),
            ],
            "flow_steps": [
                (
                    "Choose the channel"
                    if language == "en"
                    else "Choose the channel"
                ),
                (
                    "Check the validation outcome"
                    if language == "en"
                    else "Check the validation outcome"
                ),
                (
                    "Read the delivery result"
                    if language == "en"
                    else "Read the delivery result"
                ),
            ],
        },
        "help_links": [
            {"label": "User Guide", "href": f"/docs/user?lang={doc_lang}"},
            {"label": "Demo Guide", "href": f"/docs/demo?lang={doc_lang}"},
            {"label": "Admin Guide", "href": f"/docs/admin?lang={doc_lang}"},
        ],
        "ui_api_links": [
            "/api/reminder-ui/v1.3.4/payload",
            "/api/reminder-ui/v1.3.4/help",
            "/api/reminder-ui/v1.3.4/config",
            "/api/reminder-ui/v1.3.4/config/preview",
            "/api/reminder-ui/v1.3.4/results",
        ],
        "api_links": [
            "/api/reminder-ui/v1.3.4/payload",
            "/api/reminder-ui/v1.3.4/help",
            "/api/reminder-ui/v1.3.4/config",
            "/api/reminder-ui/v1.3.4/config/preview",
            "/api/reminder-ui/v1.3.4/results",
            "/api/reminder-ui/v1.3.4/health",
        ],
        "docs_highlights": [
            (
                "The docs explain delivery channels in plain language."
                if language == "en"
                else "The docs explain delivery channels in plain language."
            ),
            (
                "The demo guide gives three short stories."
                if language == "en"
                else "The demo guide gives three short stories."
            ),
            (
                "The admin guide explains every parameter with examples."
                if language == "en"
                else "The admin guide explains every parameter with examples."
            ),
        ],
        "delivery_states": [
            "sent",
            "fallback_sent",
            "blocked",
            "retrying",
            "failed",
            "skipped",
        ],
    }
    return deepcopy(payload)
