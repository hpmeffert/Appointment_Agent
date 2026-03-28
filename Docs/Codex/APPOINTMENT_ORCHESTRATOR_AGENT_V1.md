# APPOINTMENT_ORCHESTRATOR_AGENT_V1.md

# Appointment Orchestrator Agent – Variant 1  
## First Product / Architecture Draft for the LEKAB Appointment Agent

**Version:** 0.1  
**Status:** First Draft  
**Language:** English  
**Purpose:** Foundational component definition for the LEKAB Appointment Agent as an extension of the messaging platform.

---

# Table of Contents

1. Purpose
2. Product Role Inside the Messaging Platform
3. Goals
4. Non-Goals
5. Core Responsibilities
6. High-Level Architecture Position
7. Internal Subcomponents
8. Main Inputs and Outputs
9. Core Domain Model
10. Conversation States
11. Main Orchestration Flows
12. Event Model
13. Service Interfaces
14. Configuration Parameters
15. Error Handling and Recovery
16. Security and Compliance
17. Observability and KPIs
18. MVP Scope
19. Future Extensions
20. Open Questions

---

# 1. Purpose

The **Appointment Orchestrator Agent** is the central decision-making and workflow control component of the **LEKAB Appointment Agent**.

Its job is to coordinate the complete appointment journey across:

- customer communication channels
- slot search and slot selection
- calendar systems
- CRM systems
- LEKAB messaging and workflow services
- state tracking, reminders, and follow-up actions

In simple words:

> The Orchestrator is the brain of the Appointment Agent.  
> It decides what should happen next, why it should happen, and which system should do it.

It does **not** replace the messaging platform.  
It uses the messaging platform as a channel and workflow execution layer.

---

# 2. Product Role Inside the Messaging Platform

The Appointment Orchestrator Agent should be treated as a **platform capability service** that sits on top of the communication bus.

It is not just a chatbot and not just a scheduling script.

It is a reusable orchestration service that can later support:

- appointment booking
- appointment confirmation
- reminders
- rescheduling
- cancellation
- callback booking
- service visits
- consultation scheduling
- field service coordination
- public service scheduling

This means it should be designed as a **shared product component**, not as a one-off project artifact.

---

# 3. Goals

The first version of the Appointment Orchestrator Agent should achieve the following goals:

## Functional goals

- understand the current appointment journey step
- request valid appointment slots from connected adapters
- offer only real, bookable appointment options
- handle customer selection through structured replies or free text
- confirm, book, reschedule, or cancel appointments
- trigger reminders and follow-up messages
- escalate to a human when necessary

## Technical goals

- integrate cleanly with the communication bus
- use LEKAB adapters without knowing LEKAB API details directly
- support multiple calendar providers through adapters
- support multiple CRM providers through adapters
- provide explainable state transitions
- remain modular, testable, and extensible

## Business goals

- reduce manual scheduling work
- shorten time-to-booking
- improve customer convenience
- increase booking conversion
- reduce no-shows
- create reusable platform value for LEKAB

---

# 4. Non-Goals

The first version of the Appointment Orchestrator Agent should **not** try to do everything.

## Out of scope for v1

- advanced AI reasoning across many unrelated domains
- direct rendering of RCS payloads
- direct HTTP calls to Google/Microsoft/LEKAB from conversation logic
- full NLP platform for all languages
- full optimization engine for travel routing
- large-scale workforce optimization
- agent desktop UI
- billing engine
- full analytics dashboard

Those should remain separate components or later phases.

---

# 5. Core Responsibilities

The Appointment Orchestrator Agent owns the **workflow logic**.

Its main responsibilities are:

## 5.1 Journey control
Track where the customer currently is in the appointment journey.

Examples:
- initial contact
- preference collection
- slot offering
- slot confirmation
- booking completed
- reminder stage
- reschedule stage
- cancellation stage
- escalation stage

## 5.2 Decision making
Decide what action should happen next based on:
- customer response
- conversation state
- business rules
- slot availability
- policy constraints
- timeout conditions

## 5.3 Adapter coordination
Trigger the correct downstream services:
- LEKAB Adapter
- Calendar Adapter
- CRM Adapter
- State Store
- Audit Service
- Reminder Scheduler

## 5.4 State management
Keep track of:
- selected service type
- date preferences
- candidate slots
- chosen slot
- slot hold expiry
- appointment reference
- messaging history
- escalation reason

## 5.5 Policy enforcement
Make sure rules are respected, for example:
- quiet hours
- booking horizon
- reschedule cutoff
- channel restrictions
- consent rules
- appointment duration rules

