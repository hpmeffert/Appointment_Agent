from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from appointment_agent_shared.contracts import ContactUpsertCommand, CreateBookingCommand, ResolveCustomerCommand, SearchSlotsCommand
from appointment_agent_shared.db import get_session

from .service import GoogleAdapterService

router = APIRouter(prefix="/api/google/v1.0.0", tags=["google-adapter-v1.0.0"])


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterService:
    return GoogleAdapterService(session)


@router.get("/help")
def help_view() -> dict[str, object]:
    return {"module": "google_adapter", "version": "v1.0.0"}


@router.post("/slots")
def search_slots(command: SearchSlotsCommand, service: GoogleAdapterService = Depends(get_service)) -> list[dict]:
    return [slot.model_dump(mode="json") for slot in service.search_slots(command)]


@router.post("/bookings")
def create_booking(command: CreateBookingCommand, service: GoogleAdapterService = Depends(get_service)) -> dict:
    return service.create_booking(command).model_dump(mode="json")


@router.post("/contacts/upsert")
def upsert_contact(command: ContactUpsertCommand, service: GoogleAdapterService = Depends(get_service)) -> dict[str, str]:
    return service.upsert_contact(command)


@router.post("/contacts/resolve")
def resolve_contact(command: ResolveCustomerCommand, service: GoogleAdapterService = Depends(get_service)) -> dict[str, Optional[str]]:
    return service.resolve_customer(command)
