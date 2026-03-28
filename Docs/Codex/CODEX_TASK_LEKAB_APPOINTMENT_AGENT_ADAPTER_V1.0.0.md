# CODEX_TASK_LEKAB_APPOINTMENT_AGENT_ADAPTER_V1.0.0

## Title
Build the LEKAB Adapter Service for the Appointment Agent

## Objective
Implement a production-ready LEKAB Adapter Service for the Appointment Scheduling Agent.
The adapter must connect the Appointment Orchestrator / Communication Bus with the documented LEKAB APIs for Authentication, Messaging Workflow Dispatch, Addressbook synchronization, and callback ingestion.

## Business Context
LEKAB must be treated as a workflow-aware integration service, not as a thin send-message gateway.
The uploaded docs show:
- OAuth token handling via `/token` and `/revoke`
- workflow template discovery via `/listsavedjobs`
- workflow execution via `/startsavedjob`
- POST callbacks for `JOB_START`, `JOB_ASSIGN`, and `JOB_FINISH`
- addressbook sync and contact/tag APIs

## Scope
### In Scope
- auth client
- dispatch client
- addressbook client
- callback endpoint
- event mapping
- config and secret handling
- retries, timeouts, idempotency, observability
- tests
- admin/developer docs
- standardized test runbook

### Out of Scope
- full calendar provider implementation
- full CRM provider implementation
- frontend work
- full conversational AI logic

## Repo / Structure Rules
Recommended placement:
- `docs/codex/CODEX_TASK_LEKAB_APPOINTMENT_AGENT_ADAPTER_V1.0.0.md`
- `docs/codex/V1_TEST_RUNBOOK_LEKAB_APPOINTMENT_AGENT_ADAPTER.md`
- `docs/admin/lekab_adapter_service.md`
- `src/.../integrations/lekab/`
- `tests/unit/...`
- `tests/integration/...`

Do not commit runtime artifacts, logs, exports, or generated summaries.

## Architecture Goal
```text
Appointment Orchestrator
        |
        v
Communication Bus / Domain Events
        |
        v
LEKAB Adapter Service
   |        |         |
   |        |         +--> Addressbook Client
   |        +------------> Dispatch Client
   +---------------------> Auth Client
        |
        v
Callback Ingestion / Event Mapper
        |
        v
Internal Domain Events
```

## Required LEKAB API Coverage

### 1. Authentication API
Implement support for:
- `POST /auth/api/v1/token`
- `POST /auth/api/v1/revoke`

Implement:
- token fetch
- token cache with expiry margin
- safe refresh
- revoke support
- auth error classification

### 2. Dispatch API
Implement support for:
- `GET/POST /dispatch/api/listsavedjobs`
- `GET/POST /dispatch/api/startsavedjob`

Support common parameters:
- `jobid`
- `jobname`
- `message`
- `tonumbers`
- `toaddressbookcustomtagfilter`
- `toaddressbooktagfilterjson`
- `toaddressbooksavedtagfilters`
- `toaddressbookgroups`
- `excludenumbers`
- `excludecustomtagfilter`
- `excludetagfilterjson`
- `tokeep`
- `responsegoal`
- `scheduledstart`

Use GenericMonitoredMessage as the first appointment-oriented workflow model.

### 3. Callback Handling
Implement inbound POST callback handling for:
- `JOB_START`
- `JOB_ASSIGN`
- `JOB_FINISH`

Map to internal events:
- `lekab.job.started`
- `lekab.job.assigned`
- `lekab.job.finished`

Add:
- schema validation
- idempotency
- duplicate suppression
- correlation mapping
- async publish into bus

### 4. Addressbook API
Implement support for:
- `/listaddressbooks`
- `/listtags`
- `/getcontact`
- `/findcontactbyaddress`
- `/contacts/createdafter/...`
- `/contacts/modifiedafter/...`
- `/addcontact`
- `/updatecontact`
- `/deletecontact`

Add helpers for:
- contact upsert
- address normalization
- tag normalization
- delta sync
- safe delete

Do not enable `deleteallcontacts` by default.

## Internal Services
Define internal classes/interfaces:
- `LekabAuthClient`
- `LekabDispatchClient`
- `LekabAddressbookClient`
- `LekabCallbackHandler`
- `LekabAdapterService`

## Internal Domain Events
Recommended:
- `lekab.auth.token.refreshed`
- `lekab.dispatch.jobs.listed`
- `lekab.dispatch.job.started`
- `lekab.dispatch.job.start.failed`
- `lekab.addressbook.contact.upserted`
- `lekab.callback.received`
- `lekab.job.started`
- `lekab.job.assigned`
- `lekab.job.finished`
- `lekab.callback.duplicate_ignored`

## Configuration
Required config keys:
- `LEKAB_BASE_URL`
- `LEKAB_AUTH_BASE_URL`
- `LEKAB_ADDRESSBOOK_BASE_URL`
- `LEKAB_DISPATCH_BASE_URL`
- `LEKAB_AUTH_MODE`
- `LEKAB_USERNAME`
- `LEKAB_PASSWORD`
- `LEKAB_API_KEY`
- `LEKAB_TOKEN_REFRESH_SKEW_SECONDS`
- `LEKAB_HTTP_TIMEOUT_SECONDS`
- `LEKAB_MAX_RETRIES`
- `LEKAB_RETRY_BACKOFF_MS`
- `LEKAB_CALLBACK_PATH`
- `LEKAB_CALLBACK_SHARED_SECRET`
- `LEKAB_DEFAULT_ADDRESSBOOK_ID`
- `LEKAB_ENABLE_CONTACT_UPSERT`
- `LEKAB_ENABLE_CONTACT_DELETE`
- `LEKAB_ENABLE_DELETE_ALL_CONTACTS=false`

