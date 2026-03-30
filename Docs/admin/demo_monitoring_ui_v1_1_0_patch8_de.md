# Demo Monitoring UI v1.1.0 Patch 8

Version: v1.1.0-patch8
Audience: Admin
Language: DE

## Was Patch 8 hinzufuegt

Patch 8 behaelt dieselbe Incident-artige UI, aber das Google-Backend wird realistischer.

Neue Google-Endpunkte unterstuetzen jetzt:

- Live-Slot-Abruf
- Verfuegbarkeitspruefung vor der Buchung
- Konflikterkennung
- alternative Slot-Vorschlaege
- Create-, Cancel- und Reschedule-Flows

## Wichtige Endpunkte

- `/api/google/v1.1.0-patch8/availability/slots`
  Liefert normalisierte freie Slots.

- `/api/google/v1.1.0-patch8/availability/check`
  Prueft, ob ein ausgewaehlter Slot noch frei ist.

- `/api/google/v1.1.0-patch8/booking/create`
  Erstellt eine Buchung, wenn der Slot noch frei ist.

- `/api/google/v1.1.0-patch8/booking/cancel`
  Sagt eine bestehende Buchung ab.

- `/api/google/v1.1.0-patch8/booking/reschedule`
  Prueft den neuen Slot erneut und verschiebt dann die Buchung.

## Provider-neutrales Slot-Modell

Jeder Slot wird normalisiert als:

- `slot_id`
- `start`
- `end`
- `label`
- `available`
- `calendar_provider`

Das ist wichtig, weil die UI bei einem spaeteren Wechsel von Simulation auf Google oder Microsoft nicht neu gebaut werden soll.

## Konfliktbehandlung

Bevor eine Buchung erstellt oder verschoben wird, prueft der Adapter auf Ueberschneidungen.

Bei einem Konflikt:

- wird die Buchung blockiert
- wird `slot.conflict_detected` erzeugt
- werden alternative Slots zurueckgegeben

## Wichtige Monitoring-Labels

- `slot.checked`
- `slot.conflict_detected`
- `booking.created`
- `booking.failed`
- `booking.rescheduled`
- `booking.cancelled`
