# Quellenprüfung 0.7.10

Stand: 15.09.2026. Zeitabhängige Aussagen wurden gegen Primärquellen geprüft.

| Aussage | Primärquelle | Ergebnis |
|---|---|---|
| IANA unterscheidet Special-Purpose-Netze nach „Globally Reachable“; `100.64.0.0/10` ist nicht global erreichbar. | https://ftp.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.txt | bestätigt |
| IPv6 `2002::/16` ist 6to4/Special Purpose; `64:ff9b::/96` ist als IPv4/IPv6-Translation registriert. | https://ftp.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.txt | bestätigt; Auditpolicy blockiert Transition/Translation konservativ |
| Playwright `routeWebSocket()` ist für WebSocket-Routing vorgesehen; bei Request-Interception sind Service Worker gesondert zu beachten. | https://playwright.dev/docs/api/class-browsercontext | bestätigt; bestehende 0.7.9-Policy beibehalten |
| Google Consent Mode unterscheidet Basic/Advanced; HTTP-Parameter wie `gcs`/`gcd` sind codierte Signale und keine vom Toolkit selbst zu pflegende stabile String-Wahrheit. | https://developers.google.com/tag-platform/security/concepts/consent-mode | bestätigt; alte harte Regel vollständig aus Skill/Referenz entfernt |
| `disable-model-invocation: true` begrenzt Skills auf explizite Nutzerinvocation. | https://code.claude.com/docs/en/skills | bestätigt; alle Workflow-Skills bleiben user-only |
