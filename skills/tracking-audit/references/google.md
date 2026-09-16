# Google: Consent Mode v2, GA4, Google Ads, Click-IDs

Stand der Recherche: 09/2026. „unbestätigt“ = nicht aus offizieller Quelle belegt → im Report so kennzeichnen.

## Consent Mode v2
- Parameter: `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization` (+ optional `functionality_storage`, `personalization_storage`, `security_storage`). https://developers.google.com/tag-platform/security/concepts/consent-mode
- **Basic**: Google-Tags laden erst nach Einwilligung; vorher werden keine Daten gesendet, nicht einmal der Consent-Status. **Advanced**: Tags laden sofort; bei „denied“ gehen cookielose Pings raus (Consent-Status, u. a. User-Agent, Bildschirmauflösung, IP; GA speichert laut Google keine IP). Quellen: obige Seite + https://support.google.com/google-ads/answer/13802165
- `consent default` muss **vor** allen Messbefehlen stehen (Consent-Initialization-Trigger). `wait_for_update` in ms (Google-Beispiel 500).
- `ads_data_redaction: true` + `ad_storage` denied → Klick-IDs in Ads-/Floodlight-Requests werden geschwärzt. `url_passthrough: true` → gclid/dclid/gclsrc/_gl/wbraid werden an interne Links gehängt. https://developers.google.com/tag-platform/security/guides/consent
- Regionale Defaults über `region` (ISO 3166-2).
- **Pflicht für EWR, UK, CH**: ohne Consent-Signale (inkl. `ad_user_data`) keine volle Personalisierung/Messung; erkennbar an `&eea=1`. https://support.google.com/google-ads/answer/13695607 · https://support.google.com/google-ads/answer/16142339
- **Änderung 15.06.2026**: Consent Mode (`ad_storage`) ist die einzige Steuerung, ob GA-Daten in Google Ads genutzt werden; Google Signals regelt nur noch die Verknüpfung angemeldeter Nutzer im Reporting. https://support.google.com/analytics/answer/17016975
- Werbetreibende brauchen **keine** Google-zertifizierte CMP (Pflicht nur für Publisher mit AdSense/Ad Manager/AdMob), müssen aber Consent-Signale senden. https://support.google.com/google-ads/answer/16724512

### Consent-Status in Netzwerk-Hits lesen
- `gcs` und `gcd` sind codierte Consent-Signale in Google-Requests. Das Toolkit speichert die beobachteten Werte als Evidenz, behandelt aber keine selbst gepflegte Stringtabelle als stabile Ja/Nein-API. Google weist darauf hin, dass HTTP-Parameter codiert sind und sich mit der Weiterentwicklung der Dienste ändern können. Quelle: https://developers.google.com/tag-platform/security/concepts/consent-mode
- Bewertung: Vor Einwilligung beobachtete Google-Collection-Requests zusammen mit `gcs`/`gcd` als **Beobachtung** dokumentieren. Den tatsächlichen Consent-Zustand mit aktueller Google-Dokumentation bzw. Tag Assistant verifizieren; aus einem einzelnen `gcs`-String nicht automatisch „granted“, „denied“ oder einen Rechtsverstoß ableiten.
- Basic vs. Advanced Consent Mode anhand des tatsächlichen Tag-Verhaltens und der Google-Konfiguration prüfen: Im Basic Mode werden Google-Tags vor Einwilligung blockiert; im Advanced Mode können bei `denied` cookielose Signale gesendet werden. Rechtliche Einordnung separat (`cms-recht.md`).

## GA4 & Server-Side
- sGTM-Domain: Subdomain (z. B. `metrics.kunde.de`) oder **Same Origin** (`kunde.de/metrics`, braucht CDN/Load Balancer). Standard-`*.run.app`-Domain setzt nur JS-Cookies. https://developers.google.com/tag-platform/tag-manager/server-side/custom-domain
- Google Tag → Konfigurationsparameter `server_container_url` = sGTM-URL (exakt gleicher Host wie im Preview, sonst leere Preview). Doppelte GA4-Initialisierung (Inline-gtag, Plugins) ohne `server_container_url` umgeht den Server.
- **Google tag gateway for advertisers** (ehem. First-party mode, GA seit 08.05.2025; Cloud-Load-Balancer-Integration GA seit 01.06.2026): Google-Tag lädt über eigene Domain/Pfad, Events werden an Google weitergeleitet; Cloudflare-Integration kostenlos. Nur Google-Dienste – kein Ersatz für sGTM mit Meta CAPI. https://support.google.com/tagmanager/answer/16061406 · https://blog.cloudflare.com/google-tag-gateway-for-advertisers
- Empfohlene Events: Lead-Gen `generate_lead` (+ `qualify_lead`, `close_convert_lead` …), E-Commerce `view_item`, `add_to_cart`, `begin_checkout`, `purchase` (Pflicht: `currency` ISO 4217, `value` ohne Versand/Steuer, `transaction_id`, `items` mit `item_id` oder `item_name`). https://developers.google.com/analytics/devguides/collection/ga4/reference/events
- „Conversions“ heißen in GA4 **Key Events**. https://support.google.com/analytics/answer/13965727

