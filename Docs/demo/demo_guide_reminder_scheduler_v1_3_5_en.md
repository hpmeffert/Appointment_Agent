# Demo Guide Reminder Scheduler v1.3.5

Version: v1.3.5
Audience: Demo
Language: EN

## What this demo should show

This demo should show that the delivery layer is easy to explain:
- choose a channel
- check the validation outcome
- read the delivery result
- show the runtime health in simple words

Use this line:

- "The operator sees the delivery path, the checks, and the result in one view."

## Suggested screen order

1. Open `Dashboard`.
2. Show `Delivery`.
3. Switch the primary channel.
4. Open `Validation`.
5. Open `Results`.
6. Open `Channels`.
7. Open `Operator`.
8. End with `Help`.

## Story 1: Primary channel works

1. Open `Delivery`.
2. Show that `RCS/SMS` is active.
3. Explain that validation passes.
4. Open `Results` and point at the `sent` entry.

What to say:
- "This is the normal path. The first channel is ready, so the message goes out right away."

Why this matters:
- the operator sees a simple and fast delivery path
- the result is easy to explain

## Story 2: Validation blocks a bad target

1. Open `Delivery`.
2. Turn off all channels or lower the message length limit.
3. Open `Validation`.
4. Show the `blocked` outcome.

What to say:
- "The cockpit stops bad delivery before anything is sent."

Why this matters:
- the operator sees the problem early
- the team can explain the block in plain words

## Story 3: Fallback saves the delivery

1. Open `Delivery`.
2. Keep the primary channel off but allow fallback.
3. Open `Results`.
4. Point at the `fallback_sent` entry.

What to say:
- "If the first channel is not ready, the backup channel takes over."

Why this matters:
- the operator sees why the result changed
- the delivery still succeeds in a safe way

## Important parameters to explain

- `enabled`
  Turns delivery on or off.
- `delivery_mode`
  Shows if the cockpit uses one main path or a fallback chain.
- `primary_channel`
  Shows the first channel the system tries.
- `allow_fallback_channels`
  Shows if the system may use another channel.
- `validate_recipient`
  Shows if the target is checked first.
- `validate_channel`
  Shows if the chosen channel is checked first.
- `max_retry_count`
  Shows how many retries are allowed.
- `delivery_window_minutes`
  Shows how long the delivery stays open.
- `message_length_limit`
  Shows the biggest message size allowed.
- `result_retention_days`
  Shows how long the result stays visible.

## Closing line

- "This cockpit makes delivery easy to explain, even for a new operator."
- "It also shows what happens next and whether the runtime is healthy."
