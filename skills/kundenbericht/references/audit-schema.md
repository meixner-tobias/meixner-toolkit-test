# audit.json – gemeinsames Ergebnisformat aller Audits

Alle Audit-Skills (`seogeo`, `tracking-audit`, `launch`) schreiben neben dem Markdown-Report eine JSON-Datei in diesem Format. Texte darin sind **kundenverständlich** formuliert (kein Fachjargon ohne Erklärung); technische Details bleiben im Markdown.

```json
{
  "typ": "seogeo | seo | geo | tracking | launch",
  "kunde": "Beispiel GmbH",
  "ansprechpartner": "Frau Muster (optional, für die Anrede)",
  "anschreiben": "optional: 2–3 eigene Einleitungssätze statt des Standardtexts",
  "domain": "https://www.beispiel.de",
  "datum": "2026-09-11",
  "umfang": "14 Seiten geprüft, Datenquellen: Crawl, PageSpeed, Websuche",
  "zusammenfassung": "2–4 Sätze in Alltagssprache.",
  "scorecard": [
    {"bereich": "Technik", "status": "gut | mittel | kritisch | nicht_geprueft", "anzahl": 3}
  ],
  "findings": [
    {
      "id": "TECH-01",
      "bereich": "Technik (einer der acht Bereiche unten, gleicher Name wie in scorecard)",
      "prioritaet": "kritisch | hoch | mittel | niedrig",
      "titel": "Der Umzug von der alten Domain ist nicht abgeschlossen",
      "problem": "Was los ist – ein Satz, verständlich, ohne Lösung.",
      "auswirkung": "Was es den Kunden kostet (Sichtbarkeit, Anfragen, Messung, Recht) – ein Satz.",
      "massnahme": "Was zu tun ist – erscheint NUR mit --voll, nie im Standardbericht.",
      "aufwand": "S | M | L",
      "nachweis": "optional: ein Satz Beleg (Messwert, Werkzeug, Datum) – erscheint im Bericht aufklappbar als „Wie ich das geprüft habe“"
    }
  ],
  "positiv": ["Was bereits gut ist"],
  "naechste_schritte": ["Konkrete Empfehlung 1", "…"],
  "nicht_geprueft": ["optional"]
}
```

## Bereiche – feste Liste

`bereich` ist der Name, den der **Kunde** liest. Er wird nicht je Audit neu erfunden: Jedes Finding gehört über sein ID-Präfix zu genau einem dieser acht Bereiche. Der Bericht gruppiert in dieser Reihenfolge, und der Recheck kann Läufe dadurch vergleichen.

| Reihenfolge | `bereich` | ID-Präfixe | Frage, die der Bereich beantwortet |
|---|---|---|---|
| 1 | Technik | `TECH-`, `SCHEMA-`, `GOLIVE-` | Kommt Google überhaupt sauber an die Seite? |
| 2 | Ladezeit | `PERF-` | Wie schnell ist die Seite für echte Besucher? |
| 3 | Inhalte | `ONPAGE-`, `CONT-` | Steht auf den Seiten, wonach die Kundschaft sucht? |
| 4 | KI-Suche | `GEO-` | Wird das Unternehmen in ChatGPT, Perplexity und KI-Übersichten genannt? |
| 5 | Google-Profil & Einträge | `LOCAL-` | Stimmen Unternehmensprofil, Adresse und Verzeichnisse? |
| 6 | Messung | `GTM-`, `GA4-`, `DATA-`, `SGTM-` | Wird richtig gezählt, was zählt? |
| 7 | Werbekonten | `ADS-`, `META-` | Kommen Conversions vollständig in Ads und Meta an? |
| 8 | Recht & Einwilligung | `TRUST-`, `LEGAL-`, `CONSENT-` | Pflichtangaben vorhanden, nichts ohne Einwilligung? |

Regeln dazu:
- Kein eigener Bereichsname, auch nicht „ähnlich“. Passt ein Finding in keinen Bereich, gehört es meist unter Technik – oder das Finding ist zu unscharf formuliert.
- `scorecard` enthält dieselben Namen in derselben Reihenfolge, auch mit `anzahl: 0` (dann `status: "gut"`), wenn der Bereich geprüft wurde und sauber war.
- Nicht geprüfte Bereiche mit `status: "nicht_geprueft"` aufnehmen, nicht weglassen – sonst sieht es aus, als wäre dort alles in Ordnung.
- `render_report.mjs` meldet abweichende Namen beim Rendern als Hinweis auf der Konsole.

Regeln
- `findings` nach Priorität sortiert. Im Bericht erscheinen **alle** Punkte, gruppiert nach `bereich` (Reihenfolge der `scorecard`), je Punkt zum Aufklappen. Nur `--teaser` zeigt eine Auswahl.
- `titel` ist die zugeklappt sichtbare Zeile: vollständige Aussage, rund 60 Zeichen, kein Fachbegriff.
- `aufwand` wird dem Kunden als „gering / mittel / größer“ angezeigt – realistisch setzen.
- `bereich` immer aus der festen Liste oben; jeder `bereich` der Findings steht auch in der `scorecard`.
- `problem` und `auswirkung` werden hintereinander als Absatz gedruckt → jeweils mit Punkt abschließen.
- Schreibregeln: Skill `kundenbericht` → „Schreibregeln“.
- Nur Fakten aus dem Audit – keine neuen Behauptungen im Bericht.
- Keine Preise im JSON; Angebot kommt aus `config.json → angebot`.
