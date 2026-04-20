from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.events import (
    AddressAssignedToAppointment,
    AddressLinkedToAppointment,
    AddressRecordCreated,
    AddressRecordDeactivated,
    AddressRecordUpdated,
    AppointmentCreatedWithAddress,
    EventEnvelope,
)
from appointment_agent_shared.models import AddressProfile, AppointmentCacheRecord, MessageRecord, ReminderJobRecord
from appointment_agent_shared.repositories import AddressAppointmentLinkRepository, AddressRepository


class AddressInput(BaseModel):
    address_id: Optional[str] = None
    external_ref: Optional[str] = None
    customer_number: Optional[str] = None
    display_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = "Europe/Berlin"
    preferred_channel: Optional[str] = None
    notes: Optional[str] = None
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    application_id: Optional[str] = None
    is_active: bool = True


class AddressLinkInput(BaseModel):
    address_id: str
    appointment_external_id: str
    booking_reference: Optional[str] = None
    calendar_ref: Optional[str] = None
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"


class AddressDatabaseService:
    """Create a reusable address entity layer for v1.3.9.

    The address module is intentionally not just a UI helper. It becomes the
    stable correlation anchor that later links appointments, reminders, and
    communications back to one known entity.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.addresses = AddressRepository(session)
        self.links = AddressAppointmentLinkRepository(session)

    def _to_profile(self, record) -> AddressProfile:
        return AddressProfile(
            address_id=record.address_id,
            external_ref=record.external_ref,
            customer_number=record.customer_number,
            display_name=record.display_name,
            first_name=record.first_name,
            last_name=record.last_name,
            company_name=record.company_name,
            street=record.street,
            house_number=record.house_number,
            postal_code=record.postal_code,
            city=record.city,
            country=record.country,
            email=record.email,
            phone=record.phone,
            timezone=record.timezone,
            preferred_channel=record.preferred_channel,
            notes=record.notes,
            correlation_ref=record.correlation_ref,
            tenant_id=record.tenant_id,
            application_id=record.application_id,
            is_active=record.is_active,
            created_at_utc=record.created_at.isoformat() + "Z",
            updated_at_utc=record.updated_at.isoformat() + "Z",
        )

    def _publish(self, *, event_type: str, correlation_ref: str, payload: dict[str, Any]) -> None:
        event_bus.publish(
            EventEnvelope(
                event_type=event_type,
                correlation_id=correlation_ref,
                trace_id=f"address-{uuid4().hex[:16]}",
                tenant_id=str(payload.get("tenant_id") or "default"),
                source="address_database",
                payload=payload,
            )
        )

    def _backfill_cross_module_linkage(
        self,
        *,
        address_id: str,
        appointment_external_id: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        """Propagate new address linkage into already persisted module records."""

        if appointment_external_id:
            for row in self.session.scalars(
                select(AppointmentCacheRecord).where(AppointmentCacheRecord.external_appointment_id == appointment_external_id)
            ):
                row.address_id = address_id
                row.correlation_ref = correlation_ref or row.correlation_ref
            for row in self.session.scalars(
                select(ReminderJobRecord).where(ReminderJobRecord.external_appointment_id == appointment_external_id)
            ):
                row.address_id = address_id
                row.correlation_ref = correlation_ref or row.correlation_ref
            for row in self.session.scalars(
                select(MessageRecord).where(MessageRecord.appointment_id == appointment_external_id)
            ):
                row.address_id = address_id
                row.correlation_ref = correlation_ref or row.correlation_ref

        if phone or email:
            query = select(MessageRecord)
            if phone and email:
                query = query.where((MessageRecord.phone_number == phone) | (MessageRecord.contact_reference == email))
            elif phone:
                query = query.where(MessageRecord.phone_number == phone)
            else:
                query = query.where(MessageRecord.contact_reference == email)
            for row in self.session.scalars(query):
                row.address_id = row.address_id or address_id
                row.correlation_ref = correlation_ref or row.correlation_ref
        self.session.commit()

    def list_addresses(
        self,
        *,
        tenant_id: Optional[str] = None,
        query_text: Optional[str] = None,
        city: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 200,
    ) -> list[AddressProfile]:
        return [
            self._to_profile(record)
            for record in self.addresses.list_addresses(
                tenant_id=tenant_id,
                query_text=query_text,
                city=city,
                is_active=is_active,
                limit=limit,
            )
        ]

    def get_address(self, address_id: str) -> Optional[AddressProfile]:
        record = self.addresses.get(address_id)
        if record is None:
            return None
        return self._to_profile(record)

    def save_address(self, request: AddressInput) -> AddressProfile:
        address_id = request.address_id or f"addr-{uuid4().hex[:12]}"
        correlation_ref = request.correlation_ref or f"corr-{address_id}"
        existing = self.addresses.get(address_id)
        record = self.addresses.create_or_update(
            address_id=address_id,
            external_ref=request.external_ref,
            customer_number=request.customer_number,
            display_name=request.display_name,
            first_name=request.first_name,
            last_name=request.last_name,
            company_name=request.company_name,
            street=request.street,
            house_number=request.house_number,
            postal_code=request.postal_code,
            city=request.city,
            country=request.country,
            email=request.email,
            phone=request.phone,
            timezone=request.timezone,
            preferred_channel=request.preferred_channel,
            notes=request.notes,
            correlation_ref=correlation_ref,
            tenant_id=request.tenant_id,
            application_id=request.application_id,
            is_active=request.is_active,
        )
        self._backfill_cross_module_linkage(
            address_id=record.address_id,
            correlation_ref=correlation_ref,
            phone=record.phone,
            email=record.email,
        )
        if existing is None:
            self._publish(
                event_type="AddressRecordCreated",
                correlation_ref=correlation_ref,
                payload=AddressRecordCreated(
                    address_id=address_id,
                    correlation_ref=correlation_ref,
                    tenant_id=request.tenant_id,
                    display_name=request.display_name,
                ).model_dump(mode="json"),
            )
        else:
            changed_fields = [key for key, value in request.model_dump().items() if key != "address_id" and value is not None]
            self._publish(
                event_type="AddressRecordUpdated",
                correlation_ref=correlation_ref,
                payload=AddressRecordUpdated(
                    address_id=address_id,
                    correlation_ref=correlation_ref,
                    tenant_id=request.tenant_id,
                    changed_fields=changed_fields,
                ).model_dump(mode="json"),
            )
        return self._to_profile(record)

    def deactivate_address(self, address_id: str, *, reason: str = "manual_deactivate") -> Optional[AddressProfile]:
        record = self.addresses.deactivate(address_id)
        if record is None:
            return None
        correlation_ref = record.correlation_ref or f"corr-{address_id}"
        self._publish(
            event_type="AddressRecordDeactivated",
            correlation_ref=correlation_ref,
            payload=AddressRecordDeactivated(
                address_id=address_id,
                correlation_ref=correlation_ref,
                tenant_id=record.tenant_id,
                reason=reason,
            ).model_dump(mode="json"),
        )
        return self._to_profile(record)

    def link_address_to_appointment(self, request: AddressLinkInput) -> dict[str, Any]:
        link_id = f"addr-link-{uuid4().hex[:12]}"
        correlation_ref = request.correlation_ref or f"corr-{request.address_id}-{request.appointment_external_id}"
        record = self.links.link(
            link_id=link_id,
            address_id=request.address_id,
            appointment_external_id=request.appointment_external_id,
            booking_reference=request.booking_reference,
            calendar_ref=request.calendar_ref,
            correlation_ref=correlation_ref,
            tenant_id=request.tenant_id,
        )
        address = self.addresses.get(request.address_id)
        self._backfill_cross_module_linkage(
            address_id=request.address_id,
            appointment_external_id=request.appointment_external_id,
            correlation_ref=correlation_ref,
            phone=getattr(address, "phone", None),
            email=getattr(address, "email", None),
        )
        self._publish(
            event_type="AddressLinkedToAppointment",
            correlation_ref=correlation_ref,
            payload=AddressLinkedToAppointment(
                address_id=request.address_id,
                appointment_external_id=request.appointment_external_id,
                correlation_ref=correlation_ref,
                tenant_id=request.tenant_id,
                booking_reference=request.booking_reference,
                calendar_ref=request.calendar_ref,
            ).model_dump(mode="json"),
        )
        self._publish(
            event_type="AddressAssignedToAppointment",
            correlation_ref=correlation_ref,
            payload=AddressAssignedToAppointment(
                address_id=request.address_id,
                appointment_external_id=request.appointment_external_id,
                correlation_ref=correlation_ref,
                tenant_id=request.tenant_id,
                booking_reference=request.booking_reference,
                calendar_ref=request.calendar_ref,
            ).model_dump(mode="json"),
        )
        if request.calendar_ref or request.booking_reference:
            # In the demonstrator the explicit assignment often happens right
            # after a generated calendar reservation is created. Publishing this
            # lightweight event keeps that linkage visible to later modules
            # without forcing them to infer creation state from free-text notes.
            self._publish(
                event_type="AppointmentCreatedWithAddress",
                correlation_ref=correlation_ref,
                payload=AppointmentCreatedWithAddress(
                    appointment_external_id=request.appointment_external_id,
                    address_id=request.address_id,
                    correlation_ref=correlation_ref,
                    tenant_id=request.tenant_id,
                    booking_reference=request.booking_reference,
                    calendar_ref=request.calendar_ref,
                    provider="google" if request.calendar_ref else None,
                ).model_dump(mode="json"),
            )
        return {
            "link_id": record.link_id,
            "address_id": record.address_id,
            "appointment_external_id": record.appointment_external_id,
            "booking_reference": record.booking_reference,
            "calendar_ref": record.calendar_ref,
            "correlation_ref": record.correlation_ref,
            "tenant_id": record.tenant_id,
            "address_summary": self._to_profile(address).model_dump(mode="json") if address is not None else None,
        }

    def list_links_for_address(self, address_id: str) -> list[dict[str, Any]]:
        return [
            {
                "link_id": record.link_id,
                "address_id": record.address_id,
                "appointment_external_id": record.appointment_external_id,
                "booking_reference": record.booking_reference,
                "calendar_ref": record.calendar_ref,
                "correlation_ref": record.correlation_ref,
                "tenant_id": record.tenant_id,
            }
            for record in self.links.list_for_address(address_id)
        ]

    def list_links_for_appointment(self, appointment_external_id: str) -> list[dict[str, Any]]:
        return [
            {
                "link_id": record.link_id,
                "address_id": record.address_id,
                "appointment_external_id": record.appointment_external_id,
                "booking_reference": record.booking_reference,
                "calendar_ref": record.calendar_ref,
                "correlation_ref": record.correlation_ref,
                "tenant_id": record.tenant_id,
                "address_summary": self._to_profile(address).model_dump(mode="json") if address is not None else None,
            }
            for record in self.links.list_for_appointment(appointment_external_id)
            for address in [self.addresses.get(record.address_id)]
        ]
