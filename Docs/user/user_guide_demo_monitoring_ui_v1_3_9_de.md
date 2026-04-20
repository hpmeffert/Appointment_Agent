# Benutzerleitfaden v1.3.9 Patch 9

## Was Patch 9 hinzufuegt

Patch 9 behaelt die interaktive Journey aus Patch 7 bei und stellt die zuvor verifizierte Google-Calendar-Ausgabe fuer bestaetigte Real- und Simulations-Reschedules wieder her.

Zusätzlich verbessert Patch 9:

- LEKAB-RCS-Testverbindung mit klareren Auth-Diagnosen
- Google Demo Control mit robusterer Validierung und Refresh-Logik
- erzeugte Google-Termine mit wiederhergestelltem Titel-, Beschreibungs- und Address-/Kontakt-Vertrag

Es gibt jetzt sichtbare Reply-Buttons fuer:

- `Bestaetigen`
- `Verschieben`
- `Absagen`

Wenn `Verschieben` gewaehlt wird, geht derselbe Bereich mit gefuehrten Buttons weiter fuer:

- `Diese Woche`
- `Naechste Woche`
- `Diesen Monat`
- `Naechsten Monat`
- `Naechster freier Slot`

Danach folgt die Journey mit expliziten Datums-Buttons und anschliessend mit expliziten Zeit-Buttons.

## So benutzt du die gefuehrte Journey

1. Oeffne `Dashboard`.
2. Waehle ein `Scenario`.
3. Waehle `Simulation` oder `Real`.
4. Waehle eine `Selected Address`.
5. Klicke `Run Scenario (Simulation)` oder `Run Scenario (Real)`.
6. Bleibe in `Messages and Customer Journey`.
7. Klicke die sichtbaren Reply-Buttons, um die Story weiterzuschalten.

## Was Simulation macht

`simulation` behaelt die Interaktion komplett im Demonstrator.

Jeder Button-Klick:

- aktualisiert die sichtbare Journey
- protokolliert den gewaehlten Button
- schaltet auf den naechsten gefuehrten Schritt
- schreibt Protokoll-, Demo-Log- und Summary-Dateien

## Was Real macht

`real` behaelt dieselbe Operator-Sicht, bereitet aber zusaetzlich die ausgehende RCS-Suggestion-Payload vor.

Dadurch sieht der Operator weiterhin:

- welche Buttons gesendet wurden
- welche Buttons aktuell erwartet werden
- welcher Button oder welche Reply gewaehlt wurde
- welcher Journey-Schritt jetzt aktiv ist

Patch 9 haelt jetzt ausserdem den echten Mobilpfad und den Dashboard-Spiegel zusammen:

- ausgehende reale Reminder nutzen die aktiven LEKAB-Runtime-Settings
- der Adapter setzt `/rime/seturl` mit den persistierten Incoming- und Receipt-Callback-URLs
- eingehende Mobilgeraet-Callbacks aktualisieren den gespeicherten Journey-State
- die sichtbare Button-Zeile bleibt im `real`-Modus read-only und spiegelt das echte Callback-Ergebnis
- Callback-Follow-ups koennen die Journey mit dem naechsten echten Button-Set fortsetzen

## Wichtige Felder

- `scenario_id`
  Die aktuell ausgewaehlte Appointment-Story.
- `mode`
  `simulation` oder `real`.
- `current_step`
  Der aktive gefuehrte Interaktionsschritt wie `relative_choice`, `date_choice` oder `time_choice`.
- `available_actions`
  Die kanonischen Button-Werte des aktuellen Schritts.
- `suggestion_buttons`
  Die lokalisierten Button-Beschriftungen in UI und RCS-Payload.
- `real_channel_payload`
  Die ausgehende RCS-nahe Payload mit Suggestion-Buttons.
- `customer_journey_message`
  Der persistierte aktuelle Real-/Simulation-Message-Vertrag, den das Cockpit fuer den Spiegel nutzt.
- `selected_button`
  Die zuletzt sichtbare Auswahl in der Journey.
- `selected_source`
  Zeigt, ob der Schritt aus einem Simulationsklick oder aus dem Real-/Test-Pfad kam.

## Typischer Operator-Ablauf

1. Starte mit `Termin bestaetigen` oder `Termin verschieben`.
2. Klicke `Verschieben`.
3. Klicke ein relatives Fenster wie `Naechste Woche`.
4. Klicke ein Datum.
5. Klicke eine Uhrzeit.
6. Bestaetige oder storniere den resultierenden Flow.

## Google als Source of Truth

Wenn eine gueltige ausgewaehlte Adresse vorhanden ist, behandelt Patch 9 die Address Database als verbindliche Quelle fuer die Google-Demo-Erzeugung und den bestaetigten Kalender-Write:

- der erzeugte Event-Titel nutzt das Format `<Appointment Type> – <Customer Name>`
- die erzeugte Beschreibung enthaelt die vollstaendige ausgewaehlte Adresse und den Reschedule-/Confirm-Kontext
- die gespeicherten Metadaten behalten stabile `correlation_id`, `booking_reference`, `appointment_id` und `address_id`
- generische Fallback-Namen werden nicht verwendet, solange gueltige Adressdaten vorhanden sind

## Lokal geschriebene Dateien

Szenariolaeufe schreiben weiterhin Evidenzdateien nach:

- `runtime-artifacts/demo-scenarios/v1_3_9`

Diese Dateien sind lokale Laufzeit-Ausgaben und sollen nicht committet werden.
