# CODEX_TASK_GOOGLE_CALENDAR_ADAPTER_AND_CUSTOMER_CONTACT_SERVICE_V1.0.0

## Title
Build the Google Calendar Adapter and Customer Contact Service for the LEKAB Appointment Agent

## Objective
Implement two foundational product components for the LEKAB Appointment Agent:

1. **Google Calendar Adapter**
2. **Customer Contact Service**

These components must support the Appointment Orchestrator Agent and the broader messaging-platform strategy.

The design goal is clean separation of concerns:

- **Google Calendar** handles scheduling availability and booking
- **Customer Contact Service** handles customer identity and contact master data
- **LEKAB Adapter** handles messaging, workflow dispatch, and messaging-facing contact synchronization
- **Appointment Orchestrator** handles workflow logic and decisions

This workorder is the first implementation-oriented definition for Codex.

---

## Business Context
The LEKAB Appointment Agent is intended to become a reusable product capability on top of the messaging platform.

For Google-based environments, a critical architecture rule applies:

- Google Calendar is excellent for **free/busy availability** and **event creation**
- Google Calendar is **not** the right system of record for customer master data
- Google People / Contacts can be used as an optional contact source, but should not be the only long-term customer master for serious external booking journeys

Google officially documents:
- `freeBusy.query` as `POST /calendar/v3/freeBusy` with `timeMin`, `timeMax`, `timeZone`, and calendar `items[]` for availability checks. citeturn997811search3
- `events.insert` for creating calendar events under `/calendar/v3/calendars/{calendarId}/events`. citeturn482398search1
- `people.connections.list` for listing the authenticated user’s contacts, with support for sync tokens that expire after 7 days. citeturn997811search1
- `people.searchContacts` for searching grouped contacts from the `CONTACT` source, including the requirement for a warmup request with an empty query before real searches. citeturn997811search0turn997811search7

This means the platform should use:
- Google Calendar API for scheduling
- Customer Contact Service as platform-owned customer master
- optional Google People sync/import
- optional LEKAB Addressbook synchronization for messaging purposes

---

## Scope

### In Scope
1. Implement a provider-specific **Google Calendar Adapter**
2. Implement a platform-owned **Customer Contact Service**
3. Add optional **Google People sync/import support**
4. Define normalized interfaces for the Appointment Orchestrator
5. Add event and command contracts
6. Add tests, docs, and runbook
7. Preserve future compatibility with Microsoft CRM path

### Out of Scope
1. Microsoft CRM implementation itself
2. Google Workspace admin provisioning automation
3. Full UI/Frontend for contact administration
4. Full analytics dashboard
5. Full workforce routing optimizer
6. Full identity verification stack

---

## Product Architecture Position

```text
Customer
  |
  v
LEKAB RCS / SMS
  |
  v
Appointment Orchestrator
  |                |                    |
  |                |                    |
  v                v                    v
Customer Contact   Google Calendar      LEKAB Adapter
Service            Adapter              (Messaging / Addressbook / Workflow)
  |
  +--> optional Google People sync/import
```

### Architectural rule
The Appointment Orchestrator must never call Google APIs directly.
It must call stable internal interfaces only.

---

## Component 1: Google Calendar Adapter

## Goal
Expose a provider-neutral scheduling interface to the Appointment Orchestrator while hiding Google-specific details.

## Responsibilities
- query availability
- compute candidate slots from free/busy data
- create bookings
- update bookings
- cancel bookings
- retrieve bookings when needed
- normalize Google event payloads into internal booking objects

## Non-Responsibilities
- customer identity master
- RCS/SMS rendering
- conversation workflow logic
- slot hold state ownership unless explicitly designed later

## Required Google API Coverage

### 1. FreeBusy query
Support Google `freeBusy.query` using:
- `timeMin`
- `timeMax`
- `timeZone`
- `items[]`
- optional expansion settings as needed

Use this for:
- checking advisor/staff/resource calendars
- validating availability before offering slots
- checking multiple calendars in one request

### 2. Event creation
Support Google `events.insert` for confirmed bookings.

Use this for:
- creating final appointments after user confirmation
- writing event title, description, attendees, and metadata
- storing the resulting external event id

### 3. Event update
Support update/patch logic for:
- reschedule
- metadata updates
- attendee changes where needed

