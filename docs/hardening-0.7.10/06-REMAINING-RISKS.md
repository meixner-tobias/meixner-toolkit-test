# Verbleibende Risiken 0.7.10

1. **Chromium-E2E lokal nicht verifiziert:** Paketinstallation war in der Build-Sandbox wegen fehlendem Registry-/Netzzugriff nicht möglich. Der Test ist in CI verdrahtet, produktive Freigabe sollte einen grünen Browser-Security-Lauf voraussetzen.
2. **Playwright-DNS-Rebinding:** Der Browserguard prüft DNS vor Requests, pinnt Chromiums TCP-Socket aber nicht selbst. Die Policy reduziert SSRF stark, ist kein formaler Ausschluss jeder Rebinding-Race. Der separate Launch-SSL-Pfad wurde dagegen auf verifizierte IP gepinnt.
3. **Konservative IPv6-Policy:** Transition/Translation-Präfixe (u. a. NAT64/6to4) werden für den Auditbrowser bewusst restriktiv behandelt. Das kann selten legitime Ziele ablehnen; sicherheitsseitig ist dies fail-closed.
4. **Windows ACLs:** POSIX `0600/0700` garantieren unter Windows keine entsprechenden ACLs.
5. **SiteOne HTTP-Auth:** Zugangsdaten werden im Toolkit-Output redigiert, müssen für die externe CLI aber weiterhin als Prozessargument übergeben werden, sofern SiteOne keine sicherere offizielle Eingabeform anbietet. Prozesslisten-Sichtbarkeit bleibt damit ein Plattform-/Tool-Risiko.
6. **Consent ist kein Rechtsgutachten:** Technische Requests, Cookies und Storage werden als Evidenz/Risiko berichtet; rechtliche Endbewertung bleibt getrennt.
7. **Playwright 1.56.1 bleibt gepinnt:** Kein blindes Upstream-Upgrade in diesem Hardening-Pass; ein Versionswechsel braucht separat grüne Browser-/Consent-Tests.
