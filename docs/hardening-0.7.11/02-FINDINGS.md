# Findings 0.7.11

| ID | Finding | Status | Fix / Vertrag |
|---|---|---|---|
| K1 | Fachlich notwendige Trackingdaten konnten zuvor nur promptseitig fehlen | CLOSED | deterministisches `tracking_plan.py` + `plan_gate.py`; fehlende Evidenz/offene Fragen blockieren Build |
| K2 | GEO-Prompt-Sampling war zu dominant für Google-AI-Sichtbarkeit | CLOSED | Search-Console-Generative-AI-Report als bevorzugte quantitative Quelle; Prompts nur qualitativ |
| K3 | Agent-Readiness nicht systematisch prüfbar | CLOSED | `agent_readiness.py`; native Semantik/Accessible Names/ARIA getrennt von Ranking bewerten |
| K4 | Ein GTM-JSON konnte zu leicht als „Master“ bezeichnet werden | CLOSED | Candidate → echter Import/Preview/Re-Export → semantischer `gtm_master_verify.py`-Roundtrip → Verified-Manifest |
| K5 | Reale Produktionscontainer enthalten wertvolle Struktur, aber auch Secrets/Kundenlogik | CLOSED für Paket | Sanitizer + Reference Guard + Production Reference/Core/Pattern-Trennung; Originale nie paketieren |
| K6 | Reales Serverexport enthielt Meta-CAPI-Token im Klartext | CLOSED im Plugin / EXTERN ACTION REQUIRED | Token wird nicht übernommen; Originaltoken muss außerhalb des Plugins rotiert werden |
| K7 | Reale Referenz hatte kundenfeste Currency/Events/Selectors/Consent | CLOSED | nur Architekturbeleg; keine dieser Entscheidungen wird als Default geerbt |
| K8 | Scroll-/Microevents könnten aus Referenz irrtümlich Ads-/Meta-Conversions werden | CLOSED | Pattern Library markiert Engagement ausdrücklich als nicht standardmäßige Conversion |
| K9 | Stape-Wissensbasis enthielt veraltete Requestformel und harten Gateway-Preis | CLOSED | aktuelle Request-Schätzung/Limitlogik; Preise live prüfen statt festschreiben |
