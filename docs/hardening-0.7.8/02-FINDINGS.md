# Findings 0.7.8

| ID | Finding | Status | Evidenz | Fix | Test | Ergebnis |
|---|---|---|---|---|---|---|
| **P2-A** | **0.7.7 dokumentierte eine `ctx.route()`-Sperre, die im Code nicht existierte** | `CONFIRMED` | `grep "\.route("` im ausgelieferten `consent_test.mjs` → null Treffer; `03-SECURITY.md` beschrieb sie samt Restrisiko | Ursache: ein Patch-Anker aus der 0.7.5-Runde griff nie (die `newContext`-Zeile trug damals noch `userAgent`), das Ergebnis wurde nicht geprüft | Abschnitt I prüft jetzt den **Quelltext** auf Vorhandensein und Reihenfolge | `CLOSED` |
| **P1-A** | Browser-/Playwright-SSRF | `CONFIRMED` | keine Start-URL-Prüfung, keine Request-Kontrolle | `lib/netpolicy.mjs` (eigenes Modul, ohne Browser testbar): Schema-, Port-, Userinfo-, IPv4-, IPv6- und Hostname-Regeln plus DNS-Auflösung. Schicht A vor `page.goto()`, Schicht B über `context.route("**/*")` für Navigation, Subressourcen, XHR/fetch und Frames | 23 Tests (Abschnitt I) | `CLOSED` |
| **P1-D** | Mutierende Skills ohne technische Grenze | `CONFIRMED` | `disable-model-invocation` in keinem Frontmatter | `seogeo`, `tracking-audit`, `launch`, `kundenbericht`, `setup` auf `true`. `start` und `wissen-update` bleiben modellaufrufbar (read-only) | Abschnitt J prüft jedes Frontmatter | `CLOSED` |
| **P1-F** | SiteOne-Test war eine Attrappe | `CONFIRMED` | Der Test prüfte nur, dass `REVIEW_REQUIRED` **fehlt**; der Prozess starb in Wirklichkeit an der DNS-Auflösung | Test belegt jetzt, **wo** der Abbruch erfolgt: Scope-Prüfung passiert, Abbruch erst an der Ziel-URL | 2 Tests | `CLOSED` |
| **P1-B** | Consent-Interpretation ohne OBSERVED/INTERPRETED/RISK/LEGAL_REVIEW_REQUIRED | `CONFIRMED` | `assess()` springt vom Messwert zur Einstufung | **keiner** | – | `OPEN` |
| **P1-C** | Storage erfasst, aber nicht bewertet; `indexedDB: "vorhanden"` meint nur die API | `CONFIRMED` | `res.speicher` wird in `assess()` nie gelesen | **keiner** | – | `OPEN` |
| **P1-E** | Browser-/Consent-Pfad nicht in CI | `CONFIRMED` | CI installiert kein Chromium | **keiner** | – | `OPEN` |
| **P1-G** | Launch-Integrationstest beweist nur „kein Crash" | `CONFIRMED` | Fixture auf `127.0.0.1` wird vom eigenen Guard blockiert | **keiner** – eine Transport-Injektion wäre ein Umbau, den diese Phase ausschließt | – | `OPEN` |
| **P1-H** | Dateirechte uneinheitlich | `PARTIALLY_CONFIRMED` | 0600 in `siteone.py` und `render_report.mjs`, nicht in `consent_test.mjs` und `launch_check.py` | **keiner** | – | `OPEN` |
| **P1-I** | Doctor findet Playwright nur in `~/.cache/mt-playwright` | `NOT_REPRODUCED` | `CLAUDE_PLUGIN_ROOT` wird seit 0.7.5 mitgeprüft, in `doctor.py` und in beiden `.mjs` | keiner nötig | Abschnitt G | `KEIN FEHLER` |
| **P2-B** | Pauschale CSR-/Crawler-Regeln | **nicht geprüft** | – | – | – | `OPEN` |
| **P2-C** | Skill-Kurzform | `CONFIRMED`, in 0.7.7 entschärft | – | Formulierung bereits korrigiert | – | `CLOSED` |
| **P2-D** | Cowork-Dokumentation | `CONFIRMED` als unbelegt | Aussage in 0.7.7 zurückgezogen, aber **nicht** durch eine belegte ersetzt | **keiner** | – | `PARTIALLY_FIXED` |
| **P2-E** | Playwright-Version | `NOT_REPRODUCED` als Problem | 1.56.1 gepinnt, Lockfile mit Integrity-Hash | Pin bewusst behalten; Upstream-Stand **nicht geprüft** | Abschnitt H | `OPEN (dokumentiert)` |
| **Q1** | Hermetische Suite | `CONFIRMED`, erledigt | – | Resolver injizierbar in Python und Node | Abschnitte B, I | `CLOSED` |
| **Q2** | CI-Vollständigkeit | `CONFIRMED` | Browser-Pfad fehlt | teilweise – Kernsuite läuft, Chromium nicht | – | `PARTIALLY_FIXED` |
| **Q3** | Packaging-Integrität | `CONFIRMED`, erledigt | 0.7.6 lieferte leere Doku-Verzeichnisse | ZIP wird nach dem Packen erneut geöffnet und inventarisiert | – | `CLOSED` |

**Regel für diesen Bericht:** `CLOSED` steht nur dort, wo Code vorhanden, Test vorhanden, Test ausgeführt und grün ist. Alles andere heißt `OPEN` oder `PARTIALLY_FIXED`. Genau diese Regel wurde in 0.7.7 verletzt.
