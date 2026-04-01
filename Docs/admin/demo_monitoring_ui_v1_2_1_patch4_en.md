# Admin Guide Demo Monitoring UI v1.2.1-patch4

Version: v1.2.1-patch4
Audience: Admin
Language: EN

## Patch goal

`v1.2.1-patch4` keeps the stable Incident-style shell and improves demo control.

The main goal is simple:
- make the product easier to present live
- keep the runtime behavior stable
- explain the platform more clearly inside the UI itself

## Main architecture idea

The cockpit is still only the front door. The real platform is modular:
- `LEKAB Adapter`
  Messaging adapter for RCS and SMS style traffic.
- `Appointment Orchestrator`
  Journey and decision layer.
- `Google Adapter`
  Slot search, hold, create, reschedule, cancel, and conflict checks.
- `Service Bus`
  Internal contract layer between modules.

Patch 4 adds a stronger presentation layer on top of that architecture.

## New patch 4 elements

- `guided_demo`
  Payload-driven story engine for presenters.
- `guidedMode`
  UI state for `free` or `guided`.
- `guidedStepIndex`
  Current step in the presenter story.
- `autoDemoRunning`
  Tells the UI whether the guided story advances automatically.
- `platform_visibility`
  Structured visibility block for channels, integrations, and AI.

## Why payload-driven guidance matters

The guided story is not hardcoded in ten separate UI conditions.

Instead, the payload defines:
- `step_id`
- `title`
- `description`
- `ui_focus`
- `action`

That matters because:
- docs and UI can stay aligned
- story order can change without rewriting all render logic
- future releases can extend the story engine safely

## Main UI state fields

- `page`
  Current shell page such as `dashboard` or `monitoring`.
- `scenarioId`
  Active business story.
- `stepIndex`
  Current scenario step in the transcript flow.
- `guidedMode`
  Presenter mode state.
- `guidedStepIndex`
  Current guided story step.
- `autoDemoRunning`
  Timer-driven walkthrough state.
- `selectedAction`
  Current reply action selected by the operator.
- `selectedSlot`
  Current slot label selected by the operator.
- `holdStatus`
  Hold lifecycle state such as `idle`, `active`, `released`, or `consumed`.

## Important operator-facing parameters

- `slot_hold_minutes`
  Duration of a temporary slot reservation.
  Bigger value means more protection, but also longer temporary blocking.
- `auto_run_interval_ms`
  Speed of the automatic guided story.
  Lower value means faster autoplay.
- `googleMode`
  `simulation` avoids real writes.
  `test` allows writes to the configured test calendar.
- `selectedAppointmentType`
  Defines which business example data the Google demo should use.

## LEKAB settings backend in patch 4

Patch 4 keeps the `v1.2.1-patch4` LEKAB route line:
- `/api/lekab/v1.2.1-patch4/settings/rcs`
- `/api/lekab/v1.2.1-patch4/settings/rcs/validate`
- `/api/lekab/v1.2.1-patch4/settings/rcs/test-connection`

Important behavior:
- secrets stay masked
- blank password fields keep the saved secret
- readiness stays visible in the UI
- the settings page is still SQLite-backed for local prototype use

## Documentation rule in this patch

Patch 4 docs should explain the system like this:
- simple enough for a motivated 16-year-old to follow
- technical enough that an operator or admin can still use the parameters
- clear examples instead of vague wording

## Verification focus

For this patch, verify:
- dashboard route loads
- help and payload routes load
- guided demo data exists in the payload
- root and help show the new release version
- LEKAB patch-4 settings route loads
- smoke test points to patch-4 URLs

![Annotated cockpit overview](/docs/assets/screenshots/v1_2_1_patch4/cockpit-overview.svg)
![Annotated RCS settings page](/docs/assets/screenshots/v1_2_1_patch4/rcs-settings.svg)
