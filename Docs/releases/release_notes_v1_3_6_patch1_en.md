# Release Notes v1.3.6-patch1

Version: v1.3.6-patch1
Language: EN

## Summary

`v1.3.6-patch1` is a combined documentation release.

It joins:
- the incident-style demo cockpit from `v1.2.1-patch4`
- the reminder and Google demo story from `v1.3.6`

## What changed

- added a new combined menu item for the reminder and Google demo
- kept the patch-4 cockpit style stable
- added simple docs for the combined operator flow
- explained the important parameters in plain language
- added three short demo stories
- kept the version visible in the header and help text

## Important parameters

- `silence_threshold_ms`
  Default is `1300 ms`.
- `reminder_offsets_minutes`
  The reminder times before the appointment.
- `google_calendar_id`
  The Google calendar used for the linked appointment.
- `appointment_type`
  The type of appointment shown in the demo.
- `job_status`
  The state of a reminder job.

## What is in this release

- the incident-style cockpit now has one extra menu item for the `v1.3.6` reminder and Google demo
- the user guide explains the combined cockpit in simple words
- the demo guide includes three short story scenarios
- the admin guide explains the new combined menu item and the main parameters
- the release notes point to the new combined release line

## Verification

- header shows `v1.3.6-patch1`
- help shows `v1.3.6-patch1`
- the cockpit contains the new reminder / Google menu item
- the docs explain the parameter names in simple language

