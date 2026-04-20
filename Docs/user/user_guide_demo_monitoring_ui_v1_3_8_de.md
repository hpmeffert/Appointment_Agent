# Benutzerleitfaden v1.3.8

## Was jetzt moeglich ist

Du kannst jetzt in der Demo zeigen, wie aus einer Kundenantwort ein fachlicher Aktionskandidat wird.

Beispiele:

- `Bitte Termin absagen`
- `Naechste Woche passt`
- `Der erste`
- `05 Mai, 16:00`

## Wo du es oeffnest

- Hauptdemo: `/ui/demo-monitoring/v1.3.8`
- Reminder-Einstieg: `/ui/reminder-cockpit/v1.3.8`

## Einfache Erklaerung

Das System macht jetzt vier Schritte:

1. Antwort empfangen
2. in ein sicheres internes Kommunikationsereignis umwandeln
3. die wahrscheinliche Nutzerabsicht erkennen
4. die naechste interne Termin-Aktion vorbereiten

## Wichtige Felder im Message Monitor

- `Reply Intent`
  Die wahrscheinliche Bedeutung der Antwort.
- `Action Candidate`
  Die interne Aktion, die die Plattform als Naechstes anfordern wuerde.
- `Interpretation State`
  `safe` bedeutet: die Bedeutung ist klar. `ambiguous` bedeutet: es gibt mehrere moegliche Bedeutungen. `review` bedeutet: ein Mensch sollte pruefen.
- `Date/Time Candidates`
  Datums- oder Uhrzeitangaben, die im Text gefunden wurden.
