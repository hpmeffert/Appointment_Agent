# User Guide v1.0.0

The prototype exposes a single API surface on port `8080`.

- `/help` shows the active version header and module overview.
- `/api/lekab/v1.0.0/*` provides LEKAB adapter prototype endpoints.
- `/api/orchestrator/v1.0.0/journeys/start` starts a journey and prepares slot offers.
- `/api/orchestrator/v1.0.0/journeys/select` stores the customer slot choice and moves to confirmation.
- `/api/orchestrator/v1.0.0/journeys/confirm` books the appointment and triggers confirmation dispatch.
- `/api/orchestrator/v1.0.0/journeys/remind` triggers a reminder workflow for active bookings.
- `/api/orchestrator/v1.0.0/journeys/cancel` closes a journey through the cancellation flow.
- `/api/google/v1.0.0/*` provides Google scheduling and customer contact prototype endpoints.
