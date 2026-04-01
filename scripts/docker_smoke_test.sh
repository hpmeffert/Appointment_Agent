#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"

echo "Checking root endpoint..."
curl -fsS "${BASE_URL}/" >/dev/null

echo "Checking health endpoint..."
health_payload="$(curl -fsS "${BASE_URL}/health")"
grep -q '"status":"ok"' <<<"${health_payload}"

echo "Checking demo UI..."
demo_payload="$(curl -fsS "${BASE_URL}/ui/demo-monitoring/v1.2.1-patch4")"
grep -q "Appointment Agent Cockpit v1.2.1-patch4" <<<"${demo_payload}"
grep -q "Guided Demo Mode" <<<"${demo_payload}"
grep -q "RCS Settings" <<<"${demo_payload}"

echo "Checking cockpit payload API..."
scenario_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.2.1-patch4/payload")"
grep -q 'guided_demo' <<<"${scenario_payload}"

echo "Checking help API..."
help_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.2.1-patch4/help")"
grep -q 'story_engine_steps' <<<"${help_payload}"

echo "Checking Google operator API..."
google_payload="$(curl -fsS "${BASE_URL}/api/google/v1.2.0/mode")"
grep -q 'simulation' <<<"${google_payload}"

echo "Checking LEKAB monitor API..."
lekab_payload="$(curl -fsS "${BASE_URL}/api/lekab/v1.2.1-patch4/settings/rcs")"
grep -q 'storage_mode' <<<"${lekab_payload}"

echo "Checking docs route..."
docs_payload="$(curl -fsS "${BASE_URL}/docs/demo?lang=en")"
grep -q 'Demo Guide' <<<"${docs_payload}"

echo "Docker smoke test passed for ${BASE_URL}"
