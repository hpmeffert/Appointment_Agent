# Demo Guide Demo Monitoring UI v1.2.0

Version: v1.2.0
Audience: Demo
Language: EN

## Presenter flow

1. “Here the customer sees a reminder message.”
2. “Now I click Reschedule.”
3. “The system loads real next slots from the booking backend.”
4. “Now I click one slot.”
5. “The slot is now temporarily reserved for this journey.”
6. “Now I click Confirm.”
7. “Before booking, the system checks Google Calendar live once more.”
8. “If the slot is still free, the booking succeeds.”
9. “If not, the system shows alternatives instead of failing silently.”

## Aha lines

- “This is not just UI. The click actually drives the booking logic.”
- “The slot is temporarily reserved and then checked live again.”
- “That is how the system safely handles parallel booking attempts.”

## Demo preparation

1. Open `/ui/demo-monitoring/v1.2.0`
2. Pick `Simulation` or `Test`
3. Use Google Demo Control for generate/reset
4. After the demo, clean the test calendar again
