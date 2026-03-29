# Google Live Sync v1.1.0 Patch 3 User Guide

Version: v1.1.0-patch3
Audience: User
Language: EN

## What live sync means

Live sync means the system can check the current Google Calendar state instead of only trusting older local data.

## Why this matters

Sometimes a slot looked free earlier, but another event was added later.

This patch helps the system notice that.

## What a conflict means

A conflict means the system found a reason why it should not continue safely.

Examples:

- the slot is already occupied
- the Google event was deleted manually
- the stored Google event reference is stale

## What the operator can now see

- whether Google data is live or simulated
- when the last sync check happened
- whether a conflict was found
- what the next safe actions are
