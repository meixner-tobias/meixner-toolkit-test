# Findings 0.7.10

| ID | Finding | Status | Evidenz/Fix | Regression |
|---|---|---|---|---|
| P1-J | Consent-Abbruch kann Summary crashen | CLOSED | vollständiger Szenariovertrag via `emptyScenario`; Summary zusätzlich defensiv | Pure-Logic-Vertrag + 178er Suite |
| P1-K | Report `.part`-Symlink kann fremde Datei überschreiben | CLOSED | exklusives `wx`, realer Parent-Check, fremde `.part`-Datei wird weder verfolgt noch gelöscht | echter POSIX-Symlink-Test |
| P1-B | Harte `gcs`-Heuristik noch in Skill/Referenz | CLOSED | alte Decodierung aus `SKILL.md` und `references/google.md` entfernt | Dokumentations-Regression |
| Q1 | Builder-Success-Test nicht hermetisch / stille Nicht-Assertion | CLOSED | Resolver in `Builder` injizierbar; Server-Build wird direkt und zwingend asserted | hermetischer vollständiger Build |
| P2-NET | 6to4/Special Transition | CLOSED konservativ | `2002::/16` blockiert; Translation/Transition-Präfixe bewusst konservativ | Node-Policy + Browser-E2E-Fall |
| P2-SGTM | `server_container_url` akzeptierte Shared Address Space | CLOSED | Prüfung auf tatsächliche globale Erreichbarkeit (`is_global`, mapped IPv4 berücksichtigt) | 100.64.0.1-Ablehnung + Server-Build |
| P2-LAUNCH | SSL-Socket umging zentrale URLGuard-DNS-Grenze | CLOSED | TLS-Verbindung auf unmittelbar verifizierte IP gepinnt; SNI bleibt Originalhost | hermetischer TLS-Ziel-Test |
| P2-REPORT-NET | `--remote-logo`/PDF als separater Browser-Netzpfad | CLOSED | Remote-Logo vor Einbettung geprüft; PDF-Context nutzt `installiereNetzPolicy` | privates Remote-Logo Regression + Syntax |
| P2-PERM | Toolkit-Home-Verzeichnisse mit Default-Rechten | CLOSED best-effort POSIX | neue Verzeichnisse `0700`, `config.json` `0600`; Windows bleibt ACL-Risiko | Code-/Gesamttest |