### 4. Event delete / cancellation
Support cancellation flow through delete or equivalent lifecycle handling according to product policy.

### 5. Optional future additions
- calendar list retrieval
- watch/subscription support
- incremental sync support
- room/resource support

---

## Internal Interface for Google Calendar Adapter

### Suggested interface
```python
class CalendarAdapter:
    def search_slots(self, request): ...
    def hold_slot(self, request): ...
    def release_slot(self, request): ...
    def create_booking(self, request): ...
    def update_booking(self, request): ...
    def cancel_booking(self, request): ...
    def get_booking(self, request): ...
```

### Rule for `hold_slot`
Google Calendar does not provide a general-purpose slot hold abstraction.
The **platform should own temporary slot hold state**, not Google Calendar itself.

The adapter may support revalidation checks before commit, but not rely on Google as the hold engine.

---

## Suggested Package Layout
```text
src/<project>/integrations/google_calendar/
  config.py
  models.py
  exceptions.py
  auth.py
  client.py
  adapter.py
  slot_engine.py
  serializers.py
  validators.py
```

---

## Commands and DTOs for Calendar Adapter

### `SearchSlotsCommand`
Fields:
- `tenant_id`
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

### `CreateBookingCommand`
Fields:
- `tenant_id`
- `journey_id`
- `customer_id`
- `slot_id`
- `calendar_target`
- `title`
- `description`
- `attendees`
- `timezone`
- `crm_reference`
- `metadata`

### `UpdateBookingCommand`
Fields:
- `booking_reference`
- `external_calendar_id`
- `new_start`
- `new_end`
- `new_title`
- `new_description`
- `attendees`

### `CancelBookingCommand`
Fields:
- `booking_reference`
- `external_calendar_id`
- `reason`
- `requested_by`

---

## Normalized Outputs

### `CandidateSlot`
Fields:
- `slot_id`
- `start_time`
- `end_time`
- `resource_id`
- `resource_type`
- `timezone`
- `location`
- `score`
- `metadata`

### `BookingResult`
Fields:
- `booking_reference`
- `external_calendar_id`
- `status`
- `start_time`
- `end_time`
- `calendar_target`
- `attendees`
- `provider`
- `provider_payload_reference`

---

## Implementation Guidance for Google Calendar Adapter

### Availability strategy
1. Call `freeBusy.query`
2. Convert busy blocks into free windows
3. Apply product/business rules:
   - working hours
   - duration
   - booking horizon
   - buffer time
   - daypart preference
4. Generate ranked offerable slots
5. Return a normalized list

### Booking strategy
1. Revalidate chosen slot if necessary
2. Call `events.insert`
3. Capture returned Google event id
4. Return normalized booking result
5. Emit booking-created event for CRM write-back and audit

### Time handling
- use explicit timezone fields everywhere
- never rely on server local time
- validate daylight saving boundary cases in tests

---

## Example Implementation Payloads

### FreeBusy request shape
```json
{
  "timeMin": "2026-04-01T00:00:00+02:00",
  "timeMax": "2026-04-10T23:59:59+02:00",
  "timeZone": "Europe/Berlin",
  "items": [
    {"id": "advisor1@example.com"},
    {"id": "advisor2@example.com"}
  ]
}
```

### Internal slot search response
```json
{
  "slots": [
    {
      "slot_id": "SLOT-1",
      "start_time": "2026-04-02T13:00:00+02:00",
      "end_time": "2026-04-02T14:00:00+02:00",
      "resource_id": "advisor1@example.com",
      "score": 0.94
    }
  ]
}
```

---

## Component 2: Customer Contact Service

## Goal
Provide a platform-owned customer/contact master layer for appointment journeys.

This service should hold the customer-facing data that Google Calendar should not own.

## Responsibilities
- store customer identity
- resolve customers by mobile number, email, or external id
- store language and timezone preferences
- store contactability and consent flags
- store CRM reference if present
- store LEKAB addressbook linkage if present
- store optional Google People linkage if present
- provide normalized customer context to the Appointment Orchestrator

## Non-Responsibilities
- direct scheduling logic
- direct messaging workflow execution
- calendar event ownership
- full enterprise CRM replacement

---

