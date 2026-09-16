# Verbleibende Risiken 0.7.9

1. **Browser-E2E lokal nicht ausgeführt:** Die Build-Sandbox konnte `npm ci` nicht abschließen. CI ist so konfiguriert, dass Playwright Chromium installiert und `tests/browser_security.mjs` ausführt. Produktive Freigabe erst nach grünem CI-Lauf.
2. **DNS-Rebinding:** Node/Playwright prüfen DNS-Ziele, pinnen Chromiums Socket aber nicht an die geprüfte IP. Das reduziert SSRF-Risiko stark, ist aber kein mathematischer Ausschluss von Rebinding.
3. **Consent ist kein Rechtsgutachten:** Technische Requests/Storage werden als Beobachtung bzw. Compliance-Risk formuliert. Rechtliche Einordnung bleibt separat.
4. **Service Worker werden im Consent-Audit blockiert:** Das verbessert die Netzwerksicherheitsgrenze, kann aber Seiten mit Service-Worker-spezifischer Logik anders verhalten lassen; der Report weist darauf hin.
5. **Windows-Dateirechte:** `0600/0700` sind POSIX-Semantik und keine Windows-ACL-Garantie.
6. **Playwright 1.56.1 bleibt bewusst gepinnt:** `routeWebSocket` ist seit 1.48 vorhanden. Ein Upstream-Upgrade wurde nicht erzwungen, weil der Lockfile-Pin reproduzierbar bleiben soll und ein Major/Minor-Upgrade separat getestet werden sollte.
