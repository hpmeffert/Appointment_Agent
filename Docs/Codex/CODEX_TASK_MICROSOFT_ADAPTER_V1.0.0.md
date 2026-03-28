
# CODEX_TASK_MICROSOFT_CRM_GRAPH_ADAPTER_V1.0.0

## Title
Build Microsoft CRM / Microsoft Graph Adapter for Appointment Agent

## Objective
Implement a production-ready adapter for:
- Microsoft Graph (Calendar, Users)
- Microsoft Dynamics 365 / CRM (Customer data)

This adapter must integrate with:
- Appointment Orchestrator
- Communication Bus
- Customer Contact Service
- LEKAB Adapter

---

## Architecture Role

```text
Appointment Orchestrator
        |
        v
Communication Bus
        |
        v
Microsoft Adapter
   |              |
   v              v
Graph Calendar   CRM / Dynamics
```

---

## Scope

### In Scope
- Microsoft Graph Calendar integration
- CRM customer lookup and write-back
- Booking creation, update, cancel
- Availability (free/busy)
- Event mapping
- Tests, docs, runbook

### Out of Scope
- Full Dynamics customization
- UI
- Identity platform setup

---

## Microsoft Graph Calendar

### APIs
- `/me/calendar/getSchedule` (availability)
- `/me/events` (create event)
- `/me/events/{id}` (update/delete)

### Capabilities
- availability lookup
- booking creation
- attendee handling
- timezone handling

---

## CRM / Dynamics Capabilities

### Functions
- lookup customer by phone/email
- load account/contact
- write booking result
- append activity/log

---

## Internal Interface

```python
class MicrosoftAdapter:
    def search_slots(self, request): ...
    def create_booking(self, request): ...
    def update_booking(self, request): ...
    def cancel_booking(self, request): ...
    def resolve_customer(self, request): ...
    def write_back(self, request): ...
```

---

## Domain Events

Inbound:
- `channel.message.received`
- `customer.lookup.requested`

Outbound:
- `calendar.slots.found`
- `calendar.booking.created`
- `crm.customer.resolved`
- `crm.booking.updated`

---

## Configuration

- `MS_GRAPH_BASE_URL`
- `MS_GRAPH_CLIENT_ID`
- `MS_GRAPH_CLIENT_SECRET`
- `MS_GRAPH_TENANT_ID`
- `MS_GRAPH_SCOPE`
- `MS_TIMEOUT`
- `MS_RETRIES`

---

## Security
- OAuth2 client credentials
- secure token handling
- no secrets in logs

---

## Tests

### Unit
- token fetch
- slot mapping
- booking mapping

### Integration
- mocked Graph API
- mocked CRM API

---

## Acceptance Criteria
- adapter works with orchestrator
- booking lifecycle works
- customer lookup works
- tests pass
- docs exist

---

## Deliverables
- adapter code
- tests
- docs
- runbook

---

## Definition of Done
- production-ready adapter
- integrated with bus
- no security issues
