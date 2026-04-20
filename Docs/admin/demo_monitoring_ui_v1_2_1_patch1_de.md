# Admin Guide Demo Monitoring UI v1.2.1-patch1

Version: v1.2.1-patch1
Sprache: DE

## Neuer Fokus

Dieser Patch fuegt eine eigene Seite `RCS Einstellungen` hinzu.

Sie ist ueber den Kopfbereich erreichbar:
- `Einstellungen`
- `Einstellungen -> RCS`

## Wofuer die Seite da ist

Sie gibt Operatoren einen klaren Ort fuer:
- Environment- und Workspace-Werte
- Authentifizierung
- RCS Einstellungen
- SMS Einstellungen
- Addressbook-/Kontaktauflösung
- Diagnostik und Readiness

## Speichern und Laden

Die Werte werden lokal in einem SQLite-basierten Konfigurationsspeicher gesichert.

Wichtig:
- normale Felder werden direkt geladen
- Geheimnisse werden gespeichert, aber nur maskiert als `********` angezeigt
- leere Secret-Felder bedeuten: bestehendes Secret behalten
