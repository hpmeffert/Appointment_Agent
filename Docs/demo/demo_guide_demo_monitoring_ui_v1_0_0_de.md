# Demo Leitfaden Demo Monitoring UI v1.0.0 DE

Version: v1.0.4 Patch 2
Status: aktiver Demo-Patch
Language: Deutsch
Im UI-Header gezeigter Release: `v1.0.4 Patch 2`
Hinweis: Dieser Dateiname bleibt fuer die Routen-Kompatibilitaet stabil. Der Inhalt ist fuer `v1.0.4 Patch 2` aktualisiert.

## Warum es diesen Appointment Agent gibt

Dieses System gibt es, um das Hin und Her bei der manuellen Terminbuchung zu entfernen.

Einfach gesagt hilft es, weil:

- Kunden schneller Termine buchen oder aendern koennen
- Teams nicht jede kleine Buchungsanfrage per Hand beantworten muessen
- Erinnerungen verpasste Termine reduzieren
- Kommunikation und Backend-Buchungslogik automatisch verbunden bleiben

## Welche Teile zusammenarbeiten

So kannst du das System einfach erklaeren:

- `Kunde / RCS / SMS`
  Das ist die Kommunikationsseite, auf der eine Person Nachrichten sendet oder bekommt.
- `LEKAB`
  LEKAB uebernimmt die Kommunikations- und Workflow-Seite. Dort werden Nachrichten versendet und message-bezogene Jobs verfolgt.
- `Service Bus`
  Stell dir den Bus wie eine zentrale Autobahn vor. Jeder Teil sendet dort Nachrichten hin, aber die Teile brauchen keine starre Direktverbindung zu allen anderen Teilen.
- `Appointment Orchestrator`
  Das ist das Gehirn. Er entscheidet, was als Naechstes passieren soll.
- `Google Adapter`
  Dieser Teil prueft freie Zeitslots und schreibt Buchungsaenderungen in die Google-Seite.
- `CRM Event Layer`
  Dieser Teil bereitet geschaeftliche Folgeinformationen vor.
- `Audit / Monitoring`
  Dieser Teil zeigt, was passiert ist, und hilft bei Fehlersuche und Vertrauen.

## Was "orchestriert" hier bedeutet

Orchestriert bedeutet, dass die Arbeit in klare Rollen getrennt ist:

- ein Teil sendet die Nachricht
- ein Teil entscheidet den naechsten Schritt
- ein Teil prueft und bucht Termine
- ein Teil speichert geschaeftliche Folgeinformationen und technische Historie

Diese Trennung ist wichtig, weil das System dadurch leichter zu verstehen, zu skalieren und spaeter zu verbessern ist.

## Praktisches Architekturdiagramm

```text
Kunde
  ↓
RCS / SMS
  ↓
LEKAB Messaging / Workflow Layer
  ↓
Service Bus
  ↓
Appointment Orchestrator
  ↓
Google Adapter
  ↓
Google Calendar
  ↓
Buchungsergebnis
  ↘
   CRM Event / Audit / Monitoring
```

So erklaerst du das Diagramm:

- der Kunde startet auf der Kommunikationsseite
- LEKAB uebernimmt Nachrichtenversand und Workflow-Jobs
- der Service Bus transportiert Nachrichten zwischen den Teilen
- der Orchestrator entscheidet, was als Naechstes passiert
- der Google Adapter spricht mit der Kalender-Seite
- das Ergebnis erscheint als Buchungsstatus, CRM-Event und Audit-Information

## Startsatz fuer die Demo

Bester Startsatz:

"Links siehst du den Kunden. Rechts siehst du, was das System macht."

Guter zweiter Satz:

"Die Version im Header zeigt genau, welchen Release wir gerade demonstrieren."

## Story 1 - Standard-Terminbuchung

Nutze das Szenario `Standard-Terminbuchung`.

Das kannst du sagen:

1. Der Kunde fragt nach einem Termin.
2. LEKAB nimmt die Nachricht auf der Kommunikationsseite entgegen.
3. Der Orchestrator fragt echte Verfuegbarkeit an.
4. Der Google Adapter liefert echte Slots zurueck.
5. Der Kunde waehlt einen Slot.
6. Die Plattform erstellt eine echte Buchung.

Wichtiger Satz:

"Das ist kein Chatbot. Das ist Prozessautomatisierung."

## Story 2 - Verschiebung

Nutze das Szenario `Verschiebung`.

Das kannst du sagen:

1. Das ist keine neue Buchung.
2. Das ist eine Aenderung einer bestehenden Buchung.
3. Die `provider_reference` ist die externe Buchungs-ID beim Provider.
4. Die `message_id` verfolgt die Kommunikationsseite, waehrend `booking_reference` die Terminseite verfolgt.
5. Der Orchestrator behaelt die Journey-Logik, waehrend der Google Adapter die Provider-Buchung aktualisiert.

