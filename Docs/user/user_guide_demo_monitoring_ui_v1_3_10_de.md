# Appointment Agent Benutzerleitfaden v1.3.10 (DE)

## Umfang
Version `v1.3.10` verbessert zwei Kernverhalten im Appointment-Agent-Demonstrator:
- sicherere Terminidentifikation
- ausschließlich zukunftsgültige Slot-Vorschläge

Ziel ist, dass das System zuerst den richtigen Termin identifiziert und danach nur noch gültige zukünftige Daten und Uhrzeiten anbietet.

## Was sich geändert hat
- Das System kann jetzt stärker mit Terminreferenzen wie Reservierungsreferenzen, Appointment-/Kalenderreferenzen, Correlation-Referenzen, Kundennummern und normalisierten Telefonnummern arbeiten.
- Wenn mehrere zukünftige Termine zu einem Kunden passen, rät das System nicht mehr. Es fragt nach, welcher Termin bearbeitet werden soll.
- Slot-Vorschläge sind ausschließlich zukunftsgültig und berücksichtigen eine Mindestvorlaufzeit.
- Ein ausgewählter Slot wird vor der Mutation erneut geprüft, damit veraltete oder bereits vergangene Slots nicht versehentlich bestätigt werden.

## Kundenerlebnis
### 1. Klare Terminzuordnung
Wenn der Kunde nur einen relevanten zukünftigen Termin hat, läuft der Prozess direkt weiter.

### 2. Explizite Auswahl bei mehreren Terminen
Wenn mehr als ein Termin passt, fragt das System, welcher Termin bestätigt, abgesagt oder verschoben werden soll.

### 3. Nur zukünftige Slot-Vorschläge
Das System schlägt nur noch Slots vor, die in der Zukunft noch gültig sind. Alte oder am selben Tag bereits abgelaufene Slots werden herausgefiltert.

## Erwartetes Verhalten
- `Bestaetigen` behält den aktuellen Termin nur dann bei, wenn das Ziel eindeutig aufgelöst ist.
- `Verschieben` läuft nur weiter, wenn der betroffene Termin bekannt ist.
- `Absagen` betrifft nur den aufgelösten Termin und rät niemals zwischen mehreren Terminen.
- `Kein Treffer` führt zu einer sicheren Nachfrage oder einer No-Op-Antwort.

## Sicherheits-Defaults
- Mindestvorlaufzeit: `30 Minuten`
- Maximales Suchfenster: durch die konfigurierte Booking-Window-Grenze begrenzt
- Maximale Anzahl vorgeschlagener Daten/Uhrzeiten: durch die aktive Flow-Konfiguration begrenzt
- Silence Threshold Default: `1300 ms`

## Typischer Ablauf
1. Erinnerung wird zugestellt.
2. Der Kunde wählt `Verschieben`.
3. Das System löst auf, welcher Termin gemeint ist.
4. Falls mehrere Termine existieren, fragt das System nach dem konkreten Zieltermin.
5. Das System schlägt nur zukünftige Slots vor.
6. Der Kunde wählt einen Slot.
7. Der Slot wird vor der Buchungsmutation erneut geprüft.

## Hinweise
- `v1.3.10` ist additiv und soll geschütztes `v1.x`-Verhalten nicht brechen.
- Mehrdeutige Terminaktionen werden absichtlich blockiert, bis der Zieltermin explizit feststeht.
