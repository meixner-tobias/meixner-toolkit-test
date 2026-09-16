# GTM-Import-JSON – Format & Workflow

Stand 09/2026.

## Drei Ebenen statt blindem Copy/Paste
1. **Generator** `scripts/build_web_container.py plan.json -o gtm-web-import.json` – Web-Container aus dem verifizierten Kundenplan.
2. **Production Reference** `masters/production-reference/*.sanitized.json` – strukturell aus einem real funktionierenden Web-/Server-Paar, aber voll sanitisiert. Nur Architektur- und Pattern-Evidenz; nie direkt als Kunden-Setup kopieren. Verbindlich: `masters/REFERENCE-POLICY.md`.
3. **Core-/Verified Master** `scripts/fill_template.py master.json values.json -o import.json` – fuer Galerie-/Server-Strukturen. Die mitgelieferten `masters/core/*.candidate.json` sind absichtlich **nicht verified**. Fuer Wiederverwendung braucht ein Master echten GTM Import -> Preview -> Re-Export + `gtm_master_verify.py`; nur erster Bootstrap bewusst `--candidate-only`.

Events kommen aus dem Kundenplan + `masters/patterns/event-patterns.json`, nicht aus dem Production Reference. Insbesondere werden feste Waehrung, Ads-Labels, Meta-Consent, Scroll-Ads-Conversions, CSS/Pfade oder Eventnamen der Referenz nicht vererbt.

## Import in GTM
Verwaltung → Container importieren → Datei wählen → **Neuer Workspace** (Name z. B. „meixner-toolkit Import <Datum>“) → **Zusammenführen** → „Konflikte umbenennen“ (sicher) bzw. „überschreiben“ (nur bewusst). „Überschreiben“ als Importoption löscht alle bestehenden Tags/Trigger/Variablen (GTM legt vorher eine Version an). https://support.google.com/tagmanager/answer/6106997
Danach: Vorschau/Tag Assistant → Testprotokoll → erst dann veröffentlichen (Freigabe durch Tobias).

## Format (an echten Exporten geprüft)
- Top-Level: `exportFormatVersion: 2`, `exportTime`, `containerVersion{ container{usageContext:["WEB"|"SERVER"]}, tag[], trigger[], variable[], builtInVariable[], customTemplate[], folder[], client[] (Server) }`.
- Tag: `tagId`, `name`, `type`, `parameter[]` (`TEMPLATE`/`BOOLEAN`/`LIST`/`MAP`), `firingTriggerId[]`, `tagFiringOption`, `consentSettings`.
- Tabellen (z. B. `eventSettingsTable`, `configSettingsTable`): `LIST` von `MAP` mit Schlüsseln `parameter` / `parameterValue`.
- Eingebauter Trigger „Initialization – All Pages“ = `2147479573` (in Exporten belegt). Andere Built-in-IDs (All Pages 2147479553, Consent Initialization 2147479572) unbestätigt → Generator nutzt eigene PAGEVIEW-/DOM_READY-Trigger.
- Trigger-Typen im Export groß: `PAGEVIEW`, `DOM_READY`, `CUSTOM_EVENT` (Filter `{{_event}}` EQUALS/MATCH_REGEX).
- Tag-Typen: `googtag` Google Tag · `gaawe` GA4-Event (`eventName`, `measurementIdOverride`, `sendEcommerceData`, `getEcommerceDataFrom`, `eventSettingsTable`) · `awct` Ads-Conversion (`conversionId`, `conversionLabel`, `conversionValue`, `currencyCode`, `orderId`, `enableConversionLinker`) · `awud` User-Provided Data (`userDataVariable`, `conversionId`) · `gclidw` Conversion Linker · `sp` Ads-Remarketing · `html` Custom HTML (`html`, `supportDocumentWrite`). Quellen: GTM4WP-Vorlage 08/2026 (github.com/duracelltomi/gtm4wp), Shopify-Rezepte, https://developers.google.com/tag-platform/tag-manager/restrict
- Variablen-Typen: `v` dataLayer (`dataLayerVersion` 2, `name`), `c` Konstante (`value`), `jsm` Custom JS (`javascript`), `awec` User-Provided Data (`mode`, `dataSource`), `k` 1st-Party-Cookie, `u` URL, `ed` Event-Daten (Server).
- Galerie-Templates: Tag-Typ `cvt_<containerId>_<templateId>` + Eintrag in `customTemplate[]` mit `templateData` und `galleryReference`. Nicht selbst erzeugen – aus Master übernehmen oder in GTM aus der Galerie hinzufügen.
- **Zusätzliche Einwilligungsprüfung** (Generator setzt sie an Meta-Custom-HTML-Tags): `{"consentStatus":"NEEDED","consentType":{"type":"LIST","list":[{"type":"TEMPLATE","value":"ad_storage"}]}}` – aus der GTM-API abgeleitet, **an keinem Export belegt** → nach Import im Tag unter „Einwilligungseinstellungen“ prüfen. Fällt der Import deswegen fehl: `--no-consent-settings` und Einwilligung in GTM manuell setzen.
- Custom-HTML-Tags: `{{Variable}}` ohne Anführungszeichen wird zur Laufzeit als `google_tag_manager[…].macro(n)` aufgelöst (Wert behält Typ, z. B. Zahl); in Anführungszeichen löst GTM sie vorab als String auf. Beides funktioniert; der Generator nutzt die Variante ohne Anführungszeichen. https://www.simoahava.com/gtm-tips/mysterious-macro-call-custom-html-tags/