## Why a separate Customer Contact Service is needed

Because customer booking needs data such as:
- phone number
- email
- name
- preferred language
- consent
- account / contract number
- customer segment
- region
- CRM references
- messageability status

This is **customer master data**, not calendar data.

Google Calendar events can include attendees, but that does not make Calendar a customer master.

Google People can supply contact records, but those records remain user-/workspace-centric rather than product-centric customer-state records.

---

## Customer Contact Service Internal Interface

### Suggested interface
```python
class CustomerContactService:
    def resolve_customer(self, request): ...
    def create_customer(self, request): ...
    def update_customer(self, request): ...
    def link_google_contact(self, request): ...
    def link_lekab_contact(self, request): ...
    def search_customers(self, request): ...
    def upsert_contactability(self, request): ...
```

---

## Core Domain Model

### `CustomerProfile`
Fields:
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
- `status`
- `crm_reference`
- `lekab_contact_id`
- `google_person_resource_name`
- `created_at`
- `updated_at`

### `CustomerContactMethod`
Fields:
- `customer_id`
- `channel_type`
- `address`
- `is_primary`
- `is_verified`
- `is_reachable`
- `last_verified_at`

### `CustomerConsent`
Fields:
- `customer_id`
- `consent_type`
- `granted`
- `source`
- `timestamp`

---

## Optional Google People Integration

## Purpose
Allow import, search, or enrichment from Google People / Contacts in Google-based customer environments.

## Supported Google People methods
- `people.connections.list`
- `people.searchContacts`

## Use cases
- import customer/contact seeds from Google Contacts
- enrich missing contact data
- resolve known contacts in low-complexity Google Workspace deployments

## Important product rule
Google People support should be **optional** and **replaceable**.

It must not become a hidden hard dependency for the Appointment Agent product.

---

## Suggested Package Layout for Customer Contact Service
```text
src/<project>/services/customer_contact/
  config.py
  models.py
  exceptions.py
  service.py
  repository.py
  validators.py
  serializers.py
  google_people_sync.py
```

---

## Recommended Sync Strategy

### Preferred model
- platform Customer Contact Service is the master
- Google People is a source/enrichment path
- LEKAB Addressbook is a messaging/contact-sync target
- Microsoft CRM can later become a higher-priority master in Microsoft-based deployments

### Google People sync modes
1. **Import only**
   - initial load from Google contacts
2. **Lookup only**
   - live search for operator assistance or low-friction matching
3. **Periodic sync**
   - use `people.connections.list` plus sync token
4. **Search assist**
   - use `people.searchContacts` after required warmup request

---

## Event Model

### Inbound / Source events
- `channel.message.received`
- `customer.lookup.requested`
- `google.people.sync.requested`
- `calendar.slots.search.requested`
- `booking.create.requested`

### Events emitted by Customer Contact Service
- `customer.resolved`
- `customer.created`
- `customer.updated`
- `customer.google_linked`
- `customer.lekab_linked`
- `customer.contactability.updated`
- `customer.lookup.failed`

### Events emitted by Google Calendar Adapter
- `calendar.slots.found`
- `calendar.slots.not_found`
- `calendar.booking.created`
- `calendar.booking.updated`
- `calendar.booking.cancelled`
- `calendar.booking.failed`

---

## Configuration Parameters

### Google Calendar Adapter
- `GOOGLE_CALENDAR_ENABLED`
- `GOOGLE_CALENDAR_CREDENTIALS_PATH`
- `GOOGLE_CALENDAR_IMPERSONATION_ENABLED`
- `GOOGLE_CALENDAR_DEFAULT_TIMEZONE`
- `GOOGLE_CALENDAR_HTTP_TIMEOUT_SECONDS`
- `GOOGLE_CALENDAR_MAX_RETRIES`
- `GOOGLE_CALENDAR_RETRY_BACKOFF_MS`
- `GOOGLE_CALENDAR_FREEBUSY_SCOPE_MODE`
- `GOOGLE_CALENDAR_EVENT_WRITE_ENABLED`

