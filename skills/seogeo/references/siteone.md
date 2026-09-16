# SiteOne Crawler als Crawl-Engine

Stand 09/2026. Quelle: https://github.com/janreges/siteone-crawler (MIT, Ján Regeš), Doku: https://crawler.siteone.io

**Wichtig:** SiteOne Crawler ist **keine Cloud-API mit API-Key**, sondern eine lokale CLI (ein natives Binary, Rust). Es gibt nichts zu verbinden: Der Crawl läuft auf Tobias' Rechner, das Ergebnis liegt als JSON auf der Platte, und dieses JSON ist die Eingabe für das Audit. Vorteile: keine Kosten, keine Kundendaten bei Dritten, kein Rate-Limit, reproduzierbar.

## Zwei Wege, den Crawler zu benutzen
1. **Desktop-App (GUI)** – https://github.com/janreges/siteone-crawler-gui (Electron, macOS/Windows/Linux). Tobias klickt den Crawl selbst, exportiert auf dem Tab „Result“ den **JSON-Report**; alle Dateien landen im Ordner `SiteOne-Crawler` auf dem Schreibtisch. Das Plugin wertet die neueste JSON automatisch aus:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py"            # nimmt die neueste JSON aus ~/Desktop/SiteOne-Crawler
   python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" --from-json <pfad>
   ```
   Liegt der Ordner woanders: `SITEONE_OUTPUT_DIR` setzen. In Cowork ohne Dateizugriff: die JSON einfach in den Chat hochladen.
   Soll der Skill mitlaufen, während Tobias in der App klickt: `python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" --watch` wartet auf den neuen Export und wertet ihn sofort aus.
2. **CLI** – dann startet der Skill den Crawl selbst (unten): eine URL genügt, Crawl und Auswertung laufen in einem Rutsch. Ergebnis identisch, nur ohne Klicken.

Die GUI ist nur eine Oberfläche für dieselbe Engine. **Eine API oder einen Server-Modus hat keine der beiden Varianten** (im Quellcode geprüft; die dabei betrachtete Version ist nicht dokumentiert worden – vor einer Wiederverwendung dieser Aussage gegen die aktuellen Releases auf github.com/janreges/siteone-crawler prüfen): Der Crawler kann nur ausgehend ein LLM anrufen (`--ai-*`, eigener Schlüssel, kostet), aber nichts und niemand kann ihn von außen abfragen. Die Übergabe läuft deshalb über die exportierte Datei.

## Installation der CLI (einmalig)
```bash
brew install janreges/tap/siteone-crawler   # macOS/Linux
siteone-crawler --version
```
**Windows:** ZIP `siteone-crawler-v<version>-win-x64.zip` aus den [Releases](https://github.com/janreges/siteone-crawler/releases) entpacken, Ordner z. B. nach `C:\Tools\siteone-crawler`, dann entweder in den PATH aufnehmen oder den vollen Pfad setzen:
```powershell
setx SITEONE_BIN "C:\Tools\siteone-crawler\siteone-crawler.exe"
py -3 "<skill-pfad>\scripts\siteone.py" https://www.kunde.de --out-dir .\crawl
```
Abweichender Pfad: `--bin` oder Umgebungsvariable `SITEONE_BIN`.

## Aufruf über das Plugin
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" https://www.kunde.de --out-dir ./crawl        # Standard
python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" https://www.kunde.de --out-dir ./crawl --browser   # JS-/SPA-Seiten
python3 "${CLAUDE_SKILL_DIR}/scripts/siteone.py" --from-json ./crawl/siteone-raw.json          # nur auswerten
```
Erzeugt `crawl/siteone-raw.json` (Rohdaten), `crawl/siteone-report.html` (interaktiver Report, kann man dem Kunden zeigen) und `crawl/crawl-summary.json` (verdichtet). Das Skript druckt einen kurzen Textauszug – **immer den Auszug lesen, nie die Roh-JSON** (mehrere hundert KB).
Standardmäßig höflich: 2 Worker, 5 Requests/Sekunde, robots.txt wird respektiert. Für große Sites `--max-depth` setzen.

## Was der Crawler liefert (und das Audit nicht mehr selbst erheben muss)
- Alle URLs mit Statuscode, Antwortzeit, Größe, Cache-Headern; 404-Liste inkl. verlinkender Seite; Weiterleitungen
- SEO-Tabelle je Seite: Title, Description, H1, Indexierbarkeit, robots.txt-Sperre; doppelte Titel/Descriptions; Überschriftenstruktur mit Fehlerzählung; Open Graph / Twitter Cards
- Security-Header (CSP, HSTS …) mit Einstufung, SSL/TLS-Zertifikat und Protokolle, DNS/IPv6
- Barrierefreiheit (Alt-Texte, Lang-Attribut, Formular-Labels, ARIA, Überschriften-Sprünge) und Best Practices (DOM-Tiefe, Brotli, WebP/AVIF, Inline-SVG)
- Qualitäts-Scores 0–10 je Kategorie **mit Begründung je Abzug** – nützlich als schneller Gesamteindruck, aber im Kundenbericht nie ungeprüft übernehmen
- Optional: `--browser` rendert jede Seite in echtem Chromium (Post-Render-DOM, Konsolenfehler, fehlgeschlagene Requests, Screenshots), `--markdown-export-dir` exportiert die Texte aller Seiten als Markdown – ideal für die inhaltliche Bewertung

## Was er nicht kann (bleibt Aufgabe des Skills)
- **GEO / KI-Sichtbarkeit**: Zugang für KI-Bots, Entität und Erwähnungen im Netz, Stichprobe in KI-Antworten
- **Consent- und Tracking-Verhalten**: dafür `consent_test.mjs` aus `tracking-audit` (SiteOne kann Cookie-Banner nur für Screenshots ausblenden)
- **Core Web Vitals aus Felddaten**: dafür PageSpeed Insights (CrUX); SiteOne misst nur eigene Antwortzeiten
- **Rankings, Klicks, Suchvolumen, Backlinks**: dafür Search Console/GA4-Exporte bzw. kostenpflichtige Dienste
- **Alte Domains, www/https-Varianten, Soft-404**: dafür `launch_check.py`
- **Bewertung**: Der Crawler meldet Abweichungen, nicht deren Geschäftsrelevanz. Priorisierung, Suchintent, Content-Lücken und Formulierung bleiben Aufgabe des Audits.

## Grenzen und Vorsicht
- Ohne `--browser` wird kein JavaScript ausgeführt. Bei SPA-Seiten sonst massenhaft Falschmeldungen („keine H1“).
- Mit `--browser` wird jede Seite doppelt geladen (Status + Rendering), HTTP-Auth und Cookies werden nicht an den Browser weitergereicht.
- Der Crawler erzeugt echten Traffic. Auf kleinen Hostern Worker und Rate niedrig halten, nicht während Lastspitzen crawlen, bei Kundenprojekten vorher Bescheid geben.
- Ein Score von 10 bedeutet nicht, dass die Seite gut gefunden wird. Schwellwerte (z. B. Title-Länge) sind Richtwerte, keine Regeln.
- Die eingebaute KI-Funktion (`--ai-*`) braucht einen eigenen LLM-Schlüssel und kostet Geld. Wird **nicht** genutzt: Die Analyse macht der Skill selbst.
- Versionen ändern Tabellen und Feldnamen. `siteone.py` liest tolerant; wenn Felder fehlen, die Version im Auszug prüfen (`crawler.version`).
