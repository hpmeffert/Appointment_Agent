# CODEX_TASK_GOOGLE_ADAPTER_NEXT_EXPANSION_V1.0.1.md

## Title
Expand the Google Adapter to v1.0.1 as the next provider-ready scheduling layer

## Objective
Create the next clean release step for the Google Adapter as **v1.0.1**, following the same release discipline already used for the Appointment Orchestrator.

The goal is **not yet** full live Google API hardening in every detail.  
The goal is to make the Google Adapter **functionally complete enough** to support the Appointment Orchestrator and the shared domain contracts in a stable, provider-neutral way.

This means the Google Adapter should now support a fuller normalized scheduling lifecycle:

- `search_slots`
- `create_booking`
- `update_booking`
- `cancel_booking`
- `provider_reference` handling
- normalized `BookingResult`
- clean alignment with shared commands, events, and models

Only after this functional provider model is stable should the implementation be hardened against real Google Calendar APIs end-to-end.

---

## Current Assessment
The repo now has:
- versioned module structure
- shared domain modules in place
- LEKAB prototype path
- Appointment Orchestrator v1.0.1 with:
  - reschedule flow
  - no-slot strategy
  - escalation / handover path
  - audit persistence
  - CRM-preparation events
- green tests and release notes discipline

That means the next natural step is the **Google scheduling side**, but still in a controlled release slice.

---

## Guiding Rule
Before going too deep into real external API behavior, the adapter must first become internally correct and contract-safe.

That means:

1. normalized provider-neutral interface first
2. correct booking lifecycle semantics
3. proper provider reference handling
4. correct return contracts for the Orchestrator
5. release separation from v1.0.0
6. no leakage of raw Google payloads into shared business logic

---

## Scope

### In Scope
1. Create or expand **Google Adapter v1.0.1**
2. Implement a fuller booking lifecycle:
   - slot search
   - booking creation
   - booking update
   - booking cancel
3. Normalize provider references and booking results
4. Tighten alignment with shared domain contracts
5. Add tests for lifecycle and error cases
6. Add v1.0.1 docs and release notes

### Out of Scope
1. Full production Google OAuth hardening
2. Full Google Workspace admin provisioning
3. Full Google People API live integration unless already trivially available
4. Full analytics UI
5. Complex workforce optimization
6. Microsoft path changes

---

## Versioning Rule
Do **not** fold new feature logic into Google Adapter v1.0.0 unless it is a bugfix.

Instead:
- create or continue a separate `v1_0_1` Google Adapter path
- preserve v1.0.0 stability
- keep tests and docs versioned accordingly

Recommended structure:
```text
apps/google_adapter/v1_0_1/google_adapter/
tests/google_adapter/v1_0_1/
docs/admin/google_adapter_v1_0_1.md
docs/demo/demo_guide_v1_0_1.md
docs/releases/release_notes_v1_0_1_en.md
docs/releases/release_notes_v1_0_1_de.md
docs/user/user_guide_v1_0_1.md
```

If some shared docs are reused, make the version impact explicit.

---

## Priority 1 – Functional Booking Lifecycle

## Goal
The Google Adapter must support the complete basic provider-side lifecycle expected by the Orchestrator.

### Required operations
- `search_slots`
- `create_booking`
- `update_booking`
- `cancel_booking`
- optionally `get_booking` if useful for consistency

### Required behavior
The adapter must:
- accept normalized shared commands / DTOs
- return normalized shared models / results
- preserve provider-specific references internally or in metadata
- avoid leaking Google-native shapes as business contracts

---

## Priority 2 – `search_slots` Normalization

## Goal
Make slot search a clean normalized operation.

### Required behavior
`search_slots` should:
1. receive a normalized scheduling request
2. process candidate calendars/resources
3. calculate valid slots from availability windows
4. apply business filters provided by upstream logic or adapter rules
5. return normalized `CandidateSlot[]`

### Required fields on returned slots
At minimum:
- `slot_id`
- `start_time`
- `end_time`
- `timezone`
- `resource_id`
- `score`
- `provider`
- `provider_reference` when meaningful
- `metadata`

### Important rule
The adapter may use provider-specific internal helpers, but the public return contract must stay shared and stable.

---

## Priority 3 – `create_booking`

## Goal
Create a normalized booking result from a selected slot.

### Required behavior
When the Orchestrator confirms a booking request, the adapter must:
1. validate incoming booking command
2. translate it to provider-specific operation
3. return a normalized `BookingResult`
4. preserve the Google-side event identifier as a provider reference
5. emit or surface the right internal success/failure semantics

### Required result fields
At minimum:
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

### Important rule
`provider_reference` must be treated as a stable external mapping, not as the platform’s main booking identifier.

---

## Priority 4 – `update_booking`

## Goal
Support rescheduling and update flows from the Orchestrator.

### Required behavior
The adapter must support:
- changing date/time
- changing title/description if required
- updating attendee-related data if applicable
- returning normalized updated booking results
- handling missing or stale provider references safely

