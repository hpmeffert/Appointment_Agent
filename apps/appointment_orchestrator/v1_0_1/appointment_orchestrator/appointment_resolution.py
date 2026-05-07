from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Literal, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from appointment_agent_shared.models import (
    AddressAppointmentLinkRecord,
    AddressRecord,
    AppointmentJourneyRecord,
    BookingRecord,
    GoogleDemoEventRecord,
)
from appointment_agent_shared.repositories import AddressLinkageResolver, AddressRepository, JourneyRepository


ResolutionStatus = Literal["no_match", "single_match", "multiple_matches"]
TrustLevel = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass
class AppointmentResolutionContext:
    booking_reference: Optional[str] = None
    reservation_ref: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_id: Optional[str] = None
    provider_event_ref: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_number: Optional[str] = None
    contact_id: Optional[str] = None
    customer_name: Optional[str] = None
    appointment_type: Optional[str] = None
    address_id: Optional[str] = None
    requested_action: Optional[str] = None
    requested_datetime_hint: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    raw_input_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentCandidate:
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None
    provider_event_ref: Optional[str] = None
    correlation_id: Optional[str] = None
    contact_id: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    appointment_type: Optional[str] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    address_id: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    source_trust_level: Optional[TrustLevel] = None
    match_score: float = 0.0
    match_basis: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentChoiceOption:
    option_id: str
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None
    provider_event_ref: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    appointment_type: Optional[str] = None
    starts_at: Optional[str] = None
    address_label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentDisambiguationPayload:
    prompt: str
    options: List[AppointmentChoiceOption] = field(default_factory=list)
    allow_show_all: bool = False
    allow_cancel_selection: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentListOption:
    option_id: str
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None
    provider_event_ref: Optional[str] = None
    appointment_type: Optional[str] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    address_label: Optional[str] = None
    status: Optional[str] = None
    summary_line: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentListPayload:
    prompt: str
    options: List[AppointmentListOption] = field(default_factory=list)
    view_type: str = "appointment_list"
    allow_selection: bool = True
    allow_show_all_future: bool = True
    allow_cancel: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentResolutionResult:
    resolution_status: ResolutionStatus
    candidates: List[AppointmentCandidate] = field(default_factory=list)
    selected: Optional[AppointmentCandidate] = None
    match_basis: List[str] = field(default_factory=list)
    clarification_required: bool = False
    clarification_reason: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    disambiguation_payload: Optional[AppointmentDisambiguationPayload] = None
    appointment_list_payload: Optional[AppointmentListPayload] = None


def _normalized_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = "".join(character for character in str(value) if character.isdigit())
    return digits or None


