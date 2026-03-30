# Demo Monitoring UI v1.1.0 Patch 8b

Version: v1.1.0-patch8b
Audience: Admin
Language: DE

## Was Patch 8b veraendert

Patch 8b verbindet drei fruehere Linien zu einem glaubwuerdigen Ablauf:

- Patch 7 interaktive Buttons
- Patch 8 Live-Slot- und Booking-Logik
- Patch 8a Slot-Holds und Schutz gegen Parallelbuchungen

Damit kann das Cockpit jetzt von einem Button-Klick zu echter Slot-Suche, echtem Hold und echtem Booking-Call wechseln.

## Vollstaendige Parametererklaerungen

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Dauer der temporaeren Reservierung.
  Niedriger Wert: Slots kommen schneller zurueck, aber Nutzer haben weniger Zeit.
  Hoeherer Wert: sicherer fuer langsame Nutzer, aber blockierte Slots bleiben laenger weg.
  Demo-Empfehlung: `2`
  Realistische Nutzung: `3-10`, je nach Kanal und Nutzerverhalten.

- `APPOINTMENT_AGENT_BOOKING_WINDOW_DAYS`
  Wie weit die Slot-Suche in die Zukunft schauen darf.

- `APPOINTMENT_AGENT_MAX_SLOTS_PER_OFFER`
  Wie viele Slot-Vorschlaege das System zurueckgeben soll.

- `APPOINTMENT_AGENT_DEFAULT_DURATION_MINUTES`
  Standard-Laenge eines Termins.

- `APPOINTMENT_AGENT_RESCHEDULE_CUTOFF_HOURS`
  Mindestabstand in Stunden, ab wann Verschieben noch erlaubt ist.

- `APPOINTMENT_AGENT_QUIET_HOURS`
  Zeitfenster, in dem das System Kunden nicht stoeren soll.

- `GOOGLE_TEST_MODE_DEFAULT`
  Standardmodus fuer Operatoren.
  `simulation`: keine echten Google-Kalendereintraege
  `test`: schreibt in den konfigurierten Google-Testkalender

## So funktioniert der Schutz gegen Parallelbuchungen

1. Ein Nutzer waehlt einen Slot.
2. Die Plattform erstellt einen temporaeren Hold im eigenen Status.
3. Derselbe Slot soll fuer andere Journeys verschwinden.
4. Vor der finalen Buchung wird Google Kalender noch einmal live geprueft.
5. Wenn Google sich geaendert hat, wird die Buchung blockiert und Alternativen werden gezeigt.

## Warum Google nach dem Hold trotzdem wichtig bleibt

Der Hold schuetzt den Slot innerhalb unserer Plattform.

Google bleibt trotzdem die Live-Wahrheit fuer die Belegung.
