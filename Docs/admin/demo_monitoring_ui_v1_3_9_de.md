# Demo Monitoring UI v1.3.9 Patch 9

## Was sich geaendert hat

Patch 9 erweitert das `v1.3.9`-Cockpit um den Kalender-Regression-Fix auf Basis der gestuften interaktiven Journey, LEKAB-Auth-Diagnostik und Google-Demo-Kalender-Linkage.

Die Hauptpunkte sind:

- sichtbare Reply-Buttons in `Messages and Customer Journey`
- gemeinsame Button-Definitionen fuer UI-Simulation und echte RCS-Suggestions
- gefuehrte Folgeschritte fuer relatives Fenster, Datumsvorschlag und Zeitvorschlag
- sichtbarer Operator-Zustand fuer gewaehlten Button, aktuellen Journey-Schritt und Auswahlquelle
- sichtbare Real-Mode-Payload fuer ausgehende RCS-Suggestion-Buttons
- persistiertes `customer_journey_message`-Mirroring fuer das Live-Dashboard
- `/rime/seturl`-Runtime-Konfiguration der Callback-URLs ueber die aktiven LEKAB-Settings
- echte Callback-Follow-up-Nachrichten, die die Journey in das naechste sichtbare Button-Set bewegen koennen
- wiederhergestelltes Google-Calendar-Write-Format nach dem echten Confirm-Schritt

## Gefuehrte Interaktionsschritte

Die gestufte Journey unterstuetzt jetzt:

1. Initiale Auswahl
   `Bestaetigen`, `Verschieben`, `Absagen`
2. Relative Terminwahl
   `Diese Woche`, `Naechste Woche`, `Diesen Monat`, `Naechsten Monat`, `Naechster freier Slot`
3. Datumswahl
   explizite vorgeschlagene Daten
4. Zeitwahl
   explizite vorgeschlagene Uhrzeiten

## Gemeinsame Vertraege

Der Szenario-Katalog fuehrt jetzt:

- `available_actions`
- `suggestion_buttons`
- `next_step_map`
- `real_channel_payload`
- `journey_step_type`

Diese Werte werden wiederverwendet in:

- der Cockpit-UI
- der Simulations-Klicklogik
- den Szenario-Artefakten
- den ausgehenden Real-Mode-Message-Payloads

## Sichtbares Operator-Verhalten

Der Operator sieht jetzt:

- welches Button-Set aktiv ist
- welcher Button zuletzt gewaehlt wurde
- ob der Pfad aus `simulation_click` oder `real_callback_or_test_path` kam
- welcher Journey-Schritt aktuell aktiv ist
- welche RCS-Suggestion-Payload im Real-Modus vorbereitet ist

## Versionssichtbarkeit

Die sichtbare Cockpit-Version ist `v1.3.9-patch9`.

Sie erscheint in:

- dem Cockpit-Header
- der Help-Payload
- dem Route-Contract

## Runtime-Hinweise

- Es wurde keine Breaking Change fuer die `v1.3.9`-Basisroute eingefuehrt.
- Patch-Aliase von `v1.3.9-patch1` bis `v1.3.9-patch9` zeigen auf dieselbe aktuelle Shell.
- Szenario-Evidenzdateien werden weiterhin nach `runtime-artifacts/demo-scenarios/v1_3_9` geschrieben.
- Diese Runtime-Artefakte bleiben lokal und duerfen nicht committet werden.
- Real-Mode-Reminder-Sends verwenden jetzt die persistierten LEKAB-Runtime-Settings statt eines reinen Cockpit-Platzhalterpfads.
- Die Callback-URL-Bridge speichert und meldet die aktiven Incoming- und Receipt-Callback-URLs fuer `/rime/seturl`.
- LEKAB `/rime/seturl` verwendet jetzt die providerspezifischen Payload-Felder `channels`, `incomingtype`, `incomingurl`, `receipttype` und `receipturl`.
- Fuer Webhook.site muss `/rime/seturl` die Capture-URL `https://webhook.site/<tokenId>` verwenden; das Auslesen der Callbacks laeuft separat ueber die Token-API `https://webhook.site/token/<tokenId>/...`.
- Die Callback-Normalisierung akzeptiert jetzt sowohl GET-artige Callback-Parameter als auch POST-Payloads, bevor das Ergebnis in den Dashboard Demonstrator gespiegelt wird.
- Google-Demo-Erzeugung und bestaetigte Booking-Writes nutzen jetzt die ausgewaehlte Adresse als Source of Truth fuer Titel, strukturierte Beschreibung und stabile Correlation-/Booking-/Appointment-/Address-Metadaten.
