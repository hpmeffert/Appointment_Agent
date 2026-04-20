# Reminder Scheduler v1.3.5

Version: v1.3.5
Audience: Admin
Language: EN

## Patch goal

`v1.3.5` shows the delivery layer in a simple cockpit and also makes runtime health easier to understand.

The cockpit explains three things:
- which delivery channel is chosen
- why validation passes or blocks delivery
- what delivery result happened
- what is scheduled next and when the system was last active

## Pages in the cockpit

- `Dashboard`
  Shows a short overview and the demo stories.
- `Delivery`
  Lets the operator change the delivery settings.
- `Validation`
  Shows why delivery is ready, warned, or blocked.
- `Results`
  Shows sent, fallback_sent, blocked, retrying, failed, and skipped results.
- `Channels`
  Shows which channels are ready for delivery.
- `Operator`
  Shows the simple step-by-step operator flow.
- `Help`
  Shows links and short explanations.

## Important parameters

- `enabled`
  Turns delivery on or off.
- `delivery_mode`
  `priority_order` keeps one channel first.
  `fallback_chain` allows a backup path.
- `primary_channel`
  The first channel the system tries.
- `allow_fallback_channels`
  Lets the system use another channel if the first one is not ready.
- `validate_recipient`
  Checks the target before delivery starts.
- `validate_channel`
  Checks that the selected channel is allowed.
- `max_retry_count`
  How many retry attempts are allowed.
- `delivery_window_minutes`
  How long the delivery window stays open.
- `message_length_limit`
  How long the message may be before the cockpit blocks delivery.
- `result_retention_days`
  How long delivery results stay visible.
- `channel_email_enabled`
  Allows email delivery.
- `channel_voice_enabled`
  Allows voice delivery.
- `channel_rcs_sms_enabled`
  Allows RCS/SMS delivery.

## Validation outcomes

- `passed`
  Delivery is ready.
- `warning`
  The operator should check the setup carefully.
- `blocked`
  Delivery should not start yet.

## Delivery results

- `sent`
  The message was delivered on the chosen channel.
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

## API routes for this release line

- `GET /api/reminder-ui/v1.3.5/payload`
- `GET /api/reminder-ui/v1.3.5/help`
- `GET /api/reminder-ui/v1.3.5/config`
- `GET /api/reminder-ui/v1.3.5/config/preview`
- `GET /api/reminder-ui/v1.3.5/results`
- `GET /api/reminder-ui/v1.3.5/health`
- `GET /api/reminders/v1.3.5/health`

## What the admin should verify

1. The header shows `v1.3.5`.
2. The cockpit shows delivery channels, validation outcomes, and delivery results.
3. The help page explains the parameters in simple words.
4. The demo stories are visible and short enough to present quickly.
