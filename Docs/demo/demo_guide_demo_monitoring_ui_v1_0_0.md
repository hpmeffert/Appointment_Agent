# Demo Guide Demo Monitoring UI v1.0.0

## Grundsatz fuer die Vorfuehrung

Sage am Anfang:

"On the left you see the customer. On the right you see what the system is doing."

Wichtig:

- immer `Combined` Modus nutzen
- langsam sprechen
- links immer die Nutzerseite erklaeren
- rechts immer die Systemseite erklaeren

## Szenario 1 - Standard Booking

Schritte:

1. `Combined` Modus waehlen
2. Szenario `Standard Booking` waehlen
3. `Next Step` klicken
4. sagen:
   "The message comes in via messaging and enters the system."
5. wieder `Next Step` klicken
6. sagen:
   "Now we connect to Google Calendar and check availability."
7. wieder `Next Step` klicken
8. sagen:
   "The user selects a slot. Now we have a concrete intent."
9. wieder `Next Step` klicken
10. sagen:
   "Now we create a real booking and update backend systems."

Abschluss:

"This is not a chatbot. This is process automation."

## Szenario 2 - Reschedule

Schritte:

1. Szenario `Reschedule` waehlen
2. erklaeren:
   "This is not a new booking. This is a change to an existing booking."
3. rechts auf `provider_reference` zeigen
4. sagen:
   "This is the external Google-side reference."
5. den Update-Pfad im Event-Bereich erklaeren

## Szenario 3 - Cancellation

Schritte:

1. Szenario `Cancellation` waehlen
2. erklaeren:
   "The cancellation starts in messaging, but it has to finish cleanly in the backend too."
3. rechts `crm.booking.cancel.requested` zeigen
4. erklaeren, dass auch das CRM vorbereitet wird

## Szenario 4 - No Slot and Escalation

Schritte:

1. Szenario `No Slot and Escalation` waehlen
2. sagen:
   "Good automation must know when it cannot solve the problem alone."
3. erklaeren:
   - keine freien Slots gefunden
   - Alternativen werden angeboten
   - menschliche Hilfe wird vorbereitet

## Szenario 5 - Provider Failure

Schritte:

1. Szenario `Provider Failure` waehlen
2. sagen:
   "Even when the provider fails, the system still reacts in a clear and safe way."
3. rechts Event-, Audit- und Eskalationsbereich zeigen

## Technische Kernerklaerung fuer Rueckfragen

- `journey_id`
  Ein kompletter Termin-Ablauf hat seine eigene ID.

- `correlation_id`
  Damit verbindet man passende Events miteinander.

- `trace_id`
  Diese ID hilft bei technischer Fehlersuche.

- `booking_reference`
  Unsere eigene interne Termin-ID.

- `provider_reference`
  Die externe Google-ID.

## Antwort auf die 20-Nutzer-Frage

Wenn jemand fragt:
"What happens if 20 users book at the same time?"

Dann kannst du sagen:

- jeder Nutzer bekommt einen eigenen `journey_id`
- die Ablaeufe stoeren sich nicht gegenseitig
- Slots werden vorsichtig behandelt
- Konflikte fuehren zu Fallback oder neuen Optionen
