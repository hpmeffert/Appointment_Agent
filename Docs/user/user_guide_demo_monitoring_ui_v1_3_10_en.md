# Appointment Agent User Guide v1.3.10 (EN)

## Scope
Version `v1.3.10` introduces `Dashboard+`, a simplified real-mode cockpit view for sales demonstrations. It keeps the proven `Messages and Customer Journey` area, but reduces the operator panel to the controls a presenter needs in front of a customer.

## What Changed
- `Dashboard+` is now the first top-menu entry, before the existing `Dashboard`.
- The existing `Dashboard` remains available for detailed operator, monitoring, guided-demo, and protocol views.
- `Dashboard+` always runs the scenario in `Real` mode.
- The operator can choose whether the outbound message target comes from the selected address or from a manually entered mobile number.
- If manual phone mode is selected and no mobile number is entered, the cockpit shows an error and blocks the real send.
- The release remains additive and non-breaking for protected `v1.x` behavior.

## Dashboard+ Operator Panel
1. Select a `Scenario`.
2. Confirm that `Scenario Mode` shows `Real`.
3. Choose the contact target:
   - `Selected Address`: uses the phone number stored on the selected address record.
   - `Phone Number`: uses the manually entered mobile number.
4. Select the `Appointment Type`.
5. Start the demo.

## Contact Target Rules
- Default target mode is `Selected Address`.
- Address mode keeps the previous behavior: the selected address phone number is used for sending.
- Phone mode overrides only the message target phone number. The selected address can still provide appointment and correlation context.
- Empty phone mode is rejected with a visible missing-mobile-number error.
- Manual phone input is limited to `40` characters.

## Messages And Customer Journey
The `Messages and Customer Journey` area behaves like before:
- It shows the live outbound prompt, reply suggestions, journey state, and slot/confirmation steps.
- In `Real` mode, reply buttons are read-only because the cockpit waits for the provider callback.
- Message monitor, RCS callback polling, and journey-state rendering continue to use the same underlying APIs.

## Safety Defaults
- Silence threshold default: `1300 ms`
- Manual phone input limit: `40` characters
- Scenario execution mode in Dashboard+: `Real`
- Existing detailed dashboard and message monitor remain available for troubleshooting.

## Typical Sales Demo Flow
1. Open `/ui/demo-monitoring/v1.3.10`.
2. Stay on `Dashboard+`.
3. Select the scenario, address or manual phone target, and appointment type.
4. Start the demo.
5. Show that the outbound journey appears in `Messages and Customer Journey`.
6. Use the provider callback path or Message Monitor to show the customer response.
