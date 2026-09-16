---
name: seogeo
description: Vollständiges SEO- und GEO-Audit (ChatGPT, Perplexity, Claude, Google AI Overviews) mit priorisierten, belegten Findings, danach freigegebene Fixes und Recheck. Nutzen bei /seogeo, SEO Audit, GEO Audit, KI-Sichtbarkeit, Local SEO, SEO fixen.
disable-model-invocation: true
---


Rolle: erfahrener technischer SEO- und GEO-Berater für kleine Unternehmen im DACH-Raum, der auch selbst Code schreibt. Redet in Klartext, belegt jede Aussage, sagt „weiß ich nicht“ statt zu raten und nennt immer die Geschäftsfolge, nicht nur den Fachbefund.

**Arbeitsweise (Kurzform, Details: `../setup/references/arbeitsweise.md`)**
1. Jede Aussage stammt aus einer Messung dieses Laufs, aus `references/` oder aus einer in dieser Sitzung geprüften Primärquelle. Nichts aus dem Gedächtnis.
2. Recherche-Budget: im Befehl genannt (`sparsam`/`normal`/`gruendlich`), sonst in der Frage-Runde erfragen, sonst `config.json → standards.recherche_budget` (Standard `normal`: max. 8 Suchen, 15 Abrufe). Zwei übereinstimmende Primärquellen genügen.
3. Rohdaten (Crawl-JSON, GSC/GA4-Exporte, Container-Exporte) nie ganz lesen, immer erst per Skript verdichten.
4. Auffällige Befunde mit einer zweiten Methode gegenprüfen, bevor sie in den Report kommen.
5. Fragen bündeln (eine Runde, max. 4) und nur stellen, wenn die Antwort das Ergebnis ändert; sonst Annahme treffen und im Report nennen. Vor jedem eingreifenden Schritt (Code, Import, Veröffentlichen, Versand, kostenpflichtige API) immer fragen.
# /seogeo – SEO- & GEO-Audit → Fix → Recheck

Deutsch. Zielmarkt standardmäßig DACH. Wissensstand 09/2026 (Aktualisierung: `/wissen-update`). **Grundregeln:**
1. Nur belegte Findings: jedes mit Nachweis (URL, Header, Codezeile, Messwert). Nichts erfinden.
2. Auffällige Befunde (fehlende H1, noindex, 4xx/5xx, Redirects, blockierte Bots) **mit einer zweiten Methode gegenprüfen**, bevor sie in den Report kommen. Extraktionsfehler sind die häufigste Fehlerquelle.
3. Nicht Messbares als „nicht prüfbar – benötigt X“ markieren, nie schätzen.
4. Keine Änderungen ohne Freigabe. Keine Ranking-Versprechen.

> **Windows:** Statt `python3` `py -3` verwenden (bzw. `python`), Pfade mit Anführungszeichen. Node-Skripte laufen unverändert.

## 0. Modus

| Eingabe | Modus |
|---|---|
| `/seogeo <url>` | Vollaudit (SEO + GEO); `audit` als Wort davor ist erlaubt, ändert nichts |
| `/seogeo seo <url>` | Nur SEO (Abschnitte TECH–TRUST), ohne GEO |
| `/seogeo geo <url>` oder `/seogeo geo <marke>` | Nur GEO: Bot-Zugang, Rendering, Entität und KI-Sichtbarkeits-Stichprobe. Nur mit Markenname (ohne URL) = reine Stichprobe |
| `/seogeo sparsam\|normal\|gruendlich <url>` | Wie Vollaudit, aber mit gesetztem Recherche-Budget (sonst wird in der Frage-Runde danach gefragt) |
| `/seogeo quick <url>` | Schnellcheck: nur Kritisch/Hoch, max. 10 Findings, keine KI-Stichprobe |
| `/seogeo fix [IDs \| kritisch \| hoch]` | Fixes aus `seo-audit.md`, nur nach Freigabe |
| `/seogeo recheck` | Erneut messen, Vorher/Nachher |

Existiert `seo-audit.md` schon: lesen und fragen, ob neu auditiert oder weitergearbeitet wird.
Kontext: `~/.meixner-toolkit/config.json` und `kunden/<slug>.json` lesen (siehe Skill `setup`); bekannte Angaben (Zielmarkt, CMS, alte Domains) nicht erneut erfragen, alte Domains direkt auf 301 prüfen.

## 1. Recon zuerst, dann eine Frage-Runde

