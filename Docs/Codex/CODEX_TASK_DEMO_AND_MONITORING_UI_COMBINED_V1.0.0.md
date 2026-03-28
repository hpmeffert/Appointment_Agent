# CODEX_TASK_DEMO_AND_MONITORING_UI_COMBINED_V1.0.0.md

## Title
Build a combined live Demo UI + Monitoring Dashboard for the LEKAB Appointment Agent

## Objective
Create a **combined presentation and simulation UI** for the LEKAB Appointment Agent that supports both:

1. **Interactive Demo Mode**
   - customer-facing simulation
   - guided click-through appointment journey
   - ideal for sales, presales, management demos, and storytelling

2. **Technical Monitoring Mode**
   - internal flow visibility
   - event progression across LEKAB, Orchestrator, Google Adapter, and platform state
   - ideal for architecture demos, internal reviews, and debugging walkthroughs

3. **Combined Live Mode**
   - both views visible together and synchronized
   - customer actions on the left drive technical state changes on the right
   - ideal for showing how a user action becomes a platform workflow event

This UI is a **mockup / simulation layer**, not yet a production admin UI.
Its first job is to make the product understandable and demonstrable on screen.

---

## Why this matters
The LEKAB Appointment Agent is becoming a real multi-component platform:

- LEKAB messaging/workflow layer
- Appointment Orchestrator
- Google Adapter
- shared domain contracts
- audit
- CRM-preparation events
- no-slot logic
- escalation logic

This is powerful, but hard to explain in meetings unless people can **see** what happens.

The combined Demo + Monitoring UI should solve that.

---

## Product Goal
Build a presentation-friendly mockup that can visually answer two questions:

### Customer / Sales View
“What does the appointment journey feel like for the customer?”

### Technical / Management View
“What happens inside the system while that journey runs?”

---

## Scope

### In Scope
1. Build a visual UI mockup with:
   - Demo Mode
   - Monitoring Mode
   - Combined Live Mode
2. Simulate the appointment journey end-to-end
3. Show key state transitions visually
4. Show event progression visually
5. Show Google-side booking activity visually
6. Show LEKAB / Orchestrator / Google flow boundaries clearly
7. Provide scenario switching
8. Make the mockup suitable for screen presentation

### Out of Scope
1. Real production admin authentication
2. Real live LEKAB / Google API connectivity
3. Full backend persistence integration
4. Full analytics dashboard
5. Full design system hardening
6. Enterprise permission model

---

## Core UX Requirement
The UI must support **three modes**:

### 1. Demo Mode
Focus on the customer journey only.

Example screen elements:
- message input / RCS simulation
- slot offer cards or buttons
- confirmation view
- reschedule / cancel path
- no-slot path
- escalation option

### 2. Monitoring Mode
Focus on the internal system flow only.

Example screen elements:
- live step cards for:
  - LEKAB
  - Orchestrator
  - Google Adapter
  - CRM event layer
- journey state
- correlation id
- provider reference
- audit log
- event stream / timeline
- slot hold status

### 3. Combined Live Mode
Show both views side by side and keep them synchronized.

Recommended layout:
- **left side:** customer demo/chat journey
- **right side:** technical monitoring/dashboard view

When the user clicks something on the left, the right side should update immediately.

---

## Recommended UI Layout

### Layout A – Combined Live View
```text
+---------------------------------------------------------------+
| Header: Appointment Agent Demo / Monitoring                   |
+-------------------------------+-------------------------------+
| Left: Interactive Demo        | Right: Monitoring Dashboard   |
|-------------------------------|-------------------------------|
| Customer chat / RCS view      | Live event timeline           |
| Slot buttons                  | Current journey state         |
| Confirmation message          | LEKAB step status             |
| Reschedule / cancel actions   | Orchestrator status           |
| No-slot fallback options      | Google Adapter status         |
| Escalation action             | Audit log / CRM events        |
+-------------------------------+-------------------------------+
```

### Layout B – Separate Toggle Views
Allow switching between:
- Demo Mode
- Monitoring Mode
- Combined Mode

---

## Required Scenario Set
The UI must support at least these demo scenarios:

### Scenario 1 – Standard Booking
Flow:
1. customer requests appointment
2. slots are searched
3. slots are returned
4. customer selects a slot
5. booking is created
6. confirmation is sent

### Scenario 2 – Reschedule
Flow:
1. existing booking loaded
2. customer requests change
3. new slots searched
4. new slot selected
5. booking updated
6. confirmation updated

### Scenario 3 – Cancellation
Flow:
1. existing booking loaded
2. customer cancels
3. provider cancellation executed
4. CRM cancel event emitted
5. audit updated

### Scenario 4 – No-slot / Escalation
Flow:
1. no slots found
2. broader search or next month option shown
3. customer requests help or system escalates
4. human handover / callback path visualized

### Scenario 5 – Provider Failure
Flow:
1. booking update/cancel fails
2. error shown in monitoring
3. audit shows failure
4. escalation or retry decision shown

---

## Demo Mode Requirements

### Functional requirements
Demo Mode must let the presenter simulate:
- sending initial booking request
- choosing a slot
- confirming a slot
- requesting reschedule
- requesting cancellation
- selecting fallback options
- triggering escalation/help

### UX requirements
- easy to understand for non-technical viewers
- visually clean
- low clutter
- large buttons for actions
- readable status messages
- strong storytelling flow

### Example demo content
- “I want to book an appointment”
- “Available slots”
- “Tomorrow 10:00”
- “Next week”
- “Next month”
- “Need human help”
- “Appointment confirmed”

---

## Monitoring Mode Requirements

