# Changelog

## 0.7.10 — 15.09.2026

### Security
- Kundenbericht schreibt HTML/PDF jetzt ueber exklusiv erzeugte `.part`-Dateien (`wx`) und prueft den realen Ausgabeordner. Vorbereitete `.part`-Symlinks bzw. symlinkte Ausgabeordner koennen nicht mehr auf fremde Dateien umleiten.
- Remote-Logos laufen auch bei explizitem `--remote-logo` durch die zentrale Public-Network-Policy; der PDF-Browser nutzt dieselbe Netzpolicy.
- Launch-SSL verbindet nicht mehr erneut per Hostname, sondern pinnt den TLS-Socket auf eine unmittelbar zuvor durch `urlguard.py` verifizierte IP; SNI/Zertifikatspruefung bleibt auf dem Originalhost.
- Browser-Netzpolicy blockiert zusaetzlich 6to4 (`2002::/16`) konservativ als Transition-Mechanismus.
- `doctor.py --init` setzt neue Toolkit-Verzeichnisse auf POSIX best-effort auf `0700` und `config.json` auf `0600`.

### Correctness
- Consent-Szenarien initialisieren jetzt alle Summary-Felder (`hits`, `cookies_after`, Storage etc.) bereits vor der Navigation. Fruehe Abbrueche wie `CMP_BUTTON_NICHT_GEFUNDEN` koennen die Abschlussausgabe daher nicht mehr mit `TypeError` abbrechen.
- Alte harte `gcs≠G100`/`G111`-Decodierungsregeln wurden auch aus Skill und Google-Referenz entfernt; Runtime und Wissensbasis behandeln `gcs`/`gcd` konsistent als codierte Evidenz.
- `server_container_url` akzeptiert nur global erreichbare IPs; Shared Address Space (`100.64.0.0/10`) und andere nicht globale Ziele werden abgelehnt. Resolver ist fuer hermetische Tests injizierbar.

### Tests / Release-Integritaet
- 164 → **178 Kern-Regressionstests**, inklusive `.part`-Symlink-Overwrite, symlinktem Ausgabeordner, privatem Remote-Logo, Consent-Szenariovertrag, 6to4, TLS-IP-Pinning und echtem hermetischem `architecture=server`-Build.
- Korrektur zum 0.7.9-Testbericht: Der damalige Tracking-Builder-Test enthielt trotz `Q1 CLOSED` noch einen realen DNS-Pfad und konnte bei `out=None` ohne Assertion gruen bleiben. Der Erfolgspfad wird jetzt direkt mit injiziertem Resolver gebaut und zwingend asserted.
- Chromium-E2E bleibt Teil der CI. In der lokalen Build-Sandbox konnte `npm ci` wegen fehlendem Registry-/Netzzugriff nicht abgeschlossen werden; der Browserlauf ist deshalb lokal weiterhin `NOT_VERIFIED`.
- Hardening-Nachweise unter `docs/hardening-0.7.10/`.

## 0.7.9 — 15.09.2026

### Security
- Browser-Netzpolicy gegen IPv4-mapped IPv6 und weitere nicht-global routbare/special-use Netze gehärtet; WebSockets werden über `routeWebSocket()` geprüft, Service Worker im Consent-Audit für die Request-Interception blockiert.
- `start` und `wissen-update` sind wie die übrigen Workflow-Skills user-only (`disable-model-invocation: true`).
- Consent- und SiteOne-Rohoutputs werden auf POSIX restriktiver geschrieben/nachgehärtet.

### Correctness
- Consent-Audit lässt Tracking-Libraries laden und blockiert im sicheren Standardmodus nur Collection-Requests. Dadurch sabotiert das Audit nicht mehr GTM/gtag/Meta-Library-Ausführung.
- Browser-/CMP-Fehler (`status: unknown`) werden nicht mehr fachlich ausgewertet.
- Harte `gcs`-String-Decodierung entfernt; Google-Consent-Parameter werden als codierte Beobachtung behandelt.
- LocalStorage, SessionStorage und IndexedDB werden vor/nach Consent unterschieden und als Delta bewertet.
- Doctor findet Playwright auch im Claude-Plugin-Root.
- CSR-only ist kein pauschales `kritisch` mehr; Bewertung ist bot-/evidenzspezifisch.

