# Benutzerleitfaden v1.3.11d

## Wofuer dieses Release da ist

`v1.3.11d` soll den Appointment Agent leichter als gehostetes Demo-System nutzbar machen.

Das bedeutet: Das System wird so vorbereitet, dass der Vertrieb spaeter eine gehostete URL oeffnen und mit einer stabilen Docker-basierten Demo-Runtime arbeiten kann.

## Was in der Demo nutzbar ist

- das kombinierte Appointment-Cockpit
- das Reminder-Cockpit
- die Address Database
- der Google Demo Control Bereich
- der Message Monitor

## Was fuer eine sichere Demo wichtig ist

Fuer das einfachste Setup sollte die gehostete Demo normalerweise in sicheren Simulations-Defaults bleiben.

Wichtige Werte:

- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE=true`
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE=true`
- `GOOGLE_REAL_INTEGRATION_ENABLED=false`

## Haupteinstieg

Oeffne:

- `/ui/demo-monitoring/v1.3.10`
