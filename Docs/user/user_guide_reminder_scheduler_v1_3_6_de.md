# User Guide Reminder Scheduler v1.3.6

Version: v1.3.6
Audience: User
Language: DE

## Was das Cockpit zeigt

Dieses Cockpit zeigt den Reminder-Weg in einer einfachen Ansicht.

Es zeigt:
- woher der Termin kommt
- wie Google Calendar verbunden ist
- welche Termindaten gespeichert sind
- welche Reminder-Regeln aktiv sind
- was die Vorschau daraus macht
- welche Reminder Jobs offen sind
- ob die Laufzeit gesund ist
- welche stabilen IDs die Google-Quelle mit dem Reminder-Plan verbinden

## So nutzt man die Seiten

- `Dashboard`
  Hier anfangen. Die ganze Story steht auf einer kurzen Seite.
- `Source`
  Hier sieht man die Terminquelle und die Google-Verbindung.
- `Details`
  Hier stehen Name, Zeit, Ort und Terminart.
- `Policy`
  Hier sieht man, wann Erinnerungen gesendet werden.
- `Preview`
  Hier sieht man die Reihenfolge der Erinnerungen, bevor etwas gesendet wird.
- `Jobs`
  Hier sieht man geplante, aktualisierte, abgebrochene und gesendete Jobs.
- `Health`
  Hier sieht man, ob das System bereit ist.
- `Help`
  Hier stehen die Parameter-Erklaerungen und die Doku-Links.

## Wichtige Parameter in einfachen Worten

- `silence_threshold_ms`
  Wie lange das System wartet, bevor es denkt, dass der Nutzer aufgehört hat zu sprechen.
  In dieser Version ist der Standard `1300 ms`.
- `reminder_offsets_minutes`
  Wie viele Minuten vor dem Termin Erinnerungen geplant werden.
- `google_calendar_id`
  Der Kalender, in dem der verknuepfte Termin liegt.
- `appointment_type`
  Die Art des Termins, zum Beispiel Zahnarzt, Wallbox, Gaszaehler oder Wasserzaehler.
- `quiet_hours`
  Die Zeit, in der keine Erinnerung gesendet werden soll.
- `job_status`
  Zeigt, ob ein Job geplant, aktualisiert, abgebrochen oder gesendet ist.
- `next_due_at`
  Wann das System als Nächstes arbeiten will.
- `worker_status`
  Zeigt, ob der Worker bereit ist.

## Was man in einer Demo sagen kann

- "Dieses Cockpit zeigt den ganzen Reminder-Weg auf einer einzigen Seite."
- "Der Termin kommt aus Google Calendar und wird zu Reminder Jobs."
- "Wenn der Termin verschoben oder abgesagt wird, aendert sich der Plan mit."

## Sprache und Theme

- Mit `EN` oder `DE` im Header kann man die Sprache wechseln.
- Mit `Theme` kann man zwischen Tages- und Nachtmodus wechseln.

## Sicherheits-Hinweis

Diese Version ist eine UI- und Doku-Version.
Sie behaelt das bekannte Layout und erklaert alles in einfacher Sprache.
