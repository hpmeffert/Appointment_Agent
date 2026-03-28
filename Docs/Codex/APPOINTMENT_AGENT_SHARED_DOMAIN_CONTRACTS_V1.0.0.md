# APPOINTMENT_AGENT_SHARED_DOMAIN_CONTRACTS_V1.0.0

## Title
Shared Domain Contracts v1.0.0 for the LEKAB Appointment Agent Platform

## Status
Draft v1.0.0

## Purpose
This document defines the **shared domain contracts** for the LEKAB Appointment Agent platform.

It is the technical foundation for:
- Appointment Orchestrator
- LEKAB Adapter
- Google Calendar Adapter
- Microsoft Adapter
- Customer Contact Service
- Communication Bus
- State Store
- Audit / Analytics components

The goal is simple:

> Every component must speak the same language.

That means:
- same event envelope
- same command envelope
- same core domain objects
- same identifiers
- same state model
- same error shape
- same tracing and idempotency rules

This file should become the reference point for implementation and future versioning.

---

# Table of Contents

1. Design Principles
2. Versioning Rules
3. Global Naming Rules
4. Core Envelope Contracts
5. Core Identifiers
6. Shared Domain Models
7. Journey State Model
8. Shared Commands
9. Shared Events
10. Error Contract
11. Idempotency Rules
12. Time and Timezone Rules
13. Consent and Policy Fields
14. Audit and Observability Fields
15. Adapter Mapping Rules
16. Serialization Rules
17. Compatibility Rules
18. Recommended Package Structure
19. Acceptance Rules
20. Open Questions

---

# 1. Design Principles

The shared contracts must follow these principles:

## 1.1 Provider-neutral
Contracts must not expose provider-specific payloads as the primary business objects.

Bad:
- raw Google event payload as platform domain object
- raw LEKAB callback body as central journey state

Good:
- normalized booking result
- normalized appointment journey event
- normalized customer profile

## 1.2 Stable across adapters
Google, Microsoft, and LEKAB integrations must all map into the same internal contracts.

## 1.3 Explicit, not implicit
Every important transition must be represented as a command or event.

## 1.4 Traceable
Every contract must support:
- correlation
- causation
- tracing
- tenant separation
- replay/idempotency logic

## 1.5 Versioned
Contracts must evolve with explicit version control.

## 1.6 Minimal but sufficient
Do not put everything into the shared model.
Only move objects into shared contracts if multiple components need them.

---

# 2. Versioning Rules

## 2.1 Contract version
This document defines:

- **Contract Version:** `v1.0.0`

## 2.2 Semantic intent
- major = breaking contract change
- minor = backward-compatible addition
- patch = clarification or non-breaking refinement

## 2.3 Envelope version field
Every command/event envelope must include:

- `payload_version`

Example:
```json
"payload_version": "v1.0.0"
```

## 2.4 Version folder guidance
Recommended repo placement:
```text
apps/shared/v1_0_0/appointment_agent_shared/
```

---

# 3. Global Naming Rules

## 3.1 Event names
Use lowercase dot-separated names.

Examples:
- `appointment.search.requested`
- `calendar.slots.found`
- `lekab.job.started`
- `customer.resolved`

## 3.2 Command names
Use PascalCase in code, dot-separated intent names in event transport if needed.

Examples:
- `SearchSlotsCommand`
- `CreateBookingCommand`
- `ResolveCustomerCommand`

## 3.3 IDs
Use stable opaque IDs, not provider-specific IDs as primary keys.

Examples:
- `journey_id`
- `booking_reference`
- `customer_id`
- `event_id`

Provider IDs should be stored as external references.

---

# 4. Core Envelope Contracts

The platform needs two main envelopes:

1. `EventEnvelope`
2. `CommandEnvelope`

---

## 4.1 EventEnvelope

### Purpose
Wrap every domain event consistently.

### Required fields
- `event_id`
- `event_type`
- `payload_version`
- `timestamp_utc`
- `correlation_id`
- `causation_id`
- `trace_id`
- `tenant_id`
- `journey_id`
- `source`
- `idempotency_key`
- `payload`

