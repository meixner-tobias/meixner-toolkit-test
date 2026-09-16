# Verträge 0.7.9

- Audit-/Report-Schema bleibt unverändert gegenüber 0.7.8.
- `lib/netpolicy.mjs`: `pruefeZiel(url, resolver?) -> {erlaubt, grund?}`; Resolver ist für hermetische Tests injizierbar.
- `installiereNetzPolicy(ctx, ...)` schützt HTTP(S) und WebSocket; Consent-Context muss Service Worker für diese Auditgrenze blockieren.
- Tracking-Hits besitzen zusätzlich `role: loader|collection`. Nur `collection` wird im sicheren Modus aktiv abgebrochen.
- Consent-Szenario ist nur auswertbar bei `status=geprueft`, ohne `abbruch` und ohne Fehler.
- Storage: `speicher_before`, `speicher_after`, `speicher_delta`; IndexedDB unterscheidet API-Verfügbarkeit von tatsächlich gefundenen Datenbanken.
- Alle Workflow-Skills: `disable-model-invocation: true`.
