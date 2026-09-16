# Findings 0.7.9

| ID | Finding | Status | Evidenz/Fix | Regression |
|---|---|---|---|---|
| P1-A | Browser-SSRF: mapped IPv6 / special-use / WebSocket | CLOSED im Code | robuste IPv4/IPv6-CIDR-Policy, `routeWebSocket`, Service Worker block | Unit-Policy + `tests/browser_security.mjs` |
| P1-B | `gcs`-Heuristik als harte Consent-Aussage | CLOSED | harte granted-Decodierung entfernt; Beobachtung/Compliance-Risk getrennt | Consent-Pure-Logic Tests |
| P1-C | Storage nur gesammelt, nicht bewertet | CLOSED | before/after Snapshots, Delta, IndexedDB-Namen soweit API verfügbar | Storage-Delta-Test |
| P1-D | Side-effect Skills automatisch aufrufbar | CLOSED | alle sieben Workflow-Skills user-only | Frontmatter-Tests |
| P1-E | Browsersecurity nicht in CI | CLOSED in CI-Konfiguration | Chromium-Installation + Browser-Sicherheitstest | `.github/workflows/test.yml` |
| P1-F | SiteOne-Test nicht hermetisch | CLOSED | pure Scope-Funktion + injizierter Guard; Range-Prüfung vor DNS | Regression |
| P1-G | Launch-Test bewies nur „kein Crash“ | CLOSED | zusätzlicher kompletter hermetischer Main-Erfolgspfad mit injiziertem Transport/SSL | Regression |
| P1-H | Dateirechte inkonsistent | PARTIALLY_FIXED | Consent 0600; SiteOne raw/html best-effort 0600 POSIX; Windows ACL bleibt Plattformgrenze | statisch/Regression |
| P1-I | Doctor ignorierte Plugin-Root | CLOSED | kontrollierte Roots inkl. `CLAUDE_PLUGIN_ROOT`/inferred Plugin-Root | Doctor-Tests |
| P2-B | CSR pauschal kritisch | CLOSED | bot-/evidenzspezifische Bewertung statt pauschaler Severity | Dokumentationsprüfung |
| Q1 | Kern-Suite externes DNS | CLOSED für geänderte Tests | Resolver/Scope injiziert; keine Produktionsdomain für Success-Beweise | 164/164 lokal |
| Q2 | Browser-E2E | ADDED, lokal nicht ausführbar | Testdatei + CI-Job vorhanden; lokaler Container hatte kein installierbares Playwright | CI erforderlich |


> **Korrektur aus 0.7.10:** P1-B war in 0.7.9 nur in der Runtime geschlossen; `SKILL.md` und `references/google.md` enthielten weiterhin die alte harte `gcs≠G100`-Regel. Q1 war ebenfalls zu früh als geschlossen markiert (Builder-DNS-Pfad). Beide Punkte sind in 0.7.10 korrigiert und regressionsgetestet.
