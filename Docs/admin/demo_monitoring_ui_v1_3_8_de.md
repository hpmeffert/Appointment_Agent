# Demo Monitoring UI v1.3.8

## Was dieses Release hinzufuegt

Dieses Release fuegt die **Reply-to-Action Engine** in die kombinierte Demo-Shell ein.

Das bedeutet: Die Plattform zeigt nicht nur, dass eine Kundenantwort angekommen ist. Sie zeigt auch:

- was die Antwort wahrscheinlich bedeutet
- welche interne Termin-Aktion angefordert wuerde
- ob diese Interpretation sicher, mehrdeutig oder pruefpflichtig ist

## Wichtige Routen

- Kombinierte Demo UI: `/ui/demo-monitoring/v1.3.8`
- Eigenstaendiges Reminder Cockpit: `/ui/reminder-cockpit/v1.3.8`
- LEKAB Monitor API: `/api/lekab/v1.3.8/monitor`

## Wichtige Parameter

- `normalized_event_type`
  Zeigt, welche Art Kommunikationsereignis passiert ist. Beispiele: `message.delivered`, `message.failed`, `message.reply_received`.
- `reply_intent`
  Das ist die erste fachliche Bedeutung, die der Parser in der Antwort erkennt. Beispiele: `cancel`, `confirm`, `reschedule`, `appointment_next_week`.
- `reply_datetime_candidates`
  Das ist eine Liste mit gefundenen Datums- oder Uhrzeitangaben aus der Antwort.
- `action_candidate`
  Das ist die interne Termin-Aktion, die das System als naechsten Schritt anfordern wuerde.
- `interpretation_state`
  Zeigt, wie sicher die Interpretation ist. Werte: `safe`, `ambiguous`, `review`.
- `interpretation_confidence`
  Ein einfacher Sicherheitswert zwischen `0.0` und `1.0`.

## Worauf Operatoren achten sollten

1. `Message Monitor` oeffnen.
2. Die neueste eingehende Antwort auswaehlen.
3. `Reply Intent` lesen.
4. `Action Candidate` lesen.
5. `Interpretation State` pruefen.

Wenn der Zustand `safe` ist, ist die naechste Plattform-Aktion klar.

Wenn der Zustand `ambiguous` oder `review` ist, sollte ein Operator den Fall zuerst pruefen.
