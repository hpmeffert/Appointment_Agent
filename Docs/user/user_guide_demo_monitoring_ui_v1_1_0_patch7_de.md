# User Guide Demo Monitoring UI v1.1.0 Patch 7

Version: v1.1.0-patch7
Audience: User
Language: DE

## Was fuer dich neu ist

Die Demo ist jetzt nicht mehr nur eine Textansicht.

Du kannst jetzt klicken auf:

- `Behalten`
- `Verschieben`
- `Absagen`
- `Zurueckrufen lassen`
- echte Slot-Buttons mit Datum und Uhrzeit

## Was die Buttons bedeuten

- `Behalten`
  Der Termin bleibt wie er ist.

- `Verschieben`
  Die Demo oeffnet einen neuen Schritt zur Slot-Auswahl.

- `Absagen`
  Die Demo wechselt in den Absagepfad.

- `Zurueckrufen lassen`
  Die Demo zeigt einen Rueckruf- oder Human-Handover-Pfad.

## Was nach einem Klick passiert

Wenn du einen Button klickst, aktualisiert sich die Seite an mehreren Stellen:

- das Chat-Transkript waechst
- die Zusammenfassung der aktuellen Story aendert sich
- die Operator-Zusammenfassung aendert sich
- das Monitoring zeigt ein neues technisches Event

## Was Slot-Buttons machen

Ein Slot-Button ist eine anklickbare Terminwahl wie `Freitag 09:00`.

Wenn du ihn klickst:

- wird der ausgewaehlte Slot gemerkt
- oeffnet sich der passende naechste Demo-Schritt, wenn es ihn gibt
- schreibt das Monitoring `slot.option.selected`

## Wie Dashboard, Monitoring und Google Demo Control zusammenpassen

- `Dashboard`
  Zeigt die Story und die interaktive Kommunikation.

- `Monitoring`
  Zeigt technische Events und Trace-Informationen.

- `Google Demo Control`
  Bereitet Demo-Kalendereintraege vor, erzeugt sie, loescht sie oder setzt sie zurueck.

## Wichtiger Hinweis

Die interaktive Kommunikation in Patch 7 ist Demo-Logik im Cockpit.

Das Erzeugen und Loeschen echter Google-Kalendereintraege passiert weiter ueber `Google Demo Control`.