### Required command support
Align with shared:
- `UpdateBookingCommand`

### Required tests
- update existing booking
- update with missing provider reference
- update with invalid payload
- update returning normalized result
- update failure path

---

## Priority 5 – `cancel_booking`

## Goal
Support cancellation as a first-class provider action.

### Required behavior
The adapter must:
- accept normalized cancel requests
- map them to provider cancellation behavior
- return or emit normalized cancellation outcome
- preserve booking/provider references for audit and CRM write-back

### Required tests
- happy path cancellation
- cancellation with missing provider reference
- duplicate cancellation behavior
- cancellation failure path

---

## Priority 6 – Provider Reference Handling

## Goal
Make provider references explicit and consistent.

### Why
The platform now has:
- `booking_reference` as platform-owned reference
- `provider_reference` as external provider-specific reference

The Google Adapter must respect this distinction everywhere.

### Required rules
1. Do not use raw Google event IDs as primary platform booking IDs
2. Always return/store provider references in normalized form
3. Keep provider reference available for:
   - update
   - cancel
   - audit
   - CRM write-back support

### Suggested implementation
Use:
- `ProviderReference`
- `BookingResult`
- `AppointmentBooking`
from the shared domain layer wherever possible

---

## Priority 7 – Shared Domain Contract Alignment

## Goal
Bring the Google Adapter onto the new shared backbone.

The adapter must align with:
- `commands.py`
- `events.py`
- `models.py`
- `errors.py`
- `enums.py`
- `validators.py`

### Required checks
Make sure the Google Adapter:
- consumes shared booking/search commands
- returns shared models
- uses shared error categories or normalized provider errors
- preserves `correlation_id`, `trace_id`, `journey_id` where relevant
- stays compatible with Orchestrator expectations

### Important rule
Do not build new Google-local DTO shapes if shared equivalents already exist.

---

## Priority 8 – Error Handling

## Goal
Make Google Adapter failures predictable and safe.

### Required categories
Map failures into normalized categories such as:
- `VALIDATION`
- `NOT_FOUND`
- `CONFLICT`
- `TIMEOUT`
- `UPSTREAM_4XX`
- `UPSTREAM_5XX`
- `NETWORK`
- `MAPPING`
- `UNKNOWN`

### Required behavior
- no silent failures
- no raw provider exception leakage as public contract
- preserve provider-specific details only in safe structured metadata or logs
- support retry logic only where safe and clearly retryable

---

## Priority 9 – Tests

## Required new tests
Create or extend tests in:
```text
tests/google_adapter/v1_0_1/
```

### Minimum test coverage
1. slot search returns normalized slots
2. booking creation returns normalized booking result
3. booking update returns normalized booking result
4. booking cancel works and preserves references
5. provider reference is handled consistently
6. invalid payloads fail predictably
7. stale/missing references fail safely
8. compatibility with shared contracts is validated
9. no raw Google payload leakage into normalized return objects

### Keep green
- `./scripts/run_tests.sh` must remain green
- keep separated result artifacts / summaries consistent with repo practice

---

## Priority 10 – Documentation

## Required docs
Add or update:
- `docs/admin/google_adapter_v1_0_1.md`
- `docs/user/user_guide_v1_0_1.md`
- `docs/demo/demo_guide_v1_0_1.md`
- `docs/releases/release_notes_v1_0_1_en.md`
- `docs/releases/release_notes_v1_0_1_de.md`

### Documentation topics
Include:
- what changed from v1.0.0 to v1.0.1
- supported operations
- normalized contracts used
- provider reference handling
- current limitations
- next step toward real API hardening

---

## Recommended Implementation Areas
Adjust to repo reality, but likely files include:
- `apps/google_adapter/v1_0_1/google_adapter/service.py`
- `apps/google_adapter/v1_0_1/google_adapter/app.py`
- possibly shared utility or adapter-local mapping helpers
- `tests/google_adapter/v1_0_1/...`

Add files only where it improves clarity:
- `mappers.py`
- `provider_models.py`
- `booking_mapper.py`
- `availability_engine.py`

Do not introduce unnecessary complexity.

---

## Acceptance Criteria
This work is complete only if:

1. Google Adapter v1.0.1 exists as a distinct release step.
2. It supports normalized:
   - slot search
   - booking create
   - booking update
   - booking cancel
3. Provider references are handled explicitly and consistently.
4. Shared domain contracts are used more directly.
5. Error handling is normalized.
6. Tests pass.
7. Docs are updated.
8. No breaking repo-structure changes are introduced.

---

## Definition of Done
Done means:
- the Google Adapter is no longer just an early prototype
- it can support the richer Orchestrator flows safely
- the platform remains provider-neutral at the internal contract level
- the adapter is ready for a later real Google API hardening step

---

## Recommended Next Step After Completion
After this workorder, the next likely step should be one of:

1. harden the Google Adapter against real Google Calendar API calls  
or  
2. refactor the LEKAB Adapter more directly onto the shared domain modules

The preferred order depends on whether the next priority is scheduling realism or messaging/workflow realism.
