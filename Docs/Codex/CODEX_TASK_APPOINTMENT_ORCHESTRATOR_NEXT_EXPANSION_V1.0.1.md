# CODEX_TASK_APPOINTMENT_ORCHESTRATOR_NEXT_EXPANSION_V1.0.1.md

## Title
Expand the Appointment Orchestrator v1.0.1 toward the product specification

## Objective
Continue the Appointment Orchestrator implementation in the current repo, but **do not** move to real Google API integration yet.

The next priority is to **close the functional workflow gaps inside the Orchestrator itself** so that the internal product logic is stable before deeper provider integration starts.

This workorder extends the current v1.0.0 prototype toward a more complete orchestration core.

---

## Current Assessment
The current Orchestrator has already moved beyond a thin proxy and now includes:

- persisted journey state
- conversation turns
- early policy checks
- first working flows for:
  - start
  - select
  - confirm
  - remind
  - cancel
- green test execution
- updated user/release documentation

That is a good base.

However, the product specification is still not fully implemented.  
The next step is to complete the **core appointment workflow logic** before hardening external provider integrations.

---

## Guiding Rule
Before connecting more real provider APIs, the platform must first be internally correct.

That means:

1. the Orchestrator must know how to behave when no slots exist
2. it must support rescheduling as a first-class flow
3. it must explain and persist important decisions through audit records
4. it must emit clean write-back commands/events for later CRM integration
5. it must align tightly with the shared domain contracts

---

## Scope

### In Scope
1. Implement **Reschedule Flow**
2. Implement **No-slot Strategy**
3. Implement **Escalation / Human Handover flow**
4. Implement **Audit Layer**
5. Implement **CRM Write-back preparation events/commands**
6. Tighten Orchestrator conformance to shared domain contracts
7. Add tests and documentation for the new flows

### Out of Scope
1. Real Google Calendar API integration
2. Real Microsoft Graph/Dynamics integration
3. Full analytics UI
4. Full external CRM adapter implementation
5. Advanced NLP expansion
6. Workforce routing optimization

---

## Implementation Priorities

# Priority 1 – Reschedule Flow

## Goal
Make rescheduling a real journey path, not an afterthought.

## Required behavior
The Orchestrator must support:

1. receiving reschedule intent
2. loading the current booking
3. checking whether rescheduling is allowed by policy
4. initiating a new slot search
5. offering replacement slots
6. handling customer choice
7. confirming the new slot if required
8. generating a booking update request
9. updating state and audit trail
10. transitioning the journey correctly

## Required states / transitions
At minimum support transitions like:

- `BOOKED` -> `RESCHEDULE_FLOW`
- `RESCHEDULE_FLOW` -> `SEARCHING_SLOTS`
- `SEARCHING_SLOTS` -> `OFFERING_SLOTS`
- `WAITING_FOR_SELECTION` -> `WAITING_FOR_CONFIRMATION`
- `WAITING_FOR_CONFIRMATION` -> `BOOKING_APPOINTMENT`
- `BOOKING_APPOINTMENT` -> `BOOKED`
- fallback to `ESCALATED` or `FAILED` where needed

## Required internal events / commands
Examples:
- `appointment.reschedule.requested`
- `appointment.reschedule.allowed`
- `appointment.reschedule.rejected`
- `appointment.booking.update.requested`
- `appointment.booking.rescheduled`

## Tests required
- happy path reschedule
- reschedule rejected by policy
- reschedule with no replacement slots
- reschedule with expired hold / stale slot
- reschedule with escalation fallback

---

# Priority 2 – No-slot Strategy

## Goal
The Orchestrator must behave intelligently when no valid slots are found.

## Required behavior
When `calendar.slots.not_found` or equivalent happens, the Orchestrator must not simply fail.

It must support configurable strategies such as:
- widen search window
- offer next 7–10 days
- offer next month
- request customer preference refinement
- escalate to human/manual scheduling
- offer callback fallback if configured

## Required decision model
Create an explicit no-slot decision path.

Suggested next-step actions:
- `RETRY_WITH_BROADER_WINDOW`
- `ASK_FOR_MONTH`
- `ASK_FOR_DAYPART`
- `ESCALATE_TO_HUMAN`
- `OFFER_CALLBACK`
- `CLOSE_WITH_NO_BOOKING`

## Suggested new states or state usage
You may:
- reuse `COLLECTING_PREFERENCES`
- reuse `ESCALATED`
- reuse `FAILED`
- or introduce a bounded internal no-slot decision stage if it stays clean and backward-safe

## Required events
Examples:
- `appointment.no_slots.detected`
- `appointment.no_slots.retry_requested`
- `appointment.no_slots.escalation_requested`
- `appointment.callback.offer.requested`

## Tests required
- no-slot → broader search
- no-slot → next month question
- no-slot → escalation
- no-slot → callback fallback
- no-slot with policy block

---

# Priority 3 – Escalation / Human Handover

## Goal
Make human takeover a real controlled flow.

## Required triggers
Escalation should be possible when:
- no slots are available
- policy blocks automation
- customer explicitly requests help
- repeated clarification fails
- provider errors break user experience
- customer sentiment / message intent indicates frustration (simple placeholder logic is fine for now)

## Required behavior
When escalation happens:
- state must move to `ESCALATED`
- escalation reason must be persisted
- audit record must be created
- follow-up command/event must be emitted for later handover integration

## Required events
Examples:
- `appointment.escalation.requested`
- `appointment.escalated`
- `appointment.handover.target.pending`