## Deterministisches Completeness Gate
Vor jedem Build verlangt `lib/tracking_plan.py` explizite, verifizierte Requirements **und Evidenznotizen**. Fehlende Entscheidungen werden nicht geraten, sondern als Fragen ausgegeben (`scripts/plan_gate.py`). Ein nacktes `*_verified: true` reicht nicht: `requirements.evidence` und `requirements.event_evidence` muessen die beobachtete Quelle nennen. Der Builder fuehrt dasselbe Gate erneut aus. Besonders bei E-Commerce, Enhanced Conversions und Server-Side werden zusaetzliche Pflichtentscheidungen verlangt. `requirements.open_questions` muss leer sein. Das Gate ist eine Vollstaendigkeitsbarriere, kein Ersatz fuer Tag Assistant/Preview. Cross-Domain wird vom Direktgenerator absichtlich nicht approximiert; dafuer einen real roundtrip-verifizierten Master verwenden.

## plan.json (Generator-Eingabe)
```json
{
  "container_name": "Kunde – Web",
  "default_currency": "EUR",
  "ga4": {"measurement_id": "G-XXXX"},
  "server_container_url": "https://www.kunde.de/metrics",
  "google_ads": {"conversion_id": "AW-123", "enhanced_conversions": true},
  "meta": {"pixel_id": "123", "browser_pixel": true},
  "form_listeners": ["cf7", "elementor", "wpforms"],
  "lead_event": "generate_lead",
  "events": [
    {"name": "generate_lead", "params": {"form_id": "form_id"}, "ads_label": "AbC", "value": 50, "meta_event": "Lead"},
    {"name": "purchase", "ecommerce": true, "ads_label": "XyZ", "meta_event": "Purchase"}
  ],
  "requirements": {
    "gate_version": 1,
    "open_questions": [],
    "site_type": "mpa",
    "primary_domain": "www.kunde.de",
    "event_source": "dataLayer",
    "event_source_verified": true,
    "conversion_success_verified": true,
    "consent_strategy_verified": true,
    "cross_domain": "not_required",
    "internal_traffic": "filter",
    "ecommerce_contract_verified": true,
    "refund_strategy": "manual",
    "payment_referrals": "not_required",
    "enhanced_conversions_verified": true,
    "enhanced_conversions_source": "dataLayer user_data",
    "server_strategy_verified": true,
    "evidence": {
      "event_source": "GTM Preview: dataLayer Event beobachtet",
      "conversion_success": "Danke-/Kauf-Erfolg im Testablauf beobachtet",
      "consent_strategy": "CMP + Consent-Update im Preview/Consent-Test beobachtet",
      "ecommerce_contract": "Testkauf: transaction_id/value/currency/items beobachtet",
      "enhanced_conversions": "user_data-Quelle und Consent-Pfad verifiziert",
      "server_strategy": "sGTM-Ziel + Browser-vs-Server-Zustaendigkeit verifiziert"
    },
    "event_evidence": {
      "generate_lead": "GTM Preview: generate_lead beobachtet",
      "purchase": "GTM Preview: purchase mit transaction_id beobachtet"
    }
  }
}
```
- `params`: GA4-Parametername → dataLayer-Pfad (wird als DLV-Variable angelegt).
- `trigger_event`: abweichender dataLayer-Eventname (Standard = `name`).
- Alle Events erwarten `dataLayer.push({event: "<name>", …})`. Klick-/Formular-Erkennung ohne dataLayer → Listener (`form_listeners`) oder manuell in GTM.
- Mit `server_container_url` bzw. Meta bekommt jedes GA4-Event `event_id` = `{{CJS - Event ID}}` (gleiche ID wie Pixel-`eventID`) → Stape-Meta-Tag kann deduplizieren.
- Enhanced Conversions erwarten `user_data` im dataLayer (Objekt mit `email`, `phone_number`, `address{…}`) – Quelle klären (Formular, Shop-Plugin).
Beispiele: `examples/plan-lead-wordpress.json`, `examples/plan-shop.json`.

## Golden-Master / echte Import-Verifikation
Google Tag Manager unterstützt Container-Export und -Import als JSON ausdrücklich: https://support.google.com/tagmanager/answer/6106997
Das Toolkit trennt deshalb drei Stati:
1. **generated/candidate** – syntaktisch und intern validiert, aber noch nicht von GTM importiert.
2. **verified_by_gtm_import_roundtrip** – Candidate wurde in GTM importiert, derselbe Workspace wieder exportiert und `scripts/gtm_master_verify.py` findet keine semantischen Abweichungen.
3. **preview_verified** – zusätzlich Tag Assistant bzw. Server-Preview am echten Ziel getestet (menschliches Testprotokoll; nicht aus JSON ableitbar).

Nie Status 2 oder 3 ohne die jeweilige Evidenz behaupten. Für Community-/Stape-Templates keine IDs/Parameter erfinden; einen realen Server-Master einmal in GTM aufbauen, exportieren, roundtrip-verifizieren und erst danach mit `fill_template.py --verified-manifest ...` wiederverwenden.


## 0.7.11 Production-Reference-Vertrag
- `scripts/reference_guard.py` muss vor Release/Build gruen sein.
- `scripts/sanitize_gtm_reference.py` erzeugt aus einem echten Export eine nicht-importable, kundenneutrale Referenz. Originale mit Tokens/IDs bleiben ausserhalb des Plugins.
- `scripts/build_reference_assets.py` leitet Core-Candidates + Pattern-Katalog ausschliesslich aus bereits sanitisierten Referenzen ab.
- `registry.json` trennt `verified_masters`, `candidate_masters` und `reference_assets`. Ein Reference/Candidate darf nie automatisch in `verified_masters` aufsteigen.
- Ein echter Access Token in einem GTM-Export gilt nach Weitergabe/Commit als offengelegt und sollte rotiert werden; im Plugin sind nur Platzhalter zulaessig.
