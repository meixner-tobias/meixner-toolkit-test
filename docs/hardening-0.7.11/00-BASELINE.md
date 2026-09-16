# Baseline 0.7.10 → 0.7.11

- Ausgangspunkt: `meixner-toolkit-0.7.10.zip` (technisch gehärtete 0.7.10).
- Ziel 0.7.11: Fachqualität für SEO/GEO/Tracking erhöhen, fehlende Entscheidungen deterministisch blockieren und reale GTM-Strukturbelege sicher als Referenz nutzbar machen.
- Zusätzlich wurden zwei vom Nutzer bereitgestellte, real eingesetzte GTM-Exporte (Web + Server) ausschließlich als Analysequelle verwendet.
- Die Original-GTM-Exporte werden **nicht** in das Plugin paketiert. Der Serverexport enthielt einen echten Meta-CAPI-Access-Token und weitere Kunden-/Plattformwerte; deshalb wird nur eine reproduzierbar sanitisierte Referenz ausgeliefert.
- Referenzarchitektur: Web Google Tag/GA4 → First-Party-sGTM; Server GA4-Client → serverseitiger Conversion Linker / plattformspezifische Tags. Kundenereignisse und Consent-Entscheidungen sind kein Default.
