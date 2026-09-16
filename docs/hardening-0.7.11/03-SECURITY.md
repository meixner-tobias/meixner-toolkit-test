# Sicherheitsbericht 0.7.11

## Produktionsreferenzen und Secrets
Die zwei realen GTM-Exporte sind Eingabe-/Analysequellen, keine Paketdateien. `sanitize_gtm_reference.py` ersetzt Account-/Container-/GTM-/GA4-/Ads-/Meta-/Domain-/Label-/Form-/Selector-/Pfadwerte durch verständliche Platzhalter. `reference_guard.py` scannt die ausgelieferten Master-/Referenz-JSONs auf bekannte Kundenmarker, secret-artige Konstanten und fälschlich als VERIFIED markierte Candidates.

Ein im Originalexport vorhandener Meta-CAPI-Access-Token wird niemals in die ausgelieferten Referenzen kopiert. Die Sicherheitsmaßnahme im Plugin ersetzt keine Rotation des bereits exportierten Tokens beim Plattformanbieter.

## Master-Trust-Grenze
`candidate_reference_only` ist absichtlich nicht `verified`. `fill_template.py` blockiert stilles Verwenden eines Candidate als vertrauenswürdigen Master. Verifiziert wird erst nach realem GTM Import, Preview und Re-Export mit semantischem Roundtrip-Manifest. Dynamische GTM-/Community-Template-IDs dürfen variieren; semantische Tags/Trigger/Variablen nicht.

## Entscheidungs-/Datenminimierung
Kundenspezifische Consent-Einstellungen, IDs, Währungen, Conversion-Labels, Eventnamen, CSS-Selektoren, Form-IDs und Domains werden nicht geerbt. Tokens/Passwörter gehören weiterhin nicht in Chat, Git oder Kundenkonfiguration.
