# User Guide Demo Monitoring UI v1.2.1

Version: v1.2.1
Sprache: DE

## Was du jetzt sehen kannst

Das Cockpit zeigt jetzt nicht nur Terminlogik, sondern auch Nachrichtenverkehr.

Der neue `Message Monitor` hilft dir zu verstehen:
- was das System gesendet hat
- was der Kunde zurueckgeschickt hat
- ob die Nachricht ueber `RCS` oder `SMS` lief
- zu welcher Journey oder Buchung die Nachricht gehoert

## Wichtige Begriffe einfach erklaert

- `outbound`: Die Plattform hat die Nachricht gesendet.
- `inbound`: Der Kunde hat die Nachricht zurueckgesendet.
- `channel`: Der technische Kanal, zum Beispiel `RCS` oder `SMS`.
- `status`: Der aktuelle Zustand der Nachricht.
- `journey_id`: Die Workflow-ID fuer die Kundenreise.
- `booking_reference`: Die Termin-ID zur Nachricht.

## Filter

Du kannst nach diesen Parametern filtern:
- `channel`
- `direction`
- `status`

## Detailkarte

Wenn du eine Nachrichtenzeile anklickst, siehst du:
- Provider-Bezug
- Kunden-/Kontaktbezug
- Telefonnummer
- Journey-Bezug
- Buchungsbezug
- Nachrichtentext
- optionale Aktionen
