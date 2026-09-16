# Meta Conversions API & Stape sGTM

Stand 09/2026. Meta-Doku liegt jetzt unter `developers.facebook.com/documentation/ads-commerce/conversions-api/…`.

## Meta CAPI – Pflicht & Qualität
- Pflicht: `event_name`, `event_time` (Unix-Sekunden, max. 7 Tage alt – sonst lehnt Meta den ganzen Request ab), `user_data`, `action_source`; für Website-Events zusätzlich `event_source_url`, `client_user_agent`. https://developers.facebook.com/documentation/ads-commerce/conversions-api/parameters/server-event
- Hashing SHA-256: `em` (trim, lowercase), `ph` (nur Ziffern inkl. Ländervorwahl, ohne führende Nullen), `external_id` empfohlen gehasht. **Nicht** hashen: `client_ip_address`, `client_user_agent`, `fbp`, `fbc`. https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/customer-information-parameters
- `fbc` = `fb.1.<creationTime in ms>.<fbclid>` – fbclid unverändert (case-sensitiv). `fbp` = `fb.1.<ts>.<Zufallszahl>`. https://developers.facebook.com/documentation/ads-commerce/conversions-api/parameters/fbp-and-fbc
- **Deduplizierung**: Pixel `eventID` = CAPI `event_id` **und** Pixel `event` = CAPI `event_name`; Fenster 48 h. Fallback über `fbp`/`external_id` nur, wenn Browser-Event zuerst kommt. https://developers.facebook.com/documentation/ads-commerce/conversions-api/deduplicate-pixel-and-server-events
- Best Practice: Echtzeit senden, redundantes Setup (Pixel + CAPI mit identischen Events), EMQ 0–10. https://developers.facebook.com/documentation/ads-commerce/conversions-api/best-practices
- **Dataset Quality API** (`graph.facebook.com/v25.0/dataset_quality`): EMQ, Event Coverage, Dedup-Feedback, Freshness, ACR; braucht `ads_read` + `ads_management`/`business_management`. → Für Audits mit Token nutzen. https://developers.facebook.com/docs/marketing-api/conversions-api/dataset-quality-api/
- **Parameter Builder Library** (JS, PHP, Java, Python, Node, Ruby): liest fbc/fbp, normalisiert/hasht PII. https://developers.facebook.com/documentation/ads-commerce/conversions-api/parameter-builder-library
- **Core Setup**: schränkt Custom-Parameter und URL-Pfade ein; für Gesundheit/Finanzen/Versicherung teils automatisch aktiv (https://www.jonloomer.com/qvt/what-is-core-setup/; offizielle Hilfeseite nicht abrufbar → unbestätigt). Bei YMYL-Kunden im Events Manager prüfen und keine sensiblen Daten in URLs/Parametern senden.

## Stape – Domains
- Subdomain mit Stape Global CDN (2 CNAME), Own CDN (IPs von Website und sGTM gleich) oder ohne CDN (1 CNAME oder A/AAAA). https://stape.io/helpdesk/documentation/custom-domain-setup
- **Same Origin** (`kunde.de/metrics`) per Proxy (Cloudflare Worker, Nginx, Vercel); Pfad im Custom Loader eintragen; `server_container_url` exakt gleicher Host. https://stape.io/helpdesk/documentation/how-to-use-same-origin-approach-for-server-gtm
- Tagging Server URL im Server-Container (Admin → Container Settings) auf die Custom Domain setzen.

## Stape – Power-ups (Auswahl)
| Power-up | Zweck | Plan |
|---|---|---|
| Custom Loader | gtm.js/gtag.js über eigenen (optional verschleierten) Pfad → weniger Adblocker-Verluste | Free |
| Cookie Keeper | stellt unter ITP verfallene Cookies (`_ga`, `FPID`, `_gcl_aw`, `_fbp`, `_fbc` …) wieder her | Pro (eigene Cookies ab Business) |
| Click ID Restorer | Backup-Parameter (z. B. `backup_gclid`) → `gclid`/`msclkid` vor Verarbeitung | Free |
| GEO Headers / User Agent Info | Geo- bzw. Geräte-Header für Anreicherung | Free |
| Anonymizer | nur GA4: IP kürzen, Client-ID hashen, UA/UTMs/gclid entfernen | Free |
| Bot Detection | Score 0–100, optional Blocken ab > 75 | Pro |
| Request Delay / Schedule / File Proxy | Verzögerung, Zeitplan, Dateien über eigene Domain | Business |
Quellen: https://stape.io/helpdesk/documentation/sgtm/power-ups · https://stape.io/helpdesk/documentation/cookie-keeper-power-up · https://stape.io/helpdesk/documentation/click-id-restorer-power-up. Logs: nicht im Free-Plan (Pro: 3 Tage).

## Stape – Preise (sGTM, laut https://stape.io/price)
Free 10.000 Requests/Monat · Pro 500.000 ($17) · Business 5 Mio. ($83) · Enterprise 20 Mio. ($167). Nur eingehende Requests zählen. Free-Limit erreicht → Container deaktiviert; Pro pausiert bei 110 %; Auto-Upgrade verhindert Pausen. https://stape.io/helpdesk/documentation/request-limits-and-pause-logic
Faustregel: Requests ≈ Pageviews × (1 + Events pro Seite) nur bei Einwilligung → aus GA4-Daten hochrechnen, nicht raten.

## Stape – Tags/Clients
- **Facebook Conversions API Tag (Stape)**: Event-Name „Inherit from client“ (GA4-/Data-Client) oder „Override“; Pixel-ID + Access Token; „Test ID“ für Test-Events; „Generate _fbp cookie if it not exist“ empfohlen; „Enable Event Enhancement“ (HttpOnly-Cookie `gtmeec`); `fbc` aus fbclid/_fbc; Event-ID aus Event-Daten (`event_id`); Consent-Einstellung: nur bei Marketing-Consent senden. https://stape.io/helpdesk/documentation/how-to-set-up-meta-conversions-api
- **Data Tag (Web) + Data Client (Server)**: sendet dataLayer, Cookies und `consent_state` an `/data` – Alternative zum GA4-Transport, wenn GA4 nicht genutzt wird oder mehr Daten nötig sind. https://github.com/stape-io/data-tag
- **Google Ads im Server**: GA4-Client, Conversion-Linker-Tag (alle Seiten), Google-Ads-Conversion-Tag (ID, Label; Wert/Währung/Transaction-ID aus Ecommerce-Daten); Enhanced Conversions über user-provided data. https://developers.google.com/tag-platform/tag-manager/server-side/ads-setup
- **Meta CAPI Gateway (Stape)**: nur Meta, fast ohne Konfiguration; $10/Pixel/Monat bzw. $100 unbegrenzt. Für reine Meta-Kunden ohne sGTM-Bedarf. https://stape.io/helpdesk/knowledgebase/meta-conversions-api-gateway-cost

## Typische sGTM-Fehler (Audit-Checkliste)
- Preview leer → `server_container_url` ≠ Preview-Host, CSP/CORS blockiert, doppelte GA4-Initialisierung.
- Consent im Server ignoriert → GA4 überträgt `gcs`, Data Tag `consent_state`; Stape empfiehlt Trigger auf CMP-Consent-Events, weil GA4 nachträgliche `gcs`-Änderungen nicht erneut sendet. https://stape.io/blog/consent-mode-server-google-tag-manager
- Falsche IP hinter eigenem CDN → Header `Cf-Connecting-Ip` lesen, `ip_override` per Transformation setzen. https://stape.io/blog/accessing-original-user-ip-when-using-own-cdn
- Access Token im Server-Container: nur als Konstante im Container, nie in Git/Chat; Token mit minimalen Rechten (System-User).
