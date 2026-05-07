# Appointment Agent Demo Leitfaden v1.3.10 (DE)

## Demo-Fokus
Diese Release-Linie demonstriert:
- sichere Terminidentifikation
- explizite Auswahl bei mehreren Terminen
- ausschließlich zukunftsgültige Slot-Suche

## Story 1 — Ein Termin, direkt verschieben
### Ziel
Zeigen, dass ein eindeutiger Termin sicher identifiziert und verschoben werden kann.

### Schritte
1. Öffne den `Real`- oder `Simulation`-Flow mit einem bekannten Kunden.
2. Löse eine Erinnerung aus.
3. Wähle `Verschieben`.
4. Zeige, dass der Flow direkt weiterläuft, weil nur ein zukünftiger Termin passt.
5. Wähle einen zukünftigen Slot.
6. Bestätige die Terminänderung.

### Wichtige Punkte
- kein Mehrdeutigkeitsdialog
- nur zukunftsgültige Slots
- finaler Slot wird vor der Mutation erneut geprüft

## Story 2 — Mehrere Termine, Auswahl erforderlich
### Ziel
Zeigen, dass das System nicht rät, wenn ein Kunde mehr als einen relevanten zukünftigen Termin hat.

### Schritte
1. Bereite einen Kunden mit mindestens zwei zukünftigen Terminen vor.
2. Löse `Verschieben` oder `Absagen` aus.
3. Zeige, dass das System zuerst eine Termin-Auswahl anzeigt.
4. Wähle einen Termin explizit aus.
5. Führe danach nur auf diesem Zieltermin die gewünschte Aktion fort.

### Wichtige Punkte
- sichere Mehrdeutigkeitsbehandlung
- klare One-vs-Many-Grenze
- nachvollziehbare Zieltermin-Auswahl

## Story 3 — Zukunftsfilter für Slots
### Ziel
Zeigen, dass das System keine veralteten oder bereits vergangenen Slots anbietet.

### Schritte
1. Starte eine Slot-Suche nahe an der aktuellen Uhrzeit.
2. Zeige, dass am selben Tag bereits vergangene Slots herausgefiltert werden.
3. Wähle einen gültigen zukünftigen Slot.
4. Erkläre, dass der Slot vor der Mutation nochmals geprüft wird.

### Wichtige Punkte
- Mindestvorlaufzeit von `30 Minuten`
- Zukunftsfilter am selben Tag
- geschütztes Verhalten bei `no match` oder `stale slot`

## Operator-Hinweise
- Lasse das Dashboard offen, um Message Flow und State Transitions zu zeigen.
- Nutze die Customer-Journey-Ausgabe, um zu erklären, ob das System genau einen Termin, mehrere Kandidaten oder keinen sicheren Treffer gefunden hat.
- Erwähne, dass `v1.3.10` additiv und non-breaking ist.
