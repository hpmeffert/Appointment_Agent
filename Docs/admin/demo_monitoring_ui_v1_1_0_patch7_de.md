# Demo Monitoring UI v1.1.0 Patch 7

Version: v1.1.0-patch7
Audience: Admin
Language: DE

## Was neu ist

Patch 7 macht den Kommunikationsbereich zu einem echten Simulator.

Die Kundennachricht kann jetzt zeigen:

- Antwortbuttons
- Slot-Buttons
- strukturierte Nachrichtendaten, die spaeter gut zu LEKAB, RCS oder SMS passen

## Kommunikationsmodell

Jede sichtbare Plattformnachricht kann jetzt ein strukturiertes Objekt `communication_message` enthalten.

Wichtige Felder:

- `text`
  Der Hauptsatz, den der Kunde sieht.

- `actions`
  Eine Liste von Antwortbuttons wie `keep`, `reschedule`, `cancel` oder `call_me`.

- `slot_options`
  Eine Liste normalisierter Slot-Objekte.

- `calendar_provider`
  Die Quelle des Slot-Modells. In der Demo ist das oft `simulated`, spaeter auch `google` oder `microsoft`.

- `message_id`
  Die Nachrichtenkennung fuer Monitoring und spaetere Provider-Zuordnung.

- `lekab_job_id`
  Eine simulierte LEKAB-nahe Job-Referenz, damit man spaeter die Ausfuehrung besser verfolgen kann.

## Slot-Modell

Jeder Slot-Button nutzt eine provider-neutrale Struktur.

Wichtige Felder:

- `slot_id`
  Eine eindeutige technische Kennung fuer den Slot in der Demo.

- `label`
  Der gut lesbare Text auf dem Button, zum Beispiel `Tue, 08 Apr, 10:00`.

- `start`
  Geplanter Startzeitpunkt. Im Simulationsmodus kann das noch leer sein.

- `end`
  Geplanter Endzeitpunkt. Im Simulationsmodus kann das noch leer sein.

- `duration_minutes`
  Optionale Dauer, wenn der Provider sie schon kennt.

- `calendar_provider`
  Aus welchem Kalenderpfad der Slot kommt.

## Was beim Klick passiert

Wenn ein Antwortbutton oder Slot-Button geklickt wird, aktualisiert das Cockpit jetzt:

- sichtbares Transkript
- Zusammenfassung der aktuellen Story
- Operator-Zusammenfassung
- Monitoring-Timeline
- Monitoring-Trace
- lokalen Interaktionsstatus

## Monitoring-Events

Patch 7 fuegt lokale Demo-Events hinzu wie:

- `message.action.keep.selected`
- `message.action.reschedule.selected`
- `message.action.cancel.selected`
- `message.action.call_me.selected`
- `slot.option.selected`

Diese Events laufen noch im Demo-Kontext, sind aber schon so geformt, dass sie spaeter gut weiterverwendet werden koennen.

## Beziehung zu Simulation und Google

- Die interaktiven Kommunikationsbuttons arbeiten im Demo-Zustand im Cockpit.
- Google Demo Control bleibt fuer Kalender-Vorbereitung und Aufraeumen zustaendig.
- Simulation schreibt nicht in den Google Kalender.
- Test schreibt nur ueber das konfigurierte Google-Testsetup.

## Wartbarkeitsregel

Der neue Interaktionscode enthaelt bewusst englische Inline-Kommentare.

Diese Kommentare erklaeren:

- warum Zustandswechsel existieren
- wie Aktionen auf Szenarioschritte abgebildet werden
- wie Slots normalisiert werden
- wie die UI provider-neutral bleibt
- wie das Design spaeter zu LEKAB-Antwortaktionen passt
