from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from appointment_agent_shared.commands import (
    CancelBookingCommand,
    CreateBookingCommand,
    ResolveCustomerCommand,
    SearchSlotsCommand,
    UpdateBookingCommand,
    UpsertCustomerCommand,
)
from appointment_agent_shared.db import get_session
from appointment_agent_shared.errors import ProviderError

from .service import GoogleAdapterException, GoogleAdapterServiceV101

router = APIRouter(prefix="/api/google/v1.0.1", tags=["google-adapter-v1.0.1"])


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterServiceV101:
    return GoogleAdapterServiceV101(session)


def _raise_provider_error(error: ProviderError) -> None:
    status_code = 404 if error.error_category.value == "NOT_FOUND" else 400
    raise HTTPException(status_code=status_code, detail=error.model_dump(mode="json"))


@router.get("/help")
def help_view() -> dict[str, object]:
    return {"module": "google_adapter", "version": "v1.0.1"}


@router.post("/slots")
def search_slots(command: SearchSlotsCommand, service: GoogleAdapterServiceV101 = Depends(get_service)) -> list[dict]:
    return [slot.model_dump(mode="json") for slot in service.search_slots(command)]


@router.post("/bookings")
def create_booking(command: CreateBookingCommand, service: GoogleAdapterServiceV101 = Depends(get_service)) -> dict:
    return service.create_booking(command).model_dump(mode="json")


@router.patch("/bookings")
def update_booking(command: UpdateBookingCommand, service: GoogleAdapterServiceV101 = Depends(get_service)) -> dict:
    try:
        return service.update_booking(command).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/bookings/cancel")
def cancel_booking(command: CancelBookingCommand, service: GoogleAdapterServiceV101 = Depends(get_service)) -> dict:
    try:
        return service.cancel_booking(command).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.get("/bookings/{booking_reference}")
def get_booking(booking_reference: str, service: GoogleAdapterServiceV101 = Depends(get_service)) -> dict:
    try:
        return service.get_booking(booking_reference).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/contacts/upsert")
def upsert_contact(command: UpsertCustomerCommand, service: GoogleAdapterServiceV101 = Depends(get_service)) -> dict[str, str]:
    return service.upsert_contact(command)


@router.post("/contacts/resolve")
def resolve_contact(command: ResolveCustomerCommand, service: GoogleAdapterServiceV101 = Depends(get_service)) -> dict[str, Optional[str]]:
    return service.resolve_customer(command)