### Example
```json
{
  "event_id": "evt_01",
  "event_type": "appointment.search.requested",
  "payload_version": "v1.0.0",
  "timestamp_utc": "2026-03-27T12:00:00Z",
  "correlation_id": "corr_1001",
  "causation_id": "cmd_2001",
  "trace_id": "trace_3001",
  "tenant_id": "tenant_demo",
  "journey_id": "journey_4001",
  "source": "appointment_orchestrator",
  "idempotency_key": "idem_5001",
  "payload": {
    "service_type": "onsite_visit"
  }
}
```

---

## 4.2 CommandEnvelope

### Purpose
Wrap every domain command consistently.

### Required fields
- `command_id`
- `command_type`
- `payload_version`
- `timestamp_utc`
- `correlation_id`
- `causation_id`
- `trace_id`
- `tenant_id`
- `journey_id`
- `source`
- `idempotency_key`
- `payload`

### Example
```json
{
  "command_id": "cmd_2001",
  "command_type": "SearchSlotsCommand",
  "payload_version": "v1.0.0",
  "timestamp_utc": "2026-03-27T12:00:00Z",
  "correlation_id": "corr_1001",
  "causation_id": "evt_0000",
  "trace_id": "trace_3001",
  "tenant_id": "tenant_demo",
  "journey_id": "journey_4001",
  "source": "appointment_orchestrator",
  "idempotency_key": "idem_5001",
  "payload": {
    "duration_minutes": 60
  }
}
```

---

# 5. Core Identifiers

The following identifiers should be standard across the platform.

## 5.1 `tenant_id`
Which customer/environment owns the data.

## 5.2 `journey_id`
Unique id for one appointment journey.

## 5.3 `correlation_id`
Groups all related activity across components.

## 5.4 `causation_id`
The event or command that directly caused this one.

## 5.5 `trace_id`
Tracing id for observability.

## 5.6 `customer_id`
Platform-owned stable customer identifier.

## 5.7 `booking_reference`
Platform-owned stable booking reference exposed to users and systems.

## 5.8 `provider_reference`
Provider-specific external id, e.g.:
- Google event id
- Dynamics appointment id
- LEKAB job runtime id

---

# 6. Shared Domain Models

Only the most important shared business objects should live here.

---

## 6.1 AppointmentJourney

### Purpose
Represents one appointment workflow from start to finish.

### Fields
- `journey_id`
- `tenant_id`
- `correlation_id`
- `customer_id`
- `channel`
- `service_type`
- `locale`
- `timezone`
- `current_state`
- `created_at_utc`
- `updated_at_utc`
- `booking_reference`
- `active_provider`
- `metadata`

### Notes
This is the central lifecycle object.

---

## 6.2 CustomerProfile

### Purpose
Represents the platform-owned customer master profile.

### Fields
- `customer_id`
- `external_customer_id`
- `display_name`
- `first_name`
- `last_name`
- `company_name`
- `mobile_number`
- `email`
- `preferred_language`
- `timezone`
- `country`
- `region`
- `consent_messaging`
- `consent_reminders`
- `crm_reference`
- `lekab_contact_id`
- `google_person_resource_name`
- `status`
- `created_at_utc`
- `updated_at_utc`

---

## 6.3 AppointmentPreference

### Purpose
Represents the customer’s appointment preferences.

### Fields
- `earliest_date`
- `latest_date`
- `preferred_month`
- `preferred_weekdays`
- `preferred_daypart`
- `preferred_location_type`
- `preferred_language`
- `urgency`
- `free_text_preference`

---

## 6.4 CandidateSlot

### Purpose
Represents an offerable appointment slot.

### Fields
- `slot_id`
- `start_time`
- `end_time`
- `timezone`
- `resource_id`
- `resource_type`
- `location`
- `score`
- `hold_expires_at`
- `provider`
- `provider_reference`
- `metadata`

### Notes
This is a normalized object returned by calendar adapters.

---

## 6.5 SlotHold

### Purpose
Represents a temporary reservation of a selected slot inside the platform.

### Fields
- `hold_id`
- `journey_id`
- `slot_id`
- `customer_id`
- `created_at_utc`
- `expires_at_utc`
- `status`
- `reason`
- `metadata`

### Status values
- `ACTIVE`
- `EXPIRED`
- `RELEASED`
- `CONSUMED`

### Important rule
Slot holds are **platform-owned**, not Google-owned and not LEKAB-owned.

---

## 6.6 AppointmentBooking

### Purpose
Represents the final appointment booking.

