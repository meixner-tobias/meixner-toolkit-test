# GTM Golden Masters

Hier werden **keine erfundenen GTM-Container** als „geprüft“ mitgeliefert.

Google unterstützt den Workflow Export -> JSON bearbeiten -> Import ausdrücklich. Ein Toolkit-Master erhält den Status `verified_by_gtm_import_roundtrip` aber erst nach diesem realen Ablauf:

1. Candidate-JSON erzeugen (Web-Generator oder einmal manuell sauber gebauter Server-/Stape-Container).
2. In Google Tag Manager in **einen neuen Workspace** importieren; Import-Vorschau auf unerwartete Änderungen prüfen.
3. Tag Assistant / Server Preview ausführen; keine Veröffentlichung nötig.
4. Den unveröffentlichten Workspace wieder als JSON exportieren.
5. Verifizieren:
   ```bash
   python3 ../scripts/gtm_master_verify.py candidate.json roundtrip.json \
     --type web --name "web-standard-v1" --out web-standard-v1.verified.json
   ```
   Für Server entsprechend `--type server`.
6. Erst ein erfolgreich erzeugtes `.verified.json` darf als Beleg für „GTM hat diese Struktur importiert und wieder exportiert“ verwendet werden.

Die Prüfung ignoriert nur umgebungsspezifische IDs/Fingerprints und vergleicht die semantischen Komponenten. Ein Manifest ist **kein Beweis dafür, dass Tracking fachlich korrekt feuert**; dafür zusätzlich Preview/Testprotokoll durchführen.

## Server/Stape

Ein realer Server-Master kann nicht seriös aus Dokumentation erfunden werden, weil Community-Templates und deren IDs/Parameter aus dem tatsächlich installierten Container stammen. Einmal in GTM sauber aufbauen (mindestens benötigte Clients/Tags/Consent/Custom Domain je Kundenprofil), exportieren und über obigen Roundtrip verifizieren. Danach kann `fill_template.py` die Konstanten deterministisch pro Kunde ersetzen.


## Mitgelieferte 0.7.11-Referenz

`production-reference/` enthaelt ein voll sanitisiertes Web-/Server-Paar aus einem real verwendeten Setup. `core/` enthaelt daraus abgeleitete neutrale Candidates; `patterns/` enthaelt Event-Entscheidungsmuster. Vor Nutzung immer `REFERENCE-POLICY.md` lesen und `../scripts/reference_guard.py` ausfuehren. Keines dieser Artefakte ist allein durch Auslieferung `VERIFIED`.