## Story 3 - Absage

Nutze das Szenario `Absage`.

Das kannst du sagen:

1. Die Absage startet im Messaging.
2. Die Absage muss auch im Backend sauber abgeschlossen werden.
3. Die CRM-Schicht bekommt ein passendes Absage-Ereignis.

## Story 4 - Kein Slot und Eskalation

Nutze das Szenario `Kein Slot und Eskalation`.

Das kannst du sagen:

1. Gute Automatisierung muss wissen, wann sie ein Problem nicht alleine loesen kann.
2. Wenn kein freier Slot da ist, bleibt das System nicht stecken.
3. Es bietet Alternativen, Rueckruf oder menschliche Uebergabe an.

## Story 5 - Provider-Fehler

Nutze das Szenario `Provider-Fehler`.

Das kannst du sagen:

1. Selbst wenn der Provider scheitert, reagiert die Plattform klar.
2. Der Kunde bekommt eine sichere Antwort.
3. Audit-Trail und Eskalationsweg bleiben sichtbar.

## So funktioniert der Service Bus

Einfache Erklaerung:

Der Service Bus ist wie eine zentrale Autobahn fuer Systemnachrichten.

Das bedeutet:

- LEKAB braucht keine starre Direktverbindung zu jedem anderen Modul
- der Orchestrator kann an einer stabilen Stelle auf Events reagieren
- Adapter koennen spaeter getauscht werden, ohne die ganze Plattform neu zu bauen
- Fehlersuche wird leichter, weil man Events Schritt fuer Schritt verfolgen kann

Praesentationssatz:

"Dieses System ist auf einem Service Bus aufgebaut. Dadurch sind Kommunikation, Logik und externe Systeme sauber getrennt."

## So skaliert das System

- `20 Nutzer`
  Viele Journeys koennen schon parallel laufen. Jede Journey hat eigene IDs, deshalb ueberschreibt ein Ablauf keinen anderen.
- `100 Nutzer`
  Stateless Services koennen horizontal skaliert werden. Mehr Container teilen sich die Arbeit.
- `1000 Nutzer`
  Die wichtigsten Skalierungshebel sind mehr Container, mehr CPU, mehr Speicher, spaeter Queueing und Datenbank-Optimierung.

Kernsatz:

"Dieses System skaliert, weil Verantwortlichkeiten getrennt sind und unabhaengig laufen koennen."

## Wichtige Parameter einfach erklaert

- `journey_id`
  Eine ID fuer eine komplette Terminreise von Anfang bis Ende.

- `correlation_id`
  Eine gemeinsame ID, die zusammengehoerende Nachrichten und Events verbindet.

- `trace_id`
  Eine tiefere technische ID fuer Fehlersuche und Ablaufverfolgung.

- `booking_reference`
  Unsere interne Buchungs-ID fuer die Terminseite.

- `provider_reference`
  Die externe Buchungs-ID auf der Provider-Seite.

- `message_id`
  Die ID fuer die Nachricht auf der Kommunikationsseite. Damit laesst sich verfolgen, welche eingehende oder ausgehende Nachricht zu diesem Ablauf gehoert.

- `lekab_job_id`
  Die Workflow-Job-ID auf der LEKAB-Seite. Das ist nicht dasselbe wie `message_id`.

- `appointment_date`
  Das Datum, das in Reminder-Ablaufen gezeigt wird.

- `appointment_time`
  Die Uhrzeit, die in Reminder-Ablaufen gezeigt wird.

- `selected_action`
  Die Aktion, die in einem Reminder-Ablauf ausgewaehlt wurde, zum Beispiel `keep`, `reschedule`, `cancel` oder `call_me`.

## Neue technische Monitoring-Sicht

Der Monitoring-Bereich hat jetzt tiefere technische Tabs:

- `Timeline`
  Zeigt Events in zeitlicher Reihenfolge, mit Zeitstempel, `event_type`, `journey_id`, `correlation_id` und `trace_id`.
- `Trace`
  Hilft dir, eine einzelne Anfragekette durch das System zu verfolgen.
- `Performance`
  Zeigt simulierte Metriken wie durchschnittliche Antwortzeit, maximale Antwortzeit und Events pro Sekunde.

Gute Praesentationssaetze:

- "Diese Sicht zeigt, was im System wirklich passiert."
- "Mit correlation_id kannst du eine einzelne Anfrage durch das System verfolgen."
- "Das beweist, dass das System nicht nur Messaging ist, sondern echte Prozess-Orchestrierung."

## Empfohlene Reihenfolge fuer die Demo

1. Starte mit `Standard-Terminbuchung`.
2. Mache mit `Verschiebung` weiter.
3. Zeige `Absage`.
4. Beende mit `Kein Slot und Eskalation` oder `Provider-Fehler`.
