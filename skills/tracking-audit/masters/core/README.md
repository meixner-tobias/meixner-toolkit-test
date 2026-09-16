# Neutral Core Candidates

`web-core.candidate.json` und `server-core.candidate.json` wurden aus den sanitisierten Production References abgeleitet.

Sie enthalten nur wiederverwendbare Infrastruktur und gut lesbare Platzhalter. Sie sind absichtlich mit `candidate_reference_only` markiert und **nicht als GTM-roundtrip-verifiziert** registriert. Fuer einen echten Kunden erst Audit/Plan/Gate, dann Werte einsetzen, in neuen Workspace importieren, Preview testen, re-exportieren und mit `gtm_master_verify.py` pruefen.

Der Server-Core enthaelt das zum Referenzzeitpunkt installierte Stape Meta-CAPI-Custom-Template als Struktur-/Bootstrap-Hilfe, aber keine aktiven Meta-Conversion-Tags.
