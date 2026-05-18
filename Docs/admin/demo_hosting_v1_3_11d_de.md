# Demo Hosting v1.3.11d

## Zweck

Dieser Admin-Leitfaden erklaert, wie der Appointment Agent als gehostetes Docker-Demo-Release fuer den Azure-orientierten Vertrieb bereitgestellt wird.

## Was v1.3.11d ist

`v1.3.11d` ist ein gehostetes Demo-Paket-Release.

Es fuehrt keine komplett neue Anwendungsline ein, sondern buendelt die aktuell bewaehrten Runtime- und Cockpit-Linien zu einem dokumentierten Docker-Deployment-Paket fuer Sales-Demos.

## Versionsbild

- Paket-Release: `v1.3.11d`
- Runtime-Linie: `v1.4.0`
- kombiniertes Cockpit: `v1.3.10`
- Address Database: `v1.3.9`
- Reminder-Linie: `v1.3.6`
- LEKAB Settings und Monitor: `v1.3.8`

## Kernpunkte fuer Admins

### Docker-Topologie

Die gehostete Demo laeuft mit:

- einem Anwendungscontainer
- einem benannten Docker-Volume fuer die Datenbank

### Datenbank-Strategie

- SQLite bleibt innerhalb der Docker-Runtime
- die DB-Datei liegt unter `/app/data/appointment_agent.db`
- das Volume haelt den Demo-Zustand ueber Neustarts stabil

### Seed- und Reset-Strategie

Die gehostete Demo ist fuer einen einfachen Reset ueber das Entfernen des Docker-Volumes ausgelegt.

### Azure-relevante Parameter

Die wichtigsten Azure-bezogenen Werte sind:

- `APPOINTMENT_AGENT_PUBLIC_BASE_URL`
- `APPOINTMENT_AGENT_PUBLIC_SCHEME`
- `APPOINTMENT_AGENT_TRUST_PROXY_HEADERS`
- `APPOINTMENT_AGENT_APP_PORT`
- `APPOINTMENT_AGENT_DB_URL`

### Demo-Betrieb

Das Hauptziel fuer Operatoren ist:

- einfacher Start
- vorhersagbarer Demo-Zustand
- leichter Reset
- sichere Simulations-Defaults
