#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"

echo "Checking root endpoint..."
curl -fsS "${BASE_URL}/" >/dev/null

echo "Checking health endpoint..."
health_payload="$(curl -fsS "${BASE_URL}/health")"
grep -q '"status":"ok"' <<<"${health_payload}"

echo "Checking demo UI..."
demo_payload="$(curl -fsS "${BASE_URL}/ui/demo-monitoring/v1.1.0-patch6")"
grep -q "Appointment Agent Cockpit v1.1.0-patch6" <<<"${demo_payload}"

echo "Checking cockpit payload API..."
scenario_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.1.0-patch6/payload")"
grep -q 'appointment_types' <<<"${scenario_payload}"

echo "Checking help API..."
help_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.1.0-patch6/help")"
grep -q 'appointment_type_dropdown' <<<"${help_payload}"

echo "Checking Google operator API..."
google_payload="$(curl -fsS "${BASE_URL}/api/google/v1.1.0-patch6/mode")"
grep -q 'simulation' <<<"${google_payload}"

echo "Checking docs route..."
docs_payload="$(curl -fsS "${BASE_URL}/docs/demo?lang=en")"
grep -q 'Demo Guide' <<<"${docs_payload}"

echo "Docker smoke test passed for ${BASE_URL}"
