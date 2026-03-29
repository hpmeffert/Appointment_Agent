# Demo Monitoring UI v1.1.0 Patch 6

Version: v1.1.0-patch6
Audience: Admin
Language: EN

## What is new

`Google Demo Control` now supports:

- `from_date`
- `to_date`
- `appointment_type`

This makes demo generation more controlled and more realistic.

## Main parameters

- `from_date`
  The first day the demo generator may use.

- `to_date`
  The last day the demo generator may use.

- `appointment_type`
  The content template that defines the appointment title and wording.
  Supported values are `dentist`, `wallbox`, `gas_meter`, and `water_meter`.

- `count`
  How many appointments should be generated in the selected date range.

## Important rule

The selected date range is validated.

- `from_date` must be before or equal to `to_date`
- the maximum range follows the configured booking window
