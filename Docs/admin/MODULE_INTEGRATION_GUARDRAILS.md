# Module Integration Guardrails

Version: v1.1.0-patch5
Audience: Admin
Language: EN

## Technical baseline

Shared contracts and stable routes are the technical baseline.

New patches may extend behavior, but must not break module cooperation.

## Module responsibilities

### Demo / Monitoring UI

- presentation
- operator state switching
- visible action feedback
- demo and monitoring views
- dedicated Google Demo Control workspace

### Appointment Orchestrator

- workflow logic
- journey state transitions
- audit logic
- CRM preparation events

### Google Adapter

- Google-specific calendar operations
- live sync checks
- conflict detection
- booking-safe Google interaction

### Shared Domain

- contracts
- IDs
- models
- commands
- events
- stable payload shapes

### Settings / Config

- controlled runtime configuration
- visible non-secret runtime information
- no secret leakage to UI or logs

## Integration rules

- provider-specific logic must not leak into unrelated modules
- UI must not decide booking safety on its own
- UI may trigger Google demo actions, but booking-safe behavior still lives in the Google adapter
- Orchestrator must not embed Google API details
- Shared module changes must stay backward-safe inside the same minor line
- Docs routes must stay stable unless a new release line is intentional

## Route and version discipline

- use new route lines when behavior meaningfully changes
- do not keep redefining old route lines for new features
- README must show the current recommended route
- older lines may stay supported, but the current line must be explicit

## Integration consistency checklist

Every future patch must verify:

1. current recommended UI route is documented
2. current Google adapter route is documented
3. help and root endpoints reflect the current version
4. demo UI and Google adapter versions match intentionally
5. provider-specific logic stays inside the adapter
6. UI feedback does not fake backend success
7. tests cover the new route line
8. Docker smoke test points to the current recommended route
9. Google Demo Control remains a top-level cockpit page
