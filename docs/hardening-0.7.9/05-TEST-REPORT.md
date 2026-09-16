# Testbericht 0.7.9

Lokaler Lauf in der Build-Umgebung:

- `python3 -m compileall -q skills lib tests` → grün
- `node --check` über `.mjs` → grün
- `python3 tests/run_tests.py` → **164 Tests, 164 bestanden, 0 fehlgeschlagen**
- JSON-Parsing der ausgelieferten JSON-Dateien → im finalen Packaging-Lauf erneut geprüft

Neu abgedeckt: IPv4-mapped IPv6, Special-Use IPv4, WebSocket-/Service-Worker-Policy statisch, Tracker-Loader vs. Collection, Browserfehler nicht auswertbar, Storage-Deltas, Doctor-Plugin-Root, alle Skill-Frontmatter, hermetischer Launch-Erfolgspfad und SiteOne-Scope.

`tests/browser_security.mjs` ist ein echter Chromium-Test für private HTTP-, mapped-IPv6- und WebSocket-Ziele. Die CI installiert Chromium und führt ihn aus. **In der lokalen Build-Sandbox konnte Playwright wegen fehlendem Paket-/Netzzugriff nicht installiert werden; dieser Browserlauf ist hier deshalb NOT_VERIFIED und muss in CI/externer Umgebung grün sein, bevor produktiv freigegeben wird.**


> **Korrektur aus 0.7.10:** Die 164er Suite war nicht vollständig hermetisch: der Tracking-Builder-Serverfall verwendete `sgtm.example.com` mit echtem DNS und konnte bei `out=None` ohne Assertion grün bleiben. In 0.7.10 durch injizierten Resolver und verpflichtenden Success-Assert geschlossen.
