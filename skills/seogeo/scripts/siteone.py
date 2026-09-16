#!/usr/bin/env python3
"""Startet SiteOne Crawler (lokale CLI, MIT) und verdichtet dessen JSON zu einem kompakten Auszug.

  python3 siteone.py https://www.kunde.de --out-dir ./crawl [--browser] [--max-depth 3] [--bin /pfad/siteone-crawler]
  python3 siteone.py --from-json crawl/roh.json            # vorhandene JSON nur auswerten
  python3 siteone.py --watch                               # wartet, bis die Desktop-App eine neue JSON schreibt
  python3 siteone.py                                       # nimmt automatisch die neueste JSON der Desktop-App
                                                           # (Ordner "SiteOne-Crawler" auf dem Schreibtisch oder $SITEONE_OUTPUT_DIR)

Warum verdichten: Die Roh-JSON eines Crawls ist schnell mehrere hundert KB. Dieses Skript schreibt
`crawl-summary.json` (maschinenlesbar) und gibt einen kurzen Textauszug aus, der direkt im Audit verwendbar ist.
Nur Standardbibliothek. Installation der CLI: brew install janreges/tap/siteone-crawler (siehe references/siteone.md).
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

# Windows-Konsolen laufen oft auf cp1252; Umlaute und Sonderzeichen aus Seitentiteln
# wuerfen dort sonst einen UnicodeEncodeError mitten im Lauf.
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# Zentraler Validator aus lib/urlguard.py (Abschnitt 4). Ein Baustein fuer alle Skripte.
import importlib.util as _ilu
_guard_pfad = None
for _basis in (os.environ.get("CLAUDE_PLUGIN_ROOT"), str(Path(__file__).resolve().parents[3])):
    if _basis and (Path(_basis) / "lib" / "urlguard.py").exists():
        _guard_pfad = Path(_basis) / "lib" / "urlguard.py"
        break
if _guard_pfad is None:
    sys.exit("ABBRUCH: lib/urlguard.py nicht gefunden. Plugin unvollstaendig installiert?")
_spec = _ilu.spec_from_file_location("urlguard", _guard_pfad)
guard = _ilu.module_from_spec(_spec); _spec.loader.exec_module(guard)
from pathlib import Path

SEV = {"CRITICAL": 0, "WARNING": 1, "NOTICE": 2, "OK": 3, "INFO": 4}



def _chmod_private(path):
    """Best effort: sensible Auditdateien auf POSIX auf 0600 setzen.

    Unter Windows sind POSIX-Modi keine ACL-Garantie; dort wird bewusst nichts
    als "revisionssicher" oder "nur Benutzer" versprochen.
    """
    if os.name == "nt":
        return
    try:
        Path(path).chmod(0o600)
    except OSError:
        pass


def pruefe_crawl_domain(host, ziel, freigegeben, guard_fn=guard.pruefe):
    host = str(host or "").strip().lower()
    ziel = str(ziel or "").strip().lower().removeprefix("www.")
    if not host or "*" in host or "?" in host:
        raise ValueError("Wildcard")
    if "@" in host or ":" in host:
        raise ValueError("Zugangsdaten oder Ports")
    if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", host):
        raise ValueError("kein gueltiger Hostname")
    erlaubt = {str(d).strip().lower() for d in freigegeben or []}
    if host not in erlaubt and host != ziel and not host.endswith("." + ziel):
        raise PermissionError("REVIEW_REQUIRED")
    guard_fn("https://" + host)
    return host

def rows(data, table):
    t = (data.get("tables") or {}).get(table) or {}
    return t.get("rows") or []


ALLOWED_CRAWLER_ARGS = ("--user-agent=", "--include-regex=", "--ignore-regex=", "--accept-encoding=",
                        "--max-queue-length=", "--allowed-domain-for-crawling=", "--single-page",
                        "--disable-javascript", "--memory-limit=", "--http-auth=")


GRENZEN = {"max_depth": (0, 10),          # 0 = unbegrenzt (Standardwert des Crawlers)
           "workers": (1, 16), "rps": (1, 50),
           "timeout": (1, 120), "max_rows": (1, 500), "max_urls": (1, 20000)}

GEHEIM_ARG = re.compile(r"(--(?:http-auth|password|token|key)=)[^\s]+")

def redigiere_cmd(cmd):
    return [GEHEIM_ARG.sub(r"\1[REDACTED]", str(c)) for c in cmd]


def pruefe_bereich(name, wert):
    lo, hi = GRENZEN[name]
    if not isinstance(wert, int) or not (lo <= wert <= hi):
        sys.exit("ABBRUCH: --%s muss zwischen %d und %d liegen (erhalten: %r)"
                 % (name.replace("_", "-"), lo, hi, wert))
    return wert


def run_crawler(url, out_dir, binary, browser, max_depth, workers, rps, timeout, extra):
    out_dir = Path(out_dir)
    neu = not out_dir.exists()
    out_dir.mkdir(parents=True, exist_ok=True)
    if neu and os.name != "nt":
        try: out_dir.chmod(0o700)
        except OSError: pass
    raw = out_dir / "siteone-raw.json"
    # Eine Datei aus einem frueheren Lauf darf niemals als Ergebnis dieses Laufs gelten.
    stale_before = raw.stat().st_mtime if raw.exists() else None
    html = out_dir / "siteone-report.html"
    cmd = [binary, "--url=" + url, "--output=json", "--output-json-file=" + str(raw),
           "--output-html-report=" + str(html), "--extra-columns=Title,Description,DOM",
           "--workers=%d" % workers, "--max-reqs-per-sec=%d" % rps, "--timeout=%d" % timeout,
           "--hide-progress-bar", "--no-color"]
    if max_depth:
        cmd.append("--max-depth=%d" % max_depth)
    if browser:
        cmd.append("--browser")
    cmd += extra
    sichtbar = redigiere_cmd(cmd)
    print("→ " + " ".join(sichtbar), file=sys.stderr)
    started = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=max(60, timeout * 60), encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        sys.exit("ABBRUCH: Crawl-Prozess nach %d s abgebrochen." % max(60, timeout * 60))
    # stdout/stderr begrenzen - ein Crawler kann Megabytes produzieren
    r.stdout = (r.stdout or "")[-20000:]
    r.stderr = (r.stderr or "")[-20000:]
    if r.returncode != 0:
        print(r.stdout[-3000:] or "", file=sys.stderr)
        print(r.stderr[-3000:] or "", file=sys.stderr)
        if stale_before is not None:
            print("Hinweis: %s stammt aus einem frueheren Lauf und wird NICHT verwendet." % raw, file=sys.stderr)
        sys.exit("ABBRUCH: SiteOne Crawler endete mit Exit %s." % r.returncode)
    if not raw.exists():
        sys.exit("ABBRUCH: SiteOne Crawler lieferte keine JSON-Datei (Exit %s)." % r.returncode)
    if stale_before is not None and raw.stat().st_mtime <= stale_before:
        sys.exit("ABBRUCH: %s wurde in diesem Lauf nicht neu geschrieben - die Datei stammt "
                 "aus einem frueheren Crawl. Anderes --out-dir waehlen oder Datei entfernen." % raw)
    _chmod_private(raw)
    if html.exists():
        _chmod_private(html)
    print("Crawl fertig in %.1fs (Exit %s), Report: %s" % (time.time() - started, r.returncode, html), file=sys.stderr)
    return raw


def digest(data, max_rows):
    crawler = data.get("crawler") or {}
    stats = data.get("stats") or {}
    qs = data.get("qualityScores") or {}
    out = {
        "crawler": {"name": crawler.get("name"), "version": crawler.get("version"), "executedAt": crawler.get("executedAt"),
                    "userAgent": crawler.get("finalUserAgent")},
        "umfang": {"urls": stats.get("totalUrls"), "statuscodes": stats.get("countByStatus"),
                   "antwortzeit_avg_s": stats.get("totalRequestsTimesAvg"), "antwortzeit_max_s": stats.get("totalRequestsTimesMax"),
                   "groesse": stats.get("totalSizeFormatted")},
        "scores": {"gesamt": (qs.get("overall") or {}).get("score") if isinstance(qs.get("overall"), dict) else qs.get("overall"),
                   "kategorien": [{"name": c.get("name"), "score": c.get("score"),
                                   "abzuege": [d.get("reason") for d in (c.get("deductions") or [])]}
                                  for c in (qs.get("categories") or [])]},
        "befunde": sorted([{"status": i.get("status"), "text": i.get("text"), "code": i.get("aplCode")}
                           for i in ((data.get("summary") or {}).get("items") or [])],
                          key=lambda x: (SEV.get(x["status"], 9), x["text"]))[:max_rows * 2],
    }

    # Seiten mit SEO-Auffälligkeiten
    seo, dupes = [], {}
    for r in rows(data, "seo"):
        title, desc, h1 = (r.get("title") or "").strip(), (r.get("description") or "").strip(), (r.get("h1") or "").strip()
        probleme = []
        if not title: probleme.append("kein Title")
        elif len(title) > 70: probleme.append("Title %d Zeichen" % len(title))
        if not desc: probleme.append("keine Description")
        elif len(desc) > 170: probleme.append("Description %d Zeichen" % len(desc))
        if not h1: probleme.append("keine H1")
        if (r.get("robotsIndex") or "").lower().startswith("noindex") or "noindex" in (r.get("indexing") or "").lower():
            probleme.append("noindex")
        if str(r.get("deniedByRobotsTxt")).lower() == "true": probleme.append("per robots.txt gesperrt")
        dupes.setdefault(("title", title), []).append(r.get("urlPathAndQuery"))
        dupes.setdefault(("desc", desc), []).append(r.get("urlPathAndQuery"))
        if probleme:
            seo.append({"url": r.get("urlPathAndQuery"), "probleme": probleme, "title": title[:90], "h1": h1[:70]})
    out["seo_auffaellig"] = seo[:max_rows]
    out["seo_geprueft"] = len(rows(data, "seo"))
    out["doppelt"] = [{"art": k[0], "wert": (k[1][:60] or "(leer)"), "urls": v[:6]}
                      for k, v in dupes.items() if k[1] and len(v) > 1][:max_rows]

    # Überschriftenstruktur: nur Seiten mit gemeldeten Fehlern
    out["heading_fehler"] = [{"url": r.get("urlPathAndQuery"), "fehler": r.get("headingsErrorsCount"),
                              "struktur": (r.get("headings") or "")[:120]}
                             for r in rows(data, "seo-headings") if str(r.get("headingsErrorsCount") or "0") not in ("0", "")][:max_rows]

    out["fehlerseiten"] = [{"url": r.get("url"), "status": r.get("statusCode"), "verlinkt_von": r.get("sourceUqId")}
                           for r in rows(data, "404")][:max_rows]
    out["weiterleitungen"] = [{k: v for k, v in r.items() if k in ("url", "statusCode", "redirectUrl", "targetUrl", "sourceUqId")}
                              for r in rows(data, "redirects")][:max_rows]
    out["sicherheit"] = [{"header": r.get("header"), "kritisch": r.get("critical"), "warnung": r.get("warning"),
                          "hinweis": (r.get("recommendation") or "")[:160]}
                         for r in rows(data, "security") if str(r.get("critical") or "0") != "0" or str(r.get("warning") or "0") != "0"][:max_rows]
    out["barrierefreiheit"] = [{"pruefung": r.get("analysisName"), "kritisch": r.get("critical"), "warnung": r.get("warning")}
                               for r in rows(data, "accessibility") if str(r.get("critical") or "0") != "0" or str(r.get("warning") or "0") != "0"][:max_rows]
    out["best_practices"] = [{"pruefung": r.get("analysisName"), "kritisch": r.get("critical"), "warnung": r.get("warning")}
                             for r in rows(data, "best-practices") if str(r.get("critical") or "0") != "0" or str(r.get("warning") or "0") != "0"][:max_rows]
    out["langsamste_urls"] = [{"url": r.get("url"), "zeit_s": r.get("requestTime")} for r in rows(data, "slowest-urls")][:10]
    out["zertifikat"] = {r.get("info"): r.get("value") for r in rows(data, "certificate-info")}
    out["open_graph_fehlt"] = [r.get("urlPathAndQuery") for r in rows(data, "open-graph")
                               if not (r.get("ogTitle") or "").strip() or not (r.get("ogImage") or "").strip()][:max_rows]
    # Gesamtzahlen neben den gekuerzten Listen, damit ein Auszug nicht als Gesamtbild gilt.
    out["_gesamtzahlen"] = {
        "befunde": len(rows(data, "analysis-results")),
        "fehlerseiten": len([r for r in rows(data, "404") if r]),
        "weiterleitungen": len(rows(data, "redirects")),
        "seo_geprueft": len(rows(data, "seo")),
    }
    out["_hinweis"] = ("Listen sind auf --max-rows gekuerzt. Fuer Gesamtzahlen _gesamtzahlen "
                       "verwenden, nie die Laenge der gekuerzten Liste.")
    if data.get("ciGate"):
        out["ci_gate"] = data["ciGate"]
    return out


GUI_DIRS = ["~/Desktop/SiteOne-Crawler", "~/Schreibtisch/SiteOne-Crawler", "~/SiteOne-Crawler",
            "~/Downloads/SiteOne-Crawler"]


def _gui_candidates():
    dirs = [os.environ["SITEONE_OUTPUT_DIR"]] if os.environ.get("SITEONE_OUTPUT_DIR") else GUI_DIRS
    out = []
    for d in dirs:
        base = Path(os.path.expanduser(d))
        if base.is_dir():
            out += [p for p in base.rglob("*.json") if p.stat().st_size > 2000]
    return out


def newest_gui_json():
    """Neueste JSON-Datei aus der Desktop-App (Ordner 'SiteOne-Crawler') bzw. $SITEONE_OUTPUT_DIR."""
    cands = _gui_candidates()
    if not cands:
        return None
    newest = max(cands, key=lambda p: p.stat().st_mtime)
    print("Neueste JSON aus der GUI-App: %s (%s)" % (newest, time.strftime("%d.%m.%Y %H:%M", time.localtime(newest.stat().st_mtime))), file=sys.stderr)
    return newest


def wait_for_new_json(timeout_s):
    """Wartet, bis die Desktop-App eine neue JSON schreibt (z. B. während Tobias den Crawl klickt)."""
    before = {p: p.stat().st_mtime for p in _gui_candidates()}
    print("Warte auf einen neuen JSON-Export der Desktop-App (max. %d Minuten) …" % (timeout_s // 60), file=sys.stderr)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for p in _gui_candidates():
            if p not in before or p.stat().st_mtime > before.get(p, 0) + 1:
                time.sleep(2)  # Schreibvorgang abwarten
                print("Neue Datei gefunden: %s" % p, file=sys.stderr)
                return p
        time.sleep(3)
    sys.exit("Kein neuer Export innerhalb der Wartezeit gefunden.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--from-json", help="vorhandene SiteOne-JSON auswerten statt neu zu crawlen")
    ap.add_argument("--out-dir", default="crawl")
    ap.add_argument("--bin", default=os.environ.get("SITEONE_BIN", "siteone-crawler"))
    ap.add_argument("--browser", action="store_true", help="Chromium-Rendering (nötig bei JS-/SPA-Seiten, langsamer)")
    ap.add_argument("--max-depth", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2, help="gleichzeitige Anfragen (höflich bleiben)")
    ap.add_argument("--rps", type=int, default=5, help="max. Requests pro Sekunde")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--max-rows", type=int, default=15, help="max. Zeilen je Liste im Auszug")
    ap.add_argument("--watch", action="store_true", help="auf einen neuen JSON-Export der Desktop-App warten und ihn dann auswerten")
    ap.add_argument("--watch-timeout", type=int, default=1800, help="Wartezeit in Sekunden (Standard 30 Minuten)")
    ap.add_argument("--crawler-arg", action="append", default=[], help="zusätzliches CLI-Argument für den Crawler")
    ap.add_argument("--out", help="Zieldatei der Auswertung (Standard: <out-dir>/crawl-summary.json)")
    ap.add_argument("--schreiben", action="store_true", help="auch bei --from-json/--watch schreiben")
    ap.add_argument("--zusatz-domain", action="append", default=[],
                    help="zusaetzliche Domain ausdruecklich fuer den Crawl freigeben")
    a = ap.parse_args()

    if a.watch:
        raw = wait_for_new_json(a.watch_timeout)
    elif a.from_json or (not a.url and not a.from_json):
        raw = Path(a.from_json) if a.from_json else newest_gui_json()
        if not raw or not Path(raw).exists():
            sys.exit("Keine JSON gefunden. URL angeben, --from-json setzen oder in der GUI-App einen JSON-Report exportieren.")
    else:
        if not a.url:
            sys.exit("URL fehlt (oder --from-json angeben).")
        binary = shutil.which(a.bin) or a.bin
        if not shutil.which(binary):
            sys.exit("SiteOne Crawler nicht gefunden. Installation: brew install janreges/tap/siteone-crawler "
                     "(oder Binary von github.com/janreges/siteone-crawler/releases, Pfad mit --bin/$SITEONE_BIN).")
        # Reine Wertebereichsfehler zuerst pruefen: diese Tests benoetigen kein DNS.
        for feld in ("max_depth", "workers", "rps", "timeout"):
            pruefe_bereich(feld, getattr(a, feld))

        # Zusaetzliche Crawl-Domains sind eine Scope-Erweiterung, kein Formatdetail.
        ziel = (a.url or "").split("//")[-1].split("/")[0].lower().removeprefix("www.")
        for x in a.crawler_arg:
            if x.startswith("--allowed-domain-for-crawling="):
                host = x.split("=", 1)[1].strip().lower()
                try:
                    pruefe_crawl_domain(host, ziel, a.zusatz_domain)
                except ValueError as e:
                    sys.exit("ABBRUCH: Crawl-Domain %r abgelehnt - %s." % (host, e))
                except PermissionError:
                    sys.exit("REVIEW_REQUIRED: %s gehoert nicht zu %s. Eine fremde Domain "
                             "mitzucrawlen ist eine bewusste Entscheidung - mit "
                             "--zusatz-domain %s ausdruecklich freigeben." % (host, ziel, host))
                except guard.Blocked as e:
                    sys.exit("ABBRUCH: Zusaetzliche Crawl-Domain abgelehnt - %s" % e)
            if x.startswith("--http-auth="):
                if ":" not in x.split("=", 1)[1]:
                    sys.exit("ABBRUCH: --http-auth erwartet benutzer:passwort.")
        try:
            guard.pruefe(a.url)
        except guard.Blocked as e:
            sys.exit("ABBRUCH: Ziel-URL abgelehnt - %s" % e)
        bad = [x for x in a.crawler_arg if not x.startswith(ALLOWED_CRAWLER_ARGS)]
        if bad:
            sys.exit("ABBRUCH: --crawler-arg nicht erlaubt: %s\nErlaubt sind: %s"
                     % (bad, ", ".join(ALLOWED_CRAWLER_ARGS)))
        raw = run_crawler(a.url, a.out_dir, binary, a.browser, a.max_depth, a.workers, a.rps, a.timeout, a.crawler_arg)

    data = json.loads(Path(raw).read_text(encoding="utf-8"))
    # Gehoert die JSON ueberhaupt zum Auftrag? Bei --from-json/--watch/GUI-Import ist das offen.
    crawled = ((data.get("crawler") or {}).get("initialUrl")
               or (data.get("options") or {}).get("url") or (data.get("stats") or {}).get("initialUrl") or "")
    if a.url and crawled:
        want = a.url.split("//")[-1].split("/")[0].lower().removeprefix("www.")
        got = str(crawled).split("//")[-1].split("/")[0].lower().removeprefix("www.")
        if want and got and want != got:
            sys.exit("ABBRUCH: Die JSON gehoert zu %s, geprueft werden soll aber %s." % (got, want))
    if not a.url and crawled:
        print("Achtung: Herkunft der JSON ist %s - bitte gegen den Auftrag pruefen." % crawled, file=sys.stderr)
    alter_h = (time.time() - Path(raw).stat().st_mtime) / 3600
    if alter_h > 24:
        print("Achtung: Die JSON ist %.0f Stunden alt." % alter_h, file=sys.stderr)
    d = digest(data, a.max_rows)
    # --from-json/--watch sind Lesevorgaenge. Ohne ausdrueckliche Ausgabeoption wird nichts
    # geschrieben, sonst ueberschreibt ein Lesevorgang die Auswertung eines anderen Laufs.
    schreibt = bool(a.out) or a.schreiben or not (a.from_json or a.watch)
    if not schreibt:
        print("(read-only: keine Datei geschrieben. Mit --out <datei> oder --schreiben erzwingen)", file=sys.stderr)
        out = None
    else:
        out = Path(a.out) if a.out else Path(a.out_dir) / "crawl-summary.json"
        if out.is_symlink():
            sys.exit("ABBRUCH: %s ist ein Symlink - wird nicht beschrieben." % out)
        real = out.resolve()
        if real.exists():
            sys.exit("ABBRUCH: %s existiert bereits. Mit --out einen anderen Namen waehlen." % real)
        real.parent.mkdir(parents=True, exist_ok=True)
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=str(real.parent), suffix=".part")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        _chmod_private(tmp)              # Rohdaten koennen Kundendaten enthalten
        os.replace(tmp, real)

    p = lambda *x: print(*x)
    p("Quelle: %s (%s %s)" % (raw, d["crawler"]["name"], d["crawler"]["version"]))
    p("URLs: %s | Statuscodes: %s | Antwortzeit ⌀ %ss" % (d["umfang"]["urls"], d["umfang"]["statuscodes"], d["umfang"]["antwortzeit_avg_s"]))
    if d["scores"]["kategorien"]:
        p("Scores: " + ", ".join("%s %s" % (c["name"], c["score"]) for c in d["scores"]["kategorien"]))
    p("\nBefunde des Crawlers:")
    for b in d["befunde"][:15]:
        p("  %-8s %s" % (b["status"], b["text"]))
    p("\nSeiten mit SEO-Auffälligkeiten: %d von %d" % (len(d["seo_auffaellig"]), d["seo_geprueft"]))
    for s in d["seo_auffaellig"][:12]:
        p("  %-40s %s" % (str(s["url"])[:40], ", ".join(s["probleme"])))
    for k, label in (("doppelt", "Doppelte Titel/Descriptions"), ("heading_fehler", "Überschriften-Fehler"),
                     ("fehlerseiten", "404/Fehlerseiten"), ("weiterleitungen", "Weiterleitungen"),
                     ("sicherheit", "Security-Header"), ("barrierefreiheit", "Barrierefreiheit"), ("best_practices", "Best Practices")):
        if d.get(k):
            p("\n%s (%d):" % (label, len(d[k])))
            for row in d[k][:8]:
                p("  " + json.dumps(row, ensure_ascii=False)[:160])
    p("\nKompakter Auszug: %s" % (out if out else "(nicht geschrieben, read-only)"))


if __name__ == "__main__":
    main()
