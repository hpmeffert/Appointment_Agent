from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session

from .service import AddressDatabaseService, AddressInput, AddressLinkInput

router = APIRouter(prefix="/api/addresses/v1.3.9", tags=["address-database-v1.3.9"])


def _service(session: Session = Depends(get_session)) -> AddressDatabaseService:
    return AddressDatabaseService(session)


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "address_database",
        "version": "v1.3.9",
        "features": [
            "address_crud",
            "address_search",
            "address_to_appointment_linkage",
            "appointment_link_lookup",
            "correlation_ref_propagation",
            "bus_safe_address_events",
        ],
    }


@router.get("")
def list_addresses(
    tenant_id: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    service: AddressDatabaseService = Depends(_service),
) -> dict[str, object]:
    records = service.list_addresses(tenant_id=tenant_id, query_text=q, city=city, is_active=is_active, limit=limit)
    return {"version": "v1.3.9", "count": len(records), "addresses": [record.model_dump(mode="json") for record in records]}


@router.get("/{address_id}")
def get_address(address_id: str, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    record = service.get_address(address_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return record.model_dump(mode="json")


@router.post("")
def create_address(request: AddressInput, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    return service.save_address(request).model_dump(mode="json")


@router.put("/{address_id}")
def update_address(address_id: str, request: AddressInput, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    return service.save_address(request.model_copy(update={"address_id": address_id})).model_dump(mode="json")


@router.delete("/{address_id}")
def deactivate_address(address_id: str, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    record = service.deactivate_address(address_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return record.model_dump(mode="json")


@router.post("/link-to-appointment")
def link_to_appointment(request: AddressLinkInput, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    return service.link_address_to_appointment(request)


@router.get("/appointment-links/{appointment_external_id}")
def list_appointment_links(appointment_external_id: str, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    return {"version": "v1.3.9", "links": service.list_links_for_appointment(appointment_external_id)}


@router.get("/{address_id}/links")
def list_address_links(address_id: str, service: AddressDatabaseService = Depends(_service)) -> dict[str, object]:
    return {"version": "v1.3.9", "links": service.list_links_for_address(address_id)}