---

# 6. High-Level Architecture Position

```text
Customer
  |
  v
RCS / SMS / Future Channels
  |
  v
Channel Adapter Layer
  |
  v
Communication Bus
  |
  v
Appointment Orchestrator Agent
  |        |         |         |         |
  |        |         |         |         |
  v        v         v         v         v
State   Calendar    CRM     LEKAB    Reminder /
Store   Adapter     Adapter Adapter  Notification Logic
  |
  v
Audit / Analytics / Observability
```

## Architectural role

The Orchestrator sits in the center of the business workflow.

It should:
- receive normalized inbound events
- evaluate the current state
- decide next actions
- emit normalized outbound commands/events

It should **not** contain provider-specific channel payload logic.

---

# 7. Internal Subcomponents

A first clean internal decomposition is:

## 7.1 Journey Manager
Responsible for:
- identifying the active journey
- loading current state
- selecting the correct flow logic

## 7.2 Policy Engine
Responsible for:
- evaluating business constraints
- applying guardrails
- checking if a step is allowed

## 7.3 Slot Request Coordinator
Responsible for:
- creating normalized slot search requests
- calling the calendar adapter
- ranking and packaging valid slot options

## 7.4 Response Interpreter
Responsible for:
- interpreting structured replies
- interpreting customer free text in a bounded way
- mapping user choice to domain actions

## 7.5 Booking Coordinator
Responsible for:
- creating slot holds
- confirming slot selection
- booking the final appointment
- handling revalidation before final commit

## 7.6 Exception and Escalation Manager
Responsible for:
- handling invalid replies
- timeout or no-response logic
- no-slot situations
- human handoff triggers

## 7.7 Reminder and Follow-Up Manager
Responsible for:
- scheduling reminders
- triggering confirmations
- handling pre-appointment follow-up

---

# 8. Main Inputs and Outputs

## 8.1 Inputs

The Orchestrator receives normalized inputs such as:

- inbound message received
- button selected
- action selected
- free text received
- customer identified
- slot search completed
- slot hold expired
- appointment booked
- appointment changed externally
- reminder due
- callback/job lifecycle event received

## 8.2 Outputs

The Orchestrator emits commands/events such as:

- search slots
- hold slot
- confirm slot
- create appointment
- update CRM record
- send appointment offer
- send confirmation
- send reminder
- request escalation
- close journey
- record audit entry

---

# 9. Core Domain Model

A simple initial domain model should include:

## 9.1 AppointmentJourney
Represents one complete appointment flow.

Suggested fields:
- journey_id
- correlation_id
- tenant_id
- customer_id
- channel
- current_state
- service_type
- locale
- timezone
- created_at
- updated_at

## 9.2 AppointmentPreference
Represents what the customer wants.

Suggested fields:
- earliest_date
- latest_date
- preferred_month
- preferred_weekdays
- preferred_daypart
- preferred_location_type
- preferred_language
- urgency
- free_text_preference

## 9.3 CandidateSlot
Represents a valid offerable slot.

Suggested fields:
- slot_id
- start_time
- end_time
- resource_id
- resource_type
- location
- score
- hold_expires_at

## 9.4 AppointmentBooking
Represents the final booking.

Suggested fields:
- booking_reference
- external_calendar_id
- crm_reference
- slot_id
- status
- booked_at
- confirmation_message_id

## 9.5 ConversationTurn
Represents one inbound or outbound communication step.

Suggested fields:
- turn_id
- direction
- channel
- message_type
- raw_payload_reference
- normalized_payload
- timestamp

---

# 10. Conversation States

A first finite-state model can look like this:

```text
NEW
  -> IDENTIFYING_CUSTOMER
  -> COLLECTING_PREFERENCES
  -> SEARCHING_SLOTS
  -> OFFERING_SLOTS
  -> WAITING_FOR_SELECTION
  -> HOLDING_SLOT
  -> WAITING_FOR_CONFIRMATION
  -> BOOKING_APPOINTMENT
  -> BOOKED
  -> REMINDER_PENDING
  -> RESCHEDULE_FLOW
  -> CANCELLATION_FLOW
  -> ESCALATED
  -> CLOSED
  -> FAILED
```

## State explanations

### NEW
Journey was created but no decision has been made yet.

### IDENTIFYING_CUSTOMER
System is resolving the user or the relevant case.

### COLLECTING_PREFERENCES
System asks for date/time preferences when needed.

### SEARCHING_SLOTS
System has enough information and is querying slot availability.

