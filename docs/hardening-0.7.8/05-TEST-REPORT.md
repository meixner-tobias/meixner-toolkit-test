# Testbericht 0.7.8

*Diese Datei wird aus dem tatsächlichen Testlauf erzeugt, nicht von Hand gepflegt.*

## Ausgeführte Befehle

```bash
python3 -m compileall -q skills lib tests
node --check skills/tracking-audit/scripts/consent_test.mjs
node --check skills/kundenbericht/scripts/render_report.mjs
npm ci --dry-run --no-audit --no-fund
python3 tests/run_tests.py
```

## Ergebnis

**137 Tests, 137 bestanden, 0 fehlgeschlagen, 0 übersprungen.**

## Abschnitte

- **A.** Launch-Check\n- **B.** URL-Guard\n- **C.** Kundenbericht\n- **D.** Tracking-Builder\n- **E.** GTM-Master / fill_template\n- **F.** SiteOne-Wrapper\n- **G.** Doctor / Versionspruefung\n- **H.** Dokumentation gegen Code\n- **I.** Browser-Netzpolicy (ohne Browser, hermetisch)\n- **J.** Skill-Invocation

## Umgebung

Python 3.12.3 · Node 22.22.2 · npm 10.9.7 · Playwright 1.56.1 gepinnt, **nicht installiert** · Chromium **nicht verfügbar** · SiteOne **nicht installiert** (Tests gegen ein Fake-Binary) · Claude CLI **nicht verfügbar**

Alle Tests sind hermetisch. Einziger Netzzugriff: lokaler Fixture-Server auf `127.0.0.1:8097`. Ein Lauf mit gesperrtem DNS liefert dasselbe Ergebnis.

## Nicht ausgeführt

Consent-Test mit echtem Browser, PDF-Erzeugung, Windows-Pfadtest, echter SiteOne-Crawl, GTM-Vorschau-Modus, `claude plugin validate`. Gründe in `06-REMAINING-RISKS.md`.
