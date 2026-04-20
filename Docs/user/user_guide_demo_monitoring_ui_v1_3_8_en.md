# User Guide v1.3.8

## What you can do now

You can now use the demo to show how a customer reply becomes a business action candidate.

Examples:

- `Please cancel the appointment`
- `Next week works for me`
- `The first one`
- `05 May, 16:00`

## Where to open it

- Main demo: `/ui/demo-monitoring/v1.3.8`
- Reminder-only entry: `/ui/reminder-cockpit/v1.3.8`

## Simple explanation

The system now does four steps:

1. receive the reply
2. normalize it into a safe internal communication event
3. interpret the likely user intention
4. prepare the next internal appointment action

## Main fields in the Message Monitor

- `Reply Intent`
  The likely meaning of the reply.
- `Action Candidate`
  The internal action the platform would request next.
- `Interpretation State`
  `safe` means the meaning is clear. `ambiguous` means more than one meaning is possible. `review` means a human should inspect it.
- `Date/Time Candidates`
  Dates or times found in the reply text.
