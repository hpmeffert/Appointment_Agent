# Appointment Agent Admin Guide v1.3.10 (EN)

## Release Intent
`v1.3.10` adds `Dashboard+`, a simplified real-mode sales demonstration surface for the Appointment Agent Cockpit.

The release is additive. The existing `Dashboard`, `Message Monitor`, `Reports`, `Monitoring`, `Settings`, `Settings -> RCS`, `Google Demo Control`, `Reminder`, `Addresses`, and `Help` entries remain available.

## Admin-Relevant Changes
- New top-menu entry: `Dashboard+`, placed before `Dashboard`.
- Main demo route `/ui/demo-monitoring/v1.3.10` now opens `Dashboard+` first.
- `Dashboard+` operator panel contains:
  - `Scenario`
  - fixed `Scenario Mode = Real`
  - address target radio plus `Selected Address`
  - phone target radio plus manual phone input
  - `Appointment Type`
  - a single real-demo start action
- Manual phone mode requires a non-empty phone number.
- Manual phone input is capped at `40` characters.
- Scenario runner accepts `contact_target_mode` and `manual_phone_number` for Dashboard+ real-mode sends.

## Runtime Contract
Dashboard+ stores its contact-target state in scenario-context metadata:

```json
{
  "dashboard_plus": {
    "contact_target_mode": "address",
    "manual_phone_number": ""
  }
}
```

Supported `contact_target_mode` values:
- `address`: use the selected address phone number
- `phone`: use `manual_phone_number`

## Verification Checklist
1. Open `/ui/demo-monitoring/v1.3.10` and verify `Dashboard+` is active first.
2. Verify the top menu order is `Dashboard+`, `Dashboard`, then the existing entries.
3. Run a real scenario with contact target `Selected Address`.
4. Run a real scenario with contact target `Phone Number` and a valid mobile number.
5. Select `Phone Number`, leave the field empty, and verify the error blocks sending.
6. Confirm `Messages and Customer Journey` still renders the same journey surface.
7. Confirm `/api/demo-monitoring/v1.3.9/help` and `/api/demo-monitoring/v1.3.10/help` return version `v1.3.10`.

## Operational Defaults
- `silence_threshold_ms = 1300`
- Dashboard+ scenario mode: `Real`
- Manual phone limit: `40` characters
- Existing v1.3.9 API base remains the compatibility API route; visible display version is `v1.3.10`.

## Risk Notes
- Dashboard+ must not remove the old Dashboard. It is a simplified additional view.
- Real-mode buttons remain read-only inside the journey area because provider callbacks are the source of truth.
- Do not commit generated scenario artifacts; keep local runtime artifacts out of release commits.
