# Demo Monitoring UI Admin Leitfaden v1.0.0 DE

Version: v1.0.4 Patch 1
Status: aktiver Demo-Patch
Language: Deutsch
Im UI-Header gezeigter Release: `v1.0.4 Patch 1`
Hinweis: Dieser Dateiname bleibt fuer die Routen-Kompatibilitaet stabil. Der Inhalt ist fuer `v1.0.4 Patch 1` aktualisiert.

## Was dieses Modul ist

Diese UI ist eine Demo- und Monitoring-Oberflaeche.

Sie ist noch kein vollstaendiges produktives Admin-Portal.

Sie hat zwei Hauptaufgaben:

1. zeigen, wie sich der Terminablauf fuer einen Kunden anfuehlt
2. gleichzeitig zeigen, was die Plattform technisch macht

## Die 3 Modi

- `Demo`
  Fokus auf die sichtbare Kundengeschichte.

- `Monitoring`
  Fokus auf die technische Systemsicht.

- `Kombiniert`
  Zeigt beide Seiten zusammen. Das ist meistens der beste Modus fuer Praesentationen.

## Wichtige Routen

- `/ui/demo-monitoring/v1.0.0`
  Oeffnet die UI.

- `/api/demo-monitoring/v1.0.0/scenarios`
  Liefert das Simulations-Payload als JSON.

- `/api/demo-monitoring/v1.0.0/help`
  Liefert eine kleine Uebersicht ueber Modi und Szenario-IDs.

- `/docs/demo?lang=en|de`
  Oeffnet den lokalisierten Demo-Leitfaden.

- `/docs/user?lang=en|de`
  Oeffnet den lokalisierten Benutzerleitfaden.

- `/docs/admin?lang=en|de`
  Oeffnet den lokalisierten Admin-Leitfaden.

## Release-Sichtbarkeit

Der UI-Header zeigt jetzt die aktive Demo-Patch-Linie, damit Praesentierende genau auf den gezeigten Build verweisen koennen.

Aktuell sichtbarer Release-String:

`v1.0.4 Patch 1`

## Messaging-Kennungen

- `message_id`
  Verfolgt die simulierte eingehende oder ausgehende Nachricht auf der Kommunikationsseite.

- `lekab_job_id`
  Verfolgt den Workflow-Job auf der LEKAB-Seite.

- `message_channel`
  Zeigt den Messaging-Kanal wie `RCS` oder `SMS`.

- `message_status`
  Zeigt den Status im Nachrichtenlebenszyklus.

- `delivery_status`
  Zeigt das Lieferergebnis.

## Erklaerung zum Service Bus

Wir nutzen einen Service Bus, damit die Module locker gekoppelt bleiben.

Das bringt uns:

- sauberere Grenzen zwischen LEKAB, Orchestrator, Adaptern und CRM-Events
- leichtere spaetere Provider-Wechsel
- bessere Skalierung und sicherere Erweiterungspunkte

## Erklaerung zur Skalierung

- `20 Nutzer`
  Mehrere Journeys koennen schon parallel laufen.

- `100 Nutzer`
  Stateless Services koennen ueber mehr Container vervielfacht werden.

- `1000 Nutzer`
  Queueing, mehr Rechenleistung, bessere Datenbank-Abstimmung und staerkere Beobachtbarkeit werden wichtig.

## Wichtige Parameter

- `journey_id`
  Haupt-ID fuer eine komplette Terminreise.

- `correlation_id`
  Verbindet zusammengehoerende Events und Audit-Eintraege.

- `trace_id`
  Technische Tracking-ID fuer tiefere Fehlersuche.

- `booking_reference`
  Interne Termin-ID.

- `provider_reference`
  Externe Termin-ID beim Provider.

- `message_id`
  Nachrichten-ID der Kommunikationsseite.

- `lekab_job_id`
  LEKAB-Workflow-Job-ID.
