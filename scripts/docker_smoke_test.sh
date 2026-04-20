#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"

echo "Checking root endpoint..."
curl -fsS "${BASE_URL}/" >/dev/null

echo "Checking health endpoint..."
health_payload="$(curl -fsS "${BASE_URL}/health")"
grep -q '"status":"ok"' <<<"${health_payload}"

echo "Checking demo UI..."
demo_payload="$(curl -fsS "${BASE_URL}/ui/demo-monitoring/v1.3.9")"
grep -q "Appointment Agent Cockpit v1.3.9" <<<"${demo_payload}"
grep -q "Addresses" <<<"${demo_payload}"
grep -q "Reminder" <<<"${demo_payload}"

echo "Checking cockpit payload API..."
scenario_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.3.9/payload")"
grep -q 'reminder_scheduler_bridge' <<<"${scenario_payload}"
grep -q 'addresses' <<<"${scenario_payload}"

echo "Checking standalone address UI..."
address_ui_payload="$(curl -fsS "${BASE_URL}/ui/address-database/v1.3.9")"
grep -q "Address Database v1.3.9" <<<"${address_ui_payload}"
grep -q "page-addresses" <<<"${address_ui_payload}"

echo "Checking help API..."
help_payload="$(curl -fsS "${BASE_URL}/api/demo-monitoring/v1.3.9/help")"
grep -q 'address_database_menu_entry' <<<"${help_payload}"

echo "Checking reminder config API..."
reminder_payload="$(curl -fsS "${BASE_URL}/api/reminders/v1.3.6/config")"
grep -q '"mode":"manual"' <<<"${reminder_payload}"

echo "Checking Google operator API..."
google_payload="$(curl -fsS "${BASE_URL}/api/google/v1.3.6/linkage/demo")"
grep -q '"provider":"google"' <<<"${google_payload}"

echo "Checking LEKAB monitor API..."
lekab_payload="$(curl -fsS "${BASE_URL}/api/lekab/v1.3.8/settings/rcs")"
grep -q 'storage_mode' <<<"${lekab_payload}"

echo "Checking address database API..."
address_payload="$(curl -fsS "${BASE_URL}/api/addresses/v1.3.9/help")"
grep -q 'address_crud' <<<"${address_payload}"

echo "Checking docs route..."
docs_payload="$(curl -fsS "${BASE_URL}/docs/demo?lang=en")"
grep -q 'v1.3.9' <<<"${docs_payload}"

echo "Docker smoke test passed for ${BASE_URL}"
