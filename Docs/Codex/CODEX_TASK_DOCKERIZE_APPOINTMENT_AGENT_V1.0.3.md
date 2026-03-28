# CODEX_TASK_DOCKERIZE_APPOINTMENT_AGENT_V1.0.3.md

## Title
Make the Appointment Agent fully Docker-buildable and Docker-runnable for local demo and development

## Objective
Prepare the whole Appointment Agent project so it can be:

- built with Docker
- started with Docker Compose
- used locally for demo and development
- run in a predictable and repeatable way without manual environment patching

The goal is not only to have "some container files", but to ensure the project is **actually startable** in Docker end-to-end.

This task should make the current project state reproducible for:
- Demo UI
- Monitoring UI
- Appointment Orchestrator
- Google Adapter
- LEKAB mock / current messaging path
- shared platform services
- local database / local runtime dependencies

---

## Current Situation
The project already has:
- a versioned monorepo-style structure
- Python services
- shared domain modules
- demo/monitoring UI
- local tests
- a Docker-related foundation
- a local database approach for prototyping

However, the next step is to ensure the project is **really Docker-ready as a working local runtime**, not just partially prepared.

---

## Guiding Rule
The Docker setup must support **real local startup**, not only theoretical packaging.

That means:
1. `docker compose up --build` should work predictably
2. environment configuration should be simple for prototyping
3. logs should be understandable
4. ports and startup instructions should be documented clearly
5. the system should be demo-usable after startup

---

## Scope

### In Scope
1. Review and harden Dockerfile(s)
2. Review and harden docker-compose configuration
3. Ensure all required services are started correctly
4. Ensure local configuration via `.env` / `.env.example`
5. Ensure project builds inside containers
6. Ensure runtime entrypoints are correct
7. Ensure ports are exposed clearly
8. Ensure database/storage paths are mounted correctly where needed
9. Add Docker start/stop/reset instructions to docs
10. Add smoke tests / validation steps for Docker runtime
11. Update README and admin docs

### Out of Scope
1. Production Kubernetes deployment
2. Cloud infrastructure automation
3. Full secret-management platform
4. Production-grade HA setup
5. External managed databases
6. Real Google/LEKAB credentials for production

---

## Goal State
After this task, a developer or presenter should be able to do:

```bash
cp .env.example .env
docker compose up --build
```

And then open the relevant browser URL(s) and use:
- demo UI
- monitoring UI
- API endpoints
- local prototype flows

---

## Target Runtime Model

### Minimum desired runtime
The Docker setup should support these logical components:

- App / API service
- Demo / Monitoring UI service (or static-serving path inside app if combined)
- Local database or local persistence
- any required mock provider services if already separated
- optional volume mounts for dev convenience

### If the current architecture uses one combined app
That is acceptable for now, as long as:
- startup is clear
- routes work
- docs reflect reality

---

## Part 1 – Docker Audit

## Goal
Review the current Docker setup and identify what is missing for a real runnable stack.

### Required review points
1. Is the current `Dockerfile` sufficient to build the app?
2. Is `docker-compose.yml` sufficient to run the app?
3. Are all dependencies installed in container build?
4. Are Python import paths correct inside container runtime?
5. Are static/demo UI files available inside container?
6. Is the local DB path writable inside container?
7. Do startup commands actually point to the correct app entrypoint?
8. Are route URLs reachable from host?

### Deliverable
If current files are incomplete, fix them instead of layering hacks on top.

---

## Part 2 – Dockerfile Hardening

## Goal
Make the Dockerfile robust and predictable.

### Requirements
The Dockerfile should:
- use a sensible Python base image
- set a clean working directory
- copy only necessary files in the correct order
- install dependencies reliably
- expose the required app port(s)
- define a clear default startup command
- support the current monorepo-style package layout

### Recommended practices
- avoid unnecessary image bloat
- avoid copying runtime junk
- respect `.dockerignore` if needed
- use deterministic install flow where possible

### Validate
A clean `docker build` must succeed.

---

## Part 3 – Docker Compose Hardening

## Goal
Make `docker compose up --build` the standard local start path.

### Requirements
`docker-compose.yml` should:
- build the application image correctly
- pass required environment variables
- mount useful dev volumes only if appropriate
- expose the right ports
- define service names clearly
- support restarting the system cleanly
- optionally provide a local DB volume if persistence is needed

### If multiple services are useful
You may separate:
- app
- db
- optional mock service
But do not over-complicate the setup.

### Important
The compose file must match the real startup shape of the project, not an imagined future architecture.

---

## Part 4 – Environment Configuration

## Goal
Make local configuration simple and safe.