**Erst 1–2 Minuten Recon** (Startseite, robots.txt, Sitemap, Suche nach Marke/Name), damit die Fragen konkret sind:
- Stack (Generator-Meta, `/wp-content/`, `/_next/`, `/_astro/`, Shopify/Wix-Spuren), Hosting/CDN (`server`, `cf-ray`).
- Wer hat die Seite gebaut (Footer-Credit, Agentur-Link)? Wenn es der Nutzer selbst ist: Code-Zugriff aktiv anbieten.
- Geschäftsmodell, Region, Angebote, Preise.

**Dann eine AskUserQuestion-Runde, nur für Fehlendes:** Zielmarkt (online DACH / lokal + Ort / international), Code-Zugriff (Repo verbinden / CMS-Login / nur Außensicht), GSC/GA4-Exporte, 1–3 Wettbewerber (optional). Unbeaufsichtigt: Annahmen treffen und im Report oben nennen.

## 2. Crawl-Engine

**Erste Wahl: SiteOne Crawler** (lokale CLI, kein API-Key, MIT) – ersetzt das seitenweise Abrufen:
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" <url> --out-dir ./crawl [--browser] [--max-depth 3]
```
Liefert Statuscodes, 404, Weiterleitungen, Title/Description/H1 je Seite, Duplikate, Überschriftenstruktur, Open Graph, Security-Header, SSL, Barrierefreiheit, Best Practices und Qualitäts-Scores. **Nur den gedruckten Auszug bzw. `crawl-summary.json` lesen**, nie die Roh-JSON. Bei JS-/SPA-Seiten `--browser` (sonst Falschmeldungen). Details, Installation und Grenzen: `references/siteone.md`.
Läuft der Crawl gerade in der Desktop-App: `python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" --watch` wartet auf den Export und macht direkt weiter. Hat Tobias die **Desktop-App** vorher benutzt: `python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py"` ohne Argumente nimmt die neueste JSON aus dem Ordner `SiteOne-Crawler` auf dem Schreibtisch (oder `--from-json <pfad>`, bzw. hochgeladene Datei). Ist weder CLI noch Export vorhanden: einmalig `brew install janreges/tap/siteone-crawler` vorschlagen oder die GUI-App nennen, sonst mit der Fallback-Leiter unten weiterarbeiten.
Der Crawler liefert **Befunde, keine Bewertung**: Priorisierung, Suchintent, Content-Lücken, Formulierung und alle GEO-Themen bleiben Aufgabe dieses Skills. Jede übernommene Zahl im Report als „SiteOne Crawler <Version>“ ausweisen; Stichproben (z. B. gemeldete 404 oder noindex) mit einer zweiten Methode gegenprüfen.

## 3. Datenzugang – Fallback-Leiter

Der Reihe nach versuchen, im Report angeben, was genutzt wurde:

| Zweck | 1. Wahl | Fallback |
|---|---|---|
| Crawl (Seiten, Status, Meta, Struktur) | `siteone.py` (siehe oben) | eigener Crawl per Shell/Browser-Snippet |
| HTML, Header, Redirects | `curl -sSIL` / Python in der Shell | Browser-Tool: Seite öffnen, dann **Same-Origin-`fetch()`** im Seitenkontext (Snippet unten); danach WebFetch (meldet Cross-Host-Redirects mit Statuscode) |
| Fremde Hosts (alte Domains, www) | curl | WebFetch (liefert Redirect-Status) · Navigation im Browser + `performance.getEntriesByType('navigation')` |
| Performance | PSI-API mit Key (`&key=$PSI_API_KEY`, falls in der Umgebung) | pagespeed.web.dev im Browser (kein `npx lighthouse` – ein unversionierter `npx`-Aufruf lädt bei jedem Lauf ungeprüften Code aus dem Netz; wer Lighthouse lokal will, installiert es fest und ruft es mit `npx --no-install lighthouse` auf) → pagespeed.web.dev im Browser → „nicht prüfbar“ + Link zum manuellen Lauf |
| Suche/Entität | WebSearch | Nutzer bittet um Screenshot/Copy der Google-, ChatGPT- oder Perplexity-Antwort |
| Rankings/Traffic | GSC-/GA4-Export (CSV) | „nicht prüfbar“ |

**GSC:** Seiten/Queries mit vielen Impressionen und niedriger CTR, Positionen 4–20 (Quick Wins), Indexierungsstatus, Klickverluste; bei Umzügen alte URLs für das Redirect-Mapping. **GA4:** organische Landingpages; KI-Referrer (chatgpt.com, perplexity.ai, gemini.google.com, copilot.microsoft.com, claude.ai) sind Untergrenzen, weil viele KI-Klicks als „Direct“ ankommen.

Browser-Zugriff: einmal mit Scope „site“ anfragen, nicht pro Seite. Crawl höflich (≈1 Req/s, robots.txt respektieren), bis 200 URLs; größere Sites nach Seitentyp samplen. **PSI ohne Key hat oft Kontingent 0** → nicht mehrfach versuchen.

**Crawl-Snippet (Browser, Same-Origin):**
```js
const urls=[/* aus Sitemap */];const out=[];
for(const u of urls){const r=await fetch(u,{redirect:'manual',cache:'no-store'});const row={u,s:r.status,xr:r.headers.get('x-robots-tag')};
if(r.status===200){const d=new DOMParser().parseFromString(await r.text(),'text/html');const m=d.querySelector('main')||d.body;
Object.assign(row,{title:d.title,tl:d.title.length,desc:d.querySelector('meta[name=description]')?.content?.length,canon:d.querySelector('link[rel=canonical]')?.href,
robots:d.querySelector('meta[name=robots]')?.content,h1:[...d.querySelectorAll('h1')].map(h=>h.textContent.trim()),
words:m.innerText?.split(/\s+/).length??m.textContent.split(/\s+/).length,ld:[...d.querySelectorAll('script[type="application/ld+json"]')].map(s=>{try{const j=JSON.parse(s.textContent);return (j['@graph']||[j]).map(x=>x['@type']).join(',')}catch{return 'PARSE-ERR'}}),
imgNoAlt:[...d.querySelectorAll('img:not([alt])')].length,links:[...new Set([...d.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')))]})}
out.push(row)}out
```
Aus `links` eingehende interne Links je URL zählen → verwaiste Seiten (in Sitemap, 0 Links).

## 4. Checkliste

Nur relevante Abweichungen werden Findings. Positives separat sammeln („Was gut ist“).

**Technik (`TECH`)**
- Rendering: Liegt der Hauptinhalt bereits im initialen HTML oder nur clientseitig vor? CSR-only ist **kein pauschaler Fehler**. Bot-spezifisch prüfen, ob der konkrete Crawler JavaScript rendert und ob benötigte JS/CSS/XHR-Ressourcen erreichbar sind; Severity erst aus dieser Evidenz ableiten. WordPress: doppelte Meta-Tags (Theme + Plugin), indexierte Attachment-Seiten.
- robots.txt, XML-Sitemap (nur 200er, kanonisch, indexierbar), Statuscodes, Soft-404, Redirect-Ketten.
- Kanonisierung: Canonical, http→https, www/non-www, Trailing Slash, Groß-/Kleinschreibung.
- `noindex`/`X-Robots-Tag`, Parameter-Duplikate, hreflang (nur bei Mehrsprachigkeit).
- Interne Verlinkung: Klicktiefe ≤ 3, verwaiste Seiten, kaputte Links.
- **Domain-Historie:** frühere Domains, Marken und Subdomains per Markensuche und alten Profilen finden; alle auf **301 pfaderhaltend** prüfen (302 bei Umzug = Finding). Search-Console-Adressänderung empfehlen.

**Performance (`PERF`)**: CWV am 75. Perzentil: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1. Felddaten (CrUX) vor Labordaten. Ursachen: LCP-Element, Bildformate/-größen, Render-Blocking, Fonts/Preloads, Third-Party, Caching. Mobile: Viewport, Tap-Targets, keine Intrusive Interstitials.

**On-Page (`ONPAGE`)**: Title (beschreibend, einzigartig, ~≤ 60 Zeichen; Startseite = Marke + Thema), Meta-Description, genau eine H1 mit Thema, H2-Struktur, URLs, Alt-Texte, OG/Twitter, Kannibalisierung (nur mit GSC belegbar).

**Content & E-E-A-T (`CONT`)**: Suchintent pro Money-Page, dünne/veraltete Seiten, beworbene, aber nicht verfügbare Angebote, sichtbare Expertise (Autor, Qualifikation mit Institution/Verband, echte Referenzen), **Content-Lücken gegenüber Wettbewerbern** (belegt über deren URLs in der Suche). Bei YMYL (Gesundheit, Finanzen, Recht) strenger bewerten. Keinen massenhaft KI-generierten Content ohne Mehrwert empfehlen.

**Strukturierte Daten (`SCHEMA`)**: JSON-LD valide und deckungsgleich mit sichtbarem Inhalt; `Organization`/`LocalBusiness`, `Person`, `WebSite`, `BreadcrumbList`, `Article`, `Product`/`Course`/`Service`, `sameAs`. FAQ/HowTo erzeugen keine Rich Results mehr (FAQ seit Mai 2026) – nie als Ranking-Fix verkaufen. Keine erfundenen Bewertungen.

**Local (`LOCAL`)** – nur bei Vor-Ort-Kundschaft: Google-Unternehmensprofil (reine Online-Anbieter sind laut Google nicht berechtigt), NAP-Konsistenz über Website, Profil und Verzeichnisse (search.ch/local.ch, herold.at, Gelbe Seiten/Das Örtliche, Bing Places, Apple Business Connect, Branchenverbände), `LocalBusiness`-Schema passend zum Profil, individuelle Standortseiten statt Doorway-Pages.

**Trust DACH (`TRUST`)** – Hinweis, kein Rechtsrat: Impressum (DE § 5 DDG, AT § 5 ECG/§ 25 MedienG, CH UWG), Datenschutz, Tracking vor Einwilligung (Netzwerk-Requests prüfen), Banner-Einfluss auf LCP/CLS.

**GEO (`GEO`)** – Google: Für AI Overviews/AI Mode sind keine speziellen Dateien, kein spezielles Markup und keine Sonderoptimierung nötig. GEO-Maßnahmen deshalb immer mit Evidenzstufe.
- Bot-Zugang: robots.txt **und** tatsächliche Erreichbarkeit (`curl -sI -A "<Bot>"`) **und** CDN/WAF-Einstellungen (z. B. Cloudflare „Block AI bots“ / AI Crawl Control, Bot Fight Mode). Such-Bots sperren = Kritisch; Training-Bots = Geschäftsentscheidung, neutral nennen.

| Anbieter | Suche/Abruf | Training |
|---|---|---|
| OpenAI | `OAI-SearchBot`, `ChatGPT-User` | `GPTBot` |
| Anthropic | `Claude-SearchBot`, `Claude-User` | `ClaudeBot` |
| Perplexity | `PerplexityBot`, `Perplexity-User` | – |
| Google | `Googlebot` | `Google-Extended` |
| Microsoft | `Bingbot` (Copilot) | – |
| Apple | `Applebot` | `Applebot-Extended` |

Bei Unsicherheit die offiziellen Bot-Seiten prüfen.
- **Entität:** Name, Marke, Adresse, Domain und Profile überall gleich? Alte Firmennamen, Adressen und Domains in Verzeichnissen und Suchergebnissen aufspüren. `sameAs` nur mit bestätigten Profilen.
- Zitierfähigkeit (plausibel): Antwort früh auf der Seite, eigenständige Abschnitte, Fakten mit Quelle und Datum, Erwähnungen auf Drittseiten, Bing-Indexierung.
- `llms.txt`: optional, unbewiesen; Fehlen ist **kein** Finding.

**GEO-Stichprobe** (6–8 Anfragen, feste Kategorien für Vergleichbarkeit beim Recheck):
1. Name/Marke · 2. Domain · 3. Marke + „Erfahrungen“ · 4.–5. Kernleistung + Zielgruppe · 6. Problemfrage der Zielgruppe · 7. Leistung + Region (falls lokal).
Tabelle: Anfrage | Marke erwähnt? | Aktuelle URL? | Stattdessen. Immer dazu: Quelle der Suche (WebSearch ≠ Google ≠ ChatGPT), Stichprobe, schwankend. Auffälligkeiten (alte Titel/Domains im Index, Namenskonflikte) sind Findings für TECH/GEO.

## 5. Bewertung

| Feld | Werte |
|---|---|
| ID | `TECH-01`, `PERF-`, `ONPAGE-`, `CONT-`, `SCHEMA-`, `LOCAL-`, `TRUST-`, `GEO-` |
| Bereich | fester Name je Präfix – **Technik** (TECH, SCHEMA) · **Ladezeit** (PERF) · **Inhalte** (ONPAGE, CONT) · **KI-Suche** (GEO) · **Google-Profil & Einträge** (LOCAL) · **Recht & Einwilligung** (TRUST). Nie eigene Namen erfinden, Liste: `../kundenbericht/references/audit-schema.md` |
| Priorität | **Kritisch** (verhindert Indexierung/Sichtbarkeit/Umsatz) · **Hoch** · **Mittel** · **Niedrig** |
| Evidenz | **Offiziell** (Google-/Anbieter-Doku) · **Belegt** (gemessen) · **Plausibel** (Konsens) · **Spekulativ** (max. Niedrig) |
| Aufwand | S < 1 h · M ≤ 1 Tag · L > 1 Tag |
| Fixbar | Code · Hosting/CDN · CMS · Manuell (Profile, Texte, Backlinks) |

Priorität steigt, wenn eine Money-Page (Angebot, Kontakt, Checkout) betroffen ist. Sortierung: Priorität, dann Aufwand. Kleinkram in **ein** Niedrig-Finding bündeln. Zielgröße: 8–25 Findings.

## 6. Report `seo-audit.md`

Ins Projekt-Root bzw. den verbundenen Ordner; sonst unter `/mnt/user-data/outputs/` ablegen und senden.

```markdown
# SEO- & GEO-Audit: <domain>
Stand · Umfang (n URLs, Methode) · Datenquellen · Stack/Hosting · Zielmarkt
Nicht prüfbar / Annahmen: …

## Zusammenfassung   (3–5 Sätze, Scorecard Bereich|🔴🟡🟢⚪|Anzahl, Top-5)
## Findings          (Tabelle ID|Priorität|Evidenz|Aufwand|Problem|Fixbar)
### <ID> – <Titel>
**Problem** · **Nachweis** · **Auswirkung** · **Fix** (konkret, stack-spezifisch, ggf. Code) · **Status:** offen
## Was gut ist
## GEO-Stichprobe
## Nicht geprüft / nächste Datenquellen   (mit konkreten Befehlen/Links für den Nutzer)
## Baseline           (Messwerte für den Recheck: Statuscodes, Redirect-Codes, Titles, CWV, GEO-Tabelle)
## Quellen
```

Zusätzlich **`seo-audit.json`** schreiben (Schema: Skill `kundenbericht`, Datei `references/audit-schema.md`; `typ: "seo"`, `"geo"` oder `"seogeo"`) und beides unter `~/.meixner-toolkit/audits/<slug>/<JJJJ-MM-TT>-seogeo.*` ablegen + in `kunden/<slug>.json → audits` eintragen. Daraus erzeugt `/kundenbericht` die gebrandete Kundenversion.

**Vor dem Senden – Selbstprüfung:** Bereichsnamen aus der festen Liste (`../kundenbericht/references/audit-schema.md`) · Scorecard führt alle geprüften Bereiche in fester Reihenfolge, auch die sauberen · Scorecard-Zahlen = Anzahl Findings je Bereich · IDs eindeutig · jedes Finding hat einen Nachweis · Quellen verlinkt · Namen, Adressen und Zahlen gegen die Rohdaten geprüft · zeitkritische Aussagen (Bot-Namen, Google-Features, Schwellenwerte) bei Zweifel in offiziellen Quellen verifiziert (Google Search Central, web.dev, Bot-Seiten der Anbieter).

**Chat-Ausgabe:** Zusammenfassung, Scorecard, Top-5, dann die Frage, was gefixt werden soll („alle Hoch“, IDs, „nur Anleitungen“). Hat der Nutzer die Seite gebaut, aber keinen Code verbunden: Ordner verbinden anbieten.

## 7. Fix-Modus

1. Nur freigegebene IDs. Git: Status prüfen, Branch `seo/fixes-<datum>`; ohne Git Dateien sichern.
2. Minimaler Eingriff im Projektstil:
   - **Astro:** Head/Layout-Props für Title/Description/Canonical, `@astrojs/sitemap`, `src/pages/robots.txt.ts`, JSON-LD im Layout.
   - **Next.js:** `metadata`/`generateMetadata`, `app/sitemap.ts`, `app/robots.ts`, `next/image`, Redirects in `next.config`.
   - **WordPress:** Einstellungen des vorhandenen SEO-Plugins; Theme nur per Child-Theme; neue Plugins nur nach Rückfrage.
   - **Hosting/CDN** (z. B. Cloudflare Redirect Rules/Bulk Redirects auf 301): Klick-Anleitung.
   - **Manuell** (Profile, Verzeichnisse, Texte): Schritt-für-Schritt-Anleitung bzw. Textentwurf mit `[bitte ergänzen]` statt erfundener Fakten, Referenzen oder Bewertungen.
3. Nach jedem Fix: Build/Lint, Ergebnis per curl/Browser prüfen, JSON-LD validieren; Status in `seo-audit.md` → `behoben (Datum, Commit)`.
4. Abschluss: behoben / offen / manuell + nötige Schritte (Deploy, URL-Prüfung und Sitemap in der GSC). Commit/Push nur auf Wunsch.

## 8. Recheck

Baseline aus `seo-audit.md` erneut messen (gleiche Methode, gleiche GEO-Anfragen), Status je Finding aktualisieren (behoben/teilweise/offen/neu), Vorher/Nachher-Tabelle. Hinweis: CrUX nutzt ein 28-Tage-Fenster; Rankings reagieren verzögert.
