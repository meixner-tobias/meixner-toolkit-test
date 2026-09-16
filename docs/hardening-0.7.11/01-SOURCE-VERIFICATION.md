# Quellenprüfung 0.7.11

Stand: 16.09.2026. Zeitabhängige Fachregeln wurden gegen aktuelle Primär-/Herstellerquellen geprüft.

| Aussage | Quelle | Ergebnis |
|---|---|---|
| Google Search besitzt einen separaten Generative-AI-Performance-Bericht; weltweiter Rollout 31.08.2026. | https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports | bestätigt |
| Für AI Overviews/AI Mode gelten normale SEO-Grundlagen; keine spezielle GEO-Datei/Markup erforderlich. | https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | bestätigt |
| ChatGPT-Agenten profitieren von korrekter nativer Semantik sowie ARIA-Rollen/Labels/States; dies ist kein belegter Google-Rankingfaktor. | https://help.openai.com/en/articles/12627856-publishers-and-developers-faq | bestätigt / sauber getrennt |
| GTM-Container können als JSON exportiert, angepasst und importiert werden. | https://support.google.com/tagmanager/answer/6106997 | bestätigt |
| Serverseitige Google-Ads-Conversions: GA4-Client + serverseitiger Conversion Linker + Ads-Conversion-Tag; doppelte äquivalente Web-Conversions vermeiden. | https://developers.google.com/tag-platform/tag-manager/server-side/ads-setup | bestätigt |
| Meta Browser + CAPI erfordert für Deduplizierung denselben Eventnamen und dieselbe `event_id`. | https://stape.io/helpdesk/documentation/how-to-set-up-meta-conversions-api | bestätigt |
| Stape Setup Wizard kann Web-/Server-GTM-Konfigurationen bootstrapen; Toolkit behandelt das Ergebnis bis zum echten Roundtrip nur als Candidate. | https://stape.io/helpdesk/documentation/setup-wizard-overview | bestätigt; zusätzliche Toolkit-Sicherheitsregel |
| Stape zählt eingehende Serverrequests; grobe aktuelle Schätzung ≈ GA-Seitenaufrufe × 10. | https://stape.io/helpdesk/knowledgebase/how-do-you-calculate-requests | bestätigt |
| Stape-Pause-Logik: Pro bei 110 %, Business/Enterprise beim ersten Überlimit mit einmaliger 30-Tage-Gnadenfrist, Free-Sonderregel. | https://stape.io/helpdesk/documentation/request-limits-and-pause-logic | bestätigt |
| Gateway-Preise ändern sich und werden nicht mehr hart im Toolkit festgeschrieben. | https://stape.io/price-gateway | bestätigt / live prüfen |
