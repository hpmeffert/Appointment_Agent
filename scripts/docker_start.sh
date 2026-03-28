#!/usr/bin/env bash
set -euo pipefail

HOST="${APPOINTMENT_AGENT_APP_HOST:-0.0.0.0}"
PORT="${APPOINTMENT_AGENT_APP_PORT:-8080}"
LOG_LEVEL="${APPOINTMENT_AGENT_LOG_LEVEL:-info}"

export PYTHONPATH="/app/apps:/app/apps/shared/v1_0_0:${PYTHONPATH:-}"

mkdir -p /app/data /app/test-results

exec python -m uvicorn appointment_agent_shared.main:app \
  --host "${HOST}" \
  --port "${PORT}" \
  --log-level "${LOG_LEVEL}"
