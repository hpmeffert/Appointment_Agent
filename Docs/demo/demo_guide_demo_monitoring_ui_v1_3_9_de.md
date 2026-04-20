# Demo Leitfaden v1.3.9 Patch 9

## Fokus von Patch 9

Patch 9 behaelt die button-getriebene Journey bei und stellt den zuvor funktionierenden Google-Calendar-Vertrag nach dem echten Confirm-Schritt wieder her.

Die wichtigste Aussage ist:

- "Der Operator sieht jetzt dieselben Reply-Buttons, die auch in der echten RCS-Payload stehen, und jede Auswahl schaltet die Journey in den naechsten gefuehrten Schritt."

## Story 1: Termin bestaetigen

- Oeffne `Dashboard`
- Waehle `Termin bestaetigen`
- Bleibe in `Simulation`
- Klicke `Run Scenario (Simulation)`
- Klicke in `Messages and Customer Journey` auf `Bestaetigen`

Was du sagen kannst:

- "Das ist der kuerzeste sichere Pfad. Der Kunde bestaetigt den bestehenden Termin und die Journey protokolliert die kanonische Confirm-Aktion."

## Story 2: Verschieben mit gefuehrten relativen Auswahlfenstern

- Waehle `Termin verschieben`
- Starte das Szenario
- Klicke `Verschieben`
- Klicke `Naechste Woche`
- Klicke eines der vorgeschlagenen Daten
- Klicke eine der vorgeschlagenen Uhrzeiten

Was du sagen kannst:

- "Die Journey stoppt nicht mehr bei einer freien Reschedule-Antwort. Sie geht jetzt sichtbar ueber relatives Fenster, Datumswahl und Zeitauswahl weiter."

## Story 3: Real-Modus mit sichtbarer RCS-Suggestion-Payload

- Bleibe im gleichen oder waehle ein anderes Szenario
- Schalte auf `Real`
- Klicke `Run Scenario (Real)`
- Schaue auf `Messages and Customer Journey`
- Zeige die sichtbare Button-Leiste und den Hinweis auf die RCS-Suggestion-Payload
- Erklaere, dass die Leiste im `real`-Modus nicht klickbar bleibt und nur das echte Geraete-Ergebnis spiegelt
- Wenn ein Callback ankommt, aktualisiere den Payload und zeige den real ausgewaehlten Button-Zustand

Was du sagen kannst:

- "Der Operator sieht exakt das Suggestion-Set, das die ausgehende RCS-Nachricht traegt. Real behaelt dieselbe Journey, macht aber die Button-Payload sichtbar."

## Story 4: Reales Reschedule-Confirm schreibt den korrekten Kalendereintrag

- Bleibe in `Real`
- Starte einen reminder-getriebenen Reschedule-Flow
- Klicke `Verschieben`
- Klicke Scheduling-Fenster, Datum und Uhrzeit
- Pruefe, dass danach `Bestaetigen`, `Verschieben`, `Absagen` erscheinen
- Klicke `Bestaetigen`
- Zeige den resultierenden Google-Testkalender-Eintrag

Was du sagen kannst:

- "Nach der Zeitauswahl geht die Journey jetzt in einen expliziten Confirm-Schritt statt die Zeitbuttons zu wiederholen."
- "Der Google-Kalendereintrag nutzt die ausgewaehlte Adresse als Source of Truth fuer Titel, Beschreibung und Metadaten."

## Story 5: Echter Callback-Spiegel mit Follow-up

- Bereite gueltige LEKAB-Runtime-Settings vor
- Verifiziere, dass `/rime/seturl` aus den persistierten Callback-URLs konfiguriert wird
- Starte einen Real-Run oder Reminder-Pfad
- Druecke einen Reply-Button auf dem Mobilgeraet
- Zeige, wie das Cockpit den Callback spiegelt
- Zeige die naechste Follow-up-Nachricht, die das System wieder nach draussen sendet

Was du sagen kannst:

- "Das Dashboard ist im Real-Modus nicht mehr die Quelle der Auswahl. Es ist der Spiegel des echten Mobil-Callbacks."
- "Der Adapter nutzt dieselben aktiven Runtime-Settings fuer Outbound-Send und Callback-URL-Registrierung."

## Story 6: Absagen in derselben Journey-Shell

- Waehle `Termin absagen`
- Starte das Szenario
- Klicke `Absagen`

Was du sagen kannst:

- "Absagen wird nicht mehr nur aus Freitext abgeleitet. Es ist jetzt auch eine sichtbare gefuehrte Aktion in der Customer Journey."

## Wichtige Parameter zum Benennen

- `available_actions`
- `suggestion_buttons`
- `real_channel_payload`
- `current_step`
- `selected_button`
- `selected_source`
- `expected.action`
- `actual.action`
