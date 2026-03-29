# Demo Monitoring UI v1.1.0 Patch 6

Version: v1.1.0-patch6
Audience: Admin
Language: DE

## Was neu ist

`Google Demo Control` unterstuetzt jetzt:

- `from_date`
- `to_date`
- `appointment_type`

Dadurch wird die Demo-Erzeugung kontrollierter und realistischer.

## Wichtige Parameter

- `from_date`
  Der erste Tag, den der Demo-Generator verwenden darf.

- `to_date`
  Der letzte Tag, den der Demo-Generator verwenden darf.

- `appointment_type`
  Das Inhaltsmuster, das Titel und Formulierungen des Termins bestimmt.
  Unterstuetzte Werte sind `dentist`, `wallbox`, `gas_meter` und `water_meter`.

- `count`
  Wie viele Termine im gewaehlten Datumsbereich erzeugt werden sollen.

## Wichtige Regel

Der ausgewaehlte Datumsbereich wird validiert.

- `from_date` muss vor oder gleich `to_date` sein
- der maximale Bereich folgt dem konfigurierten Buchungsfenster
