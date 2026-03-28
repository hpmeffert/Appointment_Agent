# Documentation Style Guide

## Ziel

Alle Doku in diesem Projekt soll so geschrieben sein, dass auch eine motivierte 16-jaehrige Person sie verstehen kann.

Das bedeutet:

- kurze Saetze
- einfache Woerter
- Fachbegriffe nur dann, wenn sie wirklich gebraucht werden
- jeder wichtige Begriff wird direkt erklaert
- Parameter werden nicht nur aufgelistet, sondern in ihrer Bedeutung erklaert
- es wird immer gesagt:
  - was etwas ist
  - warum es gebraucht wird
  - was passiert, wenn man es falsch setzt

## Schreibregeln

1. Schreibe zuerst die einfache Erklaerung, dann erst die technische.
2. Erklaere neue Begriffe in einem Satz direkt an der Stelle.
3. Nutze Beispiele mit echten Werten.
4. Vermeide unerklaerte Abkuerzungen.
5. Wenn ein Endpoint Parameter erwartet, beschreibe:
   - Pflicht oder optional
   - Datentyp
   - Zweck
   - Beispielwert
6. Wenn ein Rueckgabewert wichtig ist, erklaere ebenfalls:
   - was das Feld bedeutet
   - wer es spaeter weiterbenutzt
7. Bei Fehlern erklaere:
   - warum der Fehler passieren kann
   - was man als Naechstes tun sollte

## Mini-Format fuer Parameter

Empfohlenes Format:

- `field_name`
  Bedeutung: Was dieses Feld in einfachen Worten macht.
  Typ: z. B. `string`, `boolean`, `datetime`.
  Pflicht: Ja/Nein.
  Beispiel: `"journey-1234"`.

## Mini-Format fuer technische Begriffe

Beispiel:

- `provider_reference`
  Das ist die ID, die das externe System benutzt.
  In unserem Fall ist das zum Beispiel die ID eines Google-Kalendereintrags.
  Wichtig: Das ist nicht unsere eigene Haupt-ID im System.

## Dauerregel fuer dieses Repo

Ab jetzt sollen neue oder geaenderte Doku-Dateien diesem Stil folgen.
