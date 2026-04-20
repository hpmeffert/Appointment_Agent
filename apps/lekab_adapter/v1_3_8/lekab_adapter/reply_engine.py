from __future__ import annotations

import re
from typing import Any


GERMAN_MONTHS = {
    "januar": "01",
    "jan": "01",
    "februar": "02",
    "feb": "02",
    "maerz": "03",
    "märz": "03",
    "mrz": "03",
    "april": "04",
    "apr": "04",
    "mai": "05",
    "juni": "06",
    "jun": "06",
    "juli": "07",
    "jul": "07",
    "august": "08",
    "aug": "08",
    "september": "09",
    "sep": "09",
    "sept": "09",
    "oktober": "10",
    "okt": "10",
    "november": "11",
    "nov": "11",
    "dezember": "12",
    "dez": "12",
}

ENGLISH_MONTHS = {
    "january": "01",
    "jan": "01",
    "february": "02",
    "feb": "02",
    "march": "03",
    "mar": "03",
    "april": "04",
    "apr": "04",
    "may": "05",
    "june": "06",
    "jun": "06",
    "july": "07",
    "jul": "07",
    "august": "08",
    "aug": "08",
    "september": "09",
    "sep": "09",
    "october": "10",
    "oct": "10",
    "november": "11",
    "nov": "11",
    "december": "12",
    "dec": "12",
}

ORDINAL_PATTERNS = {
    1: ("first", "1st", "erste", "ersten", "the first one"),
    2: ("second", "2nd", "zweite", "zweiten", "the second one"),
    3: ("third", "3rd", "dritte", "dritten", "the third one"),
}


