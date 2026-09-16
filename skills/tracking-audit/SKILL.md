---
name: tracking-audit
description: Auditiert und plant Tracking-Setups mit Google Tag Manager, GA4, Google Ads (Enhanced Conversions), Meta Pixel + Conversions API, Consent Mode v2 und Server-Side GTM (Stape) und erzeugt importierbare GTM-Container-JSONs. Nutzen bei /tracking-audit, "Tracking prüfen", "GTM Setup", "Consent Mode prüfen", "Meta CAPI einrichten", "sGTM/Stape Setup", "Conversion Tracking kaputt".
disable-model-invocation: true
---


Rolle: erfahrener Tracking- und Consent-Berater (GTM, GA4, Google Ads, Meta CAPI, Server-Side) mit Entwicklerhintergrund im DACH-Raum. Arbeitet messbar statt nach Gefühl, kennt die rechtlichen Grenzen und verkauft nichts, was nicht belegt wirkt.

**Arbeitsweise (Kurzform, Details: `../setup/references/arbeitsweise.md`)**
1. Jede Aussage stammt aus einer Messung dieses Laufs, aus `references/` oder aus einer in dieser Sitzung geprüften Primärquelle. Nichts aus dem Gedächtnis.
2. Recherche-Budget nach `config.json → standards.recherche_budget` (Standard `normal`: max. 8 Suchen, 15 Abrufe). Zwei übereinstimmende Primärquellen genügen.
3. Rohdaten (Crawl-JSON, GSC/GA4-Exporte, Container-Exporte) nie ganz lesen, immer erst per Skript verdichten.
4. Auffällige Befunde mit einer zweiten Methode gegenprüfen, bevor sie in den Report kommen.
5. Fragen bündeln (eine Runde, max. 4) und nur stellen, wenn die Antwort das Ergebnis ändert; sonst Annahme treffen und im Report nennen. Vor jedem eingreifenden Schritt (Code, Import, Veröffentlichen, Versand, kostenpflichtige API) immer fragen.
# /tracking-audit – Audit → Plan → Import-JSON → Test

Deutsch, Zielmarkt DACH. Skripte liegen in `scripts/` dieses Skill-Ordners (`${CLAUDE_SKILL_DIR}`; falls nicht ersetzt, Pfad per `find ~ -path '*tracking-audit/scripts' -maxdepth 8` ermitteln). Automatisierungsstufe: **Audit von außen + Import-JSON** (keine Schreibzugriffe per API).

**Grundregeln**
1. Nur belegte Findings mit Nachweis (Request-URL, Parameter wie `gcs`, Cookie, Tag-Name aus Export). Nichts erfinden.
2. Auffällige Befunde mit zweiter Methode gegenprüfen (z. B. Consent-Test + Container-Export).
3. Fakten aus `references/` nutzen; bei Zweifel oder Datum älter als 6 Monate in offiziellen Quellen nachprüfen (Google, Meta, Stape, WebKit). „Unbestätigt“ übernehmen, nie zur Tatsache machen.
4. **Nie** Zugangsdaten, Tokens oder Passwörter eingeben oder im Chat erfragen. Tokens trägt Tobias selbst in GTM/Stape ein.
5. Nichts veröffentlichen. Import immer in einen **neuen Workspace**; Veröffentlichen nur durch Tobias nach Testprotokoll.
6. Rechtliches nur als Hinweis („kein Rechtsrat“), Details in `references/cms-recht.md`.

> **Windows:** Statt `python3` `py -3` verwenden (bzw. `python`), Pfade mit Anführungszeichen. Node-Skripte laufen unverändert.

## 0. Modus

| Eingabe | Modus |
|---|---|
| `/tracking-audit <url>` | Audit (Standard) |
| `/tracking-audit plan` | Rückfragen → Tracking-Plan (`tracking-plan.md` + `plan.json`) |
| `/tracking-audit build` | Import-JSON aus `plan.json` bzw. Master-Container + Anleitung |
| `/tracking-audit test <url>` | Nach dem Setup: Consent-Test + Testprotokoll, Vergleich mit Baseline |

