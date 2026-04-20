# User Guide Reminder Scheduler v1.3.5

Version: v1.3.5
Audience: User
Language: EN

## What this cockpit is for

This cockpit helps an operator do three things:
- choose a delivery channel
- check if delivery is allowed
- see the delivery result
- understand what the system will do next

## Main pages

- `Dashboard`
  Shows the overview and the demo stories.
- `Delivery`
  Lets the operator change the delivery settings.
- `Validation`
  Shows why delivery is ready, warned, or blocked.
- `Results`
  Shows the delivery results in a simple list.
- `Channels`
  Shows which channels are ready.
- `Operator`
  Shows the simple operator flow.
- `Help`
  Shows short explanations and document links.

## The most important parameters

- `enabled`
  Turns delivery on or off.
- `delivery_mode`
  `priority_order` means the first channel wins.
  `fallback_chain` means the system can try a backup channel.
- `primary_channel`
  The first channel the system tries.
- `allow_fallback_channels`
  Lets the system try another channel if the first one is not ready.
- `validate_recipient`
  Checks that the target looks valid.
- `validate_channel`
  Checks that the channel is allowed.
- `max_retry_count`
  How many times the system may try again.
- `delivery_window_minutes`
  How long the delivery window stays open.
- `message_length_limit`
  The biggest message size allowed.
- `result_retention_days`
  How long the result stays visible.
- `db_status`
  Shows if the database connection is okay.
- `worker_status`
  Shows if the reminder worker is ready or disabled.
- `channel_email_enabled`
  Allows email delivery.
- `channel_voice_enabled`
  Allows voice delivery.
- `channel_rcs_sms_enabled`
  Allows RCS/SMS delivery.

## Validation outcomes in simple words

- `passed`
  Delivery can start.
- `warning`
  The operator should check the setup.
- `blocked`
  Delivery should not start yet.

## Delivery results in simple words

- `sent`
  The message was delivered.
- `fallback_sent`
  The message used a backup channel.
- `blocked`
  Delivery stopped before sending.
- `retrying`
  The system is trying again.
- `failed`
  Delivery did not work.
- `skipped`
  Delivery was not started.

## How to use the cockpit

1. Open `Dashboard`.
2. Open `Delivery`.
3. Change a channel or a validation setting.
4. Open `Validation`.
5. Open `Results`.
6. Open `Help` if you want short explanations.

## Simple rule of thumb

- one active channel is the easiest setup
- fallback channels help when the main channel is busy
- validation makes sure the operator sees problems early
