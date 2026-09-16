# Generative AI Search & Agent Readiness — Primärquellen-Notizen

Stand: 16.09.2026. Zeitkritische Aussagen vor Kundenreport erneut gegen die verlinkten Primärquellen prüfen.

## Google Search: generative KI

- Google Search hat einen eigenen Leitfaden für AI Overviews / AI Mode. Die normalen SEO-Grundlagen bleiben maßgeblich; es gibt **keine spezielle Datei und kein spezielles Markup**, das für diese Funktionen erforderlich wäre. Crawlability, Indexierbarkeit, hilfreiche Inhalte, interne Verlinkung, strukturierte Daten passend zum sichtbaren Inhalt und gute Seitenerfahrung bleiben relevant.
  Quelle: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Seit **31.08.2026** sind die separaten Search-Console-Berichte zur Sichtbarkeit in generativen KI-Funktionen weltweit ausgerollt. Der Bericht zeigt u. a. Impressionen sowie Aufschlüsselungen nach Seiten, Ländern, Geräten und Zeiträumen. Diese Daten sind die bevorzugte quantitative Quelle für Google-AI-Sichtbarkeit; manuelle Prompt-Stichproben sind nur eine qualitative Ergänzung.
  Quelle: https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports
- Search Console / Google liefern Sichtbarkeit, nicht automatisch Ursache oder Rankingfaktor. Aus einer Veränderung im AI-Report niemals ohne weitere Evidenz eine konkrete Optimierungsursache ableiten.

## OpenAI / ChatGPT Search

- Für Aufnahme in ChatGPT Search muss OAI-SearchBot crawlbar sein; CDN/Host müssen die veröffentlichten Bot-IP-Bereiche zulassen. GPTBot ist davon getrennt und betrifft potenzielle Trainingsnutzung.
  Quelle: https://help.openai.com/en/articles/9237897-chatgpt-search
- ChatGPT Search versieht Referral-Links mit `utm_source=chatgpt.com`; Analytics-Auswertungen sind trotzdem nur eine Untergrenze der tatsächlichen Sichtbarkeit.
  Quelle: https://help.openai.com/en/articles/12627856-publishers-and-developers-faq

## Agent Readiness / ARIA

- OpenAI empfiehlt für ChatGPT Agent in Atlas ausdrücklich barrierearme Markups. Der Agent nutzt ARIA-Rollen, -Labels und -States, um Struktur und interaktive Elemente zu verstehen. Deskriptive Rollen/Labels/States an Buttons, Menüs und Formularen verbessern die Interaktionsfähigkeit.
  Quelle: https://help.openai.com/en/articles/12627856-publishers-and-developers-faq
- Das ist **kein belegter Google-Rankingfaktor** und darf im Report nicht als solcher dargestellt werden. Es ist ein Agent-Kompatibilitäts-/Accessibility-Befund.
- ARIA ersetzt keine korrekte native HTML-Semantik. Native Elemente (`button`, `label`, `nav`, `main`, `form`) bevorzugen und ARIA nur ergänzend einsetzen.

## Website-Tools / WebMCP (optional, kein Rankingfaktor)

- OpenAI dokumentiert seit 2026 Website-Tools im integrierten ChatGPT-Desktop-Browser. Websites können dafür über **WebMCP** (vorgeschlagener Webstandard) explizite Tools bereitstellen, die ChatGPT auf der geöffneten Seite erkennen und – nach Nutzerfreigabe – verwenden kann.
  Quelle: https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app
- WebMCP ist **keine Voraussetzung** für ChatGPT Search, Crawling oder Google-Rankings. Im Toolkit deshalb nur als optionale Agent-Integration bewerten, wenn die Website transaktionale/interaktive Agent-Workflows sinnvoll unterstützen soll.
- Tool-Definitionen erhöhen die Angriffsfläche (u. a. Prompt Injection/Datenexfiltration). Nie als pauschale „GEO-Optimierung“ empfehlen; nur bei konkretem Use Case und mit Security Review.

## Bewertungsregeln im Toolkit

1. Google-AI-Sichtbarkeit quantitativ zuerst aus Search Console, sofern verfügbar.
2. Prompt-Stichproben getrennt als qualitative, schwankende Momentaufnahme behandeln.
3. Agent Readiness getrennt von SEO-Ranking bewerten: `GEO`/KI-Suche, nicht `ONPAGE`-Rankingversprechen.
4. Fehlende ARIA-Beschriftungen nur dann als Finding melden, wenn ein interaktives Element tatsächlich keinen maschinenlesbaren Namen besitzt.
5. Keine Aussage wie „ARIA verbessert Rankings“ oder „llms.txt verbessert AI-Rankings“.
