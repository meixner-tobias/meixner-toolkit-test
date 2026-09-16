---
name: start
description: Einstieg in meixner-toolkit – fragt, was heute für welchen Kunden erledigt werden soll (SEO, GEO, Tracking-Audit, GTM/Tracking-Setup, Go-Live-Abnahme, Kundenbericht, einzeln oder kombiniert) und führt die passenden Module in sinnvoller Reihenfolge aus. Nutzen bei /start, "was machen wir heute", "neuer Auftrag", "Kunde X bearbeiten", "Paket für Kunde".
disable-model-invocation: true
---

# /start – Auftrag zusammenstellen und ausführen

Arbeitsweise (Fakten, Budgets, Rückfragen): `../setup/references/arbeitsweise.md`.

Die einzelnen Skills bleiben direkt aufrufbar. `/start` ist der Einstieg, wenn der Auftrag gemischt oder noch unklar ist.

## 1. Kontext laden
`config.json` und Kundenliste lesen (siehe Skill `setup`). Fehlt die Konfiguration: kurz `/setup`-Check anbieten, aber nicht erzwingen.

## 2. Eine Frage-Runde (AskUserQuestion, max. 4 Fragen)
1. **Kunde**: bekannte Kunden als Optionen (zuletzt bearbeitete zuerst) + „Neuer Kunde (Domain im Freitext)“.
2. **Module** (Mehrfachauswahl):
   - SEO (technisch, On-Page, Content, Local)
   - GEO (KI-Sichtbarkeit, Bots, Entität)
   - Tracking-Audit (GTM, GA4, Ads, Meta, Consent)
   - Tracking-Setup (Plan → GTM-Import-JSON, auch ohne vorheriges Audit)
   - Go-Live-Abnahme (`launch`)
   - Kundenbericht (gebrandet, aus vorhandenen/neuen Audits)
3. **Tiefe** (steuert zugleich das Recherche-Budget): Schnellcheck = `sparsam` · Vollaudit = `normal` · Gründlich (Neukunde, Recht, Migration) = `gruendlich` · Audit + Fixes/Setup = `normal`. Vorauswahl aus `config.json → standards.recherche_budget`.
4. **Freitext-Details**: „Was genau soll passieren? Besonderheiten, Seiten, Deadline?“ (Option „Keine“ anbieten).

Nicht jede Kombination einzeln auflisten – Module × Tiefe decken alle Varianten ab. Bei klarer Anfrage (z. B. „nur GTM für kunde.de einrichten“) direkt ohne Menü starten und die Annahme nennen.

## 3. Ablaufplan zeigen, dann ausführen

**Invocation-Grenze:** Die Modul-Skills sind bewusst `disable-model-invocation: true`. `/start` darf sie daher nicht als automatische Skill-Aufrufe umgehen. Nach dem expliziten Nutzerstart dieses Skills die jeweiligen `../<modul>/SKILL.md` als Workflow-Referenz lesen und die dort beschriebenen read-/script-Schritte innerhalb dieses user-initiierten Auftrags ausführen; vor jedem dort definierten eingreifenden Schritt weiterhin die geforderte Freigabe einholen.

Reihenfolge (nur gewählte Module):
1. `launch` (falls Website neu/umgezogen) – findet Grundfehler zuerst
2. `seogeo` mit Fokus: nur SEO → GEO-Teil überspringen; nur GEO → Abschnitt GEO + Bot-Zugang + Entität + Stichprobe; beides → komplett
3. `tracking-audit` (Audit) → danach `tracking-audit plan/build`, wenn Setup gewählt
4. `kundenbericht` am Ende über alle Ergebnisse des Tages

Plan als kurze Tabelle zeigen (Modul · Tiefe · Ergebnisdatei), dann ohne weitere Rückfrage starten. Gemeinsame Daten (Domain, Stack, CMS, IDs) nur einmal erheben und an alle Module weitergeben. Fixes/Setup-Schritte weiterhin nur nach Freigabe je Modul.

## 4. Abschluss
Kurze Übersicht: erledigt / offen / manuelle Schritte je Modul, Dateien, Eintrag in `kunden/<slug>.json → audits`. Nächsten sinnvollen Schritt vorschlagen (z. B. „Recheck in 4 Wochen“).