### Tests / CI
- 137 → **164 Kern-Regressionstests**, inklusive mapped IPv6, Special-Use-Netzen, Consent-Pure-Logic, Storage, Doctor-Plugin-Root, vollständigem gemocktem Launch-Erfolgspfad und SiteOne-Scope.
- Neuer echter Chromium-Test `tests/browser_security.mjs`; CI installiert Chromium und prüft HTTP-/mapped-IPv6-/WebSocket-Blockaden.
- Hardening-Nachweise unter `docs/hardening-0.7.9/`.

## 0.7.8 — 15.09.2026

### Security
- **Browser-Netzwerkgrenze tatsächlich implementiert.** `lib/netpolicy.mjs` prüft Schema, Port, Zugangsdaten, IPv4- und IPv6-Bereiche, lokale Namen und löst Hostnamen auf. Zwei Schichten: Start-URL vor `page.goto()`, danach `context.route("**/*")` für Navigation, Subressourcen, XHR/fetch und Frames. **Korrektur in 0.7.9:** Der damalige Tracker-Blocker blockierte auch Loader wie `gtm.js`/`fbevents.js`; vollständige Messbarkeit war daher noch nicht gegeben.
- **Mutierende Skills sind user-only.** `seogeo`, `tracking-audit`, `launch`, `kundenbericht` und `setup` tragen `disable-model-invocation: true`.

### Fixed
- **Die 0.7.7-Sicherheitsdokumentation beschrieb eine `ctx.route()`-Sperre, die es im Code nicht gab.** Ein Patch-Anker aus der 0.7.5-Runde hatte nie gegriffen, das Ergebnis wurde nicht geprüft, die Maßnahme trotzdem als erledigt dokumentiert.
- SiteOne-Test war eine Attrappe: Er prüfte nur, dass ein Fehlertext *fehlt*, während der Prozess an der DNS-Auflösung starb. Jetzt wird belegt, an welcher Stelle der Abbruch erfolgt.

### Tests
- 94 → **137 Tests**. Neu: 23 für die Netzwerk-Policy (hermetisch, ohne Browser), 15 für Skill-Invocation, plus die reparierten SiteOne-Tests.
- Abschnitt I prüft den Quelltext von `consent_test.mjs` darauf, dass die Policy aufgerufen wird **und vor der ersten Navigation steht** — die Gegenmaßnahme gegen Patches, die nie greifen.
- `05-TEST-REPORT.md` wird aus dem echten Lauf erzeugt statt von Hand gepflegt.

### Documentation
- `docs/hardening-0.7.8/` mit sieben Berichten. `CLOSED` steht nur noch dort, wo Code, Test und grüner Lauf vorliegen; alles andere heißt `OPEN` oder `PARTIALLY_FIXED`.
- Offen und so benannt: Consent-Interpretation, Storage-Bewertung, Browser-Tests in CI, Launch-Integrationstest, Dateirechte, CSR-Regeln, Cowork, Playwright-Upstream.

## 0.7.7 — 15.09.2026

### Fixed
- `doctor.py` prüfte Versionen nicht: Python bekam ✅ unabhängig von der Version, der Hinweistext nannte „Node ≥ 18" gegen `engines: >=20`. Mindestversionen stehen jetzt zentral als `MIN_NODE`/`MIN_PYTHON`, die Parser sind testbar, Playwright ist in vier getrennte Prüfungen zerlegt, die SiteOne-Version wird ausgelesen. **Der in 0.7.5 gemeldete Fix für diesen Punkt war nie eingebaut worden.**

