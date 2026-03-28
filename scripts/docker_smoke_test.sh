#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"

echo "Checking root endpoint..."
curl -fsS "${BASE_URL}/" >/dev/null

echo "Checking health endpoint..."
health_payload="$(curl -fsS "${BASE_URL}/health")"
grep -q '"status":"ok"' <<<"${health_payload}"

echo "Checking demo UI..."
demo_payload="$(curl -fsS "${BASE_URL}/ui/demo-monitoring/v1.0.4-patch2")"
grep -q "Appointment Agent Demo + Monitoring v1.0.4-patch2" <<<"${demo_payload}"

echo "Checking scenario API..."
scenario_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.0.4-patch2/scenarios")"
grep -q 'standard-booking' <<<"${scenario_payload}"

echo "Checking help API..."
help_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.0.4-patch2/help")"
grep -q 'combined' <<<"${help_payload}"

echo "Checking docs route..."
docs_payload="$(curl -fsS "${BASE_URL}/docs/demo?lang=en")"
grep -q 'Demo Guide' <<<"${docs_payload}"

echo "Docker smoke test passed for ${BASE_URL}"