### Functional requirements
Monitoring Mode must show:
- current scenario
- current journey state
- current active component
- event progression
- audit trail
- booking state
- provider reference
- CRM write-back event(s)
- slot hold status
- escalation status if relevant

### Recommended panels
1. **Flow Steps Panel**
   - LEKAB
   - Orchestrator
   - Google Adapter
   - CRM event layer

2. **Journey State Panel**
   - current state
   - journey id
   - correlation id
   - trace id

3. **Booking Panel**
   - booking reference
   - provider reference
   - current booking status
   - slot time

4. **Audit Panel**
   - decisions
   - policy results
   - escalation reason
   - reminder/cancel/reschedule actions

5. **Event Stream Panel**
   - chronological event list
   - latest first or top-to-bottom flow

### Visual status values
- pending
- active
- done
- failed
- escalated

---

## Combined Live Mode Requirements

### Goal
Synchronize customer actions with technical flow visibility.

### Required behavior
Examples:
- Customer clicks “Tomorrow 10:00”
  - Monitoring view updates:
    - `appointment.slot.selected`
    - state -> `WAITING_FOR_CONFIRMATION`
- Customer clicks “Confirm”
  - Monitoring updates:
    - `appointment.booking.create.requested`
    - Google Adapter active
    - `calendar.booking.created`
    - CRM event emitted
- Customer clicks “Need help”
  - Monitoring updates:
    - `appointment.escalation.requested`
    - state -> `ESCALATED`
    - audit entry created

### Important rule
The two panes must not behave as two unrelated demos.
They must reflect the same simulated journey.

---

## Architecture Mapping to Show
The UI should clearly visualize this product chain:

```text
Customer / RCS / SMS
        ↓
LEKAB
        ↓
Appointment Orchestrator
        ↓
Google Adapter
        ↓
Booking Result / CRM Event / Audit
```

Optional future placeholders:
- Microsoft Adapter
- Human Agent Handover
- Customer Contact Service

---

## Shared Domain Contract Alignment
The simulation should visually reflect the shared platform semantics where practical:

- `journey_id`
- `correlation_id`
- `trace_id`
- `booking_reference`
- `provider_reference`
- journey state
- audit records
- CRM-preparation events

It is not necessary to expose every raw field, but the monitoring view should show enough to support technical explanation.

---

## UI Controls Required

### Global controls
- switch mode:
  - Demo
  - Monitoring
  - Combined
- scenario selector
- restart simulation
- next step / autoplay
- reset

### Optional useful controls
- speed control
- show/hide technical IDs
- show/hide audit details
- simulate provider failure
- simulate no-slot path

---

## Suggested Technology Direction
Because this is already being mocked visually, continue with the existing React/canvas direction.

Recommended:
- React
- Tailwind
- simple local state
- Framer Motion for lightweight animated transitions
- shadcn/ui for cards/buttons if already used

Do not overengineer this step.

---

## Recommended File Strategy
Depending on current repo/canvas structure, likely create or expand:
- one React file for the combined mockup
- optional internal components for:
  - `DemoPanel`
  - `MonitoringPanel`
  - `ScenarioSelector`
  - `EventTimeline`
  - `JourneyStateCard`
  - `AuditLogCard`

If repo integration is desired later, these can become the base for a proper demo frontend.

---

## Minimum Data Model for Simulation
The simulation layer should track at least:
- active scenario
- current step index
- journey state
- flow step statuses
- booking reference
- provider reference
- event log entries
- audit entries
- escalation flag
- selected slot
- current user message / current platform response

---

## Required Scenarios for Technical Simulation
At minimum produce event-like outputs such as:
- `channel.message.received`
- `appointment.search.requested`
- `calendar.slots.found`
- `appointment.slot.selected`
- `appointment.booking.create.requested`
- `calendar.booking.created`
- `crm.booking.create.requested`
- `appointment.escalation.requested`
- `appointment.booking.cancel.requested`
- `calendar.booking.cancelled`

---

## Presentation Quality Requirements
This UI must be suitable for:
- colleague walkthroughs
- internal architecture demos
- sales storytelling
- management briefings
- screen sharing in workshops

That means:
- clean spacing
- readable text
- strong visual hierarchy
- no cluttered developer-only layout
- polished enough for presentation, even if simulated

---

## Tests / Validation
For this mockup layer, focus on:
- mode switching works
- scenario switching works
- combined mode updates both panes
- restart/reset works
- simulated event timeline updates correctly
- simulated booking/provider references appear consistently

Formal automated tests are optional for this mockup if not already standard in the UI layer, but basic stability is expected.

---

## Documentation
Add or update lightweight demo-facing documentation describing:
- what each mode is for
- which scenario buttons exist
- what the right-side monitoring panels mean
- known limitations (simulation vs real provider integration)

---

## Acceptance Criteria
This work is complete only if:

1. Demo Mode exists and is usable on its own.
2. Monitoring Mode exists and is usable on its own.
3. Combined Live Mode exists and synchronizes both sides.
4. At least booking, reschedule, cancellation, and no-slot/escalation scenarios are visualized.
5. The monitoring side clearly shows technical flow progression.
6. The UI is presentation-friendly.
7. The result is good enough to demonstrate to colleagues and in presales contexts.

---

## Definition of Done
Done means:
- the Appointment Agent can now be explained visually both as a customer journey and as a technical platform flow
- the UI supports storytelling and architecture communication
- the product becomes easier to present internally and externally

---

## Recommended Next Step After Completion
After this combined mockup is finished, the next likely step should be:
- enrich the simulation with real backend hooks later
or
- create a second specialized technical control-center view for deeper internal monitoring
