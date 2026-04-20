# Demo Monitoring UI v1.3.8

## What this release adds

This release adds the **Reply-to-Action Engine** to the combined demo shell.

That means the platform does not only show that a customer reply arrived. It also shows:

- what the reply most likely means
- which internal appointment action would be requested
- whether this interpretation is safe, ambiguous, or needs review

## Main routes

- Combined demo UI: `/ui/demo-monitoring/v1.3.8`
- Standalone reminder cockpit: `/ui/reminder-cockpit/v1.3.8`
- LEKAB monitor API: `/api/lekab/v1.3.8/monitor`

## Important parameters

- `normalized_event_type`
  This tells you what kind of communication event happened. Examples are `message.delivered`, `message.failed`, and `message.reply_received`.
- `reply_intent`
  This is the first business meaning the parser sees in the reply. Examples are `cancel`, `confirm`, `reschedule`, or `appointment_next_week`.
- `reply_datetime_candidates`
  This is a list of dates or times found in the reply text.
- `action_candidate`
  This is the internal appointment action that the system would ask for next.
- `interpretation_state`
  This says how safe the interpretation is. Possible values are `safe`, `ambiguous`, and `review`.
- `interpretation_confidence`
  This is a simple confidence score between `0.0` and `1.0`.

## What operators should look at

1. Open `Message Monitor`.
2. Select the latest inbound reply.
3. Read `Reply Intent`.
4. Read `Action Candidate`.
5. Check `Interpretation State`.

If the state is `safe`, the next platform action is clear.

If the state is `ambiguous` or `review`, an operator should double-check before a later automated step acts on it.
