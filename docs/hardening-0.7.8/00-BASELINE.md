# Baseline 0.7.7 → 0.7.8

| Angabe | Wert |
|---|---|
| Ausgangsarchiv | `meixner-toolkit-0_7_7.zip`, **hochgeladen und geprüft** |
| SHA-256 | `862905f76d1e328db4d3c8d5547bab4e95921b845dc8d76b807d40d010933caa` |
| Identisch mit dem ausgelieferten 0.7.7-Paket | ja, bitgenau |
| Traversal / Symlinks / absolute Pfade | keine |
| Version im Archiv | 0.7.7 |
| Dateien | 52 |

## Baseline-Testlauf, aus dem entpackten Archiv

```
python3 -m compileall -q skills lib tests     → OK
node --check (alle .mjs)                      → OK
python3 tests/run_tests.py                    → 94 Tests, 94 bestanden, 0 fehlgeschlagen
dito mit gesperrtem DNS                       → 94 Tests, 94 bestanden, 0 fehlgeschlagen
```

Der extern gemeldete Wert (94/94) ist damit unabhängig bestätigt, und die Hermetik ist belegt statt behauptet.