Project carryover:
- preserve artifact policy
- preserve licensing guardrails
- preserve docs/help quality rules
- keep project default silence threshold 1300 ms unchanged if any shared voice-adjacent module is touched

## Security Requirements
- no hardcoded credentials
- redact secrets and PII in logs
- HTTPS only
- replay-safe callback handling
- least-privilege credentials
- documented key rotation

## Observability
Implement:
- structured logs
- trace/correlation ids
- endpoint latency metrics
- callback counters
- retry/failure counters
- duplicate callback counters
- safe diagnostic mode

## Error Handling
Classify:
- validation errors
- auth errors
- permission errors
- upstream 4xx
- upstream 5xx
- timeout/network errors
- duplicate callback errors
- parse/mapping errors

Rules:
- no silent failures
- retries only for retryable failures
- no destructive auto-retries on delete operations

## Suggested Package Layout
```text
src/<project>/integrations/lekab/
  config.py
  models.py
  exceptions.py
  auth_client.py
  dispatch_client.py
  addressbook_client.py
  callback_handler.py
  event_mapper.py
  adapter_service.py
  validators.py
  serializers.py
```

## Implementation Examples
### Token request
```python
payload = {
    "grant_type": "client_credentials",
    "client_id": username,
    "client_secret": password,
}
```

### Start saved job
```python
payload = {
    "jobid": 352872112744058883,
    "jobname": "Appointment Offer",
    "message": "Available slots: 1) Mon 10:00 2) Tue 14:00",
    "toaddressbooksavedtagfilters": ["AppointmentEligible"],
}
```

### Add contact
```python
payload = {
    "addressbookid": "925406391282233345",
    "contactid": "crm-contact-123",
    "contactname": "Eva Nilsson",
    "companyname": "Example Company",
    "addresses": [
        {"addresstype": "SMS", "address": "46701234567"},
        {"addresstype": "VOICE", "address": "46701234567"},
        {"addresstype": "EMAIL", "address": "eva.nilsson@example.com"},
    ],
    "tags": [
        {"tagtype": "Language", "tag": "EN"},
        {"tagtype": "Region", "tag": "Stockholm"},
    ],
}
```

### Callback mapping
```python
if payload.eventtype == "JOB_START":
    publish("lekab.job.started", ...)
elif payload.eventtype == "JOB_ASSIGN":
    publish("lekab.job.assigned", ...)
elif payload.eventtype == "JOB_FINISH":
    publish("lekab.job.finished", ...)
```

## Documentation Requirements
Create `docs/admin/lekab_adapter_service.md` covering:
- architecture
- supported endpoints
- config/env vars
- callback setup
- auth modes
- payload examples
- saved job preparation guidance
- troubleshooting
- security notes
- test execution

## Test Requirements
### Unit Tests
- token fetch success/failure
- cache refresh behavior
- list jobs parsing
- start job validation
- callback validation
- callback deduplication
- address normalization
- tag normalization
- upsert decision logic
- error classification

### Integration Tests
- mock auth token exchange
- mock list saved jobs
- mock start saved job
- mock callback handling
- mock add/update/delete contact lifecycle
- retry behavior
- timeout behavior
- redaction/logging behavior

### Non-Functional
- duplicate callback idempotency
- correlation propagation
- no secret leakage

## Acceptance Criteria
Complete only if:
1. auth/dispatch/addressbook clients exist and are wired through a stable adapter facade
2. callback endpoint maps `JOB_START`, `JOB_ASSIGN`, `JOB_FINISH`
3. list-jobs, start-job, contact upsert, contact lookup, and delete-contact are supported
4. retries, timeouts, and redaction are implemented and tested
5. config is fully externalized
6. docs are present and non-empty
7. test runbook exists
8. automated tests pass
9. no runtime artifacts are committed
10. licensing guardrails are respected

## Licensing & Commercialization Guardrails
- prefer MIT / Apache-2.0 / BSD dependencies
- avoid GPL / AGPL in the core
- isolate any copyleft dependency outside the core if ever needed
- explicitly flag license risks
- avoid unnecessary dependency sprawl

## Risks / Notes
- callbacks are configured per system user, not per job
- latest job-type settings apply when starting saved jobs
- GMM/GMA parameter restrictions matter
- destructive addressbook operations must stay tightly controlled
- keep `deleteallcontacts` disabled by default
- address types support SMS / VOICE / EMAIL / APP

## Deliverables
Codex must produce:
1. LEKAB adapter implementation
2. tests
3. admin/developer documentation
4. release note delta if applicable
5. standardized test runbook
6. SUMMARY artifact after test run (runtime artifact, not committed)

## Definition of Done
Done means:
- code merged cleanly
- docs present
- tests passing
- no artifact leakage
- adapter ready for integration by the Appointment Orchestrator and Communication Bus