### Fields
- `booking_reference`
- `journey_id`
- `customer_id`
- `slot_id`
- `status`
- `provider`
- `provider_reference`
- `calendar_target`
- `crm_reference`
- `start_time`
- `end_time`
- `timezone`
- `created_at_utc`
- `updated_at_utc`
- `metadata`

### Status values
- `PENDING`
- `CONFIRMED`
- `RESCHEDULED`
- `CANCELLED`
- `FAILED`

---

## 6.7 ConversationTurn

### Purpose
Represents one inbound or outbound interaction step.

### Fields
- `turn_id`
- `journey_id`
- `direction`
- `channel`
- `message_type`
- `provider`
- `provider_reference`
- `raw_payload_reference`
- `normalized_payload`
- `timestamp_utc`

---

## 6.8 BookingResult

### Purpose
Represents the normalized result returned by a provider adapter after booking actions.

### Fields
- `booking_reference`
- `provider`
- `provider_reference`
- `status`
- `start_time`
- `end_time`
- `timezone`
- `calendar_target`
- `attendees`
- `metadata`

---

## 6.9 ProviderError

### Purpose
Normalized external/provider error shape.

### Fields
- `provider`
- `provider_operation`
- `error_code`
- `error_category`
- `message`
- `retryable`
- `raw_reference`

---

# 7. Journey State Model

The following journey states should be shared and consistent.

## States
- `NEW`
- `IDENTIFYING_CUSTOMER`
- `COLLECTING_PREFERENCES`
- `SEARCHING_SLOTS`
- `OFFERING_SLOTS`
- `WAITING_FOR_SELECTION`
- `HOLDING_SLOT`
- `WAITING_FOR_CONFIRMATION`
- `BOOKING_APPOINTMENT`
- `BOOKED`
- `REMINDER_PENDING`
- `RESCHEDULE_FLOW`
- `CANCELLATION_FLOW`
- `ESCALATED`
- `CLOSED`
- `FAILED`

## Rule
Adapters must not invent their own journey states.
Adapters may expose provider-local statuses, but those must map into shared journey-compatible states or normalized provider result statuses.

---

# 8. Shared Commands

Below is the first common command set.

---

## 8.1 SearchSlotsCommand

### Purpose
Request slot search from a scheduling provider.

### Payload fields
- `tenant_id`
- `journey_id`
- `customer_id`
- `service_type`
- `duration_minutes`
- `date_window_start`
- `date_window_end`
- `preferred_month`
- `preferred_weekdays`
- `preferred_daypart`
- `timezone`
- `resource_candidates`
- `location_type`
- `max_slots`

---

## 8.2 HoldSlotCommand

### Purpose
Create a platform-owned temporary hold.

### Payload fields
- `journey_id`
- `customer_id`
- `slot_id`
- `hold_duration_minutes`
- `reason`

---

## 8.3 ReleaseSlotHoldCommand

### Purpose
Release an active slot hold.

### Payload fields
- `journey_id`
- `hold_id`
- `reason`

---

## 8.4 CreateBookingCommand

### Purpose
Create the final appointment with a provider.

### Payload fields
- `tenant_id`
- `journey_id`
- `customer_id`
- `booking_reference`
- `slot_id`
- `calendar_target`
- `title`
- `description`
- `attendees`
- `timezone`
- `crm_reference`
- `metadata`

---

## 8.5 UpdateBookingCommand

### Purpose
Reschedule or modify an existing appointment.

### Payload fields
- `booking_reference`
- `provider_reference`
- `new_start`
- `new_end`
- `new_title`
- `new_description`
- `attendees`
- `reason`

---

## 8.6 CancelBookingCommand

### Purpose
Cancel an appointment.

### Payload fields
- `booking_reference`
- `provider_reference`
- `reason`
- `requested_by`

---

## 8.7 ResolveCustomerCommand

### Purpose
Resolve the customer from a phone, email, external reference, or context.

### Payload fields
- `tenant_id`
- `mobile_number`
- `email`
- `external_customer_id`
- `crm_reference`
- `channel`
- `locale`

---

## 8.8 UpsertCustomerCommand

### Purpose
Create or update a platform customer profile.

### Payload fields
- `customer_profile`

---

## 8.9 LaunchAppointmentWorkflowCommand

### Purpose
Trigger LEKAB workflow dispatch for appointment messaging.

