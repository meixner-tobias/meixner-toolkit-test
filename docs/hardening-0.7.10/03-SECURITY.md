# Sicherheitsbericht 0.7.10

## Report-Dateien
HTML und PDF werden nicht mehr über ein frei überschreibbares `<ziel>.part` geschrieben. Die temporäre Datei wird exklusiv mit `wx` erzeugt, der reale Parent-Pfad muss unter einer erlaubten Wurzel liegen, vorhandene Symlinks werden nicht überschrieben und fremde `.part`-Pfade bei Fehlern nicht gelöscht. Ein reproduzierbarer Symlink-Overwrite aus 0.7.9 ist damit durch Regression abgedeckt.

## Netzwerk
Die bestehende Browserpolicy bleibt für HTTP(S), WebSockets und Service-Worker-Interception aktiv. 6to4 (`2002::/16`) wird für den Auditbrowser konservativ blockiert. `server_container_url` verlangt global erreichbare IPs. Launch-SSL verbindet direkt zu einer zuvor von `urlguard.py` freigegebenen IP, um den früheren erneuten DNS-Lookup beim TLS-Socket zu vermeiden. Remote-Logos und PDF-Rendering laufen durch die Public-Network-Policy.

## Consent
Frühe Abbrüche besitzen jetzt immer einen vollständigen Ergebnisvertrag. `status=unknown` bleibt nicht auswertbar. `gcs`/`gcd` werden in Runtime **und** Skill-Wissensbasis konsistent als codierte Beobachtung behandelt; keine feste String-Decodierung wird als rechtliche Wahrheit ausgegeben.

## Dateien und Rechte
Toolkit-Verzeichnisse werden auf POSIX best-effort `0700`, neue `config.json` `0600`. Kundenbericht/Consent/SiteOne-Ausgaben behalten die bestehenden restriktiven Mechanismen. Windows-ACLs werden dadurch nicht garantiert.
