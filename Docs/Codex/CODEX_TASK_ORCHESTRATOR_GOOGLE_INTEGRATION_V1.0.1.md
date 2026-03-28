# CODEX_TASK_ORCHESTRATOR_GOOGLE_INTEGRATION_V1.0.1.md

## Title
Integrate Appointment Orchestrator v1.0.1 with Google Adapter v1.0.1

## Objective
Create the first clean end-to-end internal product chain between:
- LEKAB messaging/workflow layer
- Appointment Orchestrator v1.0.1
- Google Adapter v1.0.1

The goal is to wire the Orchestrator onto the Google Adapter using the shared domain contracts, so that the platform can execute real internal booking flows consistently before deeper live-provider hardening.

This is an internal integration release step.
It is not yet the final full Google production hardening phase.

## Why this is the next step
The repo now already has:
- shared domain backbone modules
- LEKAB adapter prototype path
- Appointment Orchestrator v1.0.1 with:
  - reschedule flow
  - no-slot strategy
  - escalation path
  - audit persistence
  - CRM-preparation events
- Google Adapter v1.0.1 with:
  - normalized search_slots
  - normalized create_booking
  - normalized update_booking
  - normalized cancel_booking
  - provider_reference handling
  - normalized BookingResult

That means the architecture is ready for the next logical step:
connect the Orchestrator to the Google Adapter as a real internal provider path.

## Guiding Rule
Do not introduce shortcut logic inside the Orchestrator.

The Orchestrator must:
- consume shared commands/events/models
- delegate scheduling/provider actions to the Google Adapter
- remain provider-neutral at the business workflow level
- treat Google as a provider implementation, not as workflow logic

## Scope

### In Scope
1. Connect Appointment Orchestrator v1.0.1 to Google Adapter v1.0.1
2. Replace or isolate internal/mock booking behavior where the Google Adapter should now be called
3. Implement end-to-end paths for:
   - search slots
   - booking create
   - booking update / reschedule
   - booking cancel
4. Normalize returned booking/provider data into journey state
5. Preserve audit events and CRM preparation events
6. Add integration-oriented tests
7. Update docs and release notes

### Out of Scope
1. Full live Google OAuth hardening
2. Real Google People integration
3. Real Microsoft path changes
4. Full LEKAB live integration hardening
5. UI / frontend work
6. Production deployment automation

## Release Discipline
Do not collapse this work into older versions unnecessarily.

Target versions:
- Appointment Orchestrator: v1_0_1
- Google Adapter: v1_0_1

Keep:
- v1.0.0 stable
- v1.0.1 as the active internal integration line

If small bugfixes are needed in older files, keep them clearly minimal and justified.

## Architecture Target
```text
LEKAB Adapter / Messaging Layer
          |
          v
Appointment Orchestrator v1.0.1
          |
          v
Google Adapter v1.0.1
          |
          v
Normalized Booking Results / Provider References
          |
          +--> Journey State
          +--> Audit
          +--> CRM Write-back Preparation Events
```

Important rule:
The Orchestrator must not depend on raw Google-native payloads.
Only normalized return objects and shared-domain contracts may cross the boundary.

## Priority 1 – Wire search_slots Through the Google Adapter

### Goal
The Orchestrator must use Google Adapter v1.0.1 for slot search instead of relying on internal stand-in logic.

### Required behavior
When the journey enters slot search:
1. the Orchestrator constructs a normalized SearchSlotsCommand
2. passes it to the Google Adapter
3. receives normalized CandidateSlot[]
4. updates journey state accordingly
5. writes audit records
6. continues into slot offering / no-slot strategy

### Required follow-up behavior
If slots are returned:
- move to offering/select path

If no slots are returned:
- trigger the already-implemented no-slot strategy in Orchestrator v1.0.1

### Tests required
- search slots happy path
- search slots returns empty list -> no-slot flow
- slot search failure -> error handling / escalation path if configured

## Priority 2 – Wire create_booking Through the Google Adapter

