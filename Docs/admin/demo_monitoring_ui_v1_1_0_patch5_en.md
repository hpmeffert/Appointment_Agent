# Demo Monitoring UI v1.1.0 Patch 5

Version: v1.1.0-patch5
Audience: Admin
Language: EN

## What changed

This release makes the Incident Demo cockpit the permanent UI standard.

The most important visible change is that `Google Demo Control` is now its own top menu item in the header.

That means Google demo actions are no longer mixed into the dashboard.

## Why this matters

A presenter can now explain the cockpit in simple words:

- Dashboard = business and story overview
- Monitoring = technical event view
- Settings = operator parameters
- Google Demo Control = calendar test and simulation actions
- Help = documentation

## Google Demo Control page

This page contains:

- current mode: `Simulation` or `Test`
- target calendar information
- timeframe selector
- vertical selector
- `Prepare Demo Calendar`
- `Generate Demo Appointments`
- `Delete Demo Appointments`
- `Reset Demo Calendar`
- visible success and error feedback
- a clear warning that `Test` writes to the real configured Google test calendar

## Important parameter explanations

- `mode`
  This decides whether Google actions are safe preview logic or real writes.
  `simulation` means no real Google calendar entries are created.
  `test` means the configured Google test calendar can be changed.

- `timeframe`
  This decides which date range the demo helper should use.
  `day` means today.
  `week` means the current week.
  `month` means the current month.

- `count`
  This decides how many demo appointments should be generated for the action.

- `vertical`
  This decides which business example is used for titles and descriptions.
  Examples are dentist, wallbox, and district heating.

## Permanent shell rule

Future UI work must reuse this shell.

Do not invent a second cockpit style unless there is explicit approval for a larger redesign.
