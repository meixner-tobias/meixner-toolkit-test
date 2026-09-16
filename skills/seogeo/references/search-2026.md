# Google Search — aktuelle SEO-Referenz 2026

Stand: 16.09.2026. Zeitkritische Punkte vor Kundenreport gegen Google Search Central erneut pruefen.

## Title / Snippets / Headings

- Google nennt **keine feste Zeichenobergrenze** fuer `<title>` oder Meta Description. Titellinks/Snippets werden je nach Geraet und Anfrage gekuerzt. Deshalb keine „60 Zeichen = Rankingregel“-Findings; Laenge nur als Darstellungsheuristik verwenden.
  Quellen: https://developers.google.com/search/docs/appearance/title-link · https://developers.google.com/search/docs/appearance/snippet
- Google nutzt u. a. `<title>`, sichtbaren Haupttitel und Heading-Elemente fuer Titellinks. Entscheidend ist ein **klar erkennbarer Haupttitel**; mehrere gleich gewichtete Hauptueberschriften koennen verwirrend sein. Das Toolkit behandelt „mehr als eine H1“ deshalb nicht automatisch als Fehler.
  Quelle: https://developers.google.com/search/docs/appearance/title-link

## Core Web Vitals

- Gute Felddaten: LCP <= 2,5 s, INP < 200 ms, CLS < 0,1; fuer Search/UX Felddaten am 75. Perzentil priorisieren.
  Quelle: https://developers.google.com/search/docs/appearance/core-web-vitals

## Structured Data / Search Features

- FAQ Rich Results werden seit 07.05.2026 nicht mehr in Google Search angezeigt; die FAQ-Dokumentation wurde im Juni 2026 entfernt. FAQ-Inhalte koennen fuer Nutzer weiterhin sinnvoll sein, sind aber kein Rich-Result-Fix.
  Quelle: https://developers.google.com/search/updates
- Search-Features koennen regional unterschiedlich verfuegbar sein. Seit 08.09.2026 dokumentiert Google regionale Unterschiede ausdruecklich; vor einem Finding zu fehlenden/erwarteten Suchfeatures den Zielmarkt pruefen.
  Quelle: https://developers.google.com/search/updates

## Site moves / Domain variants

- Bei Domainmigrationen alle Varianten (u. a. www/non-www/Subdomains, soweit betroffen) sauber migrieren; Google hat die Change-of-Address-Anleitung im Juni 2026 entsprechend praezisiert.
  Quelle: https://developers.google.com/search/updates

## Spam / Site Reputation Abuse

- Drittinhalte, die primaer die Reputation einer etablierten Host-Site fuer Rankings ausnutzen, koennen unter Googles Site-Reputation-Abuse-Policy fallen. Seit 30.08.2026 unterscheidet sich die Wirkung entsprechender manueller Massnahmen fuer Suchende im EWR vs. ausserhalb des EWR; die Policy selbst bleibt bestehen. Nie allein aus Trafficveraenderungen auf einen Policy-Verstoss schliessen – Search-Console-Manuelle-Massnahmen und konkrete Publishing-Beziehung pruefen.
  Quelle: https://developers.google.com/search/blog/2026/08/update-site-reputation-policy

## Heuristiken im Toolkit

- „Position 4–20“, „Klicktiefe <=3“ oder ungefaehre Title-Laengen sind **Arbeitsheuristiken fuer Priorisierung**, keine Google-Grenzwerte oder Rankingfaktoren.
- Findings muessen Messung + Auswirkung begruenden; eine Heuristik allein ist kein Finding.
