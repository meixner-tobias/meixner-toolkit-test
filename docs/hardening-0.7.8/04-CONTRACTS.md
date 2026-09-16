# Verträge 0.7.8

Unverändert gegenüber 0.7.7 (audit.json, Launch-Befunde, Tracking-Plan, Mindestversionen — siehe `tests/run_tests.py` Abschnitte C, D, G, H).

## Neu: Netzwerk-Policy

`lib/netpolicy.mjs` exportiert `pruefeZiel(url, resolver?)` → `{erlaubt, grund?}` und `installiereNetzPolicy(ctx, {onBlock, resolver, trackerAbbrechen})`.

Der `resolver` ist injizierbar, damit Tests ohne DNS auskommen. `consent_test.mjs` ist der einzige Consumer. Abschnitt I der Testsuite prüft beides: die Entscheidungslogik **und** dass der Consumer sie tatsächlich aufruft, vor der ersten Navigation.

## Neu: Skill-Klassifikation

| Klasse | Skills | Frontmatter |
|---|---|---|
| A — read-only | `start`, `wissen-update` | modellaufrufbar |
| B — lokale Seiteneffekte | `setup`, `kundenbericht` | `disable-model-invocation: true` |
| B/C — Dateien plus Netzabrufe gegen fremde Domains | `seogeo`, `tracking-audit`, `launch` | `disable-model-invocation: true` |

Abschnitt J prüft diese Zuordnung bei jedem Testlauf.
