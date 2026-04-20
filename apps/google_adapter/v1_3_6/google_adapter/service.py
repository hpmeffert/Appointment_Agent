from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from appointment_agent_shared.config import settings

from google_adapter.v1_1_0_patch1.google_adapter.service import DEMO_MARKER_PREFIX
from google_adapter.v1_1_0_patch6.google_adapter.service import DemoCalendarPatch6Request
from google_adapter.v1_2_0.google_adapter.service import GoogleAdapterServiceV120


class GoogleAdapterServiceV136(GoogleAdapterServiceV120):
    """Public v1.3.6 release line for the combined Google linkage demonstrator.

    Patch 7 keeps the stable v1.3.6 routes and lifts the newer selected-
    address calendar generation behavior into this public release line.
    """

    def _customer_name_from_full_details(self, details: Any) -> str:
        text = str(details or "").replace("|", "\n").strip()
        if not text:
            return ""
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first_line

    def extract_customer_name(self, context: Any) -> str:
        if isinstance(context, dict):
            if str(context.get("linked_address_name") or "").strip():
                return str(context["linked_address_name"]).strip()
            if str(context.get("customer_name") or "").strip():
                return str(context["customer_name"]).strip()
            if str(context.get("address_name") or "").strip():
                return str(context["address_name"]).strip()
            if str(context.get("linked_address_full_details") or "").strip():
                extracted = self._customer_name_from_full_details(context.get("linked_address_full_details"))
                if extracted:
                    return extracted
            return "Unknown"

        linked_address_name = str(getattr(context, "linked_address_name", "") or "").strip()
        if linked_address_name:
            return linked_address_name
        customer_name = str(getattr(context, "customer_name", "") or "").strip()
        if customer_name:
            return customer_name
        full_details = str(getattr(context, "linked_address_full_details", "") or "").strip()
        if full_details:
            extracted = self._customer_name_from_full_details(full_details)
            if extracted:
                return extracted
        return "Unknown"

    def _resolved_customer_blueprints(
        self,
        request: DemoCalendarPatch6Request,
    ) -> list[dict[str, str]]:
        if request.linked_address_id:
            return [
                {
                    "name": self.extract_customer_name(request),
                    "mobile": request.linked_contact_phone or "",
                    "email": request.linked_contact_email or "",
                }
            ]
        return self._customer_blueprints_for_type(request.appointment_type)

    def _resolved_event_title(
        self,
        *,
        request: DemoCalendarPatch6Request,
        blueprint: dict[str, str],
        customer: dict[str, str],
    ) -> str:
        if request.linked_address_id or request.linked_address_name:
            identity = self.extract_customer_name(
                {
                    "linked_address_name": request.linked_address_name,
                    "customer_name": customer.get("name"),
                    "linked_address_full_details": request.linked_address_full_details,
                }
            )
            base_title = (blueprint.get("type") or blueprint.get("category") or blueprint["title"]).strip()
            return f"{base_title} – {identity}"
        return blueprint["title"]

    def _appointment_label(self, appointment_type: str) -> str:
        return self._title_blueprints_for_type(appointment_type)[0]["type"]

    def _resolved_booking_customer_name(self, request: Any) -> str:
        selected_name = self.extract_customer_name(request)
        return selected_name if selected_name != "Unknown" else "Demo Customer"

    def _booking_event_title(self, *, appointment_type: str, customer_name: str) -> str:
        return f"{self._appointment_label(appointment_type)} – {customer_name}"

    def _resolve_timezone_name(self, request: Any) -> str:
        candidate = str(getattr(request, "timezone", "") or "").strip()
        return candidate or settings.google_default_timezone

    def _localized_datetime(self, value: datetime, timezone_name: str) -> datetime:
        aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        try:
            target_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            target_timezone = ZoneInfo(settings.google_default_timezone)
        return aware.astimezone(target_timezone)

    def _booking_description(
        self,
        *,
        request: Any,
        booking_reference: str,
        context_label: str,
    ) -> str:
        address_lines = [
            line.strip()
            for line in str(getattr(request, "linked_address_full_details", "") or "").replace("|", "\n").splitlines()
            if line.strip()
        ]
        if not address_lines:
            address_lines = [self._resolved_booking_customer_name(request)]
        localized_start = self._localized_datetime(
            request.start_time,
            self._resolve_timezone_name(request),
        )
        date_label = localized_start.strftime("%d %b %Y")
        time_label = localized_start.strftime("%H:%M")
        return "\n".join(
            [
                "Address:",
                *address_lines,
                "",
                "Context:",
                context_label,
                f"Date: {date_label}",
                f"Time: {time_label}",
                "",
                f"Booking reference: {booking_reference}",
            ]
        )

    def build_calendar_event(self, context: dict[str, Any]) -> dict[str, Any]:
        customer_name = str(context.get("customer_name") or "").strip() or "Demo Customer"
        appointment_type = str(context.get("appointment_type") or "dentist")
        metadata = {
            "correlation_id": context.get("correlation_id") or "",
            "booking_reference": context.get("booking_reference") or "",
            "appointment_id": context.get("appointment_id") or "",
            "address_id": context.get("address_id") or "",
            "linked_contact_reference_id": context.get("linked_contact_reference_id") or context.get("address_id") or "",
        }
        lines = [line for line in context.get("address_lines") or [] if str(line).strip()]
        if not lines:
            lines = [customer_name]
        description_lines = [
            "Address:",
            *[str(line).strip() for line in lines],
            "",
            "Context:",
            str(context.get("context_label") or "Appointment confirmed"),
        ]
        if context.get("date_label"):
            description_lines.append(f"Date: {context['date_label']}")
        if context.get("time_label"):
            description_lines.append(f"Time: {context['time_label']}")
        description_lines.extend(
            [
                "",
                f"Booking reference: {metadata['booking_reference']}",
            ]
        )
        return {
            "summary": self._booking_event_title(
                appointment_type=appointment_type,
                customer_name=customer_name,
            ),
            "description": "\n".join(description_lines),
            "metadata": metadata,
        }

    def _build_patch6_description(
        self,
        *,
        blueprint: dict[str, str],
        customer: dict[str, str],
        booking_reference: str,
        request: DemoCalendarPatch6Request,
    ) -> str:
        address_lines = [
            line.strip()
            for line in str(request.linked_address_full_details or "").replace("|", "\n").splitlines()
            if line.strip()
        ]
        if request.linked_address_id or request.linked_address_name:
            event = self.build_calendar_event(
                {
                    "appointment_type": request.appointment_type,
                    "customer_name": request.linked_address_name or customer.get("name") or "Selected Address",
                    "address_lines": address_lines or [request.linked_address_name or customer.get("name") or "Selected Address"],
                    "context_label": "Rescheduled appointment confirmed",
                    "booking_reference": booking_reference,
                    "correlation_id": request.linked_correlation_ref or "",
                    "appointment_id": "",
                    "address_id": request.linked_address_id or "",
                    "linked_contact_reference_id": request.linked_contact_reference_id or request.linked_address_id or "",
                }
            )
            if not request.include_description:
                return event["description"].split("\n\n", 1)[0]
            return event["description"]
        base_description = self._build_description(
            blueprint=blueprint,
            customer=customer,
            booking_reference=booking_reference,
            include_description=request.include_description,
        )
        linkage_lines = [
            f"Linked address id: {request.linked_address_id or '-'}",
            f"Linked address name: {request.linked_address_name or customer.get('name') or '-'}",
            f"Linked contact reference: {request.linked_contact_reference_id or request.linked_address_id or '-'}",
            f"Linked correlation ref: {request.linked_correlation_ref or '-'}",
            f"Linked contact phone: {request.linked_contact_phone or customer.get('mobile') or '-'}",
            f"Linked contact email: {request.linked_contact_email or customer.get('email') or '-'}",
        ]
        if request.linked_address_full_details:
            linkage_lines.append(f"Linked address details: {request.linked_address_full_details}")
        if not request.include_description:
            compact = [base_description, linkage_lines[0], linkage_lines[1], linkage_lines[2]]
            if request.linked_address_full_details:
                compact.append(linkage_lines[-1])
            return "\n".join(compact)
        return "\n".join([base_description, *linkage_lines])

    def _booking_event_metadata(self, *, request: Any, booking_reference: str) -> dict[str, str]:
        customer_name = self._resolved_booking_customer_name(request)
        return {
            "appointment_agent_demo": "true",
            "appointment_agent_release": "v1.3.9-patch9",
            "appointment_agent_booking_reference": booking_reference,
            "appointment_agent_customer_name": customer_name,
            "appointment_agent_appointment_type": request.appointment_type,
            "appointment_agent_address_id": str(getattr(request, "address_id", "") or ""),
            "appointment_agent_address_name": customer_name,
            "appointment_agent_contact_phone": str(getattr(request, "customer_mobile", "") or ""),
            "appointment_agent_contact_email": str(getattr(request, "customer_email", "") or ""),
            "appointment_agent_contact_id": str(getattr(request, "linked_contact_reference_id", "") or getattr(request, "address_id", "") or ""),
            "appointment_agent_correlation_ref": str(getattr(request, "correlation_id", "") or ""),
            "appointment_agent_address_full_details": str(getattr(request, "linked_address_full_details", "") or ""),
            "appointment_agent_appointment_id": str(getattr(request, "appointment_id", "") or ""),
        }

    def _preview_events_patch6(
        self,
        request: DemoCalendarPatch6Request,
        window_start: datetime,
        window_end: datetime,
    ) -> list[dict[str, Any]]:
        preview_count = min(request.count, 5)
        blueprints = self._title_blueprints_for_type(request.appointment_type)
        customers = self._resolved_customer_blueprints(request)
        items: list[dict[str, Any]] = []
        for index in range(preview_count):
            blueprint = blueprints[index % len(blueprints)]
            customer = customers[index % len(customers)]
            slot_start = self._spread_slot_start(window_start, window_end, index, preview_count)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo6-preview-{}".format(uuid4().hex[:8])
            items.append(
                {
                    "booking_reference": booking_reference,
                    "provider_reference": "preview-{}".format(booking_reference),
                    "title": self._resolved_event_title(request=request, blueprint=blueprint, customer=customer),
                    "customer_name": customer["name"] if request.include_customer_name else "Demo Customer",
                    "mobile_number": customer.get("mobile") or None,
                    "email": customer.get("email") or None,
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "timeframe": "custom_range",
                    "mode": request.mode,
                    "live_written": False,
                    "link_state": "preview_only",
                    "description_marker": DEMO_MARKER_PREFIX,
                    "details": {
                        "appointment_type": request.appointment_type,
                        "purpose": blueprint["purpose"],
                        "description": self._build_patch6_description(
                            blueprint=blueprint,
                            customer=customer,
                            booking_reference=booking_reference,
                            request=request,
                        ),
                        "location": (request.linked_location_text or blueprint["location"]) if request.include_location else "",
                        "preview_only": "true",
                        "linked_address_id": request.linked_address_id or "",
                        "linked_address_name": request.linked_address_name or customer["name"],
                        "linked_contact_phone": request.linked_contact_phone or customer.get("mobile") or "",
                        "linked_contact_email": request.linked_contact_email or customer.get("email") or "",
                        "linked_correlation_ref": request.linked_correlation_ref or "",
                        "linked_contact_reference_id": request.linked_contact_reference_id or request.linked_address_id or "",
                        "linked_address_full_details": request.linked_address_full_details or "",
                        "title_strategy": (
                            "appointment_type_plus_selected_address"
                            if request.linked_address_id or request.linked_address_name
                            else "blueprint_title"
                        ),
                    },
                }
            )
        return items

    def _generate_events_patch6(
        self,
        *,
        operation_id: str,
        request: DemoCalendarPatch6Request,
        window_start: datetime,
        window_end: datetime,
        live_writes: bool,
    ) -> list[dict[str, Any]]:
        blueprints = self._title_blueprints_for_type(request.appointment_type)
        customers = self._resolved_customer_blueprints(request)
        items: list[dict[str, Any]] = []
        for index in range(request.count):
            blueprint = blueprints[index % len(blueprints)]
            customer = customers[index % len(customers)]
            slot_start = self._spread_slot_start(window_start, window_end, index, request.count)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo6-book-{}".format(uuid4().hex[:8])
            title = self._resolved_event_title(request=request, blueprint=blueprint, customer=customer)
            description = self._build_patch6_description(
                blueprint=blueprint,
                customer=customer,
                booking_reference=booking_reference,
                request=request,
            )
            provider_reference = "simulation-{}".format(booking_reference)
            details = {
                "appointment_type": request.appointment_type,
                "purpose": blueprint["purpose"],
                "description": description,
                "location": (request.linked_location_text or blueprint["location"]) if request.include_location else "",
                "category": blueprint.get("category", request.appointment_type),
                "scenario_label": blueprint.get("scenario_label", request.appointment_type),
                "title": title,
                "customer_prompt": blueprint.get("customer_prompt", ""),
                "reminder_text": blueprint.get("reminder_text", ""),
                "follow_up_action": blueprint.get("follow_up_action", ""),
                "monitoring_label": blueprint.get("monitoring_label", ""),
                "linked_address_id": request.linked_address_id or "",
                "linked_address_name": request.linked_address_name or customer["name"],
                "linked_contact_phone": request.linked_contact_phone or customer.get("mobile") or "",
                "linked_contact_email": request.linked_contact_email or customer.get("email") or "",
                "linked_correlation_ref": request.linked_correlation_ref or "",
                "linked_contact_reference_id": request.linked_contact_reference_id or request.linked_address_id or "",
                "linked_address_full_details": request.linked_address_full_details or "",
                "title_strategy": (
                    "appointment_type_plus_selected_address"
                    if request.linked_address_id or request.linked_address_name
                    else "blueprint_title"
                ),
            }
            if live_writes:
                event_result = self.gateway.create_demo_event(
                    title=title,
                    description=description,
                    location=(request.linked_location_text or blueprint["location"]) if request.include_location else None,
                    start_time=slot_start,
                    end_time=slot_end,
                    metadata={
                        "appointment_agent_demo": "true",
                        "appointment_agent_release": "v1.3.6",
                        "appointment_agent_booking_reference": booking_reference,
                        "appointment_agent_customer_name": customer["name"],
                        "appointment_agent_appointment_type": request.appointment_type,
                        "appointment_agent_address_id": request.linked_address_id or "",
                        "appointment_agent_address_name": request.linked_address_name or customer["name"],
                        "appointment_agent_contact_phone": request.linked_contact_phone or customer.get("mobile") or "",
                        "appointment_agent_contact_email": request.linked_contact_email or customer.get("email") or "",
                        "appointment_agent_contact_id": request.linked_contact_reference_id or request.linked_address_id or "",
                        "appointment_agent_correlation_ref": request.linked_correlation_ref or "",
                        "appointment_agent_address_full_details": request.linked_address_full_details or "",
                    },
                )
                provider_reference = event_result.provider_reference
                details["html_link"] = event_result.html_link or ""
                event_id = event_result.event_id
            else:
                event_id = "simulation-{}".format(booking_reference)
            self.demo_events.save(
                operation_id=operation_id,
                mode=request.mode,
                timeframe="custom_range",
                calendar_id=self._calendar_id(),
                event_id=event_id,
                booking_reference=booking_reference,
                title=title,
                customer_name=customer["name"] if request.include_customer_name else "Demo Customer",
                mobile_number=customer.get("mobile") or None,
                start_time_utc=slot_start.astimezone(timezone.utc).replace(tzinfo=None),
                end_time_utc=slot_end.astimezone(timezone.utc).replace(tzinfo=None),
                timezone=settings.google_default_timezone,
                provider_reference=provider_reference,
                details=details,
            )
            items.append(
                {
                    "booking_reference": booking_reference,
                    "provider_reference": provider_reference,
                    "title": title,
                    "customer_name": customer["name"] if request.include_customer_name else "Demo Customer",
                    "mobile_number": customer.get("mobile") or None,
                    "email": customer.get("email") or None,
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "timeframe": "custom_range",
                    "mode": request.mode,
                    "live_written": live_writes,
                    "link_state": "linked_with_mobile" if customer.get("mobile") else "linked_without_mobile",
                    "description_marker": DEMO_MARKER_PREFIX,
                    "details": details,
                }
            )
        return items

    def create_booking_patch8(self, request):
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        request_timezone = self._resolve_timezone_name(request)
        availability = self.check_availability_patch8(
            self._availability_request_model(
                mode=request.mode,
                start_time=request.start_time,
                end_time=request.end_time,
                timezone=request_timezone,
            )
        )
        if not availability.slot_available:
            return self._booking_result_model(
                success=False,
                action="create",
                mode=status.mode,
                google_source=availability.google_source,
                message=availability.message,
                status="conflict",
                conflict_detected=True,
                selected_slot=availability.selected_slot,
                alternative_slots=availability.alternative_slots,
                monitoring_labels=["slot.checked", "slot.conflict_detected", "booking.failed"],
                technical_reason=availability.technical_reason,
            )
        booking_reference = request.booking_reference or "gpatch9-book-{}".format(uuid4().hex[:8])
        provider_reference = "simulation-{}".format(booking_reference)
        event_id = provider_reference
        customer_name = self._resolved_booking_customer_name(request)
        description = self._booking_description(
            request=request,
            booking_reference=booking_reference,
            context_label=str(getattr(request, "context_label", "") or "Rescheduled appointment confirmed"),
        )
        title = self._booking_event_title(
            appointment_type=request.appointment_type,
            customer_name=customer_name,
        )
        if status.live_calendar_writes:
            event_result = self.gateway.create_demo_event(
                title=title,
                description=description,
                location=None,
                start_time=request.start_time,
                end_time=request.end_time,
                timezone_name=request_timezone,
                metadata=self._booking_event_metadata(request=request, booking_reference=booking_reference),
            )
            provider_reference = event_result.provider_reference
            event_id = event_result.event_id
        self.bookings.save(
            booking_reference=booking_reference,
            journey_id="patch8-google-journey",
            customer_id=customer_name or "demo-customer",
            provider="google",
            external_id=provider_reference,
            status="confirmed",
            payload={
                "slot_id": request.slot_id,
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "appointment_type": request.appointment_type,
                "provider_reference": {"external_id": provider_reference},
                "correlation_id": getattr(request, "correlation_id", None),
                "appointment_id": getattr(request, "appointment_id", None),
                "address_id": getattr(request, "address_id", None),
                "linked_contact_reference_id": getattr(request, "linked_contact_reference_id", None),
                "linked_address_full_details": getattr(request, "linked_address_full_details", None),
            },
        )
        self.demo_events.save(
            operation_id="patch9-booking-create",
            mode=request.mode,
            timeframe="patch9_booking",
            calendar_id=self._calendar_id(),
            event_id=event_id,
            booking_reference=booking_reference,
            title=title,
            customer_name=customer_name,
            mobile_number=getattr(request, "customer_mobile", None),
            start_time_utc=request.start_time.astimezone(timezone.utc).replace(tzinfo=None),
            end_time_utc=request.end_time.astimezone(timezone.utc).replace(tzinfo=None),
            timezone=request_timezone,
            provider_reference=provider_reference,
            details={
                "label": request.label,
                "appointment_type": request.appointment_type,
                "correlation_id": getattr(request, "correlation_id", "") or "",
                "booking_reference": booking_reference,
                "appointment_id": getattr(request, "appointment_id", "") or "",
                "address_id": getattr(request, "address_id", "") or "",
                "linked_contact_reference_id": getattr(request, "linked_contact_reference_id", "") or getattr(request, "address_id", "") or "",
                "linked_address_full_details": getattr(request, "linked_address_full_details", "") or "",
                "description": description,
            },
            is_demo_generated=True,
        )
        return self._booking_result_model(
            success=True,
            action="create",
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            booking_reference=booking_reference,
            provider_reference=provider_reference,
            message="Booking created successfully.",
            status="confirmed",
            selected_slot=self._normalize_slot(
                request.start_time,
                request.end_time,
                slot_id=request.slot_id,
                provider="google" if status.live_calendar_writes else "simulated",
                timezone_name=request_timezone,
            ),
            monitoring_labels=["slot.checked", "booking.created"],
        )

    def reschedule_booking_patch8(self, request):
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        record = self.bookings.get(request.booking_reference)
        if record is None:
            raise self._not_found_error("reschedule_booking_patch8")
        current_provider_reference = request.provider_reference or record.external_id
        request_timezone = self._resolve_timezone_name(request)
        availability = self.check_availability_patch8(
            self._availability_request_model(
                mode=request.mode,
                start_time=request.start_time,
                end_time=request.end_time,
                exclude_provider_reference=current_provider_reference,
                timezone=request_timezone,
            )
        )
        if not availability.slot_available:
            return self._booking_result_model(
                success=False,
                action="reschedule",
                mode=status.mode,
                google_source=availability.google_source,
                booking_reference=request.booking_reference,
                provider_reference=current_provider_reference,
                message=availability.message,
                status="conflict",
                conflict_detected=True,
                selected_slot=availability.selected_slot,
                alternative_slots=availability.alternative_slots,
                monitoring_labels=["slot.checked", "slot.conflict_detected", "booking.failed"],
                technical_reason=availability.technical_reason,
            )
        if status.live_calendar_writes and current_provider_reference and self.gateway.get_event(current_provider_reference):
            self.gateway.delete_event(current_provider_reference)
        provider_reference = "simulation-{}".format(request.booking_reference)
        event_id = provider_reference
        customer_name = self._resolved_booking_customer_name(request)
        description = self._booking_description(
            request=request,
            booking_reference=request.booking_reference,
            context_label=str(getattr(request, "context_label", "") or "Rescheduled appointment confirmed"),
        )
        title = self._booking_event_title(
            appointment_type=request.appointment_type,
            customer_name=customer_name,
        )
        if status.live_calendar_writes:
            event_result = self.gateway.create_demo_event(
                title=title,
                description=description,
                location=None,
                start_time=request.start_time,
                end_time=request.end_time,
                timezone_name=request_timezone,
                metadata=self._booking_event_metadata(request=request, booking_reference=request.booking_reference),
            )
            provider_reference = event_result.provider_reference
            event_id = event_result.event_id
        self.bookings.save(
            booking_reference=request.booking_reference,
            journey_id=record.journey_id,
            customer_id=record.customer_id,
            provider=record.provider,
            external_id=provider_reference,
            status="rescheduled",
            payload={
                **(record.payload or {}),
                "slot_id": request.slot_id,
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "appointment_type": request.appointment_type,
                "provider_reference": {"external_id": provider_reference},
                "correlation_id": getattr(request, "correlation_id", None),
                "appointment_id": getattr(request, "appointment_id", None),
                "address_id": getattr(request, "address_id", None),
                "linked_contact_reference_id": getattr(request, "linked_contact_reference_id", None),
                "linked_address_full_details": getattr(request, "linked_address_full_details", None),
            },
        )
        self.demo_events.save(
            operation_id="patch9-booking-reschedule",
            mode=request.mode,
            timeframe="patch9_reschedule",
            calendar_id=self._calendar_id(),
            event_id=event_id,
            booking_reference=request.booking_reference,
            title=title,
            customer_name=customer_name,
            mobile_number=getattr(request, "customer_mobile", None),
            start_time_utc=request.start_time.astimezone(timezone.utc).replace(tzinfo=None),
            end_time_utc=request.end_time.astimezone(timezone.utc).replace(tzinfo=None),
            timezone=request_timezone,
            provider_reference=provider_reference,
            details={
                "label": request.label,
                "appointment_type": request.appointment_type,
                "correlation_id": getattr(request, "correlation_id", "") or "",
                "booking_reference": request.booking_reference,
                "appointment_id": getattr(request, "appointment_id", "") or "",
                "address_id": getattr(request, "address_id", "") or "",
                "linked_contact_reference_id": getattr(request, "linked_contact_reference_id", "") or getattr(request, "address_id", "") or "",
                "linked_address_full_details": getattr(request, "linked_address_full_details", "") or "",
                "description": description,
            },
            is_demo_generated=True,
        )
        return self._booking_result_model(
            success=True,
            action="reschedule",
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            booking_reference=request.booking_reference,
            provider_reference=provider_reference,
            message="Booking rescheduled successfully.",
            status="rescheduled",
            selected_slot=self._normalize_slot(
                request.start_time,
                request.end_time,
                slot_id=request.slot_id,
                provider="google" if status.live_calendar_writes else "simulated",
                timezone_name=request_timezone,
            ),
            monitoring_labels=["slot.checked", "booking.rescheduled"],
        )

    def _availability_request_model(self, **kwargs):
        from google_adapter.v1_1_0_patch8a.google_adapter.service import GoogleAvailabilityCheckRequest

        return GoogleAvailabilityCheckRequest(**kwargs)

    def _booking_result_model(self, **kwargs):
        from google_adapter.v1_1_0_patch8a.google_adapter.service import GoogleBookingActionResult

        return GoogleBookingActionResult(**kwargs)

    def _not_found_error(self, operation: str):
        from appointment_agent_shared.enums import ErrorCategory
        from appointment_agent_shared.errors import ProviderError
        from google_adapter.v1_1_0_patch1.google_adapter.service import GoogleAdapterException

        return GoogleAdapterException(
            ProviderError(
                provider="google",
                provider_operation=operation,
                error_category=ErrorCategory.NOT_FOUND,
                message="Booking reference was not found.",
            )
        )