### Payload fields
- `correlation_id`
- `booking_reference`
- `lekab_job_template_id`
- `job_name`
- `message_text`
- `recipient_phone_numbers`
- `saved_tag_filters`
- `groups`
- `custom_tag_filter`
- `exclude_numbers`
- `exclude_filter`
- `scheduled_start`
- `response_goal`
- `keep_existing_recipients`
- `metadata`

---

## 8.10 HandleProviderCallbackCommand

### Purpose
Handle an inbound provider callback such as LEKAB webhook callback.

### Payload fields
- `provider`
- `raw_payload`
- `headers`
- `received_at_utc`
- `remote_ip`

---

# 9. Shared Events

Below is the first common event set.

---

## 9.1 Journey lifecycle events
- `appointment.journey.created`
- `appointment.journey.state.changed`
- `appointment.journey.closed`
- `appointment.journey.failed`

---

## 9.2 Customer events
- `customer.lookup.requested`
- `customer.resolved`
- `customer.lookup.failed`
- `customer.created`
- `customer.updated`
- `customer.contactability.updated`
- `customer.consent.updated`

---

## 9.3 Slot events
- `appointment.search.requested`
- `calendar.slots.found`
- `calendar.slots.not_found`
- `appointment.slot.selected`
- `appointment.slot.hold.created`
- `appointment.slot.hold.expired`
- `appointment.slot.hold.released`

---

## 9.4 Booking events
- `appointment.booking.create.requested`
- `calendar.booking.created`
- `calendar.booking.updated`
- `calendar.booking.cancelled`
- `calendar.booking.failed`
- `appointment.booking.confirmed`
- `appointment.booking.rescheduled`
- `appointment.booking.cancelled`

---

## 9.5 Messaging / LEKAB events
- `lekab.auth.token.refreshed`
- `lekab.dispatch.jobs.listed`
- `lekab.dispatch.job.start.requested`
- `lekab.dispatch.job.started`
- `lekab.dispatch.job.start.failed`
- `lekab.callback.received`
- `lekab.callback.duplicate_ignored`
- `lekab.job.started`
- `lekab.job.assigned`
- `lekab.job.finished`

---

## 9.6 Reminder / escalation events
- `appointment.reminder.scheduled`
- `appointment.reminder.due`
- `appointment.escalation.requested`
- `appointment.escalated`

---

## 9.7 Audit events
- `appointment.audit.recorded`
- `appointment.policy.checked`

---

# 10. Error Contract

All modules should use a normalized internal error shape.

## 10.1 SharedError

### Fields
- `error_id`
- `error_type`
- `error_category`
- `message`
- `details`
- `retryable`
- `provider`
- `provider_operation`
- `trace_id`
- `correlation_id`
- `journey_id`
- `timestamp_utc`

## 10.2 Error categories
- `VALIDATION`
- `AUTH`
- `PERMISSION`
- `NOT_FOUND`
- `CONFLICT`
- `POLICY`
- `TIMEOUT`
- `UPSTREAM_4XX`
- `UPSTREAM_5XX`
- `NETWORK`
- `DUPLICATE`
- `MAPPING`
- `UNKNOWN`

## 10.3 Rule
Provider-specific raw errors may be logged or referenced, but platform flows should rely on the normalized error categories.

---

# 11. Idempotency Rules

Idempotency is mandatory.

## 11.1 Every command/event must carry:
- `idempotency_key`

## 11.2 Recommended generation
Use a stable key derived from:
- event/command type
- journey_id
- provider_reference if available
- logical action intent

## 11.3 Duplicate handling
If a duplicate command/event is detected:
- do not re-execute destructive actions
- emit a safe duplicate/ignored event if needed
- preserve audit trail

## 11.4 Critical areas
Idempotency is especially important for:
- LEKAB callback ingestion
- booking creation
- reschedule flows
- reminder scheduling
- customer upsert operations

---

# 12. Time and Timezone Rules

Time must be treated as a first-class concern.

## 12.1 UTC storage
All system timestamps must be stored and transported as UTC.

## 12.2 Explicit timezone for business time
Every appointment-related object must carry:
- local business timezone when relevant

## 12.3 No server-local assumptions
Never rely on implicit server local time.

## 12.4 DST awareness
All adapters and scheduling logic must be tested for daylight saving transitions.

