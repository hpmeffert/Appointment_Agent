from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from address_database.v1_3_9.address_database.service import AddressDatabaseService
from appointment_agent_shared.db import get_session
from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_v139_payload
from .scenario_context import DemoScenarioContextService, DemoScenarioContextUpdate
from .scenario_testing import DemoScenarioTestingService

router = APIRouter(tags=["demo-monitoring-ui-v1.3.9"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"
BASE_VERSION = "v1.3.9"
PATCH_VERSION = "v1.3.9-patch9"
PATCH_ALIASES = (
    "v1.3.9-patch1",
    "v1.3.9-patch2",
    "v1.3.9-patch3",
    "v1.3.9-patch4",
    "v1.3.9-patch5",
    "v1.3.9-patch6",
    "v1.3.9-patch7",
    "v1.3.9-patch8",
    PATCH_VERSION,
)
GOOGLE_API_VERSION = "v1.3.6"
LEKAB_API_VERSION = "v1.3.8"
ADDRESS_API_VERSION = "v1.3.9"


def _decorate_selected_button_states(
    buttons: Optional[list[dict]],
    *,
    selected_action: Optional[str] = None,
    selected_value: Optional[str] = None,
    button_state: Optional[str] = None,
) -> list[dict]:
    decorated: list[dict] = []
    normalized_action = (selected_action or "").strip().lower()
    canonical_aliases = {
        "keep": "appointment.confirm_requested",
        "confirm": "appointment.confirm_requested",
        "reschedule": "appointment.reschedule_requested",
        "cancel": "appointment.cancel_requested",
        "call_me": "appointment.call_requested",
    }
    normalized_canonical_action = canonical_aliases.get(normalized_action, normalized_action)
    normalized_value = (selected_value or "").strip().lower()
    for item in buttons or []:
        button = dict(item)
        matches_action = normalized_canonical_action and str(button.get("canonical_action") or button.get("action_type") or "").strip().lower() == normalized_canonical_action
        matches_value = normalized_value and str(button.get("value") or button.get("label") or "").strip().lower() == normalized_value
        if matches_action or matches_value:
            button["state"] = button_state or "selected"
            button["selected"] = True
        decorated.append(button)
    return decorated


def _contains_selected_button(buttons: Optional[list[dict]]) -> bool:
    return any(bool((item or {}).get("selected")) for item in (buttons or []))


def resolve_demo_display_version() -> str:
    return PATCH_VERSION


def resolve_demo_api_version() -> str:
    return BASE_VERSION


def resolve_demo_route_contract() -> dict:
    # One route contract keeps the server-rendered shell and the browser-side
    # fetch paths in sync so the cockpit cannot silently drift again.
    return {
        "display_version": resolve_demo_display_version(),
        "demo_api_version": resolve_demo_api_version(),
        "google_api_version": GOOGLE_API_VERSION,
        "lekab_api_version": LEKAB_API_VERSION,
        "address_api_version": ADDRESS_API_VERSION,
        "ui_routes": {
            "base": f"/ui/demo-monitoring/{BASE_VERSION}",
            "patch": f"/ui/demo-monitoring/{PATCH_VERSION}",
            "patch_aliases": [f"/ui/demo-monitoring/{alias}" for alias in PATCH_ALIASES],
            "address_base": f"/ui/address-database/{BASE_VERSION}",
            "address_patch": f"/ui/address-database/{PATCH_VERSION}",
            "address_patch_aliases": [f"/ui/address-database/{alias}" for alias in PATCH_ALIASES],
        },
        "api_routes": {
            "payload_base": f"/api/demo-monitoring/{BASE_VERSION}/payload",
            "payload_patch": f"/api/demo-monitoring/{PATCH_VERSION}/payload",
            "payload_patch_aliases": [f"/api/demo-monitoring/{alias}/payload" for alias in PATCH_ALIASES],
            "help_base": f"/api/demo-monitoring/{BASE_VERSION}/help",
            "help_patch": f"/api/demo-monitoring/{PATCH_VERSION}/help",
            "scenario_context_base": f"/api/demo-monitoring/{BASE_VERSION}/scenario-context",
            "scenario_context_patch": f"/api/demo-monitoring/{PATCH_VERSION}/scenario-context",
        },
    }


class RunScenarioRequest(BaseModel):
    scenario_id: str
    mode: Literal["simulation", "real"] = "simulation"
    lang: str = "en"
    address_id: Optional[str] = None
    output_channel: Optional[str] = None
    appointment_type: str = "dentist"
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class ScenarioContextRequest(BaseModel):
    scenario_id: Optional[str] = None
    mode: Optional[Literal["simulation", "real"]] = None
    address_id: Optional[str] = None
    output_channel: Optional[str] = None
    appointment_type: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    current_step: Optional[str] = None
    status: Optional[str] = None


def get_scenario_service(session: Session = Depends(get_session)) -> DemoScenarioTestingService:
    return DemoScenarioTestingService(session)


def get_context_service(session: Session = Depends(get_session)) -> DemoScenarioContextService:
    return DemoScenarioContextService(session)


def build_live_cockpit_payload(*, session: Session, lang: str) -> dict:
    payload = build_v139_payload(lang=lang)
    context_service = DemoScenarioContextService(session)
    address_service = AddressDatabaseService(session)
    context = context_service.get_context().model_dump(mode="json")
    addresses = [item.model_dump(mode="json") for item in address_service.list_addresses(is_active=True, limit=200)]
    if not addresses and context.get("selected_address"):
        addresses = [context["selected_address"]]

    route_contract = resolve_demo_route_contract()
    scenario_options = [
        {
            "id": item["id"],
            "label": item["title"],
            "summary": item.get("summary"),
            "expected_action": item.get("expected_action"),
        }
        for item in payload.get("scenarios", [])
    ]
    address_options = [
        {
            "address_id": item.get("address_id"),
            "label": item.get("display_name") or item.get("address_id"),
            "city": item.get("city"),
            "preferred_channel": item.get("preferred_channel"),
            "correlation_ref": item.get("correlation_ref"),
        }
        for item in addresses
    ]
    selected_scenario = next((item for item in payload.get("scenarios", []) if item.get("id") == context.get("scenario_id")), None)
    if selected_scenario is None and payload.get("scenarios"):
        selected_scenario = payload["scenarios"][0]

    selected_address = next((item for item in addresses if item.get("address_id") == context.get("address_id")), None)
    if selected_address is None:
        selected_address = context.get("selected_address")
    context_metadata = context.get("metadata") or {}
    real_callback = (context_metadata.get("real_callback") or {})
    selected_action = real_callback.get("selected_action")
    selected_value = real_callback.get("incoming_data")
    button_state = real_callback.get("button_state") or "selected"
    first_message = ((selected_scenario or {}).get("steps") or [{}])[0].get("communication_message", {})
    current_message = dict(context_metadata.get("customer_journey_message") or first_message or {})
    suggestion_buttons = _decorate_selected_button_states(
        current_message.get("suggestion_buttons") or current_message.get("actions", []) or [],
        selected_action=selected_action,
        selected_value=selected_value,
        button_state=button_state,
    )
    if selected_action and not _contains_selected_button(suggestion_buttons):
        current_message = dict(first_message or current_message)
        suggestion_buttons = _decorate_selected_button_states(
            current_message.get("suggestion_buttons") or current_message.get("actions", []) or [],
            selected_action=selected_action,
            selected_value=selected_value,
            button_state=button_state,
        )
    real_channel_payload = dict(current_message.get("real_channel_payload", {}) or {})
    if real_channel_payload:
        real_channel_payload["suggestions"] = _decorate_selected_button_states(
            real_channel_payload.get("suggestions", []),
            selected_action=selected_action,
            selected_value=selected_value,
            button_state=button_state,
        )
        real_channel_payload["selected_action"] = selected_action
        real_channel_payload["selected_value"] = selected_value

    from datetime import datetime, timezone

    payload["ui_version"] = PATCH_VERSION
    payload["api_version"] = BASE_VERSION
    payload["generated_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload["route_meta"] = route_contract
    payload["menus"] = payload.get("pages", [])
    payload["scenario_options"] = scenario_options
    payload["address_options"] = address_options
    payload["operator_panel"] = {
        "scenario_options": scenario_options,
        "address_options": address_options,
        "selected_scenario_id": context.get("scenario_id"),
        "selected_address_id": context.get("address_id"),
        "scenario_mode": context.get("mode"),
        "dashboard_modes": payload.get("dashboard_modes", []),
        "guided_modes": (payload.get("guided_demo") or {}).get("modes", []),
    }
    payload["current_story"] = {
        "id": selected_scenario.get("id") if selected_scenario else None,
        "title": selected_scenario.get("title") if selected_scenario else None,
        "summary": selected_scenario.get("summary") if selected_scenario else None,
        "current_step": context.get("current_step"),
        "status": context.get("status"),
    }
    payload["current_mode"] = {
        "scenario_mode": context.get("mode"),
        "output_channel": context.get("output_channel"),
        "appointment_type": context.get("appointment_type"),
        "status": context.get("status"),
    }
    payload["google_workspace"] = {
        "calendar_ref": context.get("calendar_ref"),
        "selected_address": selected_address.get("display_name") if selected_address else None,
        "selected_address_id": selected_address.get("address_id") if selected_address else None,
        "appointment_type": context.get("appointment_type"),
    }
    payload["messages_customer_journey"] = {
        "scenario_id": context.get("scenario_id"),
        "mode": context.get("mode"),
        "appointment_id": context.get("appointment_id"),
        "booking_reference": context.get("booking_reference"),
        "correlation_ref": context.get("correlation_ref"),
        "address_id": context.get("address_id"),
        "selected_address_name": selected_address.get("display_name") if selected_address else None,
        "current_step": context.get("current_step"),
        "status": context.get("status"),
        "selected_action": selected_action,
        "current_message": {
            **current_message,
            "actions": suggestion_buttons,
            "suggestion_buttons": suggestion_buttons,
            "real_channel_payload": real_channel_payload,
        },
        "available_actions": (selected_scenario or {}).get("available_actions", []),
        "suggestion_buttons": suggestion_buttons,
        "real_channel_payload": real_channel_payload,
    }
    payload["diagnostics"] = {
        "payload_loaded": True,
        "route_contract": route_contract,
        "payload_loaded_at": payload.get("generated_at_utc") or None,
        "scenario_source_status": "loaded" if scenario_options else "empty",
        "address_source_status": "loaded" if address_options else "empty",
        "required_contract_fields": [
            "menus",
            "operator_panel",
            "scenario_options",
            "address_options",
            "current_story",
            "current_mode",
            "google_workspace",
            "messages_customer_journey",
            "diagnostics",
        ],
    }
    return payload


def _render_html(*, initial_page: str = "dashboard", page_title: str = "Appointment Agent Cockpit") -> str:
    contract = resolve_demo_route_contract()
    html = (
        HTML_PATH.read_text(encoding="utf-8")
        .replace("__VERSION__", contract["display_version"])
        .replace("__DEMO_API_VERSION__", contract["demo_api_version"])
        .replace("__GOOGLE_API_VERSION__", contract["google_api_version"])
        .replace("__LEKAB_API_VERSION__", contract["lekab_api_version"])
        .replace("__ADDRESS_API_VERSION__", contract["address_api_version"])
        .replace("__INITIAL_PAGE__", initial_page)
        .replace("__PAGE_TITLE__", page_title)
    )
    return html


@router.get(f"/ui/demo-monitoring/{BASE_VERSION}")
@router.get("/ui/demo-monitoring/v1.3.9-patch1")
@router.get("/ui/demo-monitoring/v1.3.9-patch2")
@router.get("/ui/demo-monitoring/v1.3.9-patch3")
@router.get("/ui/demo-monitoring/v1.3.9-patch4")
@router.get("/ui/demo-monitoring/v1.3.9-patch5")
@router.get("/ui/demo-monitoring/v1.3.9-patch6")
@router.get("/ui/demo-monitoring/v1.3.9-patch7")
@router.get("/ui/demo-monitoring/v1.3.9-patch8")
@router.get(f"/ui/demo-monitoring/{PATCH_VERSION}")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get(f"/ui/address-database/{BASE_VERSION}")
@router.get("/ui/address-database/v1.3.9-patch1")
@router.get("/ui/address-database/v1.3.9-patch2")
@router.get("/ui/address-database/v1.3.9-patch3")
@router.get("/ui/address-database/v1.3.9-patch4")
@router.get("/ui/address-database/v1.3.9-patch5")
@router.get("/ui/address-database/v1.3.9-patch6")
@router.get("/ui/address-database/v1.3.9-patch7")
@router.get("/ui/address-database/v1.3.9-patch8")
@router.get(f"/ui/address-database/{PATCH_VERSION}")
def address_database_view() -> HTMLResponse:
    return HTMLResponse(_render_html(initial_page="addresses", page_title="Address Database"))


@router.get(f"/api/demo-monitoring/{BASE_VERSION}/help")
@router.get("/api/demo-monitoring/v1.3.9-patch1/help")
@router.get("/api/demo-monitoring/v1.3.9-patch2/help")
@router.get("/api/demo-monitoring/v1.3.9-patch3/help")
@router.get("/api/demo-monitoring/v1.3.9-patch4/help")
@router.get("/api/demo-monitoring/v1.3.9-patch5/help")
@router.get("/api/demo-monitoring/v1.3.9-patch6/help")
@router.get("/api/demo-monitoring/v1.3.9-patch7/help")
@router.get("/api/demo-monitoring/v1.3.9-patch8/help")
@router.get(f"/api/demo-monitoring/{PATCH_VERSION}/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v139_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": resolve_demo_display_version(),
        "route_contract": resolve_demo_route_contract(),
        "pages": [page["id"] for page in payload["pages"]],
        "integrated_features": [
            "address_database_menu_entry",
            "address_database_standalone_route",
            "address_crud_ui",
            "address_linkage_visibility",
            "cross_module_address_anchor",
            "appointment_address_assignment_controls",
            "generated_calendar_assignment_preservation",
            "message_monitor_address_context",
            "message_monitor_action_resolution_preview",
            "reminder_address_context",
            "reply_to_action_engine_visibility",
            "scenario_runner_buttons",
            "unified_demo_scenario_context",
            "operator_mode_selector",
            "address_aware_google_generation",
            "file_based_protocol_artifacts",
            "messages_and_customer_journey_replay",
        ],
        "design_baseline": "Incident Demo UI based on v1.3.8 with v1.3.9 address database UI, unified scenario context, appointment-address assignment flow, and reply action preview layer",
    }


@router.get(f"/api/demo-monitoring/{BASE_VERSION}/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch1/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch2/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch3/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch4/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch5/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch6/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch7/payload")
@router.get("/api/demo-monitoring/v1.3.9-patch8/payload")
@router.get(f"/api/demo-monitoring/{PATCH_VERSION}/payload")
def payload_view(
    lang: str = Query(default="en"),
    session: Session = Depends(get_session),
) -> dict:
    return build_live_cockpit_payload(session=session, lang="de" if lang == "de" else "en")


@router.get(f"/api/demo-monitoring/{BASE_VERSION}/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch1/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch2/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch3/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch4/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch5/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch6/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch7/scenario-testing/help")
@router.get("/api/demo-monitoring/v1.3.9-patch8/scenario-testing/help")
@router.get(f"/api/demo-monitoring/{PATCH_VERSION}/scenario-testing/help")
def scenario_testing_help(
    lang: str = Query(default="en"),
    service: DemoScenarioTestingService = Depends(get_scenario_service),
) -> dict:
    return service.scenario_help(lang="de" if lang == "de" else "en")


@router.post(f"/api/demo-monitoring/{BASE_VERSION}/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch1/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch2/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch3/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch4/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch5/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch6/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch7/scenario-testing/run")
@router.post("/api/demo-monitoring/v1.3.9-patch8/scenario-testing/run")
@router.post(f"/api/demo-monitoring/{PATCH_VERSION}/scenario-testing/run")
def run_scenario(
    payload: RunScenarioRequest,
    service: DemoScenarioTestingService = Depends(get_scenario_service),
) -> dict:
    return service.run_scenario(
        scenario_id=payload.scenario_id,
        mode=payload.mode,
        lang="de" if payload.lang == "de" else "en",
        address_id=payload.address_id,
        output_channel=payload.output_channel,
        appointment_type=payload.appointment_type,
        from_date=payload.from_date,
        to_date=payload.to_date,
    )


@router.get(f"/api/demo-monitoring/{BASE_VERSION}/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch1/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch2/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch3/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch4/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch5/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch6/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch7/scenario-context")
@router.get("/api/demo-monitoring/v1.3.9-patch8/scenario-context")
@router.get(f"/api/demo-monitoring/{PATCH_VERSION}/scenario-context")
def scenario_context(
    service: DemoScenarioContextService = Depends(get_context_service),
) -> dict:
    return service.get_context().model_dump(mode="json")


@router.put(f"/api/demo-monitoring/{BASE_VERSION}/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch1/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch2/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch3/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch4/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch5/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch6/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch7/scenario-context")
@router.put("/api/demo-monitoring/v1.3.9-patch8/scenario-context")
@router.put(f"/api/demo-monitoring/{PATCH_VERSION}/scenario-context")
def update_scenario_context(
    payload: ScenarioContextRequest,
    service: DemoScenarioContextService = Depends(get_context_service),
) -> dict:
    return service.save_context(
        DemoScenarioContextUpdate(
            scenario_id=payload.scenario_id,
            mode=payload.mode,
            address_id=payload.address_id,
            output_channel=payload.output_channel,
            appointment_type=payload.appointment_type,
            from_date=payload.from_date,
            to_date=payload.to_date,
            current_step=payload.current_step,
            status=payload.status,
            metadata={"updated_from": "operator_panel"},
        )
    ).model_dump(mode="json")


@router.get(f"/api/demo-monitoring/{BASE_VERSION}/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch1/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch2/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch3/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch4/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch5/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch6/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch7/scenario-testing/latest")
@router.get("/api/demo-monitoring/v1.3.9-patch8/scenario-testing/latest")
@router.get(f"/api/demo-monitoring/{PATCH_VERSION}/scenario-testing/latest")
def latest_scenario_artifacts(
    service: DemoScenarioTestingService = Depends(get_scenario_service),
) -> dict:
    return service.latest_artifacts()


@router.get(f"/api/demo-monitoring/{BASE_VERSION}/scenario-testing/artifacts/latest/{{kind}}")
@router.get("/api/demo-monitoring/v1.3.9-patch1/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch2/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch3/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch4/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch5/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch6/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch7/scenario-testing/artifacts/latest/{kind}")
@router.get("/api/demo-monitoring/v1.3.9-patch8/scenario-testing/artifacts/latest/{kind}")
@router.get(f"/api/demo-monitoring/{PATCH_VERSION}/scenario-testing/artifacts/latest/{{kind}}")
def latest_scenario_artifact_text(
    kind: str,
    service: DemoScenarioTestingService = Depends(get_scenario_service),
):
    return service.latest_artifact_text(kind)


router.include_router(docs_router)