### OFFERING_SLOTS
System has valid options and is preparing/sending them.

### WAITING_FOR_SELECTION
System is waiting for the user to choose or refine.

### HOLDING_SLOT
A slot has been tentatively reserved.

### WAITING_FOR_CONFIRMATION
The user must explicitly confirm the chosen slot.

### BOOKING_APPOINTMENT
The final booking is being written to external systems.

### BOOKED
Appointment has been successfully created.

### REMINDER_PENDING
Journey remains active for reminders and pre-visit interactions.

### RESCHEDULE_FLOW
Journey is now in appointment change mode.

### CANCELLATION_FLOW
Journey is now in cancellation mode.

### ESCALATED
The workflow has been handed to a human or another system.

### CLOSED
The journey is complete.

### FAILED
The workflow ended due to an unrecoverable technical or business failure.

---

# 11. Main Orchestration Flows

## 11.1 Standard booking flow

1. Receive booking trigger
2. Identify customer and context
3. Request slot search
4. Rank valid slots
5. Send slot offer
6. Receive customer choice
7. Hold selected slot
8. Ask for confirmation if required
9. Book appointment
10. Write back to CRM
11. Send confirmation
12. Schedule reminders
13. Close active booking part of the journey

## 11.2 No-slot flow

1. Receive booking trigger
2. Search slots
3. No valid slots found
4. Offer broader choices:
   - next 7–10 days
   - next month
   - human help
5. Repeat search or escalate

## 11.3 Reschedule flow

1. Receive reschedule intent
2. Retrieve current booking
3. Validate reschedule policy
4. Search replacement slots
5. Offer alternatives
6. Confirm new choice
7. Update calendar + CRM
8. Send updated confirmation

## 11.4 Cancel flow

1. Receive cancel intent
2. Validate cancellation policy
3. Cancel appointment
4. Update external systems
5. Confirm cancellation
6. Optionally offer rebooking path

## 11.5 Reminder flow

1. Reminder due event received
2. Check booking still active
3. Send reminder
4. Process confirm/change/cancel reply
5. Branch into next flow accordingly

---

# 12. Event Model

The Appointment Orchestrator Agent should consume and emit normalized events.

## 12.1 Inbound events

Suggested first set:
- `channel.message.received`
- `channel.button.selected`
- `channel.action.selected`
- `customer.identified`
- `calendar.slots.found`
- `calendar.slots.not_found`
- `booking.slot.held`
- `booking.slot.hold_expired`
- `booking.created`
- `booking.updated`
- `booking.cancelled`
- `crm.lookup.completed`
- `lekab.job.started`
- `lekab.job.assigned`
- `lekab.job.finished`
- `reminder.due`

## 12.2 Outbound events / commands

Suggested first set:
- `appointment.search.requested`
- `appointment.offer.prepare`
- `appointment.offer.send`
- `appointment.slot.hold.requested`
- `appointment.booking.create.requested`
- `appointment.booking.update.requested`
- `appointment.booking.cancel.requested`
- `appointment.confirmation.send`
- `appointment.reminder.schedule`
- `appointment.escalation.requested`
- `appointment.audit.record`

## 12.3 Event envelope

Every event should include:
- event_id
- event_type
- correlation_id
- causation_id
- tenant_id
- journey_id
- timestamp_utc
- source
- payload_version
- trace_id
- payload

---

# 13. Service Interfaces

The Orchestrator should use stable internal interfaces.

## 13.1 Calendar Adapter Interface

Example methods:
- `search_slots(request)`
- `hold_slot(request)`
- `release_slot(request)`
- `create_booking(request)`
- `update_booking(request)`
- `cancel_booking(request)`

## 13.2 CRM Adapter Interface

Example methods:
- `lookup_customer(context)`
- `load_case(reference)`
- `write_booking_result(payload)`
- `append_activity(payload)`

## 13.3 LEKAB Adapter Interface

Example methods:
- `launch_appointment_offer(payload)`
- `launch_confirmation(payload)`
- `launch_reminder(payload)`
- `resolve_contact_by_phone(payload)`
- `sync_contact(payload)`

## 13.4 State Store Interface

Example methods:
- `load_journey(journey_id)`
- `save_journey(journey)`
- `append_turn(turn)`
- `store_candidate_slots(slots)`
- `mark_state(state)`

## 13.5 Audit Interface

Example methods:
- `record_decision(payload)`
- `record_policy_check(payload)`
- `record_external_write(payload)`

---

# 14. Configuration Parameters

A first version should support configurable behavior.

