# User Guide Demo Monitoring UI v1.1.0 Patch 8b

Version: v1.1.0-patch8b
Audience: User
Language: DE

## Was passiert, wenn du einen Button klickst

Patch 8b macht die Demo realistischer.

Wenn du `Verschieben` klickst, aendert das System nicht nur den Bildschirm.
Es laedt wirklich die naechsten verfuegbaren Termine aus dem Booking-Backend.

## Was passiert, wenn du einen Slot klickst

Wenn du einen Slot waehlst:

1. wird der Slot normalisiert
2. wird ein temporaerer Hold erstellt
3. zeigt die UI, dass der Slot kurzzeitig reserviert ist
4. wartet das System auf deine Bestaetigung

## Warum ein Slot nur temporaer reserviert wird

So verhindert das System Doppelbuchungen.

## Warum ein Slot ploetzlich nicht mehr verfuegbar sein kann

Ein Slot kann verschwinden, weil:

- ein anderer Nutzer ihn genommen hat
- der Hold abgelaufen ist
- ein echter Google-Kalendereintrag ihn blockiert

Dann zeigt das System eine klare Meldung und bietet andere Zeiten an.
