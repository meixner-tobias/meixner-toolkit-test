# Testbericht 0.7.11

**Stand: 16.09.2026 – Release-Candidate-Audit**

## Regression

Die Suite besteht aus 15 isolierbaren Testblöcken A–O. Alle Blöcke wurden nach den finalen Codeänderungen einzeln in frischen Python-Prozessen ausgeführt:

- Phase A–E: **78/78 bestanden**
- Phase F–O: **143/143 bestanden**
- Gesamt: **221/221 bestanden, 0 fehlgeschlagen**

Der zuvor beobachtete Hänger war kein Produkt-Thread-Leak. Ursache war ein flakey Test-Harness mit vielen nacheinander gestarteten Python-CLI-Subprozessen in einzelnen Regressionstests. Negativfälle rufen nun die gleiche Produktlogik direkt auf; echte CLI-Smoke-Tests bleiben erhalten. `tests/run_tests.py --case <name>` und `tests/run_all.sh` unterstützen isolierte Ausführung.

## Statische / Packaging-Prüfungen

- Python `compileall`: **PASS**
- Node `--check` für ausgelieferte JS/MJS-Dateien: **PASS**
- JSON-Parsing: **15/15 gültig**
- `reference_guard.py`: **PASS** (7 Master-/Referenz-JSONs geprüft)
- generischer Secret-Scan auf Meta-/GitHub-Token und Private-Key-Muster: **0 Treffer**
- strukturierter Abgleich der echten kundenspezifischen Konstanten aus den beiden Produktions-Exporten: **keine echten Meta-Pixel-/CAPI-Token-/Testcode-Werte im Plugin**
- Core-Master bleiben `candidate_reference_only`; Registry enthält **keine erfundenen VERIFIED-Master**

## Browser-E2E

`tests/browser_security.mjs` bleibt verpflichtender CI-Test. In der aktuellen Build-Sandbox war `node_modules` nicht vorhanden und `npm ci` konnte wegen fehlendem/stockendem Registry-Zugriff nicht abgeschlossen werden. Daher ist der **exakte Playwright-1.56.1-Chromium-Lauf auf diesem 0.7.11-Artefakt lokal nicht verifiziert**. Das Lockfile pinnt Playwright 1.56.1; vor Production-Freigabe muss der GitHub-Actions-Lauf inklusive Chromium grün sein.

## Freigabestatus

**READY_FOR_EXTERNAL_CI / RELEASE CANDIDATE.** Production-Freigabe erst nach grünem GitHub-Actions-Lauf der frisch ausgelieferten ZIP/Commit-Version.
