# GOOGLE_CALENDAR_INTERFACE_AND_CUSTOMER_ADDRESSBOOK_STRATEGY_V1.md

# Google Calendar Interface and Customer Address Book Strategy  
## For the LEKAB Appointment Agent / Appointment Orchestrator Agent

**Version:** 0.1  
**Status:** First Draft  
**Language:** English

---

# Table of Contents

1. Purpose
2. Short Answer
3. What the Google Calendar Interface Should Look Like
4. Recommended Adapter Boundary
5. Core Google Calendar Operations
6. Suggested Internal API for the Calendar Adapter
7. Example Request / Response Shapes
8. Booking Flow with Google Calendar
9. Where the Customer Data Should Come From
10. Does Google Have an Address Book?
11. Recommended Customer Data Strategy for Google-Based Environments
12. Architecture Recommendation
13. Practical Decision Matrix
14. Risks and Limits
15. Recommended MVP Decision
16. Open Questions

---

# 1. Purpose

This document explains two important design questions for the LEKAB Appointment Agent:

1. **What should the interface to Google Calendar look like?**
2. **Where should the customer/contact data come from when a customer wants to book an appointment in a Google-based environment?**

This is especially important because the architecture should stay clean and reusable across:
- Google Calendar environments
- Microsoft CRM environments
- LEKAB messaging workflows
- future platform modules

---

# 2. Short Answer

## 2.1 Google Calendar interface
The Appointment Orchestrator should **not call Google Calendar directly**.  
It should call a **Calendar Adapter** with a clean internal interface such as:

- `search_slots()`
- `hold_slot()`
- `create_booking()`
- `update_booking()`
- `cancel_booking()`

The Google-specific adapter then maps those calls to the Google Calendar API.

Google Calendar provides a `freeBusy.query` endpoint for availability checks and an `events.insert` endpoint to create bookings. citeturn482398search0turn482398search1

## 2.2 Customer address book
Google Calendar is **not** the right place to keep the customer master record.

For Google-based environments, there are three realistic options:

1. **Best option:** use a platform/customer master record outside Google Calendar  
2. **Possible option:** use Google People API / Google Contacts as a contact source  
3. **Weak option:** rely only on ad hoc booking payload data

The Google People API can list and manage the authenticated user’s contacts, and it supports source types such as `CONTACT`, `PROFILE`, `DOMAIN_CONTACT`, and `OTHER_CONTACT`. citeturn383059search3turn383059search7

### Important practical conclusion
For an external customer booking scenario, **Google Calendar should be the scheduling system, not the customer database**.  
The customer/contact record should preferably live in:
- CRM
- a customer registry
- LEKAB address book sync layer
- or a dedicated platform contact service

---

# 3. What the Google Calendar Interface Should Look Like

The cleanest design is to hide Google-specific details behind a provider-neutral internal adapter.

## 3.1 Why
The Orchestrator should think in business actions:
- find valid slots
- book slot
- change slot
- cancel slot

It should not think in raw Google HTTP endpoints.

## 3.2 Goal
This keeps the Appointment Orchestrator reusable across:
- Google Calendar
- Microsoft Graph calendars
- Dynamics scheduling
- custom scheduling engines later

---

# 4. Recommended Adapter Boundary

```text
Appointment Orchestrator Agent
        |
        v
Calendar Adapter Interface
        |
        +-------------------+
        |                   |
        v                   v
Google Calendar Adapter   Microsoft Calendar Adapter
        |
        v
Google Calendar API
```

## Rule
The Orchestrator sends **normalized requests** and receives **normalized responses**.

That means:
- Google-specific scopes stay inside the adapter
- Google calendar IDs stay inside the adapter
- Google event payloads stay inside the adapter
- Google time handling logic stays inside the adapter

---

# 5. Core Google Calendar Operations

The Google Calendar API should mainly be used for these jobs.

## 5.1 Availability lookup
Use Google `freeBusy.query`.

This endpoint:
- returns busy/free information for a set of calendars
- is a `POST` request to `/calendar/v3/freeBusy`
- supports `timeMin`, `timeMax`, `timeZone`, and a list of calendar IDs in `items[]` citeturn482398search0

### Meaning for the product
This is ideal for:
- checking staff availability
- checking room/resource availability
- checking multiple calendars at once before offering slots

## 5.2 Create booking
Use Google `events.insert`.

This endpoint:
- creates an event
- is a `POST` request to `/calendar/v3/calendars/{calendarId}/events`
- supports using `primary` as the logged-in user’s primary calendar
- supports attendee and conference-related options citeturn482398search1

### Meaning for the product
This is ideal for:
- final appointment creation after confirmation
- writing booking details into the selected calendar
- linking staff/resource schedules to the appointment

## 5.3 Optional supporting operations
In practice, the adapter will also usually need:
- event read
- event update
- event delete
- calendar list
- push/sync strategy later

Google’s overview confirms that the API is REST-based and exposes calendars, calendar lists, and events as core resources. citeturn482398search7

