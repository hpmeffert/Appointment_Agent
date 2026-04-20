# User Guide Demo Monitoring UI v1.2.1-patch3

Version: v1.2.1-patch3
Audience: User
Language: DE

## Was diese Oberflaeche macht

Das Cockpit ist die Operator-Sicht auf die Appointment-Agent-Plattform.

Es hilft dabei:
- die Kundenkonversation zu verfolgen
- zu verstehen, was das System im Hintergrund tut
- Kalenderaktionen sicher zu testen
- Messaging-Einstellungen ohne Code-Lesen zu pruefen

## Hauptseiten

- `Dashboard`
  Zeigt aktuelle Story, aktuellen Modus und Operator Summary.
- `Message Monitor`
  Zeigt eingehende und ausgehende Nachrichten in einer gemeinsamen Liste.
- `Reports`
  Zeigt zusammengefasste Kommunikationskarten.
- `Monitoring`
  Zeigt technische Events, Traces und Performance-Infos.
- `Settings`
  Zeigt allgemeine Laufzeitwerte wie Hold-Minuten.
- `Settings -> RCS`
  Zeigt LEKAB-Messaging-Parameter und Readiness.
- `Google Demo Control`
  Steuert Demo-Kalenderaktionen in Simulation oder Test.
- `Help`
  Oeffnet Demo-, User- und Admin-Dokumente.

![Annotierte Cockpit-Uebersicht](/docs/assets/screenshots/v1_2_1_patch3/cockpit-overview.svg)

## Neu in Patch 3

Das Dashboard zeigt jetzt zusaetzlich:
- `How the Platform Works`
- `Demo Storyboard`

So kann ein Operator oder Presenter das Produkt besser erklaeren, ohne das Cockpit zu verlassen.

## Warum die Buttons in diesem Patch anders aussehen

Im Day Mode nutzen Aktionsbuttons jetzt:
- grauen Hintergrund
- weisse Schrift
- staerkeren Rand
- deutlichere Klick-Optik

Das betrifft:
- Demo-Buttons
- Operator-Panel-Buttons
- Slot-Buttons
- Story-Buttons
- Kommunikationsaktionen

## Was die wichtigsten Buttons tun

- `Demo`
  Zeigt den Kundenfluss.
- `Monitoring`
  Schaltet den Dashboard-Bereich auf technische Sicht um.
- `Restart Story`
  Setzt die aktuelle Story auf den Anfang zurueck.
- `Confirm`
  Bestaetigt den gewaehlten Slot.
- `Reschedule`
  Laedt neue Terminoptionen fuer einen vorhandenen Termin.
- `Cancel`
  Stoppt den aktuellen Pfad oder storniert einen Termin.
- `Call Me`
  Fordert einen Rueckruf oder Human Handover an.

## Was passiert, wenn ein Slot geklickt wird

1. Der Slot wird in der Journey gespeichert.
2. Das Backend erstellt einen kurzen Hold.
3. Der Hold wird in der Summary sichtbar.
4. Monitoring speichert das Event.
5. Bei `Confirm` wird erneut geprueft, ob der Slot noch frei ist.

So schuetzt die Plattform gegen parallele Buchungen.

## Google Demo Control Parameter

- `Mode`
  `simulation` aendert keinen echten Google-Kalender.
  `test` darf den konfigurierten Testkalender aendern.
- `From Date`
  Erster Tag fuer die Demo-Termine.
- `To Date`
  Letzter Tag fuer die Demo-Termine.
- `Appointment Type`
  Bestimmt, welche Art Beispieltermine erzeugt werden.
- `Prepare`
  Zeigt nur die Vorschau.
- `Generate`
  Erzeugt Demo-Termine.
- `Delete`
  Loescht Demo-Termine.
- `Reset`
  Loescht und erzeugt den Demo-Zustand neu.

## RCS Settings Seite

Die Seite `Settings -> RCS` erklaert das LEKAB-Setup in einfacher Sprache.

Sie zeigt:
- welche Werte schon gespeichert sind
- welche Secrets maskiert sind
- ob der Adapter bereit ist
- welche Pflichtfelder noch fehlen

![Annotierte RCS-Settings-Seite](/docs/assets/screenshots/v1_2_1_patch3/rcs-settings.svg)

## Wichtige Begriffe

- `ready`
  Der Adapter hat genug Pflichtwerte fuer ein brauchbares Test-Setup.
- `missing fields`
  Diese Werte fehlen noch.
- `warnings`
  Diese blockieren nicht immer, sind aber fuer Operatoren wichtig.
- `SMS fallback`
  Wenn RCS nicht moeglich ist, kann das System auf SMS wechseln.
- `channel_priority`
  Legt fest, welcher Kanal zuerst probiert wird.