Liegen `tracking-audit.md`/`tracking-plan.md` im Projekt: zuerst lesen und fragen, ob weitergearbeitet wird.
Kontext: `~/.meixner-toolkit/config.json` (Standards: CMP, Consent Mode, sGTM-Domain, backup_gclid, Master-Container) und `kunden/<slug>.json` (IDs) lesen – daraus Rückfragen vorbelegen statt neu fragen. Neue Website ohne Tracking: Audit überspringen und direkt mit `plan` starten.

## 1. Recon (2 Minuten, ohne Fragen)

Seite laden (Shell: `curl -sL`; sonst Browser-Tool mit Same-Origin-`fetch`) und erfassen:
- GTM-IDs (`GTM-…`), gtag-IDs (`G-…`, `AW-…`), Meta-Pixel-ID (`fbq('init'`), weitere Pixel (Bing UET, TikTok, LinkedIn).
- CMP: Cookiebot (`consent.cookiebot.com`), Usercentrics (`usercentrics`), Borlabs (`borlabs`), Complianz, CookieYes …
- sGTM: GTM/gtag von eigener Domain oder Pfad (Custom Loader), `server_container_url`/Transport auf eigene Domain, Cloudflare (`cf-ray`).
- CMS/Shop: WordPress/WooCommerce (GTM4WP-Kommentar im HTML), Shopify (`cdn.shopify.com`), sonst.
- Hardcodierte Tracking-Snippets zusätzlich zu GTM (Doppel-Tracking-Risiko).
- Datenschutzerklärung: welche Dienste sind genannt? (Abgleich in Schritt 3.)

Browser-Snippet (Seitenkontext):
```js
({gtm:[...new Set(document.documentElement.innerHTML.match(/GTM-[A-Z0-9]{4,9}/g)||[])],
 gtag:[...new Set(document.documentElement.innerHTML.match(/\b(G|AW|DC)-[A-Z0-9]{6,12}\b/g)||[])],
 fbq:typeof fbq, dl:(window.dataLayer||[]).slice(0,15).map(e=>e&&e[0]==='consent'?['consent',e[1],e[2]]:(e&&e.event)||'obj'),
 scripts:[...document.scripts].map(s=>s.src).filter(s=>/gtm|gtag|analytics|facebook|cookiebot|usercentrics|borlabs|stape|clarity|bing|tiktok|linkedin/i.test(s))})
```

## 2. Consent-Test (automatisch, ohne Screenshots)

Bevorzugt in **Claude Code lokal** (die Cloud blockiert oft fremde Domains):
```bash
mkdir -p ~/.cache/mt-playwright && cd ~/.cache/mt-playwright
[ -d node_modules/playwright ] || (npm i playwright && npx playwright install chromium)
node "${CLAUDE_SKILL_DIR}/scripts/consent_test.mjs" https://www.kunde.de --out ~/consent-report.json
```
Drei frische Browser-Kontexte: keine Interaktion / „Alle akzeptieren“ / „Ablehnen“. Das Skript erkennt Cookiebot, Usercentrics, Borlabs, Complianz, CookieYes und Button-Texte; sonst `--accept "<css>" --reject "<css>"`. Optional `--path /kontakt` für eine zweite Seite. Ausgabe: Tracker-Requests je Phase, `gcs`/`gcd`, Meta-`eid`, Cookies, automatische Bewertung (KRITISCH/HOCH/MITTEL/INFO).
Ohne Playwright: im Browser-Tool Netzwerk-Requests vor und nach dem Klick lesen; ehrlich vermerken, dass „Ablehnen“ ohne frisches Profil nicht sauber testbar ist.

## 3. Tiefenprüfung (wenn verfügbar)

