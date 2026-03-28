# Appointment Agent Shared v1.0.0

Shared domain contracts for the Appointment Agent platform.

## Usage

- Use `events.py` for `EventEnvelope` and `CommandEnvelope`.
- Use `commands.py` for provider-neutral commands shared across adapters and orchestrator.
- Use `models.py` for shared DTOs and persisted ORM records.
- Use `contracts.py` only as a compatibility facade while existing modules are being refactored.
