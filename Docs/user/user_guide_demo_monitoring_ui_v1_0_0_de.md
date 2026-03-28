# Demo Monitoring UI Benutzerleitfaden v1.0.0 DE

Version: v1.0.4 Patch 1
Status: aktiver Demo-Patch
Language: Deutsch
Im UI-Header gezeigter Release: `v1.0.4 Patch 1`
Hinweis: Dieser Dateiname bleibt fuer die Routen-Kompatibilitaet stabil. Der Inhalt ist fuer `v1.0.4 Patch 1` aktualisiert.

## Was diese Seite macht

Diese Seite hilft dir, den Appointment Agent sichtbar und einfach zu erklaeren.

Auf der linken Seite siehst du:

- was der Kunde schreibt
- welche Optionen der Kunde bekommt
- was die Plattform antwortet

Auf der rechten Seite siehst du:

- welches Modul gerade aktiv ist
- welche Events erzeugt werden
- welche Buchungsdetails sichtbar sind
- welche Messaging-Details sichtbar sind
- welche Audit-Notizen existieren

## Haupt-URL

Diese Seite oeffnest du im Browser:

`/ui/demo-monitoring/v1.0.0`

## Wichtige Steuerelemente

- `Modus`
  Hier wechselst du zwischen `Demo`, `Monitoring` und `Kombiniert`.

- `Szenario`
  Hier waehlst du den Ablauf aus, den du zeigen willst.

- `Neustart`
  Springt auf den ersten Schritt des aktuellen Szenarios zurueck.

- `Naechster Schritt`
  Geht manuell einen Schritt weiter.

- `Auto abspielen`
  Spielt das Szenario automatisch ab.

- `IDs zeigen`
  Blendet technische IDs wie `booking_reference`, `provider_reference` und message-bezogene Kennungen ein oder aus.

- `Audit Details zeigen`
  Blendet Audit-Eintraege ein oder aus.

- `EN` und `DE`
  Wechseln die Sprache der ganzen UI.

## Was die rechten Bereiche bedeuten

- `Journey-Status`
  Der aktuelle Status des Terminablaufs.

- `Ablaufschritte`
  Zeigt, welche Module offen, aktiv, fertig, fehlgeschlagen oder eskaliert sind.

- `Event-Zeitleiste`
  Zeigt die wichtigsten Ereignisse in zeitlicher Reihenfolge.

- `Buchungsdetails`
  Zeigt interne und externe Buchungsreferenzen.

- `Messaging-Details`
  Zeigt message-bezogene Tracking-Informationen von der LEKAB-Seite.

- `Audit-Protokoll`
  Zeigt wichtige Entscheidungen der Plattform.

- `Wichtige Parameter`
  Erklaert wichtige technische Parameter in einfacher Sprache.

- `CRM-Ereignisse`
  Zeigt, welche Ereignisse an eine CRM-Schicht weitergegeben werden koennten.

## Was die Messaging-IDs bedeuten

- `message_id`
  Das ist die Kennung fuer die Nachricht auf der Kommunikationsseite. Damit siehst du, welche eingehende oder ausgehende Nachricht zu einer Journey gehoert.

- `lekab_job_id`
  Das ist die Workflow-Job-Kennung auf der LEKAB-Seite. Sie verfolgt den Workflow-Job, nicht die Nachricht selbst.

- `message_channel`
  Zeigt, ob die simulierte Nachricht ueber `RCS` oder `SMS` laeuft.

- `message_status`
  Zeigt den aktuellen Nachrichtenstatus wie `sent` oder `received`.

- `delivery_status`
  Zeigt das Lieferergebnis wie `delivered`.

## Was der Service Bus bedeutet

Der Service Bus ist der Nachrichtenweg zwischen den Modulen.

Einfache Idee:

- ein Modul sendet ein Event
- ein anderes Modul reagiert darauf
- die Plattform bleibt modular, weil die Module nicht zu viele starre Direktverbindungen brauchen

## So skaliert das System

- `20 Nutzer`
  Viele Termin-Journeys koennen schon parallel laufen.
- `100 Nutzer`
  Mehr Container koennen sich die Last teilen.
- `1000 Nutzer`
  Mehr Rechenleistung, bessere Datenbankabstimmung, Queue-basiertes Puffern und die klare Trennung zwischen Orchestrator, Messaging und Adaptern werden wichtiger.

## Wichtige Parameter

- `journey_id`
  Eine ID fuer eine komplette Terminreise des Kunden.

- `correlation_id`
  Hilft dabei, zusammengehoerende Events zu verbinden.

- `trace_id`
  Hilft bei tiefer technischer Fehlersuche.

- `booking_reference`
  Interne Buchungs-ID der Plattform.

- `provider_reference`
  Externe Buchungs-ID beim Provider.

- `message_id`
  Nachrichten-ID der Kommunikationsseite.

- `lekab_job_id`
  LEKAB-Workflow-Job-ID.

- `appointment_date`
  Das Datum, das in Reminder-Ablaufen gezeigt wird.

- `appointment_time`
  Die Uhrzeit, die in Reminder-Ablaufen gezeigt wird.

- `selected_action`
  Die Aktion, die der Kunde im Reminder-Ablauf ausgewaehlt hat.
