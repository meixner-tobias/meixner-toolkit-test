# Quellenprüfung 0.7.9

Stand: 15.09.2026. Für zeitabhängige Aussagen wurden Primärquellen geprüft.

| Aussage | Primärquelle | Ergebnis |
|---|---|---|
| `browserContext.route()` kann Service-Worker-Requests verfehlen; bei Request-Interception empfiehlt Playwright `serviceWorkers: 'block'`. | https://playwright.dev/docs/api/class-browsercontext · https://playwright.dev/docs/network | bestätigt |
| `browserContext.routeWebSocket()` existiert seit Playwright 1.48 und kann WebSocket-Verbindungen routen. | https://playwright.dev/docs/api/class-browsercontext · https://playwright.dev/docs/release-notes | bestätigt; Pin 1.56.1 unterstützt die API |
| Google Consent Mode unterscheidet Basic/Advanced; `gcs`/`gcd` sind codierte HTTP-Parameter und können sich ändern. | https://developers.google.com/tag-platform/security/concepts/consent-mode | bestätigt; deshalb keine harte String-Decodierung als Rechts-/Consent-Wahrheit |
| IANA führt Special-Purpose IPv4/IPv6-Adressräume; z. B. Shared Address Space ist nicht global routbar. | https://www.iana.org/numbers/registries | bestätigt; Browserpolicy blockiert relevante nicht-globale/special-use Bereiche konservativ |
| Claude-Skills können mit `disable-model-invocation: true` auf explizite Nutzeraufrufe begrenzt werden. | https://code.claude.com/docs/en/skills | bestätigt; alle ausgelieferten Workflow-Skills sind user-only |
| Cowork läuft standardmäßig cloudseitig; lokale Ausführung kann bei bestehenden Desktop-Setups existieren. | https://support.claude.com/en/articles/14479288-claude-cowork-architecture-overview | bestätigt |