## 14.1 Business configuration
- booking_window_days
- max_slots_per_offer
- default_duration_minutes
- slot_hold_minutes
- reschedule_cutoff_hours
- quiet_hours
- working_days
- timezone_strategy

## 14.2 Conversation configuration
- default_language
- free_text_enabled
- clarification_retry_limit
- ask_confirmation_before_commit
- no_slot_strategy
- human_handoff_enabled

## 14.3 Channel configuration
- prefer_rcs
- allow_sms_fallback
- max_sms_options
- allow_calendar_action
- reminder_channel_strategy

## 14.4 Technical configuration
- event_schema_version
- callback_timeout_seconds
- state_ttl_days
- audit_retention_days
- idempotency_enabled
- metrics_enabled

---

# 15. Error Handling and Recovery

The Orchestrator must fail safely.

## 15.1 Error categories
- invalid customer input
- no valid slots
- policy rejection
- adapter timeout
- adapter validation failure
- duplicate callback/event
- stale slot
- booking conflict
- CRM write failure
- calendar write failure

## 15.2 Recovery principles
- never silently ignore an important error
- retry only retryable technical failures
- revalidate before committing a booking
- escalate if customer experience would otherwise break
- keep audit history for every failed transition

## 15.3 Example fallback decisions
- if slot hold expired -> return to OFFERING_SLOTS
- if booking write fails after slot chosen -> try safe recovery or escalate
- if customer reply is unclear -> clarification flow
- if confidence is low -> human handoff

---

# 16. Security and Compliance

The Appointment Orchestrator Agent must follow strict operational rules.

## Key principles
- minimal personal data in journey state
- no secrets inside journey payloads
- structured redaction in logs
- explicit consent and channel policy checks
- traceability of automated decisions
- role-based access to sensitive journey details
- encryption in transit
- retention policy for customer interaction records

## Compliance-sensitive topics
- consent for messaging
- reminder eligibility
- time zone correctness
- customer identification
- CRM write-back integrity
- auditability of automated decisions

---

# 17. Observability and KPIs

A production-ready orchestrator must be measurable.

## 17.1 Technical metrics
- journeys started
- journeys completed
- journeys failed
- average time to first slot offer
- average time to confirmed booking
- slot hold expiry count
- escalation rate
- adapter timeout rate
- booking conflict rate

## 17.2 Business metrics
- booking conversion rate
- reschedule rate
- cancellation rate
- reminder confirmation rate
- no-show reduction indicator
- manual workload reduction estimate

## 17.3 Debugging and tracing
Every journey should be traceable via:
- correlation_id
- journey_id
- booking_reference
- customer reference
- external system reference

---

# 18. MVP Scope

The first MVP version of the Appointment Orchestrator Agent should include:

## Included
- one standard booking flow
- one reschedule flow
- one cancel flow
- one reminder flow
- state machine
- slot request orchestration
- booking orchestration
- LEKAB offer/confirmation/reminder trigger integration
- CRM write-back trigger
- audit trail
- basic escalation path

## Excluded from MVP
- advanced multilingual NLP
- workforce optimization
- predictive slot ranking using ML
- advanced analytics UI
- custom vertical templates for many industries
- voice integration

---

# 19. Future Extensions

This first variant should be designed to grow into a broader platform component.

## Possible next steps
- multilingual conversation packs
- smarter slot ranking logic
- customer history-aware scheduling
- field-service routing integration
- payment-before-booking scenarios
- document upload before appointment
- OTP / identity verification steps
- voice + messaging orchestration
- incident and crisis scheduling patterns
- richer KPI feedback loops

---

# 20. Open Questions

Before implementation, these questions should be clarified:

1. Which calendar provider is first priority?
2. Which CRM/system of record is first priority?
3. Should slot hold be handled by adapter or orchestrator-owned state?
4. Is confirmation always required before final booking?
5. Which event bus contract format is standard in the project?
6. Which languages are required in MVP?
7. What is the human handoff target system?
8. Which journey data must remain in LEKAB and which in local state?
9. Are reminders always mandatory?
10. Should no-slot scenarios propose callback booking as fallback?

---

# Closing Note

This first variant defines the **Appointment Orchestrator Agent** as a reusable workflow brain for the LEKAB Appointment Agent product family.

It should be implemented as a clean, modular, provider-agnostic orchestration service that:
- uses the communication bus
- delegates provider-specific logic to adapters
- keeps explicit state
- remains explainable
- supports future platform growth

It is the right architectural center for turning appointment scheduling into a reusable messaging-platform capability.
