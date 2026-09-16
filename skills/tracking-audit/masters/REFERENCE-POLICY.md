# Production Reference Policy — GTM Web + Server

Stand: 16.09.2026 · Bestandteil von meixner-toolkit 0.7.11

## Zweck

Die Dateien unter `production-reference/` stammen strukturell aus einem real verwendeten Web-/Server-GTM-Paar, wurden aber **vollständig sanitisiert**. Sie sind Architektur-Evidenz: Sie zeigen, wie ein funktionierendes Setup Web-GA4 ueber eine First-Party-sGTM-Domain an einen GA4-Client weiterleitet und dort u. a. Google Ads / Meta CAPI bedienen kann.

**Sie sind keine Soll-Konfiguration und duerfen nie 1:1 fuer einen neuen Kunden kopiert werden.**

## Harte Regeln

1. **Originale nie ausliefern.** Nur `*.sanitized.json` darf im Plugin liegen.
2. **Keine Kundenwerte erben:** Account-/Container-IDs, GTM-/GA4-/Ads-/Meta-IDs, Conversion-Labels, Domains, Tokens, Testcodes, Waehrungen, Form-IDs, Pfade, CSS-Selektoren, Buttontexte und kundenindividuelle Eventnamen muessen aus dem neuen Audit/Plan kommen.
3. **Consent nie erben.** Ein beobachtetes `NOT_SET`, Stape `adStorageConsent=optional` oder sonstige Consent-Einstellung ist nur Referenzbeobachtung. Der neue Kunde braucht eine verifizierte CMP-/Basic-/Advanced-/Region-Entscheidung.
4. **Business-Events nie erben.** Der Eventplan wird vor dem Build neu erstellt. Nur Patterns verwenden, deren Semantik wirklich passt.
5. **Erfolgspunkt vor Trigger:** stabile dataLayer-/Callback-/Backend-Success-Signale vor CSS-/Click-Text-/Seitenpfad-Heuristiken bevorzugen. Ein Klick ist nicht automatisch eine Conversion.
6. **Google Ads nicht doppeln:** wenn eine gleichartige Conversion serverseitig gemessen wird, nicht zusaetzlich still eine zweite Browser-Conversion erzeugen.
7. **Meta Hybrid nur dedupliziert:** Browser + CAPI nur, wenn derselbe reale Vorgang mit identischem Eventnamen und stabil identischer `event_id` auf beiden Kanaelen gesendet wird.
8. **Secrets nie in Git/Chat:** Token/Secrets nur lokal bzw. in geeigneten Secret-/Variable-Mechanismen einsetzen. Referenzen enthalten ausschliesslich Platzhalter.
9. **Core-Master bleibt Candidate:** `core/*.candidate.json` ist aus der Referenz abgeleitet und **nicht** `VERIFIED`. Erst echter GTM Import -> Preview -> Re-Export -> `gtm_master_verify.py` darf einen konkreten Master als roundtrip-verifiziert markieren.
10. **Community Templates sind versioniert:** vor neuem Release/Projekt die installierte Stape-/Gallery-Version und relevante Parameter gegen aktuelle Herstellerdoku pruefen. Kein eingebetteter Template-Stand ist ewige Wahrheit.

## Wie Claude die Referenz benutzen soll

Reihenfolge:

1. Kunden-Audit / Recon / Anforderungen erfassen.
2. `plan.json` und Completeness Gate vollstaendig machen.
3. Eventsemantik bestimmen (`patterns/event-patterns.json`).
4. Architektur waehlen (Browser, Server, Browser+Server).
5. Nur passende Core-/Event-Muster als **Strukturhilfe** verwenden.
6. Alle kundenbezogenen Werte aus verifizierten Kundendaten einsetzen.
7. JSON generieren bzw. Master befuellen.
8. Import in **neuen GTM-Workspace**, Preview/Test, dann Re-Export und Roundtrip-Check.
9. Erst nach fachlichem Test veroeffentlichen; das Plugin veroeffentlicht nicht selbst.

## Was aus dem realen Setup bewusst NICHT Default ist

- feste Waehrung (im Referenzsetup war Single-Currency moeglich)
- Scrolltiefe als Ads-/Meta-Conversion
- Meta Event Name `inherit` statt explizitem Mapping
- Meta CAPI `adStorageConsent=optional`
- pageview-/click-/CSS-Trigger fuer Business-Conversions
- konkrete Kurs-/Newsletter-/Termin-Events

Diese Punkte duerfen nur uebernommen werden, wenn das neue Projekt sie fachlich und technisch begruendet.
