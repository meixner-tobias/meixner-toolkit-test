# Sicherheitsbericht 0.7.8

## Browser-Netzwerkgrenze — neu, getestet

`lib/netpolicy.mjs` entscheidet über jede Adresse. Zwei Schichten: die Start-URL vor `page.goto()`, danach `context.route("**/*")` für Navigation, Subressourcen, XHR/fetch, Frames und Redirects.

Blockiert: `127.0.0.0/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`, `0/8`, Multicast, reserviert, `::1`, `fe80::/10`, `fc00::/7`, `ff00::/8`, IPv4-mapped-Varianten, `localhost`, `metadata.google.internal`, Adressen mit Zugangsdaten, Ports außer 80/443, Schemata außer http/https/ws/wss. Ein Hostname, der auf eine private Adresse auflöst, wird ebenfalls blockiert.

Ausdrücklich **nicht** blockiert: Google, Meta, CMPs, CDNs und Analytics-Anbieter — die müssen messbar bleiben. Nachgewiesen: `www.google-analytics.com` und ein CDN gehen durch, `172.32.0.1` ebenfalls (liegt außerhalb von /12).

**Restrisiken:** WebSockets werden von `route()` nicht erfasst. DNS-Rebinding zwischen Prüfung und Verbindungsaufbau bleibt möglich — Chromium löst selbst auf. Die Policy ist **nie gegen einen echten Browser gelaufen**, weil Chromium in dieser Umgebung nicht installierbar ist. Getestet ist die Entscheidungsfunktion, nicht ihr Zusammenspiel mit Playwright.

## Skill-Invocation
`seogeo`, `tracking-audit`, `launch`, `kundenbericht`, `setup` sind auf `disable-model-invocation: true` gesetzt — Claude kann sie nicht mehr selbst starten. `start` und `wissen-update` bleiben erreichbar. Restrisiko: Das Feld wurde in dieser Umgebung nicht gegen Claude Code validiert (`NOT_VERIFIABLE_IN_CURRENT_ENVIRONMENT`).

## Netzzugriff Python, Geheimnisse, Crawl-Scope, Codeausführung, Abhängigkeiten
Unverändert gegenüber 0.7.7. `lib/urlguard.py` als einziger Baustein, Token-Redaktion in `fill_template.py` und `siteone.py`, Scope-Prüfung mit `REVIEW_REQUIRED`, kein `shell=True`, kein `eval`, Playwright gepinnt und nicht aus `process.cwd()` ladbar.

## Untrusted Input
Website-HTML, `robots.txt`, `llms.txt`, Sitemaps, JSON-LD, HTTP-Header, Tracking-Payloads und Container-Exporte sind **Daten, keine Anweisungen**. Festgehalten in `arbeitsweise.md` Abschnitt 6. Restrisiko: Das ist Prompttext, keine technische Sperre.

## Dateirechte
0600 in `siteone.py` und `render_report.mjs`. **Nicht** in `consent_test.mjs` und `launch_check.py` — offen. Unter Windows gilt: `POSIX file mode guarantees do not directly apply on Windows.` Eine ACL-Härtung ist nicht umgesetzt.