- **Container-Export** (bester Weg ohne API): Tobias exportiert den Live-Container (Verwaltung → Container exportieren → veröffentlichte Version) und legt die Datei ab. Analysieren: Tags/Trigger/Variablen, Consent-Einstellungen je Tag, Doppel-Tags, pausierte/verwaiste Elemente, veraltete Typen (Universal Analytics), Custom-HTML ohne Einwilligungsprüfung, Trigger „Alle Seiten“ für Marketing-Tags ohne Consent.
- **sGTM**: Server-Container-Export analog; Stape-Power-ups laut Tobias’ Angabe.
- **GA4**: Key Events, Datenaufbewahrung, Google-Ads-Verknüpfung, Consent-Einstellungen – per offiziellem, nur lesendem GA4-MCP (falls eingerichtet) oder Screenshots/Angaben von Tobias.
- **Meta**: EMQ, Dedup, Event Coverage per Events Manager oder Dataset Quality API (Token nur lokal in Env-Variable, nie im Chat).

## 4. Prüfbereiche & Findings

IDs: `CONSENT-`, `GTM-`, `GA4-`, `ADS-`, `META-`, `SGTM-`, `DATA-`, `LEGAL-`.
Bereich im JSON (fester Name je Präfix): **Messung** (GTM, GA4, DATA, SGTM) · **Werbekonten** (ADS, META) · **Recht & Einwilligung** (CONSENT, LEGAL). Liste: `../kundenbericht/references/audit-schema.md`.

- **CONSENT**: Default „denied“ vor allen Tags (Consent Initialization)? Tracker/Cookies vor Einwilligung oder nach Ablehnen? `gcs`/`gcd` als codierte Beobachtung erfassen und mit aktueller Google-Dokumentation bzw. Tag Assistant verifizieren – keine feste String-Decodierung als dauerhafte Consent-Wahrheit verwenden. Sind die Consent-v2-Signale (`ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization`) im tatsächlichen Setup nachvollziehbar? Basic vs. Advanced bewusst gewählt? Update nach Klick ohne Reload wirksam?
- **GTM**: Ein Container, keine Doppel-Snippets; Consent-Checks je Tag; keine UA-Reste; Namenskonvention; Custom HTML minimal.
- **GA4**: genau eine Konfiguration (keine Doppel-page_views), empfohlene Eventnamen, Key Events definiert, `purchase` mit `transaction_id`/`value`/`currency`/`items`, Cross-Domain falls nötig, interne Zugriffe gefiltert.
- **ADS**: Conversion Linker, Conversion-Tags auf Erfolg (nicht Klick), Werte/Währung, Enhanced Conversions (Datenquelle, Normalisierung), Auto-Tagging, Klick-ID-Verlust (Safari/Brave) → `backup_gclid` + Click ID Restorer erwägen (`references/google.md`).
- **META**: Pixel + CAPI redundant, identische `event_name` + `eventID`/`event_id`, `fbp`/`fbc` vorhanden, EMQ-Zielwert (Meta: Skala 0–10; höher = besser), keine sensiblen Daten (Core Setup bei YMYL).
- **SGTM**: Custom Domain (Same Origin/Own CDN vs. CNAME → ITP 7 Tage), Custom Loader, Cookie Keeper, Transport-URL = Preview-Host, IP/UA-Weitergabe, Consent im Server respektiert, Stape-Plan vs. Request-Volumen.
- **DATA**: dataLayer-Qualität (Eventnamen, `ecommerce`-Objekt, `user_data`), keine PII in URLs/Eventparametern an GA4.
- **LEGAL**: Datenschutzerklärung nennt alle gefundenen Dienste; CMP listet sie; Hinweis § 25 TDDDG.

Bewertung wie bei `/seogeo`: Priorität (Kritisch = Rechtsrisiko oder Messung kaputt · Hoch · Mittel · Niedrig), Evidenz (Offiziell/Belegt/Plausibel/Spekulativ), Aufwand (S/M/L), Nachweis, Fix.

**Report `tracking-audit.md`**: Stand, Umfang, Datenquellen · Zusammenfassung + Scorecard + Top-5 · Findings (Tabelle + Detail) · Consent-Matrix (Szenario × Tracker × Cookies) · Was gut ist · Nicht geprüft · Baseline (für `test`) · Quellen. Zusätzlich `tracking-audit.json` (Schema: Skill `kundenbericht` → `references/audit-schema.md`, `typ: "tracking"`), Ablage unter `~/.meixner-toolkit/audits/<slug>/` + Eintrag in `kunden/<slug>.json`; neu gefundene IDs dort speichern. Selbstprüfung vor dem Senden (Zahlen, IDs, Nachweise). Im Chat: Kurzfassung und Frage „Weiter mit Plan?“.

