---
name: wissen-update
description: Prüft, ob sich seit dem letzten Stand etwas bei Google Search, KI-Suche, GTM/GA4/Google Ads, Consent Mode, Meta CAPI, Stape, Shopify/WooCommerce, Browser-Tracking-Schutz oder DSGVO/TDDDG geändert hat, und schlägt konkrete Updates für die Wissensdateien des Plugins vor. Nutzen bei /wissen-update, "was hat sich geändert", "Plugin aktualisieren", "Tracking-News", "SEO-News".
disable-model-invocation: true
---

# /wissen-update – Wissensdateien aktuell halten

Arbeitsweise (Fakten, Budgets, Rückfragen): `../setup/references/arbeitsweise.md`.

## 1. Stand ermitteln
Wissensdateien lesen: `../tracking-audit/references/*.md`, `../seogeo/SKILL.md` (Abschnitte zu FAQ/HowTo, Bots, CWV, llms.txt). Stand-Angabe („Stand MM/JJJJ“) je Datei notieren. Zeitraum = seit diesem Stand (Standard: letzte 45 Tage).

## 2. Recherche – nur Primärquellen
| Thema | Quelle |
|---|---|
| Google Search / AI Overviews | https://developers.google.com/search/updates · https://status.search.google.com · Google Search Central Blog |
| GTM / Google tag / Tag Gateway | https://support.google.com/tagmanager/answer/4620708 (Release Notes) |
| GA4 | GA4-Hilfe „What’s new“ · https://support.google.com/analytics/answer/17016975 (Consent/Ads-Datennutzung) |
| Google Ads / Consent Mode | https://developers.google.com/tag-platform/security/guides/consent · Google-Ads-Hilfe zu Consent/Enhanced Conversions |
| Meta CAPI | https://developers.facebook.com/docs/marketing-api/marketing-api-changelog · Conversions-API-Doku |
| Stape | https://stape.io/news · Stape-Doku zu Power-ups/Preisen |
| Browser | https://webkit.org/blog (ITP, Link Tracking Protection) · Firefox/Brave Privacy-Updates |
| Shop-Systeme | https://shopify.dev/changelog · GTM4WP/WooCommerce Release Notes |
| KI-Crawler | offizielle Bot-Seiten von OpenAI, Anthropic, Perplexity, Google (Google-Extended) |
| Recht | DSK (datenschutzkonferenz-online.de), EDPB, EuGH/EuG zum Data Privacy Framework |

Nur Änderungen mit Datum und Quelle aufnehmen; Branchenblogs höchstens als Hinweis „unbestätigt“.

## 3. Ergebnis
`wissen-update-<JJJJ-MM>.md`:
- Tabelle: Änderung · Datum · Quelle · betroffene Datei/Abschnitt · Auswirkung auf Audits (neuer Prüfpunkt? geänderte Empfehlung?) · Dringlichkeit.
- Pro betroffener Datei der **konkrete neue Text** (Absatz ersetzen/ergänzen) inkl. neuem „Stand“.
- „Keine relevanten Änderungen“ ist ein gültiges Ergebnis.

## 4. Übernehmen (nur nach Freigabe)
Installierte Plugin-Dateien nicht direkt bearbeiten. Mit dem Skill `cowork-plugin` (Anpassen) bzw. im Plugin-Quellordner die freigegebenen Textänderungen einarbeiten, Version erhöhen (Patch, z. B. 0.2.0 → 0.2.1) und neu paketieren.

## Automatisch
Als geplante Aufgabe monatlich möglich: Die Aufgabe führt Schritt 1–3 aus (ohne Plugin-Zugriff mit der Themenliste oben) und liefert den Bericht; übernommen wird erst nach Freigabe in einer normalen Session.