### Customer Contact Service
- `CUSTOMER_CONTACT_SERVICE_ENABLED`
- `CUSTOMER_CONTACT_DB_URL`
- `CUSTOMER_CONTACT_DEFAULT_LANGUAGE`
- `CUSTOMER_CONTACT_DEFAULT_TIMEZONE`
- `CUSTOMER_CONTACT_REQUIRE_CONSENT_FOR_REMINDERS`
- `CUSTOMER_CONTACT_ALLOW_AD_HOC_CREATE`
- `CUSTOMER_CONTACT_ALLOW_GOOGLE_IMPORT`
- `CUSTOMER_CONTACT_ALLOW_GOOGLE_LOOKUP`
- `CUSTOMER_CONTACT_ALLOW_LEKAB_SYNC`

### Google People integration
- `GOOGLE_PEOPLE_ENABLED`
- `GOOGLE_PEOPLE_SYNC_MODE`
- `GOOGLE_PEOPLE_PAGE_SIZE`
- `GOOGLE_PEOPLE_SYNC_TOKEN_CACHE_TTL`
- `GOOGLE_PEOPLE_SEARCH_WARMUP_ENABLED`

---

## Security and Compliance Requirements
1. Do not store unnecessary personal data
2. Redact phone numbers and emails in logs where required
3. Keep OAuth credentials outside code
4. Enforce consent checks before reminder workflows
5. Separate customer identity from channel event payloads where possible
6. Track data provenance:
   - entered manually
   - imported from Google People
   - synced from CRM
   - synced to LEKAB
7. Support deletion/anonymization flows later

---

## Test Requirements

### Google Calendar Adapter unit tests
- freebusy request construction
- slot computation from busy windows
- timezone conversion correctness
- create booking request mapping
- update/cancel behavior
- validation errors
- retryable failure handling

### Customer Contact Service unit tests
- resolve by phone
- resolve by email
- create/update customer
- contactability updates
- consent handling
- Google People link persistence
- LEKAB link persistence

### Integration tests
- mocked Google freebusy flow
- mocked Google event creation flow
- optional mocked Google People list/search flow
- combined orchestrator-facing flow:
  - resolve customer
  - search slots
  - create booking

### Non-functional tests
- DST boundary tests
- duplicate customer resolution behavior
- no secret leakage
- safe fallback when Google People unavailable

---

## Documentation Requirements
Codex must also create:
- `docs/admin/google_calendar_adapter.md`
- `docs/admin/customer_contact_service.md`
- optional `docs/help/...` only if any UI/admin screen is added
- release note delta if applicable
- standardized test runbook

The docs must explain:
- architecture
- config/env vars
- scopes/permissions
- sync modes
- risks
- operational guidance
- troubleshooting

---

## Acceptance Criteria
The work is complete only if:

1. A provider-neutral Google Calendar Adapter exists.
2. The adapter supports slot search, create booking, update booking, and cancel booking.
3. A Customer Contact Service exists with customer resolution and update capabilities.
4. Optional Google People import/search support is implemented behind a feature flag or separate module.
5. The Appointment Orchestrator can consume both services through stable internal interfaces.
6. Config is fully externalized.
7. Tests pass.
8. Docs exist and are non-empty.
9. No runtime artifacts are committed.
10. The architecture remains compatible with a later Microsoft CRM path.

---

## Licensing & Commercialization Guardrails
Mandatory:
- prefer MIT / Apache-2.0 / BSD dependencies
- avoid GPL / AGPL in the core
- isolate copyleft dependencies as separate sidecars if ever required
- explicitly flag license risks
- keep dependency footprint small and commercially safe

---

## Recommended MVP Decision
For the first real Google-based path of the Appointment Agent:

- **Calendar source:** Google Calendar API
- **Customer source:** platform Customer Contact Service
- **Optional enrichment:** Google People API
- **Messaging contact sync:** LEKAB Addressbook where useful

This is the cleanest architecture and the best bridge toward a future Microsoft CRM path.

---

## Deliverables
Codex must produce:
1. Google Calendar Adapter implementation
2. Customer Contact Service implementation
3. optional Google People sync/search module
4. tests
5. admin/developer docs
6. test runbook
7. SUMMARY artifact after test run (runtime artifact, not committed)

---

## Definition of Done
Done means:
- code is implemented cleanly
- interfaces are stable
- tests pass
- docs exist
- no artifact leakage occurs
- both components are ready for integration by the Appointment Orchestrator