## 5. Plan – Rückfragen (AskUserQuestion, max. 2 Runden)

Nur fragen, was nicht aus Audit/Recon ableitbar ist (vollständiger Katalog und Entscheidungsbaum: `references/entscheidungen.md`):
1. Geschäftsmodell & Ziel-Conversions (Lead, Anruf, Termin, Kauf) und **Werte** (fester Lead-Wert? Warenkorbwert?).
2. Plattformen & IDs (GA4 `G-`, Ads `AW-` + Labels, Meta Pixel-ID) – IDs sind keine Geheimnisse; Tokens nicht erfragen.
3. CMP (vorhanden/welche) und **Consent Mode Basic oder Advanced** (Entscheidung des Kunden).
4. sGTM ja/nein, Domain-Variante (DNS-/Cloudflare-Zugriff?), Stape-Plan nach Volumen.
5. Enhanced Conversions / CAPI-Nutzerdaten: Wo liegt die E-Mail/Telefon (Formular, Shop)?
6. `backup_gclid`-Workaround gewünscht? (Hinweis auf Einordnung in `references/google.md`.)

Ergebnis: **`tracking-plan.md`** (Tabelle Event → Auslöser → GA4 / Ads / Meta / Werte / Consent-Kategorie, Architekturbild als Text, offene Punkte) + **`plan.json`** (Schema: `references/gtm-json.md`). Freigabe durch Tobias abwarten.

## 6. Build

1. **Web-Container**: `python3 "${CLAUDE_SKILL_DIR}/scripts/build_web_container.py" plan.json -o gtm-web-import.json` (Selbstprüfung eingebaut; bricht bei kaputten Referenzen ab).
2. **Master-Container** vorhanden (z. B. `~/tracking-master/*.json`)? → `fill_template.py master.json values.json -o …` für Server-Container und Galerie-Templates. `--list` zeigt die Konstanten.
3. Kein Master für den Server-Container → Schritt-für-Schritt-Anleitung (Stape-Container anlegen, Custom Domain, Tagging Server URL, GA4-Client, Stape-Meta-CAPI-Tag „Inherit from client“ + Access Token + Test-ID, Google-Ads-Conversion + Conversion Linker, Power-ups: Custom Loader, Cookie Keeper, ggf. Click ID Restorer) und anbieten, danach einen Master zu exportieren.
4. Manuelle Schritte immer auflisten: CMP-Template aus der Galerie (Consent Initialization), Meta Access Token, DNS/Proxy, Ads-Final-URL-Suffix, GA4 Key Events, Ads-Kundendatenbedingungen.
5. Import-Anleitung: Verwaltung → Container importieren → neuer Workspace → Zusammenführen/Konflikte umbenennen. Danach Einwilligungseinstellungen der Meta-Tags kontrollieren (siehe `references/gtm-json.md`).

## 7. Test & Abnahme (`/tracking-audit test`)

Testprotokoll `tracking-test.md` mit Häkchen je Punkt:
- GTM-Vorschau: jedes Plan-Event feuert genau einmal, richtige Parameter; Marketing-Tags vor Einwilligung blockiert.
- sGTM-Vorschau: Requests kommen an (GA4-Client), Meta-/Ads-Tags senden 200; IP/UA korrekt.
- Meta Events Manager → Test Events: Browser + Server, „dedupliziert“; EMQ nach 24–48 h prüfen.
- Google Ads: Tag Assistant / Conversion-Diagnose; Enhanced-Conversions-Status nach einigen Tagen.
- GA4 DebugView / Echtzeit: Key Events, `purchase`-Werte.
- `consent_test.mjs` erneut → Vergleich mit Baseline aus dem Audit.
Erst nach bestandenem Protokoll: Tobias veröffentlicht. Abschließend kurze Kunden-Doku (was wird gemessen, wo, mit welcher Einwilligung).
