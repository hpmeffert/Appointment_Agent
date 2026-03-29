# Google Test Mode User Guide v1.1.0 Patch 1

Version: v1.1.0 Patch 1
Audience: User
Language: EN

## What you see in the UI

The demo now has a Google control box.

There you can choose:

- `Simulation`
- `Test`

You can also choose:

- a timeframe
- how many demo appointments to create
- whether you want to generate, delete, or reset demo data

## What the two modes mean

- `Simulation`
  The app behaves as if Google was connected, but no real Google Calendar entry is changed.

- `Test`
  The app uses the real Google Calendar from the local configuration.
  This mode can create and delete real demo events in that test calendar.

## What the buttons do

- `Prepare Demo Calendar`
  In this patch this uses the same safe generation path as `Generate Demo Appointments`.

- `Generate Demo Appointments`
  Creates realistic demo entries like dentist visits, maintenance checks, or consultations.

- `Delete Demo Appointments`
  Deletes only entries that were created by the Appointment Agent demo logic.

- `Reset Demo Calendar`
  First deletes demo-generated entries in the chosen timeframe, then creates a fresh clean set.

## Why the titles matter

Bad demo titles look fake.
Good demo titles make the calendar easy to understand live.

Example:

- `Dentist Appointment - Dr. Zahn (Check-up)`
- `Heating Maintenance - Annual Inspection`
- `Insurance Consultation - Policy Review`

## What the extra monitoring boxes mean

- `Google Test Mode`
  Shows whether live Google writes are active, which calendar is targeted, and what the last action did.

- `Manual Entry and Contact Linking`
  Shows how generated and manual calendar entries can later connect to customer contact data for SMS or RCS.
