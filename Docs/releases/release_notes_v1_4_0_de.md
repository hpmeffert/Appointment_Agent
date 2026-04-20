# Release Notes v1.4.0

## Zusammenfassung

Version `1.4.0` markiert die erste funktional produktionsreife Kernfreigabe des Appointment Agent.

Das System unterstuetzt jetzt einen verifizierten End-to-End-Terminfluss mit echtem Messaging, echter Callback-Verarbeitung, dynamischer Google-basierter Verfuegbarkeit, bestaetigten Google-Calendar-Writes und zeitzonenkorrektem Scheduling-Verhalten.

## Highlights

- Echtes LEKAB-RCS-Outbound-Messaging mit interaktiven Reply-Buttons
- Stabiler Callback-Roundtrip fuer mehrstufige Mobile-Device-Flows
- Gefuehrter Live-Flow:
  `Reminder -> Reschedule -> Zeitfenster -> Datum -> Uhrzeit -> Confirm`
- Dynamische Google-Calendar-Verfuegbarkeit fuer Datums- und Zeitvorschlaege
- Echte Google-Calendar-Booking- und Reschedule-Writes
- Korrektes Kalender-Titelformat:
  `<Appointment Type> – <Customer Name>`
- Strukturierte Event-Beschreibungen mit Adresse und Kontext
- Stabile Linkage-Metadaten fuer `correlation_id`, `booking_reference`, `appointment_id` und `address_id`
- Adressgetriebene Zeitzonenbehandlung fuer regionalkorrektes Scheduling

## Verifizierter Umfang

- Real-Device-Tests abgeschlossen
- Echter Callback-Roundtrip abgeschlossen
- Dynamische Datums-Vorschlaege verifiziert
- Dynamische Uhrzeit-Vorschlaege verifiziert
- Confirm-Flow verifiziert
- Google-Calendar-Event-Erzeugung verifiziert
- Address-/Titel-/Beschreibung-Formatierung verifiziert
- Zeitzonen-Fix fuer den aktiven Deutschland-Testfluss verifiziert

## Enthaltene Funktionsmodule

- LEKAB-RCS-Messaging
- Callback-getriebene Orchestrierung
- Mehrstufige Terminvereinbarung
- Google-Verfuegbarkeits-Engine
- Google-Booking-Write-Pfad
- Dashboard-Demonstrator
- Address-Linkage und Zeitzonen-Support

## Bekannte, fuer 1.4 akzeptable Einschraenkungen

- UX ist funktional, aber noch nicht final
- Dashboard-Design-Polish ist fuer `v1.5` geplant
- Erweiterte Retry-Logik ist noch nicht implementiert
- Vollstaendiges Monitoring und Alerting sind noch nicht implementiert

## Runtime-Hinweise

- Die Top-Level-App-Version ist als `v1.4.0` sichtbar
- Die aktuelle Demo-Cockpit-Route bleibt stabil unter `/ui/demo-monitoring/v1.3.9`
- Die aktuelle Live-Cockpit-Patch-Linie bleibt `v1.3.9-patch9`
- Silence Threshold Default bleibt `1300ms`

## Naechstes Release

Geplanter Fokus fuer `v1.5.0`:

- UX-Verbesserungen
- Demo-Dashboard-Redesign
- Usability-Optimierungen