## 12.5 Suggested fields
- `timestamp_utc`
- `start_time`
- `end_time`
- `timezone`

---

# 13. Consent and Policy Fields

Consent and policy checks must be visible in the contracts.

## Shared policy-related fields
- `consent_messaging`
- `consent_reminders`
- `quiet_hours_applicable`
- `policy_check_result`
- `handover_required`
- `reschedule_allowed`
- `cancellation_allowed`

## Rule
Do not bury critical policy outcomes only in logs.
Important policy decisions should be reflected in events and audit records.

---

# 14. Audit and Observability Fields

The following must be available across components where relevant:

- `trace_id`
- `correlation_id`
- `journey_id`
- `tenant_id`
- `source`
- `provider`
- `provider_reference`
- `idempotency_key`
- `policy_version`
- `raw_payload_reference`

These support:
- debugging
- audit
- support operations
- KPI generation

---

# 15. Adapter Mapping Rules

Each adapter must map from provider-native payloads to shared contracts.

## 15.1 LEKAB Adapter
Examples:
- `JOB_START` -> `lekab.job.started`
- `JOB_ASSIGN` -> `lekab.job.assigned`
- `JOB_FINISH` -> `lekab.job.finished`

## 15.2 Google Adapter
Examples:
- free/busy results -> `CandidateSlot[]`
- event creation result -> `BookingResult`

## 15.3 Microsoft Adapter
Examples:
- Graph/Dynamics availability -> `CandidateSlot[]`
- CRM contact/account resolution -> `CustomerProfile`
- appointment writeback -> normalized booking/writeback event

## Rule
Adapters must not leak provider-native transport objects into shared service APIs unless explicitly marked as raw/provider-specific metadata.

---

# 16. Serialization Rules

## 16.1 JSON-first transport
Commands and events should be serializable to JSON cleanly.

## 16.2 Recommended naming
Use snake_case in Python internals and JSON field names unless a bus standard requires otherwise.

## 16.3 Optional fields
Optional fields may be omitted or set to null, but required fields must always be present.

## 16.4 Unknown fields
Consumers should ignore unknown additive fields in backward-compatible upgrades where possible.

---

# 17. Compatibility Rules

## 17.1 Backward compatibility
Additive fields are preferred over breaking renames.

## 17.2 Breaking change rule
Any removal or semantic redefinition of a shared field requires a major version bump.

## 17.3 Provider extension rule
Provider-specific extension metadata should live under `metadata` or provider extension objects, not in the shared core field set unless it becomes cross-platform relevant.

---

# 18. Recommended Package Structure

Suggested shared code placement:

```text
apps/shared/v1_0_0/appointment_agent_shared/
  __init__.py
  contracts.py
  models.py
  events.py
  commands.py
  errors.py
  validators.py
  serializers.py
  ids.py
  enums.py
```

Recommended logical grouping:
- `commands.py`
- `events.py`
- `models.py`
- `errors.py`
- `validators.py`

---

# 19. Acceptance Rules

This shared contract layer is acceptable only if:

1. All adapters can map into it without leaking core provider-specific shapes.
2. The Appointment Orchestrator can consume it without special-case provider logic.
3. Correlation, tracing, idempotency, and tenant separation are present everywhere.
4. Slot holds are modeled as platform-owned state.
5. Timezone and UTC rules are explicit.
6. Consent and policy outcomes can be represented cleanly.
7. Changes can be versioned safely.

---

# 20. Open Questions

1. Which exact enum set should be frozen in code for v1.0.0?
2. Should `metadata` be unrestricted, or lightly typed?
3. Do we want a single `ProviderReference` object type for all adapters?
4. Which field names are mandatory on the event bus transport layer vs internal Python DTOs?
5. Should `raw_payload_reference` point to object storage, DB, or log correlation only?
6. How much of customer consent history belongs in shared contracts vs a specialized consent module?
7. Do we want a dedicated `AppointmentPolicyResult` object in v1.0.1?

---

# Closing Recommendation

This shared contract file should now be treated as the **technical backbone** of the product.

Recommended next step after approving this document:

1. implement `contracts.py`, `models.py`, `events.py`, `commands.py`, and `errors.py` in the shared package
2. refactor LEKAB Adapter to conform to these contracts
3. refactor Appointment Orchestrator to consume these contracts
4. then wire Google Adapter and later Microsoft Adapter to the same shared model