## Google Ads
- **Conversion Linker** speichert Klickdaten in 1st-Party-Cookies (`_gcl_aw` …), Cross-Domain via Linker. https://support.google.com/tagmanager/answer/7549390
- **Enhanced Conversions (Web)**: E-Mail, Telefon, Name, Adresse; SHA-256; normalisieren (trim, lowercase, Telefon E.164). Ungehasht senden (Google hasht) oder vorgehasht. Kundendatenbedingungen im Ads-Konto akzeptieren. https://support.google.com/google-ads/answer/9888656 · https://support.google.com/google-ads/answer/13258081
- **Enhanced Conversions for Leads**: Formulardaten gehasht beim Absenden erfassen (GTM-Tag „User-Provided Data Event“, Typ `awud`), später Offline-Import mit denselben Hashes. https://support.google.com/google-ads/answer/11347292
- `wbraid` (Web) / `gbraid` (App) = datenschutzfreundliche iOS-Klick-IDs; GBRAID case-sensitiv. https://support.google.com/google-ads/answer/10417364

## Click-ID-Stripping & backup_gclid
- Safari **Link Tracking Protection** (seit iOS 17) entfernt Tracking-Parameter in Mail, Nachrichten und privatem Surfen. https://webkit.org/blog/15697/private-browsing-2-0/ · Betroffen laut Stape: `gclid`, `fbclid`, `msclkid` (https://stape.io/blog/safari-removes-click-identifiers-solution).
- Safari 26: bekannte Fingerprinting-Skripte können Query-Parameter/Referrer nicht lesen (https://webkit.org/blog/17333/webkit-features-in-safari-26-0/). Ob `gclid` im **normalen** Browsen entfernt wird: widersprüchliche Tests (unbestätigt).
- Brave entfernt `gclid`, `fbclid`, `msclkid` standardmäßig (https://brave.com/privacy-updates/5-grab-bag/). Firefox nur in ETP „Streng“; offizielle Liste enthält `fbclid`, nicht `gclid`.
- `gbraid`/`wbraid` werden laut Branchenquelle nicht entfernt (unbestätigt).
- **backup_gclid-Workaround**:
  1. Google Ads → Verwaltung → Kontoeinstellungen → Tracking → **Final URL Suffix**: `backup_gclid={gclid}` (vorhandenes Suffix mit `&` ergänzen; `{gclid}` ist ein offizieller ValueTrack-Parameter, Einschränkungen bei PMax/Demand Gen laut https://support.google.com/google-ads/answer/6305348 – Details unbestätigt).
  2. Stape → Power-up **Click ID Restorer**: Parametername `backup_gclid` eintragen. Das Power-up schreibt ihn serverseitig zurück in `gclid` (dokumentiert für gclid und msclkid). https://stape.io/helpdesk/documentation/click-id-restorer-power-up
  3. Voraussetzungen: Auto-Tagging an, sGTM über Stape mit Custom Domain, Einwilligung. Test: Anzeigen-Vorschau-Klick → im sGTM-Preview muss `gclid` ankommen, Cookie `_gcl_aw`/`FPGCLAW` gesetzt.
  - Einordnung: Der Workaround umgeht bewusst eine Browser-Datenschutzfunktion → nur mit Consent, Kunde informieren; Wirkung entfällt, falls Browser künftig auch den Backup-Parameter entfernen. Keine offizielle Google-Aussage dazu.

## Safari ITP & Cookies
- JS-Cookies: 7 Tage ohne Interaktion; 24 h bei Landung über dekorierten Link. Server-Cookies aus CNAME-Cloaking oder von Drittanbieter-IPs: max. 7 Tage. https://webkit.org/tracking-prevention/
- Folge: sGTM per CNAME auf fremde Infrastruktur verliert Vorteile → **Same Origin** oder **Own CDN** (gleiche IP wie Website) bevorzugen; alternativ Stape **Cookie Keeper** (ab Pro).
