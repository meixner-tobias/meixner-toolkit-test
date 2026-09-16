# Sicherheitsbericht 0.7.9

## Netzwerk
`lib/netpolicy.mjs` erlaubt nur HTTP(S)/WS(S), Ports 80/443, keine Userinfo und blockiert lokale Namen sowie relevante nicht-global routbare/special-use IPv4-/IPv6-Bereiche. IPv4-mapped IPv6 wird nicht mehr als Bypass akzeptiert. Hostnamen werden aufgelöst und jede Antwort geprüft.

Playwright installiert die Policy vor dem Erzeugen von Requests. HTTP(S)-Requests laufen über `context.route`; WebSockets über `routeWebSocket`. Der Consent-Context verwendet `serviceWorkers: 'block'`, weil Playwright dies bei Request-Interception empfiehlt.

**Restrisiko:** DNS-Rebinding zwischen Policy-Prüfung und Chromiums tatsächlichem Socket-Aufbau ist ohne eigenes IP-Pinning nicht formal ausgeschlossen.

## Tracking-Audit
Der sichere Standardmodus lässt Tracking-Libraries (z. B. GTM/gtag/fbevents.js) laden, blockiert aber beobachtete Tracking-Collection-Requests vor dem Versand. So kann Tag-Logik laufen, ohne bewusst echte Conversion-/Analytics-Beacons zu senden. `--echt-senden` bleibt explizit opt-in.

Google-Consent-Parameter werden als codierte Beobachtung protokolliert; keine feste `gcs`-Stringtabelle wird als rechtliche Wahrheit verwendet. Browserfehler und nicht abgeschlossene CMP-Szenarien werden nicht ausgewertet.

## Storage
Nur Schlüsselnamen/DB-Namen werden betrachtet, keine Values. Local-/SessionStorage und IndexedDB werden vor/nach Interaktion verglichen. Namen allein beweisen keinen Tracking-Zweck; der Report formuliert entsprechend vorsichtig.

## Dateien
Eigene sensible POSIX-Outputs werden best-effort auf 0600 gesetzt; neue Crawl-Verzeichnisse auf 0700. SiteOne-Rohdateien werden nach erfolgreichem Crawl auf POSIX nachgehärtet. Windows-ACLs sind nicht durch POSIX-Modi garantiert.

## Prompt Injection
Website-/Crawl-/Tracking-Inhalte bleiben untrusted data und erhalten keinen Instruktionsrang.
