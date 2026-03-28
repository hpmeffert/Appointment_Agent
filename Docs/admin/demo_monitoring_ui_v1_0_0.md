# Demo Monitoring UI v1.0.0 Admin Notes

## Was ist das?

Diese UI ist eine Vorfuehr-Oberflaeche.
Sie ist nicht dafuer gedacht, schon ein fertiges Admin-Portal zu sein.

Sie hat zwei Aufgaben:

1. zeigen, wie sich der Termin-Ablauf fuer einen Kunden anfuehlt
2. gleichzeitig zeigen, was technisch im System passiert

## Die 3 Modi

- `Demo`
  Nur die linke Seite ist wichtig.
  Diese Sicht ist gut fuer Verkauf, Management und einfache Produkt-Demos.

- `Monitoring`
  Nur die rechte Seite ist wichtig.
  Diese Sicht ist gut fuer Technik, Architektur und Fehlersuche.

- `Combined`
  Beide Seiten sind gleichzeitig sichtbar.
  Diese Sicht ist am besten, um den Zusammenhang zwischen Klick und Systemreaktion zu zeigen.

## Wichtige Begriffe

- `journey_id`
  Die ID fuer einen kompletten Termin-Ablauf.

- `correlation_id`
  Die technische Nachverfolgungs-ID fuer Events und Audit.

- `booking_reference`
  Unsere interne Termin-ID.

- `provider_reference`
  Die externe ID beim Provider, zum Beispiel bei Google.

- `audit log`
  Eine Liste wichtiger Entscheidungen des Systems.

## Wichtige Endpunkte

- `/ui/demo-monitoring/v1.0.0`
  Zeigt die komplette UI im Browser.

- `/api/demo-monitoring/v1.0.0/scenarios`
  Liefert alle Simulations-Szenarien als JSON.

- `/api/demo-monitoring/v1.0.0/help`
  Liefert eine kleine technische Uebersicht ueber Modi und Szenarien.
