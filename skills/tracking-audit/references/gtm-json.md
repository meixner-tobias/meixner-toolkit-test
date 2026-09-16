# GTM-Import-JSON – Format & Workflow

Stand 09/2026.

## Zwei Wege zum Import-JSON
1. **Generator** `scripts/build_web_container.py plan.json -o gtm-web-import.json` – nur Web-Container, nur eingebaute Typen (siehe unten). Für Standard-Lead-Gen und E-Commerce über dataLayer.
2. **Master-Container** `scripts/fill_template.py master.json values.json -o import.json` – für alles mit Galerie-Templates (Server-Container, Stape-Tags, CMP-Tag). Tobias baut sein Standard-Setup einmal in GTM, exportiert es (Verwaltung → Container exportieren) und legt es z. B. unter `~/tracking-master/` ab. Pro Kunde nur Konstanten ersetzen. **Bevorzugter Weg für Server-Container**, weil dessen interne Typ-IDs nicht zuverlässig dokumentiert sind.

Liegt kein Master vor: Server-Container als Schritt-für-Schritt-Anleitung liefern und anbieten, nach dem ersten manuellen Aufbau einen Master zu exportieren.

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
  ]
}
```
- `params`: GA4-Parametername → dataLayer-Pfad (wird als DLV-Variable angelegt).
- `trigger_event`: abweichender dataLayer-Eventname (Standard = `name`).
- Alle Events erwarten `dataLayer.push({event: "<name>", …})`. Klick-/Formular-Erkennung ohne dataLayer → Listener (`form_listeners`) oder manuell in GTM.
- Mit `server_container_url` bzw. Meta bekommt jedes GA4-Event `event_id` = `{{CJS - Event ID}}` (gleiche ID wie Pixel-`eventID`) → Stape-Meta-Tag kann deduplizieren.
- Enhanced Conversions erwarten `user_data` im dataLayer (Objekt mit `email`, `phone_number`, `address{…}`) – Quelle klären (Formular, Shop-Plugin).
Beispiele: `examples/plan-lead-wordpress.json`, `examples/plan-shop.json`.