## Tests required
- escalation by explicit help request
- escalation by no-slot condition
- escalation by repeated invalid input
- escalation audit entry created

---

# Priority 4 – Audit Layer

## Goal
Make important orchestration decisions visible and persistent.

## Why
The platform must later answer questions like:
- Why was this slot offered?
- Why was automation blocked?
- Why was the customer escalated?
- Why was a reminder sent?
- Why was rescheduling denied?

## Required audit record types
At minimum record:
- journey state transitions
- policy check outcomes
- slot-offer decisions
- escalation reasons
- reminder decisions
- reschedule decisions
- cancellation decisions
- booking request generation

## Required fields
Each audit record should include:
- audit_id
- tenant_id
- journey_id
- correlation_id
- trace_id
- event_type or decision_type
- reason_code
- human_readable_message
- payload_reference or structured payload
- created_at_utc

## Technical rule
Do not hide important decisions only in logs.
Persist them through a dedicated audit-oriented repository or model.

## Tests required
- state transition audit
- escalation audit
- no-slot audit
- reschedule audit
- reminder audit

---

# Priority 5 – CRM Write-back Preparation

## Goal
Prepare the Orchestrator for later CRM integration without implementing the actual CRM adapter yet.

## Required behavior
The Orchestrator must emit clear internal commands/events that later adapters can consume.

## Required command/event set
At minimum introduce or formalize:
- `crm.booking.create.requested`
- `crm.booking.update.requested`
- `crm.booking.cancel.requested`
- `crm.activity.append.requested`

## Examples of when to emit them
- booking confirmed
- booking rescheduled
- booking cancelled
- escalation created
- reminder acknowledged
- no-slot fallback case recorded

## Rule
No direct CRM provider logic should be embedded in the Orchestrator.
Only emit normalized contracts.

## Tests required
- booking confirmation emits CRM create/update request
- cancellation emits CRM cancel request
- escalation emits CRM activity append request

---

# Priority 6 – Shared Domain Contract Alignment

## Goal
Bring the Orchestrator closer to the shared contract backbone.

The implementation must align with:

- `APPOINTMENT_AGENT_SHARED_DOMAIN_CONTRACTS_V1.0.0`
- shared envelope concepts
- shared journey states
- shared slot hold object
- shared booking result semantics
- shared error categories

## Required checks
Review and align:
- journey state names
- slot hold representation
- event naming
- command naming
- correlation_id usage
- trace_id usage
- idempotency_key usage
- provider reference handling
- error normalization

## Rule
Do not invent local-only meanings if a shared contract already exists.

## Tests required
- event/command shape compatibility tests where possible
- state consistency checks
- idempotency behavior for repeated inputs where relevant

---

## Persistence Requirements
Extend the persistence/repository layer as needed to support:
- journey state transitions
- conversation turns
- slot holds
- audit entries
- escalation markers
- booking update intents

Keep the prototype database approach compatible with the current local prototype setup.

---

## Recommended New or Expanded Files
Adjust according to repo reality, but likely affected areas include:

- `apps/appointment_orchestrator/v1_0_0/appointment_orchestrator/service.py`
- `apps/appointment_orchestrator/v1_0_0/appointment_orchestrator/app.py`
- `apps/shared/v1_0_0/appointment_agent_shared/contracts.py`
- `apps/shared/v1_0_0/appointment_agent_shared/models.py`
- `apps/shared/v1_0_0/appointment_agent_shared/repositories.py`
- `apps/shared/v1_0_0/appointment_agent_shared/config.py`
- `tests/appointment_orchestrator/v1_0_0/test_orchestrator.py`

Add new files if needed for audit or policy separation, for example:
- `audit.py`
- `policy_engine.py`
- `state_machine.py`

Only do this if it improves clarity.

---

## Test Requirements

### Unit / flow tests
Add or extend tests for:
- reschedule happy path
- reschedule policy rejection
- no-slot retry path
- no-slot escalation path
- callback/manual scheduling fallback
- escalation by explicit help request
- audit record creation
- CRM write-back event emission
- repeated input / idempotent handling where relevant

### Full test run
- keep `./scripts/run_tests.sh` green
- maintain separated result artifacts and protocol paths
- update structured outputs if test summaries are part of the repo workflow

---

## Documentation Requirements
Update:
- `docs/user/user_guide_v1_0_0.md`
- `docs/releases/release_notes_v1_0_0_en.md`
- `docs/releases/release_notes_v1_0_0_de.md`

Also add brief developer-facing notes if needed, especially if:
- audit concepts
- escalation concepts
- reschedule logic
- CRM write-back events
become central in the code.

---

## Acceptance Criteria
This work is complete only if:

1. Reschedule is implemented as a true orchestration flow.
2. No-slot handling behaves intentionally and does not just fail.
3. Escalation is modeled as a real stateful path.
4. Important decisions are persisted through an audit mechanism.
5. CRM-oriented write-back events/commands are emitted in normalized form.
6. Orchestrator state/event logic is more closely aligned with shared domain contracts.
7. Tests pass.
8. Docs are updated.
9. No breaking changes are introduced to the current repo structure.

---

## Definition of Done
Done means:
- the Orchestrator is meaningfully closer to the product specification
- its main workflow gaps are closed
- it can now support later real provider integrations more safely
- Google/API hardening can follow after this step without building on incomplete business logic

---

## Recommended Next Step After Completion
After this workorder is finished, the next priority should be:

1. harden the Google Adapter toward real API integration  
or, if needed first,  
2. harden the LEKAB Adapter toward real upstream integration

But only after the Orchestrator workflow logic is functionally complete enough to support them.
