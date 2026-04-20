# Appointment Agent Admin Guide v1.4.0

## Release-Position

`v1.4.0` ist die erste funktional produktionsreife Kernfreigabe.

Die stabile Live-Demonstrator-Route bleibt:

- `/ui/demo-monitoring/v1.3.9`

Die aktuelle Live-Patch-Shell bleibt:

- `/ui/demo-monitoring/v1.3.9-patch9`

## Operativer Umfang

- Echtes LEKAB-RCS-Messaging ist aktiv
- Echte Callback-Verarbeitung ist aktiv
- Dynamische Google-Verfuegbarkeit ist aktiv
- Google-Calendar-Booking-Writes sind aktiv
- Address-Linkage ist aktiv
- Address-Zeitzone kann jetzt persistiert und im Booking-Pfad verwendet werden

## Admin-Pruefpunkte

- LEKAB-RCS-Settings im Cockpit pruefen
- Callback-URLs und Webhook-Fetch-Settings pruefen
- Google-Mode-Status und Kalenderziel pruefen
- Address-Linkage vor Real-Runs pruefen
- Address-Zeitzone fuer regionensensitive Tests pruefen

## Release-Hinweise fuer Operatoren

- Die Top-Level-App-Version ist als `v1.4.0` sichtbar
- Silence Threshold Default bleibt `1300ms`
- Das Release ist funktional produktionsfaehig
- UX-Verbesserungen bleiben fuer `v1.5.0` geplant
