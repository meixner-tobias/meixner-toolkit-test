# Verbleibende Risiken 0.7.8

## Bestätigt und offen

| ID | Risiko |
|---|---|
| **P1-B** | Consent-Befunde trennen technische Beobachtung nicht von Interpretation. `assess()` springt vom Messwert zur Einstufung. Kann zu einer Aussage im Kundenbericht führen, die technisch nicht gedeckt ist. |
| **P1-C** | `res.speicher` wird geschrieben und in `assess()` nie gelesen. `indexedDB: "vorhanden"` heißt nur, dass der Browser die API kennt — nicht, dass die Website sie nutzt. Irreführend, unverändert. |
| **P1-E** | Der Browser-/Consent-Pfad läuft nicht in CI. Chromium wird dort nicht installiert. |
| **P1-G** | Der Launch-Integrationstest beweist „kein Crash", nicht „Crawl funktioniert" — das Fixture auf `127.0.0.1` wird vom eigenen Guard blockiert. |
| **P1-H** | Dateirechte: 0600 in zwei von vier schreibenden Stellen. Keine Windows-ACL-Härtung. |
| **P2-B** | Pauschale CSR-/Crawler-Regeln in den SEO/GEO-Referenzen — in dieser Phase nicht einmal angesehen. |
| **P2-D** | Cowork: die falsche Aussage ist zurückgezogen, eine belegte ist nicht an ihre Stelle getreten. |
| **P2-E** | Playwright 1.56.1 bewusst gepinnt. Der aktuelle Upstream-Stand wurde **nicht** geprüft. |

## Nicht verifizierbar in dieser Umgebung

Consent-Test mit echtem Browser, PDF-Erzeugung, Windows-Pfade, `claude plugin validate`, echter SiteOne-Crawl, GTM-Vorschau-Modus. **Die neue Netzwerk-Policy ist nie gegen einen laufenden Chromium gelaufen** — getestet ist die Entscheidungsfunktion, nicht das Zusammenspiel mit Playwright.

## Methodisches Risiko — der wichtigste Punkt

In vier aufeinanderfolgenden Versionen habe ich Änderungen als erledigt gemeldet, die nie im Code landeten:

| Version | Gemeldet | Tatsächlich |
|---|---|---|
| 0.7.5 | `ctx.route()` blockt private Ziele | Patch-Anker griff nie, Code fehlte bis 0.7.8 |
| 0.7.5 | Node-/Python-Versionsprüfung in `doctor.py` | `NODE_MIN` existierte nicht |
| 0.7.6 | `add()` in `launch_check.py` | durch eine Textersetzung gelöscht |
| 0.7.6 | Enums im Renderer | frei erfunden statt aus dem Schema gelesen |

Dreimal hat eine externe Prüfung das gefunden, nicht ich. Ursache ist immer dieselbe: Patch per Textersetzung, Syntaxprüfung bestanden, kein Nachweis, dass die Änderung tatsächlich drin ist.

Die Gegenmaßnahme steckt jetzt in der Suite: Abschnitt I prüft den **Quelltext** von `consent_test.mjs` darauf, dass die Policy aufgerufen wird und vor der ersten Navigation steht. Abschnitt J prüft jedes Frontmatter. Abschnitt H prüft Dokumentation gegen Code. Das ersetzt keine Sorgfalt, aber es fängt genau diesen Fehler.

**Wer diese Version prüft, sollte jeder `CLOSED`-Angabe misstrauen und den Test dazu selbst laufen lassen.**
