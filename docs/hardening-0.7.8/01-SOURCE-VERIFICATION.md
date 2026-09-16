# Quellenprüfung 0.7.8

In dieser Phase wurden **keine neuen externen Quellen geprüft.** Der Aufwand ging vollständig in P1-A und P2-A.

Übernommen aus 0.7.7, dort mit Datum belegt:

| Claim | Quelle | Geprüft | Ergebnis |
|---|---|---|---|
| Plugin-Skills heißen `/plugin:skill` | code.claude.com/docs/en/skills | 14.09.2026 | bestätigt |
| `disable-model-invocation` für Skills mit Seiteneffekten empfohlen | code.claude.com/docs/en/skills | 14.09.2026 | bestätigt |
| Berechtigungen setzt Claude Code durch, nicht das Modell | code.claude.com/docs/en/permissions | 14.09.2026 | bestätigt |
| „Require additional consent" prüft im Moment der Auslösung | support.google.com/tagmanager/answer/10718549 | 14.09.2026 | bestätigt |
| Consent Mode v2 verlangt `ad_user_data`/`ad_personalization` | developers.google.com/tag-platform/security/guides/consent | 14.09.2026 | bestätigt |

**Nicht geprüft, unverändert offen:** `gcs`/`gcd` als stabile öffentliche API, Basic vs. Advanced Consent Mode im Detail, Meta-CAPI-Deduplizierung, `llms.txt`, Applebot und Applebot-Extended, Google-Extended, FAQ-Rich-Results, CSR-Rendering je Bot, SiteOne-Releases, aktueller Playwright-Upstream, Cowork-Ausführungsort.

Das ist seit sechs Runden dieselbe Liste.