### Security
- `siteone.py`: `--allowed-domain-for-crawling=` akzeptierte jeden Wert. Jetzt Hostname-Syntax, kein Wildcard, keine Zugangsdaten, keine privaten Adressen; eine fremde Domain endet mit `REVIEW_REQUIRED` und muss über `--zusatz-domain` freigegeben werden. Argumentprüfung läuft vor jeder DNS-Auflösung.
- `consent_test.mjs`: Der fest verdrahtete macOS-User-Agent „Chrome/128.0" ist entfernt. Er passte weder zur Chromium-Version noch zum Betriebssystem und konnte Messergebnisse verfälschen.

### Documentation
- Unbelegte Aussagen zurückgezogen: PageSpeed-Kontingente („ohne Limit", „25.000/Tag"), SiteOne „Stand 2.6.1", Cowork „läuft auf deinem Rechner, nicht in der Cloud". Die Kurzform `/seogeo` wird nicht mehr als garantiert beschrieben.
- Sieben Hardening-Berichte erstmals tatsächlich im Paket (in 0.7.6 war das Verzeichnis leer). Die Berichte sind in 0.7.8 durch eine überarbeitete Fassung ersetzt worden, weil einer davon eine Maßnahme als erledigt beschrieb, die im Code fehlte.

### Tests
- 66 → **94 Tests**. Neu: Doctor-Versionslogik (15), Dokumentation gegen Code (7), Crawl-Scope (4), DNS-Fälle mit injiziertem Resolver (3).
- Damalige Zielsetzung: Testsuite hermetisch ohne Internet/DNS. **Korrektur in 0.7.9:** einzelne SiteOne-Pfade verwendeten weiterhin den echten Resolver; diese wurden erst in 0.7.9 vollständig aus den Success-Tests entfernt.
- Zwei Scheinbeweise aus 0.7.6 repariert: drei SiteOne-Tests bestanden, weil argparse vorher abbrach, nicht weil die Prüfung griff.

### CI
- `.github/workflows/test.yml`: Python 3.10, Node 20, `npm ci`, Syntaxprüfungen, Regressionstests, `npm audit` als Informationssignal. Keine Secrets, keine externen APIs.

## 0.7.6 — 15.09.2026

### Fixed
- `launch_check.py`: `add()` war in 0.7.5 beim Umbau auf den zentralen URL-Validator verlorengegangen. Jeder Lauf endete in `NameError: name 'add' is not defined`. Die Funktion ist wiederhergestellt, das Datenmodell (`level`/`id`/`titel`/`detail`) unverändert. Regressionstest gegen lokalen Fixture-Server.
- `render_report.mjs`: Die in 0.7.5 eingeführten Enum-Listen waren erfunden und widersprachen `references/audit-schema.md` sowie der Anzeigelogik derselben Datei. Das mitgelieferte `beispiel-seogeo.json` wurde dadurch abgelehnt. Die Listen stammen jetzt wörtlich aus dem Schema: `typ` seogeo/seo/geo/tracking/launch, `status` gut/mittel/kritisch/nicht_geprueft, `prioritaet` kritisch/hoch/mittel/niedrig.
- `siteone.py`: `--max-depth 0` (der Standardwert, Bedeutung „unbegrenzt") wurde von der neuen Wertebereichsprüfung abgelehnt.

### Security
- `siteone.py`: Der Kommandodruck gab `--http-auth=user:pass` im Klartext aus. Argumente mit `--http-auth`, `--password`, `--token` und `--key` werden jetzt als `[REDACTED]` ausgegeben.
- `fill_template.py`: Der Scan auf auffälliges Custom-HTML im Master läuft jetzt bei jedem Aufruf, auch bei `--list` — vorher erst beim Befüllen und damit zu spät.

### Tests
- Neue Testsuite `tests/run_tests.py`: 66 Tests über Launch-Check, URL-Guard, Kundenbericht, Tracking-Builder, GTM-Master und SiteOne-Wrapper. Standardbibliothek, kein Framework, lokaler Fixture-Server.

### Documentation
- Für 0.7.6 waren Hardening-Berichte angekündigt, aber **nie ausgeliefert** – das Verzeichnis war leer und überlebte das Packen nicht. Nachgeholt in 0.7.7.

## 0.7.5 und früher
Siehe die Auditberichte zu 0.7.2 bis 0.7.5.
