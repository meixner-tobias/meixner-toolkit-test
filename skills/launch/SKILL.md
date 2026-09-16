---
name: launch
description: Go-Live-Abnahme für neue oder umgezogene Websites – prüft Weiterleitungen (alte Domains, www/https), noindex- und robots-Reste, Sitemap, 404, SSL, Rechtsseiten, Formulare, Consent und Tracking und liefert ein Abnahmeprotokoll. Nutzen bei /meixner-toolkit:launch, "Website geht live", "Go-Live Check", "Relaunch prüfen", "Domain-Umzug prüfen".
disable-model-invocation: true
---


Rolle: erfahrener Web-Entwickler, der Livegänge abnimmt. Prüft misstrauisch, bevor der Kunde es merkt, und unterscheidet klar zwischen „blockiert den Start“ und „kann man später machen“.

**Arbeitsweise (Kurzform, Details: `../setup/references/arbeitsweise.md`)**
1. Jede Aussage stammt aus einer Messung dieses Laufs, aus `references/` oder aus einer in dieser Sitzung geprüften Primärquelle. Nichts aus dem Gedächtnis.
2. Recherche-Budget nach `config.json → standards.recherche_budget` (Standard `normal`: max. 8 Suchen, 15 Abrufe). Zwei übereinstimmende Primärquellen genügen.
3. Rohdaten (Crawl-JSON, GSC/GA4-Exporte, Container-Exporte) nie ganz lesen, immer erst per Skript verdichten.
4. Auffällige Befunde mit einer zweiten Methode gegenprüfen, bevor sie in den Report kommen.
5. Fragen bündeln (eine Runde, max. 4) und nur stellen, wenn die Antwort das Ergebnis ändert; sonst Annahme treffen und im Report nennen. Vor jedem eingreifenden Schritt (Code, Import, Veröffentlichen, Versand, kostenpflichtige API) immer fragen.
# /meixner-toolkit:launch – Go-Live-Abnahme

Ziel: Fehler finden, die beim Livegang typischerweise passieren (Staging-Reste, 302 statt 301, noindex, fehlende Search-Console-Meldung), bevor Kunde oder Google sie merken.

> **Windows:** Statt `python3` `py -3` verwenden (bzw. `python`), Pfade mit Anführungszeichen. Node-Skripte laufen unverändert.

## 1. Kontext
`config.json` + `kunden/<slug>.json` lesen (alte Domains, CMS, IDs). Fehlend und nicht ableitbar → eine AskUserQuestion-Runde: neue Domain, alte Domains/URLs, Livegang-Datum, wichtige Formulare, wurde Tracking eingerichtet?

## 2. Automatischer Check (Claude Code lokal oder Shell mit Netz)
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/launch_check.py" https://www.kunde.de --alt https://alt-domain.de --paths /kontakt /leistungen --out launch-check.json
```
Prüft: Host-Varianten → eine kanonische Adresse per 301/308 · alte Domains → 301 pfaderhaltend · Startseite (noindex, Title, Canonical, Staging-Links, Impressum/Datenschutz) · robots.txt (`Disallow: /`) · Sitemap-URLs (Status, noindex) · Soft-404 · SSL-Restlaufzeit · HSTS. Ohne Shell-Netz: gleiche Punkte per WebFetch (liefert Redirect-Status) und Browser-Tool prüfen und vermerken.
Für Umzüge mit geänderten Pfaden: alte URL-Liste (GSC-Export oder alte Sitemap) mit `--paths` testen.

## 3. Weitere Prüfungen
- **Tracking & Consent** (falls eingerichtet): `consent_test.mjs` aus dem Skill `tracking-audit` ausführen (Pfad: `${CLAUDE_SKILL_DIR}/../tracking-audit/scripts/consent_test.mjs`).
- **SEO-Kurzcheck**: `/meixner-toolkit:seogeo quick <url>`-Logik für Titles, H1, strukturierte Daten, Performance (PSI-Key). Ist SiteOne Crawler installiert, zusätzlich `siteone.py` aus dem Skill `seogeo` laufen lassen – findet 404, Weiterleitungen, fehlende Meta-Angaben und Security-Header über die ganze Seite.
- **Formulare**: Mit Tobias abstimmen, dann **ein** Testversand mit eindeutig markierten Testdaten (z. B. „TEST – bitte ignorieren“) – nur nach ausdrücklicher Freigabe, weil ein Formular absenden eine Aktion nach außen ist. Eingang der Mail, Danke-Seite, Conversion-Event prüfen.
- **Manuell (Checkliste für Tobias)**: Search Console – Property verifiziert, Sitemap eingereicht, bei Domainwechsel „Adressänderung“; Bing Webmaster Tools; Google-Unternehmensprofil-Website-Link; externe Profile auf neue URL; Backups und Update-Plan; Uptime-Monitoring; E-Mail-Zustellung (SPF/DKIM/DMARC) falls Mails über die Domain gehen; Staging-Umgebung geschützt (Passwort/noindex).

## 4. Abnahmeprotokoll
`launch-check.md` + `launch-audit.json` (Schema und feste Bereichsnamen: Skill `kundenbericht` → `references/audit-schema.md`, `typ: "launch"`; eigene Findings mit `GOLIVE-` → Bereich **Technik**), Ablage unter `~/.meixner-toolkit/audits/<slug>/`, Eintrag in `kunden/<slug>.json`.
Struktur: Status (✅ bereit / ⚠️ bereit mit offenen Punkten / ❌ nicht bereit) · Kritisch/Hoch zuerst mit Fix · manuelle Checkliste mit Häkchen · Nachweise (Redirect-Ketten, Statuscodes).
Fixes nur nach Freigabe (bei Code-Zugriff wie im `seogeo`-Fix-Modus). Auf Wunsch `/meixner-toolkit:kundenbericht` als Abnahmebericht für den Kunden. Recheck nach 7 Tagen vorschlagen (Indexierung, 404 in der Search Console).
