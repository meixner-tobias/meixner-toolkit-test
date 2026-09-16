# Baseline 0.7.8 → 0.7.9

- Ausgangsdatei: `meixner-toolkit-0.7.8.zip`
- SHA-256 Ausgangsdatei: `f1743a76fc8d2560c09e69c6a7b14ab5c0d638151670720514e22906b2cab150`
- Baseline-Testlauf: 137/137 grün.
- Bestätigte Blocker vor Änderung: IPv4-mapped-IPv6/Special-Use-Bypass in `netpolicy.mjs`; WebSockets nicht geroutet; Consent-Test blockierte Tracker-Libraries statt nur Collection-Requests; `status: unknown` konnte ausgewertet werden; Storage wurde nicht bewertet; Doctor suchte Playwright nicht zuverlässig im Plugin-Root; `start`/`wissen-update` waren nicht user-only; Browser-E2E fehlte in CI; SiteOne-Tests enthielten reale Resolverpfade; CSR-Regel war pauschal.
