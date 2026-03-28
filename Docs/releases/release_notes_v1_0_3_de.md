# Release Notes v1.0.3 (DE)

- Die Docker-Laufzeit wurde gehaertet, damit der Appointment Agent mit `docker compose up --build` gebaut und gestartet werden kann.
- Die Doku-Pfadauflosung wurde Linux-sicher gemacht, damit die Dokumentationsrouten auch im Docker-Container funktionieren.
- `/health` wurde fuer einfache Laufzeitpruefungen hinzugefuegt.
- Docker-Helferskripte fuer Start und Smoke-Test wurden ergaenzt.
- Ein neuer Appointment-Reminder-Flow mit Keep, Reschedule, Cancel und Call-me wurde hinzugefuegt.
- Reminder-Demo-Szenarien sowie Reminder-bezogene Audit- und CRM-Vorbereitungswege wurden ergaenzt.
- Der gemeinsame App-Header und die Help-Ausgabe zeigen jetzt den Release-Stand `v1.0.3`.
- README, Docker-Hinweise, Admin Guide, User Guide und Demo Guide wurden fuer den Docker-Release erweitert.
