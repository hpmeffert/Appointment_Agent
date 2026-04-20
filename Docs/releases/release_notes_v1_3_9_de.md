# Release Notes v1.3.9 Patch 9

## Highlights

- Sichtbare Cockpit-Version auf `v1.3.9-patch9` angehoben
- Gestufte interaktive Reply-Buttons in `Messages and Customer Journey` hinzugefuegt
- Gemeinsame Button-Sets fuer Initial-, Relative-, Datums- und Zeit-Auswahl hinzugefuegt
- Gemeinsame Felder `available_actions`, `suggestion_buttons`, `next_step_map` und `real_channel_payload` im Szenario-Modell hinzugefuegt
- Gefuehrte Simulationssteuerung fuer `Verschieben -> relatives Fenster -> Datum -> Uhrzeit` hinzugefuegt
- Sichtbare Real-Mode-RCS-Suggestion-Payload in derselben Journey-Ansicht hinzugefuegt
- Route-Aliase fuer `patch4`, `patch5`, `patch6`, `patch7`, `patch8` und `patch9` in den aktuellen Shell-Vertrag aufgenommen
- LEKAB-Provider-Testverbindung fuer OAuth/Password-Modus und 401-Diagnostik gehaertet
- Persistierte `/rime/seturl`-Callback-URL-Registrierung fuer Incoming- und Receipt-Callbacks hinzugefuegt
- Webhook.site-Behandlung korrigiert, sodass Capture-URL und Token-API-Fetch-URL in den Runtime-Settings nicht mehr vermischt werden
- LEKAB-`/rime/seturl`-Payloadschema korrigiert auf `channels`, `incomingtype`, `incomingurl`, `receipttype` und `receipturl`
- Real-Mode-Reminder-Sends an die aktiven LEKAB-Runtime-Settings und den Callback-Spiegelpfad angebunden
- Google Demo Control fuer Validierung, Refresh-Verhalten und Address-Link-Persistenz gehaertet
- Erzeugte Google-Event-Titel, Full-Address-Details und Linkage-Metadaten bei gewaehlter Adresse verbessert
- Bestaetigte Google-Calendar-Writes auf das deterministische Format `<Appointment Type> – <Customer Name>` mit strukturierter Address-/Kontext-Beschreibung und stabilen `correlation_id`, `booking_reference`, `appointment_id` und `address_id`-Metadaten zurueckgestellt

## Runtime-Hinweise

- Keine Breaking Change fuer die `v1.3.9`-Basisroute
- Die sichtbare Version in Header und Help ist jetzt `v1.3.9-patch9`
- Real-Mode-Szenariolaeufe verwenden weiterhin den konfigurierten Output-Channel-Pfad
- Real-Mode-Callback-Ergebnisse koennen jetzt den sichtbaren Button-Zustand aktualisieren und Follow-up-Outbounds ausloesen
- LEKAB-Callback-Ingest normalisiert jetzt sowohl GET-artige Callback-Parameter als auch POST-Payloads auf denselben internen Event-Pfad
- Szenario-Artefakte werden weiterhin nur nach `runtime-artifacts/demo-scenarios/v1_3_9` geschrieben

## Defaults

- Silence Threshold Default bleibt `1300ms`
- Die interaktive Journey startet mit `Bestaetigen`, `Verschieben` und `Absagen`
- Der Verschieben-Folgepfad startet mit relativen Termin-Buttons vor expliziten Datums- und Zeit-Buttons
