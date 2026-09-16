# Baseline 0.7.9 → 0.7.10

- Ausgangsdatei: `meixner-toolkit-0.7.9.zip`
- SHA-256 Ausgangsdatei: `47e22150d2ae48e022aed0729f86e40a7a2dd15aa1b1d4a8165b844733ed9091`
- Baseline laut unabhängiger Gegenprüfung: 164/164 bestehende Regressionstests grün.
- Zusätzlich reproduziert: früher Consent-Abbruch konnte wegen fehlendem `cookies_after` im Terminal-Summary crashen; `render_report.mjs` folgte einem vorbereiteten `.part`-Symlink; Skill/Google-Referenz enthielten trotz korrigierter Runtime noch die alte harte `gcs≠G100`-Regel; der Server-Builder-Success-Test verwendete echtes DNS und konnte bei `out=None` ohne Assertion grün bleiben.
- Weitere Härtung: 6to4/Transition-Pfad, sGTM-Global-Reachability, Launch-SSL-Socket, Remote-Logo/PDF-Netzpfad und POSIX-Rechte bei `doctor --init`.
