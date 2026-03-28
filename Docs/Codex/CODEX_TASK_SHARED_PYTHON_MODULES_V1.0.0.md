# CODEX_TASK_SHARED_PYTHON_MODULES_V1.0.0

## Title
Implement the concrete shared Python modules for Appointment Agent Shared Domain Contracts v1.0.0

## Objective
Create the first real shared Python backbone for the platform under:

`apps/shared/v1_0_0/appointment_agent_shared/`

Modules to implement and stabilize:
- `commands.py`
- `events.py`
- `models.py`
- `errors.py`
- `validators.py`
- `enums.py`
- `ids.py`

## Why this comes next
This is the technical contract layer that every core module must align to:
- LEKAB Adapter
- Appointment Orchestrator
- Google Adapter
- later Microsoft Adapter

Without this shared layer, adapter logic will drift and event/state semantics will become inconsistent.

## Scope
### In scope
- implement concrete DTOs and envelopes
- freeze enum set for v1.0.0
- add id generation helpers
- add validation helpers
- align package exports in `__init__.py`
- add unit tests
- document usage examples

### Out of scope
- provider-specific API logic
- persistence implementation details
- frontend/UI work
- advanced policy engine

## Required Files
- `apps/shared/v1_0_0/appointment_agent_shared/__init__.py`
- `apps/shared/v1_0_0/appointment_agent_shared/commands.py`
- `apps/shared/v1_0_0/appointment_agent_shared/events.py`
- `apps/shared/v1_0_0/appointment_agent_shared/models.py`
- `apps/shared/v1_0_0/appointment_agent_shared/errors.py`
- `apps/shared/v1_0_0/appointment_agent_shared/validators.py`
- `apps/shared/v1_0_0/appointment_agent_shared/enums.py`
- `apps/shared/v1_0_0/appointment_agent_shared/ids.py`

## Core Requirements
1. EventEnvelope and CommandEnvelope must carry:
   - correlation_id
   - causation_id
   - trace_id
   - tenant_id
   - journey_id
   - idempotency_key
   - payload_version

2. Shared models must include at least:
   - AppointmentJourney
   - CustomerProfile
   - AppointmentPreference
   - CandidateSlot
   - SlotHold
   - AppointmentBooking
   - ConversationTurn
   - BookingResult
   - ProviderReference

3. Shared commands must include at least:
   - SearchSlotsCommand
   - HoldSlotCommand
   - ReleaseSlotHoldCommand
   - CreateBookingCommand
   - UpdateBookingCommand
   - CancelBookingCommand
   - ResolveCustomerCommand
   - UpsertCustomerCommand
   - LaunchAppointmentWorkflowCommand
   - HandleProviderCallbackCommand

4. Shared errors must include:
   - SharedError
   - ProviderError
   - ErrorCategory enum usage

## Test Requirements
Add unit tests for:
- envelope serialization
- enum stability
- ISO datetime validation
- empty-field validation
- model instantiation
- command instantiation
- id helper behavior

## Acceptance Criteria
Done only if:
- modules are importable cleanly
- contracts serialize to JSON safely
- enums are stable and documented
- tests pass
- docs/reference examples exist
- no provider-specific leakage enters shared models

## Deliverable
A production-usable shared package foundation that the LEKAB Adapter and Appointment Orchestrator can immediately refactor onto.
