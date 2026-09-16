# Entscheidungsbaum & Fragenkatalog

Stand 09/2026.

## Architektur-Empfehlung
| Situation | Empfehlung | Begründung |
|---|---|---|
| Nur GA4 (+ evtl. Google Ads), kleines Budget | Google Tag über GTM + CMP + Consent Mode v2; optional **Google tag gateway** über Cloudflare (kostenlos) | Deckt nur Google ab, aber ohne sGTM-Kosten (google.md) |
| Meta Ads im Einsatz, sonst wenig | Pixel + **Stape Meta CAPI Gateway** ($10/Pixel/Monat) oder sGTM | Gateway = minimaler Aufwand, nur Meta (meta-stape.md) |
| Mehrere Plattformen (GA4 + Ads + Meta) / Leadgen mit Budget | **sGTM auf Stape**: GA4-Transport → Server; Meta CAPI + Ads im Server; Pixel redundant mit event_id | Ein Datenstrom, Dedup, Cookie-Laufzeit |
| Shop (WooCommerce) | GTM4WP („Track e-commerce“ an) + sGTM wie oben, Enhanced Conversions mit Bestelldaten | Standard-dataLayer (cms-recht.md) |
| Shop (Shopify) | Stape-App oder Custom Pixel (Customer Events) + sGTM | Checkout-Skripte abgeschaltet |
| Hoher Safari-/iOS-Anteil | Same-Origin- oder Own-CDN-Domain, Cookie Keeper (Pro), ggf. backup_gclid + Click ID Restorer | ITP & Click-ID-Stripping |
| YMYL (Gesundheit, Finanzen) | Keine sensiblen Pfade/Parameter an Meta/Ads, Core Setup prüfen, Consent Basic erwägen | Meta-Einschränkungen, Rechtsrisiko |

Domain-Wahl sGTM: Same Origin (Cloudflare/Proxy vorhanden) > Subdomain mit Own CDN > Subdomain mit Stape CDN (+ Cookie Keeper) > `*.stape.io`/`*.run.app` (nicht empfohlen).

Stape-Plan: erwartete Requests/Monat aus GA4 (Seitenaufrufe + Events, nur mit Einwilligung) hochrechnen; Free (10k) nur für Tests.

## Fragenkatalog (nur stellen, was fehlt)
**Geschäft**
- Welche Handlungen sind Conversions? (Formular, Anruf-Klick, Terminbuchung, Kauf, Newsletter)
- Fester Wert je Lead oder kein Wert? Währung?
- Welche Seiten/Formulare? Danke-Seite vorhanden?

**Plattformen**
- GA4-Property vorhanden (Mess-ID)? Google Ads (Conversion-ID + Labels je Aktion)? Meta (Pixel-/Dataset-ID, Business-Manager-Zugriff)? Weitere (Microsoft, LinkedIn, TikTok)?
- Enhanced Conversions gewünscht und Kundendatenbedingungen akzeptiert?

**Consent**
- Welche CMP? Lizenz vorhanden? Consent Mode Basic oder Advanced (Kunde entscheidet, ggf. Datenschutzberatung)?
- Regionen außerhalb EWR relevant (anderer Default)?

**Server-Side**
- Budget für Stape (Pro ab $17/Monat)? Wer hat DNS-/Cloudflare-Zugriff?
- backup_gclid-Workaround gewünscht?

**Technik**
- CMS/Shop-System und Plugins (GTM4WP, Formular-Plugin)?
- Wer darf in GTM veröffentlichen? Testumgebung/Staging vorhanden?
