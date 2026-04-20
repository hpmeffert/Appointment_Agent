# Admin Guide Demo Monitoring UI v1.2.1-patch3

Version: v1.2.1-patch3
Audience: Admin
Language: DE

## Ziel dieses Patches

`v1.2.1-patch3` behaelt die UI- und Doku-Fixes aus Patch 2 und macht die Plattform direkt im Cockpit klarer sichtbar.

Die Laufzeitlogik bleibt stabil, aber Operator-Klarheit und Doku-Qualitaet steigen deutlich.

## Plattform-Ueberblick

- `LEKAB Adapter`
  Messaging-Adapter fuer RCS- und SMS-aehnlichen Verkehr.
- `Appointment Orchestrator`
  Entscheidungslogik fuer Termin-Journeys.
- `Google Adapter`
  Scheduling-Adapter fuer Slots, Hold, Booking und Konflikte.
- `Service Bus`
  Interne Vertragsschicht, damit Adapter austauschbar bleiben.

![Annotierte Cockpit-Uebersicht](/docs/assets/screenshots/v1_2_1_patch3/cockpit-overview.svg)
![Plattform-Flow-Uebersicht](/docs/assets/screenshots/v1_2_1_patch3/platform-flow.svg)

## Neue Cockpit-Bereiche in Patch 3

- `How the Platform Works`
  Zeigt Kanaele, LEKAB, Service Bus, Orchestrator und Adapter.
- `Demo Storyboard`
  Zeigt die fuenf Kern-Stories mit Business Value und Wow-Effekt.
- `Help`
  Buendelt Plattform-Erklaerung, Storyboard, Business Value und Doku-Links.

## Neue Doku-Basis

Zu diesem Patch gehoeren:
- Demo Guide fuer Presenter
- User Guide fuer Operatoren
- Admin Guide mit Parameter-Erklaerungen
- separate Release Notes

Wichtige Regel:
- Release Notes gehoeren nicht in den Demo Guide

## Day-Mode Button Fix

Aktionsbuttons im Day Mode nutzen jetzt:
- grauen Hintergrund
- weisse Schrift
- staerkeren Rand
- deutlichere Schatten

Betroffene Bereiche:
- Demo-Modus Buttons
- Operator-Panel Buttons
- Story Buttons
- Slot Buttons
- Kommunikationsaktionen
- Settings Aktionen

## Verhalten der RCS-Settings-Seite

Pfad:
- `Settings`
- `Settings -> RCS`

Die Seite liest und speichert Werte in einem lokalen SQLite-basierten Config Store.

Wichtig:
- normale Felder werden direkt zurueckgegeben
- Secret-Felder werden gespeichert, aber als `********` zurueckgegeben
- leeres Secret bedeutet `bestehendes Secret behalten`
- Readiness wird aus Pflichtfeldern und Adapter-Zustand berechnet

![Annotierte RCS-Settings-Seite](/docs/assets/screenshots/v1_2_1_patch3/rcs-settings.svg)

## Parameter-Ueberblick

### Environment / Workspace

- `environment_name`
  Menschlich lesbarer Umgebungsname.
  Beispiel: `Demo EU`
  Wirkung: hilft Operatoren beim Einordnen der Umgebung.
- `workspace_id`
  Technische LEKAB Tenant- oder Workspace-ID.
  Beispiel: `appointment-agent-demo`
  Wirkung: bestimmt, in welchen Provider-Bereich Messaging laeuft.
- `messaging_environment`
  Laufzeitumgebung fuer Messaging.
  Beispiel: `test`
  Wirkung: trennt Demo/Test von spaeterem Livebetrieb.
- `dispatch_base_url`
  Basis-URL fuer Dispatch-Aktionen.
  Beispiel: `https://dispatch.example.test`
  Wirkung: bestimmt das Ziel fuer Workflow-Dispatch.
- `rime_base_url`
  Basis-URL fuer RCS-/Rich-Messaging-Requests.
  Beispiel: `https://rime.example.test`
  Wirkung: beeinflusst die RCS-Verarbeitung.
- `sms_base_url`
  Basis-URL fuer SMS-Requests.
  Beispiel: `https://sms.example.test`
  Wirkung: beeinflusst den SMS-Pfad.
- `addressbook_base_url`
  Basis-URL fuer Kontaktauflosung.
  Beispiel: `https://addressbook.example.test`
  Wirkung: beeinflusst spaetere Contact-Resolution.

### Authentication

- `auth_base_url`
  Basis-URL fuer Auth.
  Beispiel: `https://auth.example.test`
  Wirkung: falscher Wert blockiert Token-Abruf.
- `auth_client_id`
  Technische Client-ID.
  Beispiel: `appointment-agent-demo-client`
  Wirkung: identifiziert die Anwendung im Auth-Flow.
- `auth_client_secret`
  Secret zur Client-ID.
  Wirkung: notwendig fuer Provider-Zugriff.
- `auth_username`
  Technischer Service-User.
  Beispiel: `demo-operator`
  Wirkung: identifiziert den technischen Nutzer.
- `auth_password`
  Passwort des Service-Users.
  Wirkung: notwendig fuer Provider-Zugriff.
- `token_endpoint`
  Relativer Token-Pfad.
  Beispiel: `/oauth/token`
  Wirkung: bestimmt das Ziel fuer Token-Requests.
- `revoke_endpoint`
  Optionaler Revoke-Pfad.
  Beispiel: `/oauth/revoke`
  Wirkung: spaetere Session- oder Token-Bereinigung.

### RCS / Messaging

- `rcs_enabled`
  Aktiviert oder deaktiviert den RCS-Pfad.
- `rcs_sender_profile`
  Sichtbarer Sendername im RCS-Kontext.
- `default_template_context`
  Template-Familie oder Business-Kontext.
- `callback_url`
  Ziel fuer Inbound-Callbacks.
- `channel_priority`
  Legt fest, ob zuerst RCS oder SMS versucht wird.
- `sms_fallback_enabled`
  Erlaubt SMS, wenn RCS nicht moeglich ist.

### SMS

- `sms_enabled`
  Aktiviert oder deaktiviert SMS.
- `sms_sender_name`
  Sichtbarer SMS-Absender.
- `sms_length_mode`
  Verhalten bei langen Texten.
- `default_language`
  Standard-Sprache fuer Templates.

### Addressbook / Contact Resolution

- `addressbook_enabled`
  Aktiviert Kontaktauflosung.
- `contact_lookup_mode`
  Legt die Lookup-Reihenfolge fest.
- `phone_normalization_mode`
  Definiert das Telefonformat, zum Beispiel `E164`.

## Readiness-Logik

Die Seite zeigt:
- `ready / not ready`
- fehlende Pflichtfelder
- Warnungen wie `SMS fallback is enabled`
- aktiven Channel-Modus

`Test Connection` prueft aktuell die Adapter-Readiness, nicht einen echten Remote-Handshake.
