# LEKAB Adapter Service v1.0.0

Administrative baseline for the prototype LEKAB Adapter.

- Auth token handling is cached in-process for the prototype.
- Callback deduplication is persisted in the local SQLite database.
- Runtime-safe logs and test summaries must be written outside committed source files.
