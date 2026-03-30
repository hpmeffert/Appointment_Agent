from __future__ import annotations

from google_adapter.v1_1_0_patch8a.google_adapter.service import (
    DemoCalendarPatch6Request,
    DemoCalendarPatch6Result,
    GoogleAdapterServiceV110Patch8A,
    GoogleBookingActionResult,
    GoogleBookingCreateRequest,
    GoogleBookingRescheduleRequest,
)


class GoogleAdapterServiceV110Patch8B(GoogleAdapterServiceV110Patch8A):
    """Patch 8b keeps the proven Patch 8a behavior and only adds clearer
    monitoring labels for the end-to-end interactive booking story."""

    def create_booking_patch8a(self, request: GoogleBookingCreateRequest, *, journey_id: str, hold_id: str) -> GoogleBookingActionResult:
        result = super().create_booking_patch8a(request, journey_id=journey_id, hold_id=hold_id)
        if result.success:
            result.monitoring_labels.extend(["booking.revalidation.started", "booking.revalidation.succeeded"])
        else:
            result.monitoring_labels.extend(["booking.revalidation.started", "booking.revalidation.failed"])
            if result.conflict_detected:
                result.monitoring_labels.append("booking.blocked.by_conflict")
        result.monitoring_labels = list(dict.fromkeys(result.monitoring_labels))
        return result

    def reschedule_booking_patch8a(
        self,
        request: GoogleBookingRescheduleRequest,
        *,
        journey_id: str,
        hold_id: str,
    ) -> GoogleBookingActionResult:
        result = super().reschedule_booking_patch8a(request, journey_id=journey_id, hold_id=hold_id)
        if result.success:
            result.monitoring_labels.extend(["booking.revalidation.started", "booking.revalidation.succeeded"])
        else:
            result.monitoring_labels.extend(["booking.revalidation.started", "booking.revalidation.failed"])
            if result.conflict_detected:
                result.monitoring_labels.append("booking.blocked.by_conflict")
        result.monitoring_labels = list(dict.fromkeys(result.monitoring_labels))
        return result