---

# 6. Suggested Internal API for the Calendar Adapter

A first clean provider-neutral interface could look like this:

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

## 6.1 `search_slots(request)`
Purpose:
- return real, offerable appointment slots

Typical inputs:
- service type
- duration
- date window
- daypart preference
- timezone
- candidate calendars/resources

Typical output:
- ranked slot list

## 6.2 `hold_slot(request)`
Purpose:
- create a temporary reservation in the platform state

### Important note
Google Calendar itself does not provide a universal “slot hold” abstraction.  
So in most designs, the **hold** should be owned by the platform/state layer, not by Google Calendar itself.

## 6.3 `create_booking(request)`
Purpose:
- create the final appointment in Google Calendar

## 6.4 `update_booking(request)`
Purpose:
- reschedule or edit the event

## 6.5 `cancel_booking(request)`
Purpose:
- remove or mark the event cancelled

---

# 7. Example Request / Response Shapes

## 7.1 Example internal slot search request

```json
{
  "tenant_id": "lekab-demo",
  "customer_id": "C-100245",
  "service_type": "onsite_service_visit",
  "duration_minutes": 60,
  "date_window_start": "2026-04-01T00:00:00+02:00",
  "date_window_end": "2026-04-10T23:59:59+02:00",
  "preferred_daypart": "afternoon",
  "timezone": "Europe/Berlin",
  "resource_candidates": [
    "tech-team-1@example.com",
    "tech-team-2@example.com"
  ],
  "max_slots": 5
}
```

## 7.2 Example internal slot search response

```json
{
  "slots": [
    {
      "slot_id": "SLOT-1",
      "start": "2026-04-02T13:00:00+02:00",
      "end": "2026-04-02T14:00:00+02:00",
      "resource_id": "tech-team-1@example.com",
      "score": 0.94
    },
    {
      "slot_id": "SLOT-2",
      "start": "2026-04-03T15:00:00+02:00",
      "end": "2026-04-03T16:00:00+02:00",
      "resource_id": "tech-team-2@example.com",
      "score": 0.91
    }
  ]
}
```

## 7.3 Example internal booking request

```json
{
  "customer_id": "C-100245",
  "slot_id": "SLOT-1",
  "calendar_target": "tech-team-1@example.com",
  "title": "Wallbox service visit",
  "description": "Booked via LEKAB Appointment Agent",
  "attendees": [
    {
      "email": "customer@example.com",
      "display_name": "Eva Nilsson"
    }
  ],
  "timezone": "Europe/Berlin"
}
```

---

# 8. Booking Flow with Google Calendar

A practical booking flow should work like this:

## Step 1
The Orchestrator receives a request to schedule an appointment.

## Step 2
The Orchestrator asks the customer/contact layer for customer context.

## Step 3
The Orchestrator sends a normalized `search_slots` request to the Calendar Adapter.

## Step 4
The Google Calendar Adapter calls `freeBusy.query` to inspect availability across one or more calendars. citeturn482398search0

## Step 5
The adapter returns normalized candidate slots.

## Step 6
The Orchestrator offers a small set of real choices to the customer via LEKAB.

## Step 7
The customer selects one option.

## Step 8
The platform performs a recheck if needed, then calls `create_booking`.

## Step 9
The Google Calendar Adapter creates the final event via `events.insert`. citeturn482398search1

## Step 10
The Orchestrator stores the booking reference, updates CRM/customer state, and sends confirmation.

---

# 9. Where the Customer Data Should Come From

This is the second major design question.

The person booking the appointment is a **customer/contact**, not a calendar resource.

That means we need to separate two worlds:

## World A – scheduling resources
Examples:
- advisors
- technicians
- clinics
- rooms
- store desks
- service teams

These belong in the scheduling/calendar world.

## World B – customer/contact identity
Examples:
- mobile number
- email
- name
- language
- contract/account number
- consent flags
- region
- CRM reference

These belong in the customer/contact world.

### Key rule
Do **not** treat Google Calendar as the system of record for customer identity.

---

# 10. Does Google Have an Address Book?

## Yes — but not inside Google Calendar
Google has a contact/address-book capability through the **People API**.

The People API allows reading and managing:
- the authenticated user’s contacts
- private contacts
- “Other contacts”
- and, in Google Workspace scenarios, domain profile/domain contact data where permitted. citeturn383059search3turn383059search7

### Relevant People API methods
- `people.connections.list` → list contacts of the authenticated user citeturn383059search0
- `people.searchContacts` → search the authenticated user’s contacts citeturn383059search1

### Important details
`people.connections.list`:
- can be used for full or incremental contact sync
- supports sync tokens
- sync tokens expire after 7 days citeturn383059search0

`people.searchContacts`:
- searches the authenticated user’s grouped contacts
- only uses the `CONTACT` source by default
- requires a warmup request with an empty query before searching to refresh cache state citeturn383059search1

---

# 11. Recommended Customer Data Strategy for Google-Based Environments