### Goal
The Orchestrator must create final bookings through the Google Adapter.

### Required behavior
When a slot has been chosen and confirmation is complete:
1. build CreateBookingCommand
2. send to Google Adapter v1.0.1
3. receive normalized BookingResult
4. persist:
   - booking_reference
   - provider_reference
   - booking status
   - timing
5. transition journey state appropriately
6. emit CRM-preparation event(s)
7. create audit records

### Required field handling
The Orchestrator must clearly distinguish:
- booking_reference = platform-owned reference
- provider_reference = Google-side external reference

### Tests required
- confirmed booking path through Google Adapter
- booking result persisted to journey/booking state
- CRM create/update request event emitted
- audit record written

## Priority 3 – Wire Reschedule / update_booking

### Goal
The already-implemented reschedule flow in the Orchestrator must call Google Adapter v1.0.1 for the provider-side update.

### Required behavior
When reschedule succeeds internally:
1. build UpdateBookingCommand
2. call Google Adapter update_booking
3. receive normalized updated BookingResult
4. update local journey/booking state
5. emit:
   - booking update outcome
   - CRM update request
   - audit records

### Required failure behavior
If the provider reference is missing or stale:
- fail predictably
- preserve audit
- apply escalation or failure handling according to current policy

### Tests required
- reschedule happy path
- reschedule with missing provider reference
- reschedule failure -> audit + escalation/failure behavior
- CRM update request emitted

## Priority 4 – Wire Cancellation / cancel_booking

### Goal
The Orchestrator cancellation path must use Google Adapter v1.0.1 as the provider-side cancellation handler.

### Required behavior
When cancellation is allowed:
1. build CancelBookingCommand
2. call Google Adapter cancel_booking
3. update journey state
4. emit CRM cancellation write-back event
5. write audit record

### Required failure handling
If provider reference is missing:
- fail safely
- do not silently mark fully cancelled without evidence
- preserve error/audit path

### Tests required
- cancellation happy path
- cancellation with missing provider reference
- duplicate cancellation safe handling
- CRM cancel request emitted

## Priority 5 – Orchestrator State / Booking Persistence Alignment

### Goal
The Orchestrator must persist the provider-aware booking lifecycle correctly.

### Required persistence updates
Ensure state/repository layer can store:
- booking_reference
- provider_reference
- provider
- booking status
- start/end time
- calendar target
- update/cancel outcomes

### Rule
The journey state and the booking state must remain aligned, but do not overload the journey object with all provider details.
Use dedicated booking persistence if already available or extend it cleanly.

## Priority 6 – Audit Preservation

### Goal
The new adapter integration must not weaken the audit path.

### Required audit coverage
At minimum, audit records must exist for:
- slot search request/outcome
- no-slot decision
- booking create request/outcome
- reschedule request/outcome
- cancellation request/outcome
- escalation triggered by adapter/provider errors

### Required fields
Audit records should continue to include:
- journey_id
- correlation_id
- trace_id
- decision/event type
- reason code
- human-readable explanation
- structured payload or payload reference
- timestamp

## Priority 7 – CRM Write-back Preparation Preservation

### Goal
The Google integration must feed the already-created CRM preparation event model.

### Required events/commands
Ensure the Orchestrator still emits normalized outputs such as:
- crm.booking.create.requested
- crm.booking.update.requested
- crm.booking.cancel.requested
- crm.activity.append.requested

### Required rule
Do not move CRM logic into the Google Adapter.
The Orchestrator remains responsible for normalized cross-component workflow emission.

## Priority 8 – Shared Domain Contract Alignment

### Goal
The integration must use the new shared modules more directly.

### Required shared components
Use, where relevant:
- SearchSlotsCommand
- CreateBookingCommand
- UpdateBookingCommand
- CancelBookingCommand
- CandidateSlot
- BookingResult
- AppointmentBooking
- ProviderReference
- SharedError / ProviderError
- shared enums

