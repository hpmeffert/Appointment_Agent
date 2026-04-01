# User Guide Demo Monitoring UI v1.2.1-patch4

Version: v1.2.1-patch4
Audience: User
Language: DE

## Wofuer dieses Cockpit da ist

Das Cockpit hilft einem Operator, drei Dinge gleichzeitig zu sehen:
- was der Kunde erlebt
- was die Plattform intern tut
- welche Einstellungen oder Integrationen gerade wichtig sind

## Hauptseiten

- `Dashboard`
  Hauptseite mit Transcript, Aktionen, Slots, Guided Panel und Operator Summary.
- `Message Monitor`
  Zeigt eingehende und ausgehende Nachrichten.
- `Reports`
  Macht aus Rohdaten einfache Zusammenfassungen.
- `Monitoring`
  Zeigt technische Events, Traces und Performance-Daten.
- `Settings`
  Zeigt allgemeine Runtime-Parameter.
- `Settings -> RCS`
  Zeigt LEKAB RCS- und SMS-Konfiguration.
- `Google Demo Control`
  Sicherer Bereich fuer Google-Demo-Daten.
- `Help`
  Oeffnet die aktuellen Leitfaeden.

## Neu in Patch 4

- `Guided` und `Free` Modus
- Guided Story Panel
- `Auto Demo`
- klarere Plattform-Sichtbarkeit
- messaging-first Dashboard

## Wichtige Parameter einfach erklaert

- `guidedMode`
  `free` bedeutet manuelle Steuerung.
  `guided` bedeutet gefuehrte Praesentation.
- `guidedStepIndex`
  Nummer des aktuellen Guided-Schritts.
- `autoDemoRunning`
  Zeigt, ob die Demo automatisch weiterlaeuft.
- `slot_hold_minutes`
  Wie lange ein Slot kurzzeitig reserviert bleibt.
- `trace_id`
  Technische Spur fuer zusammenhaengende Events.
- `correlation_id`
  Verbindet zusammengehoerige Aufrufe ueber mehrere Module hinweg.

## Message Monitor Parameter

- `message_id`
  Interne ID einer Nachricht.
- `provider_message_id`
  ID derselben Nachricht beim externen Provider.
- `direction`
  `inbound` = vom Kunden zur Plattform.
  `outbound` = von der Plattform zum Kunden.
- `status`
  Zustell- oder Verarbeitungsstatus.
- `journey_id`
  Verbindet viele Nachrichten mit einer Journey.
- `booking_reference`
  Verbindet die Nachricht mit einer Buchung.

## Google Demo Control Parameter

- `Mode`
  `simulation` = keine echten Google-Aenderungen.
  `test` = echte Aenderungen im konfigurierten Testkalender.
- `From Date`
  Start des Datumsbereichs.
- `To Date`
  Ende des Datumsbereichs.
- `Appointment Count`
  Anzahl der Demo-Termine.
- `Appointment Type`
  Geschaeftlicher Typ wie `dentist`, `wallbox`, `gas_meter` oder `water_meter`.

## RCS Settings Parameter

- `workspace_id`
  Technischer LEKAB-Arbeitsbereich.
- `auth_client_id`
  App-ID fuer die Anmeldung.
- `auth_client_secret`
  Secret fuer diese App-ID.
- `channel_priority`
  Welcher Kanal zuerst versucht wird.
- `sms_fallback_enabled`
  Erlaubt SMS, wenn RCS nicht moeglich ist.
- `callback_url`
  Zieladresse fuer Statusupdates und Antworten.
