# Testbericht 0.7.10

Lokaler Build-Lauf:

- `python3 -m compileall -q skills lib tests` → grün
- `node --check` über alle `.mjs` → grün
- `python3 tests/run_tests.py` → **178 Tests, 178 bestanden, 0 fehlgeschlagen**
- JSON-Metadaten werden vor Packaging erneut geparst.

Neu abgedeckt:
- Report `.part`-Symlink-Overwrite und symlinkter Ausgabeordner
- privates Remote-Logo trotz Opt-in
- vollständiger Consent-Szenariovertrag für frühe Abbrüche
- alte `gcs≠G100`-Regel darf nicht wieder in Skill/Referenz auftauchen
- hermetischer `architecture=server`-Build mit injiziertem Resolver
- Shared Address Space als sGTM-Ziel abgelehnt
- 6to4 im Node-Netzguard
- Launch-TLS verbindet zur verifizierten IP

`tests/browser_security.mjs` wurde um einen 6to4-Fall erweitert. Der echte Chromium-Lauf konnte in dieser Build-Sandbox **nicht** lokal ausgeführt werden: `npm ci --no-audit --no-fund` lief wegen fehlendem Registry-/Netzzugriff in einen Timeout. CI installiert Chromium und führt den Browser-Test aus; dieser Teil bleibt bis zu einem grünen CI/external Run `NOT_VERIFIED_LOCALLY`.