Here is the practical answer to your question.

## 11.1 Option A — Best practice
Use a **platform customer/contact service** as the source of truth.

This service stores:
- customer identity
- mobile number
- email
- language
- consent
- external references
- CRM link if available
- LEKAB contact link if available
- optional Google People contact link

### Why this is best
Because then:
- Google Calendar handles scheduling
- LEKAB handles messaging/workflows
- the platform handles customer identity

This is the cleanest and strongest product design.

---

## 11.2 Option B — Google People API as contact source
This can work if:
- the environment is Google Workspace-heavy
- the relevant contacts are already maintained in Google Contacts
- the tenant wants low complexity at MVP stage

### But:
This is weaker than a real CRM/customer registry for external customer journeys.

Why?
Because Google Contacts are mainly personal/workspace contact records, not a full customer-process system.

---

## 11.3 Option C — LEKAB Addressbook as messaging contact layer
This is actually very interesting for your platform strategy.

Use:
- platform customer/contact service as master
- sync needed messaging addresses and tags into LEKAB addressbook
- optionally sync or enrich from Google People when useful

### Then the role split becomes:
- Google Calendar = scheduling backend
- LEKAB Addressbook = messaging target/contact segmentation layer
- platform contact service = customer master

This matches your broader messaging platform idea very well.

---

## 11.4 Option D — No persistent address book
The system just uses:
- mobile number from inbound message
- name/email typed by customer
- booking record stored in platform DB only

### This is acceptable only for:
- very small MVPs
- demo systems
- lightweight booking flows
- low governance scenarios

It is not ideal for a serious product.

---

# 12. Architecture Recommendation

## Recommended architecture for Google-based customers

```text
Customer
  |
  v
LEKAB RCS / SMS
  |
  v
Appointment Orchestrator
  |               |                  |
  |               |                  |
  v               v                  v
Customer/Contact  Google Calendar    LEKAB Adapter
Service           Adapter            (Messaging + Addressbook)
  |
  +--> optional Google People sync
```

## Explanation
- The Orchestrator never depends directly on Google Contacts semantics
- The customer/contact service resolves identity
- The Google adapter resolves availability and booking
- LEKAB handles conversation delivery and workflow callbacks

This gives you the cleanest reusable platform design.

---

# 13. Practical Decision Matrix

## If Microsoft CRM exists
Use Microsoft CRM / Dataverse as the customer master.

## If Google Calendar exists but no CRM exists
Use a platform customer store, optionally enriched by Google People contacts.

## If Google Workspace is the dominant ecosystem
Allow Google People API as an import/sync source, but do not make it the only source of truth for external customer booking.

## If LEKAB messaging segmentation matters strongly
Mirror relevant customer contact data into LEKAB Addressbook for targeting, routing, and workflow reuse.

---

# 14. Risks and Limits

## 14.1 Google Calendar is not a CRM
It is excellent for:
- availability
- events
- attendees
- scheduling logic support

It is not ideal for:
- customer lifecycle state
- consent master data
- contract/account ownership
- segmentation logic for customer operations

## 14.2 Google People API is user/contact-centric
It is useful, but it is not automatically a full enterprise customer database.

## 14.3 Slot hold logic
Google Calendar alone is not enough for robust temporary holds in a platform workflow.
The platform should own hold state.

## 14.4 External customer scale
If the product is meant for utilities, municipalities, healthcare, telecom, field service, or large appointment operations, a dedicated customer/contact master layer is the safer long-term design.

---

# 15. Recommended MVP Decision

For the first real LEKAB Appointment Agent MVP, use this rule:

## Google path recommendation
- **Calendar source:** Google Calendar API
- **Customer source:** platform customer/contact service
- **Optional enrichment:** Google People API
- **Messaging contact layer:** LEKAB Addressbook sync where useful

### Why this is the best MVP choice
Because it is:
- clean
- scalable
- platform-friendly
- not over-coupled to Google
- compatible with the Microsoft path later

---

# 16. Open Questions

1. Is Google Calendar only for staff/resource calendars, or also for customer-facing shared calendars?
2. Do we need support for rooms/resources in addition to people?
3. Will external customers already exist in a platform DB or CRM?
4. Should Google People be a live lookup source or only an import/sync source?
5. Which fields must be mandatory in the platform customer master?
6. Should LEKAB Addressbook be mandatory for all bookable customers, or only for messageable customers?
7. Do we need attendee emails in Google events for all bookings?
8. How do we handle customers who only have a mobile number and no email?
9. Which system owns booking reference generation?

---

# Final Recommendation

The clean design is this:

- **Google Calendar** = availability and appointment booking
- **Google People API** = optional contact/address-book source
- **Platform Customer/Contact Service** = customer master record
- **LEKAB Addressbook** = messaging-target/contact-sync layer
- **Appointment Orchestrator** = workflow brain

That gives you a reusable product architecture that works well today with Google and can later align cleanly with Microsoft CRM environments too.
