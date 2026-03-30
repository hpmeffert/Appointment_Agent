# User Guide Demo Monitoring UI v1.1.0 Patch 8

Version: v1.1.0-patch8
Audience: User
Language: DE

## Was neu ist

Patch 8 macht das Google-gestuetzte Buchungsverhalten realistischer.

Wenn du einen Slot auswaehlst, kann das Backend jetzt:

- pruefen, ob er noch frei ist
- die Buchung stoppen, wenn ein anderer Termin blockiert
- andere Slots vorschlagen

## Was passiert, wenn ein Slot nicht mehr frei ist

Das System gibt jetzt eine gut verstaendliche Meldung zurueck:

- der ausgewaehlte Slot ist nicht mehr verfuegbar
- bitte waehle einen der Alternativslots

So verhaelt sich die Demo mehr wie ein echtes Kalendersystem.

## Was Create, Cancel und Reschedule machen

- `Create`
  Bucht den Slot, wenn er noch frei ist.

- `Cancel`
  Entfernt die Buchung.

- `Reschedule`
  Prueft den neuen Slot erneut, bevor die Buchung verschoben wird.
