# Release Notes v1.3.10 (EN)

## Summary
Version `v1.3.10` introduces `Dashboard+`, a simplified real-mode demonstration dashboard for sales users. It keeps the existing cockpit and journey mechanics, but removes the detailed dashboard controls from the primary presenter view.

## Highlights
- Added top-menu entry `Dashboard+` before the existing `Dashboard`.
- Main cockpit route now opens `Dashboard+` as the first-screen experience.
- Kept the existing `Dashboard` unchanged for deeper operator and diagnostic use.
- Simplified the Dashboard+ Operator Panel to:
  - Scenario
  - fixed Scenario Mode `Real`
  - Selected Address
  - manual Phone Number
  - Appointment Type
- Added radio-based contact target switching between address phone and manual mobile number.
- Added validation that blocks Real mode send when manual phone mode is selected without a mobile number.
- Routed manual mobile number into the scenario runner so Real mode outbound sends use the chosen target.
- Kept `Messages and Customer Journey` behavior aligned with the existing cockpit.

## Safety
- No Real mode send when phone mode has an empty mobile number.
- Manual phone input is capped at `40` characters.
- Existing address-based send behavior is preserved.
- Silence threshold default remains `1300 ms`.

## Documentation
- User Guide updated in DE and EN.
- Demo Guide updated in DE and EN with at least 3 sales-ready story scenarios.
- Admin Guide updated in DE and EN.
- Release Notes updated in DE and EN.