def _normalized_identity(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _trust_rank(value: Optional[TrustLevel]) -> int:
    if value == "HIGH":
        return 3
    if value == "MEDIUM":
        return 2
    return 1


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


class ExistingBookingResolver:
    """APP-73 Step 3 real candidate retrieval scaffold.

    The resolver now queries real internal sources and produces normalized
    candidates plus disambiguation payloads. It still stays out of live
    confirm/reschedule/cancel mutation entrypoints until later steps.
    """

    HIGH_TRUST: TrustLevel = "HIGH"
    MEDIUM_TRUST: TrustLevel = "MEDIUM"
    LOW_TRUST: TrustLevel = "LOW"

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session
        self.journeys = JourneyRepository(session) if session is not None else None
        self.addresses = AddressRepository(session) if session is not None else None
        self.linkage = AddressLinkageResolver(session) if session is not None else None
        self._filter_notes: List[str] = []

    def resolve(self, context: AppointmentResolutionContext) -> AppointmentResolutionResult:
        self._filter_notes = []
        candidate_groups = [
            self._get_candidates_from_current_context(context),
            self._match_by_hard_identifiers(context),
            self._get_candidates_from_booking_store(context),
            self._get_candidates_from_provider_refs(context),
            self._resolve_contact_candidates(context),
        ]
        merged = self._merge_candidates(candidate_groups)
        filtered = self._filter_candidates(merged, context)
        result = self._finalize_result(filtered)
        result.notes.extend(note for note in self._filter_notes if note not in result.notes)
        if result.candidates:
            result.appointment_list_payload = self.build_appointment_list_payload(
                result.candidates,
                context,
                allow_selection=True,
                include_show_all_future=True,
            )
        if result.resolution_status == "multiple_matches":
            result.disambiguation_payload = self.build_disambiguation_payload(result.candidates, context)
        return result

    def list_appointments(self, context: AppointmentResolutionContext) -> AppointmentResolutionResult:
        self._filter_notes = []
        candidate_groups = [
            self._get_candidates_from_current_context(context),
            self._match_by_hard_identifiers(context),
            self._get_candidates_from_booking_store(context),
            self._get_candidates_from_provider_refs(context),
            self._resolve_contact_candidates(context),
        ]
        merged = self._merge_candidates(candidate_groups)
        filtered = self._filter_candidates(merged, context)
        if not filtered:
            return AppointmentResolutionResult(
                resolution_status="no_match",
                clarification_required=False,
                clarification_reason="no_candidates",
                notes=["No upcoming appointments were found.", *self._filter_notes],
                appointment_list_payload=self.build_appointment_list_payload(
                    [],
                    context,
                    allow_selection=False,
                    include_show_all_future=True,
                ),
            )
        result = AppointmentResolutionResult(
            resolution_status="multiple_matches" if len(filtered) > 1 else "single_match",
            candidates=filtered,
            selected=filtered[0] if len(filtered) == 1 else None,
            match_basis=list(filtered[0].match_basis) if len(filtered) == 1 else [],
            clarification_required=len(filtered) > 1,
            clarification_reason="multiple_candidates" if len(filtered) > 1 else None,
            notes=list(self._filter_notes),
            appointment_list_payload=self.build_appointment_list_payload(
                filtered,
                context,
                allow_selection=True,
                include_show_all_future=True,
            ),
        )
        return result

    def _get_candidates_from_current_context(
        self,
        context: AppointmentResolutionContext,
    ) -> List[AppointmentCandidate]:
        if self.session is None:
            return []

        candidates: List[AppointmentCandidate] = []
        journey_id = context.metadata.get("journey_id")
        if journey_id and self.journeys is not None:
            journey = self.journeys.get(str(journey_id))
            if journey is not None:
                candidate = self._candidate_from_journey(journey, match_basis=["journey_id"])
                if candidate is not None:
                    candidates.append(candidate)

        if context.metadata.get("current_journey") and isinstance(context.metadata["current_journey"], dict):
            snapshot = dict(context.metadata["current_journey"])
            candidates.append(
                AppointmentCandidate(
                    appointment_id=snapshot.get("appointment_id"),
                    booking_reference=snapshot.get("booking_reference"),
                    provider_event_ref=snapshot.get("provider_event_ref") or snapshot.get("provider_reference"),
                    correlation_id=snapshot.get("correlation_id"),
                    contact_id=snapshot.get("contact_id"),
                    customer_phone=snapshot.get("customer_phone"),
                    customer_name=snapshot.get("customer_name"),
                    appointment_type=snapshot.get("appointment_type"),
                    starts_at=snapshot.get("starts_at") or snapshot.get("start_time"),
                    ends_at=snapshot.get("ends_at") or snapshot.get("end_time"),
                    address_id=snapshot.get("address_id"),
                    status=snapshot.get("status") or snapshot.get("current_state"),
                    source="current_context_snapshot",
                    source_trust_level=self.HIGH_TRUST,
                    match_score=1.0,
                    match_basis=["current_context"],
                    metadata={"snapshot": snapshot},
                )
            )

        if context.metadata.get("scenario_context") and isinstance(context.metadata["scenario_context"], dict):
            snapshot = dict(context.metadata["scenario_context"])
            candidates.append(
                AppointmentCandidate(
                    appointment_id=snapshot.get("appointment_id"),
                    booking_reference=snapshot.get("booking_reference"),
                    provider_event_ref=snapshot.get("provider_event_ref"),
                    correlation_id=snapshot.get("correlation_ref") or snapshot.get("correlation_id"),
                    customer_name=snapshot.get("customer_name"),
                    appointment_type=snapshot.get("appointment_type"),
                    starts_at=snapshot.get("starts_at"),
                    ends_at=snapshot.get("ends_at"),
                    address_id=snapshot.get("address_id"),
                    status=snapshot.get("status"),
                    source="scenario_context",
                    source_trust_level=self.MEDIUM_TRUST,
                    match_score=0.85,
                    match_basis=["scenario_context"],
                    metadata={"snapshot": snapshot},
                )
            )

        return [candidate for candidate in candidates if self._candidate_has_identity(candidate)]

    def _match_by_hard_identifiers(
        self,
        context: AppointmentResolutionContext,
    ) -> List[AppointmentCandidate]:
        if self.session is None:
            return []

        candidates: List[AppointmentCandidate] = []
        if context.correlation_id and self.journeys is not None:
            journey = self.journeys.get_by_correlation_id(context.correlation_id)
            if journey is not None:
                candidate = self._candidate_from_journey(journey, match_basis=["correlation_id"])
                if candidate is not None:
                    candidates.append(candidate)

        if context.booking_reference:
            record = self.session.scalar(
                select(BookingRecord).where(BookingRecord.booking_reference == context.booking_reference)
            )
            if record is not None:
                candidates.append(self._candidate_from_booking_record(record, match_basis=["booking_reference"]))

        reservation_ref = _normalized_identity(context.reservation_ref)
        if reservation_ref:
            record = self.session.scalar(
                select(BookingRecord).where(BookingRecord.booking_reference == reservation_ref)
            )
            if record is not None:
                candidates.append(self._candidate_from_booking_record(record, match_basis=["reservation_ref"]))

        if context.provider_event_ref:
            event = self.session.scalar(
                select(GoogleDemoEventRecord).where(GoogleDemoEventRecord.provider_reference == context.provider_event_ref)
            )
            if event is not None:
                candidates.append(self._candidate_from_google_event(event, match_basis=["provider_event_ref"]))

        if context.appointment_id:
            links = list(
                self.session.scalars(
                    select(AddressAppointmentLinkRecord).where(
                        AddressAppointmentLinkRecord.appointment_external_id == context.appointment_id
                    )
                )
            )
            for link in links:
                candidate = self._candidate_from_address_link(link, match_basis=["appointment_id"])
                if candidate is not None:
                    candidates.append(candidate)

        customer_number = _normalized_identity(context.customer_number)
        if customer_number:
            addresses = list(
                self.session.scalars(
                    select(AddressRecord).where(AddressRecord.customer_number == customer_number, AddressRecord.is_active.is_(True))
                )
            )
            for address in addresses:
                links = list(
                    self.session.scalars(
                        select(AddressAppointmentLinkRecord).where(AddressAppointmentLinkRecord.address_id == address.address_id)
                    )
                )
                for link in links:
                    candidate = self._candidate_from_address_link(link, match_basis=["customer_number"])
                    if candidate is not None:
                        candidate.customer_name = candidate.customer_name or address.display_name
                        candidate.customer_phone = candidate.customer_phone or address.phone
                        candidates.append(candidate)
        return candidates

    def _get_candidates_from_booking_store(
        self,
        context: AppointmentResolutionContext,
    ) -> List[AppointmentCandidate]:
        if self.session is None:
            return []

        candidates: List[AppointmentCandidate] = []
        query = select(BookingRecord)
        clauses = []
        if context.booking_reference:
            clauses.append(BookingRecord.booking_reference == context.booking_reference)
        if context.provider_event_ref:
            clauses.append(BookingRecord.external_id == context.provider_event_ref)
        if context.customer_name:
            clauses.append(BookingRecord.customer_id == context.customer_name)
        if not clauses:
            return []
        records = list(self.session.scalars(query.where(*clauses)))
        for record in records:
            basis = []
            if context.booking_reference and record.booking_reference == context.booking_reference:
                basis.append("booking_reference")
            if context.provider_event_ref and record.external_id == context.provider_event_ref:
                basis.append("provider_event_ref")
            if context.customer_name and record.customer_id == context.customer_name:
                basis.append("customer_name")
            candidates.append(self._candidate_from_booking_record(record, match_basis=basis or ["booking_store"]))
        return candidates

    def _get_candidates_from_provider_refs(
        self,
        context: AppointmentResolutionContext,
    ) -> List[AppointmentCandidate]:
        if self.session is None:
            return []

        query = select(GoogleDemoEventRecord).where(GoogleDemoEventRecord.is_deleted.is_(False))
        clauses = []
        if context.provider_event_ref:
            clauses.append(GoogleDemoEventRecord.provider_reference == context.provider_event_ref)
        if context.booking_reference:
            clauses.append(GoogleDemoEventRecord.booking_reference == context.booking_reference)
        if context.customer_phone:
            normalized = _normalized_phone(context.customer_phone)
            if normalized:
                events = list(self.session.scalars(query))
                return [
                    self._candidate_from_google_event(event, match_basis=["customer_phone"])
                    for event in events
                    if _normalized_phone(event.mobile_number) == normalized
                ]
        if not clauses:
            return []
        return [
            self._candidate_from_google_event(event, match_basis=["provider_or_calendar_record"])
            for event in self.session.scalars(query.where(*clauses))
        ]

    def _resolve_contact_candidates(
        self,
        context: AppointmentResolutionContext,
    ) -> List[AppointmentCandidate]:
        if self.session is None or self.linkage is None:
            return []

        resolution = self.linkage.resolve(
            tenant_id=str(context.metadata.get("tenant_id") or "default"),
            address_id=context.address_id,
            appointment_id=context.appointment_id,
            booking_reference=context.booking_reference,
            correlation_ref=context.correlation_id,
            phone_number=context.customer_phone,
            email=context.metadata.get("customer_email"),
        )
        candidates: List[AppointmentCandidate] = []
        if resolution.booking_reference:
            record = self.session.scalar(
                select(BookingRecord).where(BookingRecord.booking_reference == resolution.booking_reference)
            )
            if record is not None:
                candidate = self._candidate_from_booking_record(record, match_basis=["contact_resolution"])
                candidate.address_id = candidate.address_id or resolution.address_id
                candidate.correlation_id = candidate.correlation_id or resolution.correlation_ref
                candidates.append(candidate)

        if resolution.address_id:
            address_record = self.addresses.get(resolution.address_id) if self.addresses is not None else None
            links = list(
                self.session.scalars(
                    select(AddressAppointmentLinkRecord).where(AddressAppointmentLinkRecord.address_id == resolution.address_id)
                )
            )
            for link in links:
                candidate = self._candidate_from_address_link(link, match_basis=["address_link"])
                if candidate is not None:
                    if address_record is not None:
                        candidate.customer_name = candidate.customer_name or address_record.display_name
                        candidate.customer_phone = candidate.customer_phone or address_record.phone
                    candidates.append(candidate)
        return candidates

    def _merge_candidates(self, candidate_groups: List[List[AppointmentCandidate]]) -> List[AppointmentCandidate]:
        merged: List[AppointmentCandidate] = []
        for group in candidate_groups:
            for candidate in group:
                if not self._candidate_has_identity(candidate):
                    continue
                existing = self._find_equivalent_candidate(merged, candidate)
                if existing is None:
                    merged.append(candidate)
                    continue
                merged[merged.index(existing)] = self._merge_two_candidates(existing, candidate)
        return sorted(
            merged,
            key=lambda candidate: (
                _parse_iso_datetime(candidate.starts_at) or datetime.max.replace(tzinfo=dt_timezone.utc),
                candidate.booking_reference or "",
            ),
        )

    def _filter_candidates(
        self,
        candidates: List[AppointmentCandidate],
        context: AppointmentResolutionContext,
    ) -> List[AppointmentCandidate]:
        self._filter_notes = []
        filtered: List[AppointmentCandidate] = []
        now = datetime.now(dt_timezone.utc)
        requested_type = (context.appointment_type or "").strip().lower()
        requested_address = (context.address_id or "").strip()
        requested_phone = _normalized_phone(context.customer_phone)
        requested_name = (context.customer_name or "").strip().lower()

        for candidate in candidates:
            status = (candidate.status or "").strip().lower()
            if status in {"cancelled", "cancellation_flow", "closed", "deleted"}:
                self._filter_notes.append(
                    f"Filtered candidate {candidate.booking_reference or candidate.provider_event_ref or candidate.appointment_id} due to inactive status '{status}'."
                )
                continue

            starts_at = _parse_iso_datetime(candidate.starts_at)
            if starts_at is not None:
                starts_at_utc = starts_at.astimezone(dt_timezone.utc) if starts_at.tzinfo else starts_at.replace(tzinfo=dt_timezone.utc)
                if starts_at_utc <= now:
                    self._filter_notes.append(
                        f"Filtered candidate {candidate.booking_reference or candidate.provider_event_ref or candidate.appointment_id} because it is not a future appointment."
                    )
                    continue

            if requested_type and (candidate.appointment_type or "").strip().lower() not in {"", requested_type}:
                self._filter_notes.append(
                    f"Filtered candidate {candidate.booking_reference or candidate.provider_event_ref or candidate.appointment_id} due to appointment_type mismatch."
                )
                continue

            if requested_address and candidate.address_id and candidate.address_id != requested_address:
                self._filter_notes.append(
                    f"Filtered candidate {candidate.booking_reference or candidate.provider_event_ref or candidate.appointment_id} due to address mismatch."
                )
                continue

            candidate_phone = _normalized_phone(candidate.customer_phone)
            if requested_phone and candidate_phone and requested_phone != candidate_phone:
                self._filter_notes.append(
                    f"Filtered candidate {candidate.booking_reference or candidate.provider_event_ref or candidate.appointment_id} due to phone mismatch."
                )
                continue

            candidate_name = (candidate.customer_name or "").strip().lower()
            if requested_name and candidate_name and requested_name != candidate_name:
                self._filter_notes.append(
                    f"Filtered candidate {candidate.booking_reference or candidate.provider_event_ref or candidate.appointment_id} due to customer_name mismatch."
                )
                continue

            filtered.append(candidate)

        if candidates and not filtered:
            self._filter_notes.append("All retrieved candidates were filtered out by active/future/relevance rules.")
        return filtered

    def build_disambiguation_payload(
        self,
        candidates: List[AppointmentCandidate],
        context: AppointmentResolutionContext,
    ) -> AppointmentDisambiguationPayload:
        locale = (context.locale or context.metadata.get("locale") or "en").lower()
        is_german = locale.startswith("de")
        options = [self._build_choice_option(candidate, locale=locale) for candidate in candidates]
        count = len(options)
        prompt = (
            f"Ich habe {count} Termine gefunden. Welchen möchten Sie bearbeiten?"
            if is_german
            else f"I found {count} appointments. Which one would you like to edit?"
        )
        return AppointmentDisambiguationPayload(
            prompt=prompt,
            options=options,
            allow_show_all=False,
            allow_cancel_selection=True,
            metadata={
                "locale": "de" if is_german else "en",
                "requested_action": context.requested_action,
                "candidate_count": count,
            },
        )

    def build_appointment_list_payload(
        self,
        candidates: List[AppointmentCandidate],
        context: AppointmentResolutionContext,
        *,
        allow_selection: bool,
        include_show_all_future: bool,
    ) -> AppointmentListPayload:
        locale = (context.locale or context.metadata.get("locale") or "en").lower()
        intent = (context.requested_action or "").lower()
        if not candidates:
            prompt = (
                "Ich konnte aktuell keine zukünftigen Termine finden."
                if locale.startswith("de")
                else "I could not find any upcoming appointments right now."
            )
        elif intent in {"show_appointments", "show_future_appointments"}:
            prompt = (
                "Ich habe diese zukünftigen Termine gefunden."
                if locale.startswith("de")
                else "I found these upcoming appointments."
            )
        else:
            prompt = (
                "Ich habe mehrere Termine gefunden. Bitte wählen Sie zuerst den Termin aus, den Sie bearbeiten möchten."
                if locale.startswith("de")
                else "I found multiple appointments. Please choose the appointment you want to edit first."
            )
        options = [self._build_list_option(candidate, locale=locale) for candidate in candidates]
        return AppointmentListPayload(
            prompt=prompt,
            options=options,
            view_type="appointment_list",
            allow_selection=allow_selection,
            allow_show_all_future=include_show_all_future,
            allow_cancel=True,
            metadata={
                "locale": "de" if locale.startswith("de") else "en",
                "requested_action": context.requested_action,
                "candidate_count": len(options),
            },
        )

    def _finalize_result(
        self,
        candidates: List[AppointmentCandidate],
    ) -> AppointmentResolutionResult:
        if not candidates:
            return AppointmentResolutionResult(
                resolution_status="no_match",
                clarification_required=False,
                clarification_reason="no_candidates",
                notes=["No appointment candidates survived staged resolution."],
            )

        if len(candidates) == 1:
            candidate = candidates[0]
            match_basis = list(candidate.match_basis)
            trust_level = candidate.source_trust_level or self.LOW_TRUST
            clarification_required = trust_level == self.LOW_TRUST
            clarification_reason = "low_trust_single_candidate" if clarification_required else None
            notes = []
            if clarification_required:
                notes.append("Single candidate found, but trust level is too weak for silent mutation.")
            else:
                notes.append("Single candidate found with acceptable trust level.")
            return AppointmentResolutionResult(
                resolution_status="single_match",
                candidates=candidates,
                selected=candidate,
                match_basis=match_basis,
                clarification_required=clarification_required,
                clarification_reason=clarification_reason,
                notes=notes,
            )

        aggregate_basis: List[str] = []
        for candidate in candidates:
            for basis in candidate.match_basis:
                if basis not in aggregate_basis:
                    aggregate_basis.append(basis)
        return AppointmentResolutionResult(
            resolution_status="multiple_matches",
            candidates=candidates,
            selected=None,
            match_basis=aggregate_basis,
            clarification_required=True,
            clarification_reason="multiple_candidates",
            notes=["Multiple candidates remain after staged matching; user clarification is required."],
        )

    def _candidate_from_journey(
        self,
        journey: AppointmentJourneyRecord,
        *,
        match_basis: List[str],
    ) -> Optional[AppointmentCandidate]:
        payload = dict(journey.preference_payload or {})
        candidate = AppointmentCandidate(
            appointment_id=payload.get("appointment_id"),
            booking_reference=journey.booking_reference,
            provider_event_ref=payload.get("provider_reference"),
            correlation_id=journey.correlation_id,
            contact_id=journey.customer_id,
            customer_name=payload.get("customer_name") or journey.customer_id,
            appointment_type=payload.get("appointment_type") or journey.service_type,
            starts_at=payload.get("start_time") or (journey.selected_slot or {}).get("start"),
            ends_at=payload.get("end_time") or (journey.selected_slot or {}).get("end"),
            address_id=payload.get("address_id"),
            status=journey.current_state,
            source="journey_store",
            source_trust_level=self.HIGH_TRUST,
            match_score=1.0,
            match_basis=list(match_basis),
            metadata={"journey_id": journey.journey_id},
        )
        return candidate if self._candidate_has_identity(candidate) else None

    def _candidate_from_booking_record(
        self,
        record: BookingRecord,
        *,
        match_basis: List[str],
    ) -> AppointmentCandidate:
        payload = dict(record.payload or {})
        provider_ref = record.external_id or payload.get("provider_reference", {}).get("external_id")
        return AppointmentCandidate(
            appointment_id=payload.get("appointment_id"),
            booking_reference=record.booking_reference,
            provider_event_ref=provider_ref,
            correlation_id=payload.get("correlation_id"),
            contact_id=record.customer_id,
            customer_name=payload.get("customer_name") or record.customer_id,
            appointment_type=payload.get("appointment_type"),
            starts_at=payload.get("start_time"),
            ends_at=payload.get("end_time"),
            address_id=payload.get("address_id"),
            status=record.status,
            source="booking_store",
            source_trust_level=self.HIGH_TRUST,
            match_score=0.95,
            match_basis=list(match_basis),
            metadata={"journey_id": record.journey_id},
        )

    def _candidate_from_google_event(
        self,
        event: GoogleDemoEventRecord,
        *,
        match_basis: List[str],
    ) -> AppointmentCandidate:
        starts_at = event.start_time_utc.replace(tzinfo=dt_timezone.utc).astimezone(
            dt_timezone.utc
        ).isoformat()
        ends_at = event.end_time_utc.replace(tzinfo=dt_timezone.utc).astimezone(
            dt_timezone.utc
        ).isoformat()
        details = dict(event.details or {})
        return AppointmentCandidate(
            appointment_id=details.get("appointment_id"),
            booking_reference=event.booking_reference,
            provider_event_ref=event.provider_reference or event.event_id,
            correlation_id=details.get("correlation_id"),
            customer_phone=event.mobile_number,
            customer_name=event.customer_name,
            appointment_type=details.get("appointment_type"),
            starts_at=starts_at,
            ends_at=ends_at,
            address_id=details.get("address_id"),
            status="cancelled" if event.is_deleted else "confirmed",
            source="calendar_linked_records",
            source_trust_level=self.HIGH_TRUST if (event.provider_reference or event.event_id) else self.MEDIUM_TRUST,
            match_score=0.9,
            match_basis=list(match_basis),
            metadata={"calendar_id": event.calendar_id, "timezone": event.timezone, "title": event.title},
        )

    def _candidate_from_address_link(
        self,
        link: AddressAppointmentLinkRecord,
        *,
        match_basis: List[str],
    ) -> Optional[AppointmentCandidate]:
        booking_record = None
        google_record = None
        if self.session is not None and link.booking_reference:
            booking_record = self.session.scalar(
                select(BookingRecord).where(BookingRecord.booking_reference == link.booking_reference)
            )
            google_record = self.session.scalar(
                select(GoogleDemoEventRecord).where(GoogleDemoEventRecord.booking_reference == link.booking_reference)
            )
        candidate = AppointmentCandidate(
            appointment_id=link.appointment_external_id,
            booking_reference=link.booking_reference,
            provider_event_ref=getattr(booking_record, "external_id", None)
            or getattr(google_record, "provider_reference", None),
            correlation_id=link.correlation_ref,
            appointment_type=(booking_record.payload or {}).get("appointment_type") if booking_record is not None else None,
            starts_at=(booking_record.payload or {}).get("start_time") if booking_record is not None else None,
            ends_at=(booking_record.payload or {}).get("end_time") if booking_record is not None else None,
            address_id=link.address_id,
            status=getattr(booking_record, "status", None),
            source="address_link_store",
            source_trust_level=self.HIGH_TRUST if link.booking_reference else self.MEDIUM_TRUST,
            match_score=0.8,
            match_basis=list(match_basis),
            metadata={"calendar_ref": link.calendar_ref},
        )
        return candidate if self._candidate_has_identity(candidate) else None

    def _candidate_has_identity(self, candidate: AppointmentCandidate) -> bool:
        return any(
            [
                candidate.provider_event_ref,
                candidate.booking_reference,
                candidate.appointment_id,
                candidate.correlation_id,
            ]
        )

    def _candidate_identity_key(self, candidate: AppointmentCandidate) -> str:
        if candidate.provider_event_ref:
            return f"provider:{candidate.provider_event_ref}"
        if candidate.booking_reference:
            return f"booking:{candidate.booking_reference}"
        if candidate.appointment_id:
            return f"appointment:{candidate.appointment_id}"
        if candidate.correlation_id:
            return f"correlation:{candidate.correlation_id}"
        fingerprint = sha256(
            "|".join(
                [
                    candidate.customer_name or "",
                    candidate.customer_phone or "",
                    candidate.appointment_type or "",
                    candidate.starts_at or "",
                    candidate.address_id or "",
                ]
            ).encode("utf-8")
        ).hexdigest()[:16]
        return f"fallback:{fingerprint}"

    def _find_equivalent_candidate(
        self,
        existing_candidates: List[AppointmentCandidate],
        incoming: AppointmentCandidate,
    ) -> Optional[AppointmentCandidate]:
        for candidate in existing_candidates:
            if candidate.provider_event_ref and incoming.provider_event_ref and candidate.provider_event_ref == incoming.provider_event_ref:
                return candidate
            if candidate.booking_reference and incoming.booking_reference and candidate.booking_reference == incoming.booking_reference:
                return candidate
            if candidate.appointment_id and incoming.appointment_id and candidate.appointment_id == incoming.appointment_id:
                return candidate
            if candidate.correlation_id and incoming.correlation_id and candidate.correlation_id == incoming.correlation_id:
                return candidate
        return None

    def _merge_two_candidates(
        self,
        left: AppointmentCandidate,
        right: AppointmentCandidate,
    ) -> AppointmentCandidate:
        primary, secondary = (
            (left, right)
            if _trust_rank(left.source_trust_level) >= _trust_rank(right.source_trust_level)
            else (right, left)
        )
        merged = AppointmentCandidate(
            appointment_id=primary.appointment_id or secondary.appointment_id,
            booking_reference=primary.booking_reference or secondary.booking_reference,
            provider_event_ref=primary.provider_event_ref or secondary.provider_event_ref,
            correlation_id=primary.correlation_id or secondary.correlation_id,
            contact_id=primary.contact_id or secondary.contact_id,
            customer_phone=primary.customer_phone or secondary.customer_phone,
            customer_name=primary.customer_name or secondary.customer_name,
            appointment_type=primary.appointment_type or secondary.appointment_type,
            starts_at=primary.starts_at or secondary.starts_at,
            ends_at=primary.ends_at or secondary.ends_at,
            address_id=primary.address_id or secondary.address_id,
            status=primary.status or secondary.status,
            source=primary.source,
            source_trust_level=primary.source_trust_level,
            match_score=max(primary.match_score, secondary.match_score),
            match_basis=[],
            metadata={**secondary.metadata, **primary.metadata},
        )
        for basis in list(primary.match_basis) + list(secondary.match_basis):
            if basis not in merged.match_basis:
                merged.match_basis.append(basis)
        return merged

    def _build_choice_option(
        self,
        candidate: AppointmentCandidate,
        *,
        locale: str,
    ) -> AppointmentChoiceOption:
        title = self._format_datetime_title(candidate.starts_at, locale=locale)
        appointment_type = self._humanize_appointment_type(candidate.appointment_type)
        subtitle_parts = [part for part in [appointment_type, candidate.customer_name] if part]
        address_label = self._address_label(candidate.address_id)
        if address_label:
            subtitle_parts.append(address_label)
        return AppointmentChoiceOption(
            option_id=self._choice_option_id(candidate),
            appointment_id=candidate.appointment_id,
            booking_reference=candidate.booking_reference,
            provider_event_ref=candidate.provider_event_ref,
            title=title,
            subtitle=" — ".join(subtitle_parts) if subtitle_parts else appointment_type,
            appointment_type=candidate.appointment_type,
            starts_at=candidate.starts_at,
            address_label=address_label,
            metadata={"source": candidate.source, "match_basis": list(candidate.match_basis)},
        )

    def _build_list_option(
        self,
        candidate: AppointmentCandidate,
        *,
        locale: str,
    ) -> AppointmentListOption:
        address_label = self._address_label(candidate.address_id)
        return AppointmentListOption(
            option_id=self._choice_option_id(candidate),
            appointment_id=candidate.appointment_id,
            booking_reference=candidate.booking_reference,
            provider_event_ref=candidate.provider_event_ref,
            appointment_type=candidate.appointment_type,
            starts_at=candidate.starts_at,
            ends_at=candidate.ends_at,
            address_label=address_label,
            status=candidate.status,
            summary_line=self._format_summary_line(candidate, locale=locale),
            metadata={"source": candidate.source, "match_basis": list(candidate.match_basis)},
        )

    def _choice_option_id(self, candidate: AppointmentCandidate) -> str:
        if candidate.provider_event_ref:
            return f"provider:{candidate.provider_event_ref}"
        if candidate.booking_reference:
            return f"booking:{candidate.booking_reference}"
        if candidate.appointment_id:
            return f"appointment:{candidate.appointment_id}"
        if candidate.correlation_id:
            return f"correlation:{candidate.correlation_id}"
        return self._candidate_identity_key(candidate)

    def _format_datetime_title(self, value: Optional[str], *, locale: str) -> Optional[str]:
        parsed = _parse_iso_datetime(value)
        if parsed is None:
            return None
        target = parsed if parsed.tzinfo else parsed.replace(tzinfo=dt_timezone.utc)
        if locale.lower().startswith("de"):
            weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
            months = [
                "Januar",
                "Februar",
                "März",
                "April",
                "Mai",
                "Juni",
                "Juli",
                "August",
                "September",
                "Oktober",
                "November",
                "Dezember",
            ]
            return f"{weekdays[target.weekday()]}, {target.day}. {months[target.month - 1]}, {target.strftime('%H:%M')}"
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        return f"{weekdays[target.weekday()]}, {months[target.month - 1]} {target.day}, {target.strftime('%H:%M')}"

    def _format_summary_line(self, candidate: AppointmentCandidate, *, locale: str) -> Optional[str]:
        title = self._format_datetime_title(candidate.starts_at, locale=locale)
        appointment_type = self._localized_appointment_type(candidate.appointment_type, locale=locale)
        if title and appointment_type:
            return f"{title} — {appointment_type}"
        return title or appointment_type

    def _humanize_appointment_type(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        parts = str(value).replace("_", " ").split()
        return " ".join(part.capitalize() for part in parts)

    def _localized_appointment_type(self, value: Optional[str], *, locale: str) -> Optional[str]:
        if not value:
            return None
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        if locale.lower().startswith("de"):
            mapping = {
                "dentist": "Zahnarzt",
                "doctor": "Arzt",
                "technician": "Techniker",
                "tee_time": "T-Time",
            }
            return mapping.get(normalized, self._humanize_appointment_type(value))
        mapping = {
            "dentist": "Dentist",
            "doctor": "Doctor",
            "technician": "Technician",
            "tee_time": "Tee Time",
        }
        return mapping.get(normalized, self._humanize_appointment_type(value))

    def _address_label(self, address_id: Optional[str]) -> Optional[str]:
        if not address_id or self.addresses is None:
            return None
        record: Optional[AddressRecord] = self.addresses.get(address_id)
        if record is None:
            return None
        bits = [record.display_name]
        if record.city:
            bits.append(record.city)
        return " | ".join(bit for bit in bits if bit)