### Requirements
Use:
- `.env.example` as the documented template
- `.env` for local runtime

### Required configuration clarity
At minimum document and wire:
- app host/port
- demo UI route/base
- database path or DB URL
- mock mode flags
- Google config placeholders if needed for later
- LEKAB mock mode flags if needed
- logging mode
- language defaults where relevant

### Important rule
For the prototype, simple local configuration is acceptable.
Do not overengineer secret handling at this stage.

---

## Part 5 – Startup Commands and Entrypoints

## Goal
Make service startup explicit and correct.

### Requirements
The container entrypoint must launch the correct app module.

Examples:
- FastAPI / Uvicorn app
- combined backend + static route host
- whatever is actually used in the current repo

### Validate
After startup:
- health/basic endpoints should work
- demo UI route should load
- scenario API route should work
- help/docs route should work

---

## Part 6 – Local Database / Persistence

## Goal
Make the local prototype persistence work inside Docker.

### Requirements
If the project currently uses local SQLite or similar:
- ensure the DB file path is writable in container
- ensure path is stable across restarts if desired
- use a mounted volume if persistence should survive container recreation
- document reset behavior clearly

### Example needs to support
- journey state
- audit records
- booking state
- demo scenario runtime if stored

### Important
Do not commit runtime DB files into git.

---

## Part 7 – Demo & Monitoring UI Availability

## Goal
Ensure the UI is reachable in Docker exactly as needed for demos.

### Required validation
The following must work after container startup:
- `/ui/demo-monitoring/v1.0.2`
- `/api/demo-monitoring/v1.0.2/scenarios`
- `/api/demo-monitoring/v1.0.2/help`

If routes changed, update docs accordingly.

### UX requirement
The demo must be launchable in Docker without manual patching in code.

---

## Part 8 – Smoke Test Procedure

## Goal
Create a repeatable Docker validation path.

### Required checks
After `docker compose up --build`, validate:
1. app starts without crash
2. logs are readable
3. browser UI loads
4. scenario API returns data
5. help/docs route works
6. language switching still works
7. combined mode still works
8. no obvious file-permission problem exists for the DB/runtime data

### Add a simple smoke-test note or script if helpful

---

## Part 9 – Documentation

## Goal
Make Docker startup simple even for a non-developer.

### Required documentation updates
Update at least:
- `README.md`
- docker-related admin doc
- optionally demo guide if relevant

### Must explain
1. what Docker is used for here
2. how to copy `.env.example`
3. how to build/start
4. how to stop
5. how to reset
6. what URL to open
7. what should appear on screen
8. common errors and what they mean

### Style rule
Write clearly enough that a motivated 16-year-old can follow it.

---

## Part 10 – Suggested Commands to Support

The final docs should support a command flow like this:

### Build and run
```bash
cp .env.example .env
docker compose up --build
```

### Stop
```bash
docker compose down
```

### Reset local runtime state if needed
```bash
docker compose down -v
```

If extra commands are needed, document them clearly.

---

## Part 11 – Common Failure Cases to Handle

The Docker setup and docs should address common issues such as:
- missing `.env`
- port already in use
- container cannot write DB file
- wrong app entrypoint
- missing Python module path
- static UI not found
- routes not mounted
- dependency install failure

Where useful, add clear troubleshooting notes.

---

## Part 12 – Optional Nice-to-Have
If the setup stays simple, consider:
- adding a lightweight health endpoint
- adding a `make` or helper script later
- adding named volumes for DB persistence
- adding a dev-friendly hot-reload mode later

Only if it does not complicate the current release too much.

---

## Files Likely to Touch
Adjust to repo reality, but likely:
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore` (if missing)
- `.env.example`
- `README.md`
- `docker/README.md`
- app startup module(s)
- possibly path/config handling in shared config

---

## Acceptance Criteria
This task is complete only if:

1. The project builds successfully with Docker.
2. The project starts successfully with Docker Compose.
3. The demo/monitoring UI is reachable after startup.
4. The main API/demo routes work in Docker.
5. Local config is simple and documented.
6. Runtime persistence works or is clearly documented.
7. README/start instructions are clear.
8. No secrets are committed.
9. The Docker path is good enough for demos and local development.

---

## Definition of Done
Done means:
- the Appointment Agent can be started reproducibly through Docker
- demo and monitoring UI work from the containerized setup
- the repo is easier to run on another machine
- the project is ready for more realistic integration steps later

---

## Recommended Next Step After Completion
After Docker runtime is stable, the next best move is likely:
- live demo rehearsal through Docker
- or real Google integration prototype with simple local config
- or deeper monitoring/technical visualization
