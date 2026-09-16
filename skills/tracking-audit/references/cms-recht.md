# CMS-Besonderheiten, CMP-Templates & Recht (DE/EU)

Stand 09/2026.

## CMP-Templates in GTM
- **Cookiebot CMP** (Galerie): Domain Group ID, Trigger „Consent Initialization – All Pages“, Default-Status je Region, Consent Mode per Checkbox aktivieren. Mapping: marketing → ad_storage/ad_user_data/ad_personalization; statistics → analytics_storage; preferences → functionality/personalization_storage. Custom Event `cookie_consent_update` für Tags ohne eingebaute Prüfung. https://support.cookiebot.com/hc/en-us/articles/360003793854-Google-Tag-Manager-deployment · https://support.cookiebot.com/hc/en-us/articles/360016047000-Implementing-Google-Consent-Mode
- **Usercentrics CMP** (Galerie): Settings-/Ruleset-ID, „Wait for update“ (Empfehlung 2000 ms), „Redact ads data“, URL passthrough, Default je Region (Standard denied); Auto-Blocking nicht per GTM. https://support.usercentrics.com/hc/en-us/articles/16672283975580-Implementing-Usercentrics-CMP-v3-using-Google-Tag-Manager
- Reihenfolge: Consent Initialization → Initialization → Page View → DOM Ready → Window Loaded. https://support.google.com/tagmanager/answer/7679319
- Häufig in DE auf WordPress: **Borlabs Cookie**, Complianz, Real Cookie Banner – eigene Mechanik; Consent-Mode-Unterstützung und GTM-Integration jeweils prüfen (nicht verallgemeinern).

## WooCommerce
- **GTM4WP** (Thomas Geiger): „Track e-commerce“ ist standardmäßig **aus**; eingeschaltet GA4-Ecommerce-Events mit Standardnamen im dataLayer; GA4-Import-Vorlage verfügbar (Stand 08/2026). Consent regelt die CMP. https://gtm4wp.com/google-tag-manager-for-woocommerce/how-to-setup-enhanced-ecommerce-tracking-google-analytics-4-ga4-version
- Offizielles „Google Analytics for WooCommerce“: gtag.js direkt, **keine** dataLayer-Events für GTM; Consent Mode standardmäßig denied in EWR/UK/CH. Doppel-Tracking mit GTM vermeiden. https://woocommerce.com/document/google-analytics-integration/

## Shopify
- checkout.liquid für Info/Versand/Zahlung abgeschaltet; Thank-you-/Order-Status-Seiten inkl. Additional Scripts: Plus seit 28.08.2025, Non-Plus seit 26.08.2026 abgeschaltet. https://shopify.dev/docs/storefronts/themes/architecture/layouts/checkout-liquid
- Ersatz: **Customer Events / Web Pixels** (Sandbox: kein DOM, keine Klick-/Scroll-Events; in EWR/UK nur mit Berechtigung). GTM im Custom Pixel via `analytics.subscribe()` → `dataLayer.push`; Tag-Assistant-Debugging dort nicht möglich, von Shopify „unsupported“. https://help.shopify.com/en/manual/promoting-marketing/pixels/custom-pixels/gtm-tutorial
- **Stape-App für Shopify**: GTM-Snippet, Custom Loader, dataLayer-E-Commerce-Events, Customer Privacy API, Webhooks für Bestellungen/Erstattungen (ohne Cookies → nur Fallback). https://stape.io/helpdesk/documentation/sgtm-app-config-for-shopify

## WordPress-Formulare (Lead-Erkennung)
- Contact Form 7: DOM-Event `wpcf7mailsent` (`detail.contactFormId`). https://contactform7.com/dom-events/
- Elementor Pro: jQuery-Event `submit_success` (Sekundärquelle, unbestätigt). WPForms: `wpformsAjaxSubmitSuccess` bei AJAX (unbestätigt). Robuster Fallback: Danke-Seite mit eigenem Pfad oder dataLayer-Push im Formular-Hook.
- Nie Formular-Klick als Lead zählen – nur erfolgreiche Übermittlung.

## Recht (Hinweis, keine Rechtsberatung)
- **§ 25 TDDDG**: Speichern/Auslesen auf dem Endgerät nur mit Einwilligung; Ausnahme nur, wenn „unbedingt erforderlich“ für den ausdrücklich gewünschten Dienst. Gilt unabhängig vom Personenbezug; aktives Auslesen von Geräteeigenschaften per JS gilt als Zugriff (DSK-Orientierungshilfe Digitale Dienste v1.2, 11/2024, Rn. 23–28, 78). https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf
- **Server-Side-Tracking ersetzt die Einwilligung nicht**, solange Cookies, Client-JS oder Pixel auf das Endgerät zugreifen; die Weiterverarbeitung braucht zusätzlich eine DSGVO-Rechtsgrundlage (bei Tracking praktisch Einwilligung). Nie als „cookiefrei = einwilligungsfrei“ verkaufen.
- **Consent Mode Advanced** (cookielose Pings ohne Einwilligung): rechtlich nicht abschließend geklärt → Entscheidung beim Kunden bzw. dessen Datenschutzberatung; Basic ist die konservative Wahl.
- **EU-US Data Privacy Framework**: EuG hat Latombe-Klage am 03.09.2025 abgewiesen; Berufung beim EuGH anhängig; nach US-Supreme-Court-Urteil (FTC, 29.06.2026) hat der EDPB am 31.07.2026 um Überprüfung gebeten. DPF gilt bis auf Weiteres. https://iapp.org/news/a/edpb-requests-review-of-eu-us-data-privacy-framework-following-trump-v-slaughter
- Datenschutzerklärung muss eingesetzte Dienste (GA4, Ads, Meta, Stape, CMP) nennen → im Audit mit tatsächlich gefundenen Requests abgleichen.
