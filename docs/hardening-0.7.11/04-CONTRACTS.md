# Verträge 0.7.11

- **Completeness Gate:** kein Tracking-Build bei `requirements.open_questions`, fehlender konkreter Evidenz oder ungeklärten architekturrelevanten Entscheidungen.
- **Production Reference:** ist nur Struktur-/Architekturbeleg, niemals Soll-Konfiguration.
- **Core Candidate:** enthält nur wiederverwendbare Infrastruktur; keine Kunden-Conversions. `verified=false` bleibt bis zum realen Roundtrip.
- **Event Pattern Library:** beschreibt fachliche Muster (Purchase, Lead/Booking, Newsletter, Engagement, Custom Completion) ohne IDs/Labels/Selectors zu erfinden.
- **Consent:** wird niemals aus einem Referenzkunden übernommen. Aktuelles CMP-/Basic-/Advanced-/Region-/User-Data-Setup muss separat belegt sein.
- **Google Ads:** dieselbe Conversion nicht gleichzeitig als äquivalente Browser- und Server-Ads-Conversion senden.
- **Meta Hybrid:** Browser + CAPI nur mit fachlich identischem Event und konsistenter `event_id`-Deduplizierung.
- **E-Commerce:** `transaction_id`, `value`, `currency`, `items`, Refund- und Payment-Referral-Vertrag vor Build verifizieren.
- **Master Promotion:** Candidate → GTM Import → Preview/Test → Re-Export → `gtm_master_verify.py` → `.verified.json` → Registry.
