# Appointment Agent Benutzerleitfaden v1.3.10 (DE)

## Umfang
Version `v1.3.10` fuehrt `Dashboard+` ein: eine vereinfachte Real-Modus-Ansicht fuer Vertriebsdemonstrationen. Der bewaehrte Bereich `Messages and Customer Journey` bleibt erhalten, waehrend das Operator Panel auf die noetigen Demo-Felder reduziert wird.

## Was sich geaendert hat
- `Dashboard+` steht in der oberen Menueleiste vor dem bestehenden `Dashboard`.
- Das bestehende `Dashboard` bleibt fuer Detailansichten, Monitoring, gefuehrte Demo und Protokolle verfuegbar.
- `Dashboard+` arbeitet immer im `Real`-Modus.
- Der Operator waehlt, ob die Zielnummer aus der ausgewaehlten Adresse oder aus einem manuellen Telefonnummernfeld kommt.
- Wenn Telefonnummer ausgewaehlt ist und keine Mobilnummer eingegeben wurde, zeigt das Cockpit einen Fehler und blockiert den Real-Versand.
- Die Aenderung ist additiv und non-breaking fuer geschuetztes `v1.x`-Verhalten.

## Dashboard+ Operator Panel
1. `Scenario` auswaehlen.
2. Pruefen, dass `Scenario Mode` auf `Real` steht.
3. Kontaktziel waehlen:
   - `Ausgewaehlte Adresse`: verwendet die Telefonnummer des selektierten Adressdatensatzes.
   - `Telefonnummer`: verwendet die manuell eingegebene Mobilnummer.
4. `Appointment Type` auswaehlen.
5. Demo starten.

## Regeln fuer das Kontaktziel
- Standard ist `Ausgewaehlte Adresse`.
- Der Adressmodus nutzt das bisherige Verhalten: gesendet wird an die Telefonnummer der ausgewaehlten Adresse.
- Der Telefonnummernmodus ueberschreibt nur die Zielnummer fuer die Nachricht. Die ausgewaehlte Adresse kann weiter Termin- und Korrelationskontext liefern.
- Ein leerer Telefonnummernmodus wird mit einer sichtbaren Fehlermeldung abgelehnt.
- Die manuelle Telefonnummer ist auf `40` Zeichen begrenzt.

## Messages And Customer Journey
Der Bereich `Messages and Customer Journey` funktioniert wie bisher:
- Er zeigt Outbound Prompt, Reply Suggestions, Journey-Status und Slot-/Bestaetigungsschritte.
- Im `Real`-Modus sind Reply Buttons read-only, weil das Cockpit auf den Provider Callback wartet.
- Message Monitor, RCS Callback Polling und Journey Rendering nutzen weiterhin dieselben APIs.

## Sicherheits-Defaults
- Silence Threshold Default: `1300 ms`
- Manuelles Telefonnummernfeld: maximal `40` Zeichen
- Scenario Execution Mode in Dashboard+: `Real`
- Das bestehende Detail-Dashboard und der Message Monitor bleiben fuer Troubleshooting erhalten.

## Typischer Vertriebs-Demo-Ablauf
1. `/ui/demo-monitoring/v1.3.10` oeffnen.
2. Auf `Dashboard+` bleiben.
3. Szenario, Adresse oder manuelle Telefonnummer und Terminart auswaehlen.
4. Demo starten.
5. Zeigen, dass die Outbound Journey in `Messages and Customer Journey` erscheint.
6. Den Kundencallback ueber Provider Callback oder Message Monitor zeigen.