### Required rule
Do not introduce local Google↔Orchestrator bridge DTOs if shared contracts already exist.

### Compatibility rule
If contracts.py is still used as compatibility facade, avoid adding new logic there.
Use the new shared modules directly where possible.

## Priority 9 – Error Handling Between Orchestrator and Google Adapter

### Goal
Provider failures must translate into stable orchestration behavior.

### Required behavior
The Orchestrator must distinguish between:
- validation failure
- no-slot result
- missing provider reference
- conflict/stale state
- retryable provider failure
- terminal provider failure

### Recommended mapping
- retryable provider errors -> retry path or controlled failure
- non-retryable provider errors -> audit + escalation/failure path
- missing provider reference during update/cancel -> explicit stateful failure path

### Required tests
- provider error during create
- provider error during update
- provider error during cancel
- escalation path on provider failure if configured

## Priority 10 – Integration Tests

### Goal
Prove the internal product chain behaves consistently.

### Add integration-style tests for:
1. start -> search_slots -> offer -> select -> confirm -> create_booking
2. BOOKED -> RESCHEDULE_FLOW -> update_booking
3. BOOKED -> CANCELLATION_FLOW -> cancel_booking
4. search_slots -> no slots -> no-slot strategy
5. provider failure during booking update/cancel
6. provider reference persistence and reuse

### Test structure
Likely extend:
- tests/appointment_orchestrator/v1_0_1/
- optionally add cross-module integration tests if repo style supports it

Keep:
- ./scripts/run_tests.sh green
- separated version-aware test artifacts and summaries

## Priority 11 – Documentation

### Required docs
Update or add:
- docs/admin/appointment_orchestrator_v1_0_1.md
- docs/admin/google_adapter_v1_0_1.md
- docs/user/user_guide_v1_0_1.md
- docs/demo/demo_guide_v1_0_1.md
- docs/releases/release_notes_v1_0_1_en.md
- docs/releases/release_notes_v1_0_1_de.md

### Documentation focus
Document:
- Orchestrator now uses Google Adapter v1.0.1 for provider actions
- provider reference semantics
- end-to-end internal lifecycle
- current limitations before full live Google hardening

## Likely Files to Touch
Adjust to repo reality, but likely affected areas include:
- apps/appointment_orchestrator/v1_0_1/appointment_orchestrator/service.py
- apps/appointment_orchestrator/v1_0_1/appointment_orchestrator/app.py
- apps/google_adapter/v1_0_1/google_adapter/service.py
- apps/shared/v1_0_0/appointment_agent_shared/models.py
- apps/shared/v1_0_0/appointment_agent_shared/repositories.py
- tests/appointment_orchestrator/v1_0_1/
- docs/release files

Only change v1_0_0 if a minimal compatibility bugfix is truly necessary.

## Acceptance Criteria
This work is complete only if:
1. Appointment Orchestrator v1.0.1 delegates slot search to Google Adapter v1.0.1.
2. Appointment Orchestrator v1.0.1 delegates booking creation to Google Adapter v1.0.1.
3. Reschedule/update path uses Google Adapter v1.0.1.
4. Cancel path uses Google Adapter v1.0.1.
5. booking_reference and provider_reference are handled consistently.
6. Audit records still exist for important decisions and outcomes.
7. CRM-preparation events still fire correctly.
8. Shared contracts are used more directly.
9. Tests pass.
10. Docs are updated.
11. Release separation remains clean.

## Definition of Done
Done means:
- the internal LEKAB -> Orchestrator -> Google chain is functionally connected
- richer Orchestrator flows can now execute against a real internal provider adapter layer
- the platform is ready for the next hardening step without relying on incomplete workflow glue

## Recommended Next Step After Completion
After this integration step, the next strongest option will likely be either:
1. harden LEKAB Adapter toward real upstream integration
or
2. harden Google Adapter toward real Google Calendar API interaction

The better choice depends on whether messaging realism or scheduling realism is the next product priority.