class ReplyToActionEngine:
    """Interpret inbound reply text into bus-safe action candidates.

    The parser is intentionally deterministic and conservative. For the demo we
    prefer a slightly more explicit "requires review" result over silently
    inventing a business action that later turns out to be wrong.
    """

    def extract_datetime_candidates(self, text: str) -> list[str]:
        candidates: list[str] = []
        for match in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
            candidates.append(match)
        for match in re.findall(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", text):
            candidates.append(match)
        for match in re.findall(r"\b\d{1,2}[:.]\d{2}\b", text):
            normalized = match.replace(".", ":")
            candidates.append(normalized)
        lowered = text.lower()
        month_names = {**GERMAN_MONTHS, **ENGLISH_MONTHS}
        for match in re.finditer(
            r"\b(\d{1,2})\s*(?:\.|)\s*([a-zA-ZäöüÄÖÜ]+)(?:\s*,?\s*(\d{1,2}[:.]\d{2}))?\b",
            lowered,
        ):
            day, month_name, time_value = match.groups()
            month_key = month_name.lower()
            if month_key in month_names:
                candidates.append(f"{int(day):02d}.{month_names[month_key]}")
                if time_value:
                    candidates.append(time_value.replace(".", ":"))
        for weekday_match in re.finditer(
            r"\b(next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)|naechsten?\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)|nächsten?\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag))\b",
            lowered,
        ):
            candidates.append(weekday_match.group(0))
        return list(dict.fromkeys(candidates))

    def _extract_ordinal_index(self, text: str) -> int | None:
        lowered = text.lower()
        for ordinal_index, variants in ORDINAL_PATTERNS.items():
            if any(variant in lowered for variant in variants):
                return ordinal_index
        return None

    def _build_action_candidate(
        self,
        *,
        action_type: str,
        reason: str,
        interpretation_state: str,
        confidence: float,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "event_type": "AppointmentActionRequested",
            "action_type": action_type,
            "reason": reason,
            "interpretation_state": interpretation_state,
            "interpretation_confidence": confidence,
            "requires_review": interpretation_state != "safe",
            "parameters": parameters or {},
        }

    def analyze_reply(self, text: str) -> dict[str, Any]:
        raw_text = (text or "").strip()
        normalized = raw_text.lower()
        candidates = self.extract_datetime_candidates(raw_text)
        ordinal_index = self._extract_ordinal_index(raw_text)

        if any(token in normalized for token in ("cancel", "storn", "absagen", "abbrechen")):
            return {
                "reply_intent": "cancel",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.cancel_requested",
                    reason="direct_cancel_reply",
                    interpretation_state="safe",
                    confidence=0.98,
                ),
            }
        if any(token in normalized for token in ("confirm", "confirmed", "bestätig", "bestaetig", "passt", "ok")):
            return {
                "reply_intent": "confirm",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.confirm_requested",
                    reason="direct_confirm_reply",
                    interpretation_state="safe",
                    confidence=0.95,
                ),
            }
        if any(token in normalized for token in ("next free slot", "first available", "next available", "naechster freier termin", "nächster freier termin")):
            return {
                "reply_intent": "appointment_next_free_slot",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.find_next_free_slot_requested",
                    reason="relative_next_free_slot_reply",
                    interpretation_state="safe",
                    confidence=0.93,
                ),
            }
        if any(token in normalized for token in ("new appointment", "find new date", "another slot", "neuer termin", "neuen termin", "finde neuen termin")):
            return {
                "reply_intent": "appointment_next_free_slot",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.find_next_free_slot_requested",
                    reason="new_appointment_search_reply",
                    interpretation_state="safe",
                    confidence=0.91,
                ),
            }
        if any(token in normalized for token in ("this week", "diese woche")):
            return {
                "reply_intent": "appointment_this_week",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.find_slot_this_week_requested",
                    reason="relative_this_week_reply",
                    interpretation_state="safe",
                    confidence=0.92,
                ),
            }
        if any(token in normalized for token in ("next week", "naechste woche", "nächste woche")):
            return {
                "reply_intent": "appointment_next_week",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.find_slot_next_week_requested",
                    reason="relative_next_week_reply",
                    interpretation_state="safe",
                    confidence=0.92,
                ),
            }
        if any(token in normalized for token in ("this month", "diesen monat", "diesem monat")):
            return {
                "reply_intent": "appointment_this_month",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.find_slot_this_month_requested",
                    reason="relative_this_month_reply",
                    interpretation_state="safe",
                    confidence=0.92,
                ),
            }
        if any(token in normalized for token in ("next month", "naechsten monat", "nächsten monat", "naechster monat", "nächster monat")):
            return {
                "reply_intent": "appointment_next_month",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.find_slot_next_month_requested",
                    reason="relative_next_month_reply",
                    interpretation_state="safe",
                    confidence=0.92,
                ),
            }
        if any(token in normalized for token in ("reschedule", "verschieb", "anderer termin", "neuer termin", "umplan")):
            return {
                "reply_intent": "reschedule",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.reschedule_requested",
                    reason="direct_reschedule_reply",
                    interpretation_state="safe" if not candidates else "safe",
                    confidence=0.95 if not candidates else 0.97,
                    parameters={"datetime_candidates": candidates},
                ),
            }

        if ordinal_index is not None:
            return {
                "reply_intent": "slot_selection",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.slot_selected",
                    reason="ordinal_slot_selection_reply",
                    interpretation_state="ambiguous",
                    confidence=0.74,
                    parameters={"selection_mode": "ordinal", "ordinal_index": ordinal_index},
                ),
            }

        if candidates:
            has_date_candidate = any("-" in candidate or "." in candidate for candidate in candidates)
            has_time_candidate = any(":" in candidate for candidate in candidates)
            if has_date_candidate and has_time_candidate:
                interpretation_state = "safe"
                confidence = 0.9
            else:
                interpretation_state = "ambiguous"
                confidence = 0.72
            return {
                "reply_intent": "slot_selection",
                "normalized_event_type": "message.reply_received",
                "reply_datetime_candidates": candidates,
                "action_candidate": self._build_action_candidate(
                    action_type="appointment.slot_selected",
                    reason="datetime_slot_selection_reply",
                    interpretation_state=interpretation_state,
                    confidence=confidence,
                    parameters={"selection_mode": "datetime_candidate", "datetime_candidates": candidates},
                ),
            }

        return {
            "reply_intent": "free_text",
            "normalized_event_type": "message.reply_received",
            "reply_datetime_candidates": candidates,
            "action_candidate": self._build_action_candidate(
                action_type="appointment.review_requested",
                reason="free_text_reply_requires_review",
                interpretation_state="review",
                confidence=0.2,
                parameters={"raw_text": raw_text},
            ),
        }
