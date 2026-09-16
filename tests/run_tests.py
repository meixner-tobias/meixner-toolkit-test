#!/usr/bin/env python3
"""Regressionstests fuer meixner-toolkit.

Aufruf:  python3 tests/run_tests.py
Erwartet: CLAUDE_PLUGIN_ROOT gesetzt oder Aufruf aus dem Plugin-Wurzelverzeichnis.

Bewusst ohne Testframework - eine Datei, Standardbibliothek, laeuft ueberall.
Jeder Test deckt einen Vertrag oder eine Sicherheitsgrenze ab, nicht Implementierungsdetails.
"""
import http.server
import importlib.util
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
os.environ["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
ERGEBNISSE = []


def pruefe(name, bedingung, detail=""):
    ERGEBNISSE.append((name, bool(bedingung), detail))
    print("  %-52s %s%s" % (name, "PASS" if bedingung else "FAIL",
                            "" if bedingung else "  <- " + str(detail)[:90]))


def modul(pfad, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- Fixture-Server
class Fixture(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/robots.txt":
            b, ct = b"User-agent: *\nAllow: /\nSitemap: http://127.0.0.1:8097/sitemap.xml\n", "text/plain"
        elif self.path == "/sitemap.xml":
            b, ct = (b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                     b'<url><loc>http://127.0.0.1:8097/</loc></url></urlset>'), "application/xml"
        elif self.path == "/noindex":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("x-robots-tag", "noindex")
            b = b"<html><head><title>x</title></head><body></body></html>"
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        else:
            b, ct = (b'<html><head><title>Fixture</title><meta name="description" content="d">'
                     b'</head><body><h1>Hallo</h1></body></html>'), "text/html"
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    do_HEAD = do_GET


def starte_fixture(port=8097):
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", port), Fixture)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------------------------------------------------------------- A: Launch-Check
def test_launch():
    print("\nA. Launch-Check")
    lc = modul("skills/launch/scripts/launch_check.py", "lc")
    pruefe("add() ist definiert", callable(getattr(lc, "add", None)),
           "P0-A: fehlte in 0.7.5, jeder Lauf endete im NameError")

    lc.checks.clear()
    lc.add("HOCH", "TEST", "Titel", "Detail https://x.de/a?token=geheim")
    eintrag = lc.checks[-1]
    pruefe("Befund-Datenmodell level/id/titel/detail",
           set(eintrag) == {"level", "id", "titel", "detail"}, eintrag)
    pruefe("add() redigiert URLs im Detailtext", "geheim" not in eintrag["detail"], eintrag["detail"])

    srv = starte_fixture()
    try:
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(ROOT / "skills/launch/scripts/launch_check.py"),
                                "http://127.0.0.1:8097/", "--out", d + "/lr.json"],
                               capture_output=True, text=True, timeout=120)
            pruefe("Lauf gegen Fixture ohne NameError", "NameError" not in r.stderr,
                   (r.stderr or "")[-160:])
            pruefe("Prozess terminiert regulaer", r.returncode in (0, 1, 2), r.returncode)
            ok = Path(d + "/lr.json").exists()
            pruefe("Report wird geschrieben", ok)
            if ok:
                rep = json.loads(Path(d + "/lr.json").read_text(encoding="utf-8"))
                pruefe("Report enthaelt Befunde im Vertrag",
                       isinstance(rep.get("checks"), list) and
                       all({"level", "id", "titel"} <= set(c) for c in rep["checks"]),
                       list(rep)[:6])
    finally:
        srv.shutdown()

    # Vollstaendiger, hermetischer Erfolgspfad: Netzwerk/SSL werden injiziert,
    # die produktive SSRF-Policy wird fuer Tests nicht aufgeweicht.
    lc.checks.clear(); lc.ALLOWED_HOSTS.clear()
    home = (b'<html><head><title>Fixture</title></head><body>'
            b'<a href="/impressum">Impressum</a><a href="/datenschutz">Datenschutz</a></body></html>')
    def fake_chain(u, *a, **k):
        return ([{"url": "https://example.test/", "status": 200}],
                {"Strict-Transport-Security": "max-age=31536000"}, home)
    def fake_fetch(u, *a, **k):
        if u.endswith("/robots.txt"):
            return 200, {}, b"User-agent: *\nAllow: /\nSitemap: https://example.test/sitemap.xml\n"
        if u.endswith("/sitemap.xml"):
            return 200, {}, b'<urlset><url><loc>https://example.test/</loc></url></urlset>'
        if u.endswith("-mt404"):
            return 404, {}, b""
        return 200, {}, home
    class _Sock:
        def __enter__(self): return self
        def __exit__(self, *a): return False
    class _SSock(_Sock):
        def getpeercert(self): return {"notAfter": "Jan 01 00:00:00 2099 GMT"}
    class _Ctx:
        def wrap_socket(self, *a, **k): return _SSock()
    import ipaddress
    old = (lc.chain, lc.fetch, lc.socket.create_connection, lc.ssl.create_default_context, lc.time.sleep,
           lc.guard.RESOLVER, list(sys.argv))
    ssl_targets = []
    try:
        lc.chain, lc.fetch = fake_chain, fake_fetch
        lc.guard.RESOLVER = lambda host: [ipaddress.ip_address("93.184.216.34")]
        lc.socket.create_connection = lambda target, *a, **k: (ssl_targets.append(target) or _Sock())
        lc.ssl.create_default_context = lambda: _Ctx()
        lc.time.sleep = lambda *_: None
        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "launch.json")
            sys.argv = ["launch_check.py", "https://example.test/", "--out", out]
            try:
                lc.main()
                rc = 0
            except SystemExit as e:
                rc = int(e.code or 0)
            pruefe("Launch-Erfolgspfad hermetisch komplett", rc == 0 and Path(out).exists(), rc)
            if Path(out).exists():
                rep = json.loads(Path(out).read_text(encoding="utf-8"))
                pruefe("Launch-Erfolgspfad prueft Sitemap-URL", rep.get("sitemap_urls_geprueft") == 1, rep)
                pruefe("Launch-SSL verbindet zur verifizierten IP statt erneut zum Hostnamen",
                       bool(ssl_targets) and ssl_targets[0][0] == "93.184.216.34", ssl_targets)
    finally:
        (lc.chain, lc.fetch, lc.socket.create_connection, lc.ssl.create_default_context, lc.time.sleep,
         lc.guard.RESOLVER, sys.argv) = old


# ---------------------------------------------------------------- B: URL-Guard
def test_urlguard():
    print("\nB. URL-Guard")
    g = modul("lib/urlguard.py", "urlguard")
    verboten = ["http://127.0.0.1/", "http://localhost/", "http://10.0.0.1/",
                "http://172.16.0.1/", "http://192.168.1.1/", "http://169.254.1.1/",
                "http://100.64.0.1/", "http://198.18.0.1/", "http://192.0.2.1/",
                "http://[::1]/", "http://[::ffff:7f00:1]/", "http://[2002:7f00:1::]/",
                "http://[64:ff9b::7f00:1]/", "file:///etc/passwd", "ftp://example.com/",
                "data:text/html,x", "javascript:alert(1)",
                "http://user:pw@example.com/", "http://example.com:22/"]
    for u in verboten:
        try:
            g.pruefe(u)
            pruefe("blockiert: " + u[:40], False, "wurde durchgelassen")
        except g.Blocked:
            pruefe("blockiert: " + u[:40], True)
        except Exception as e:
            pruefe("blockiert: " + u[:40], False, "falsche Ausnahme %s" % type(e).__name__)
    # Hermetisch: der Resolver wird injiziert. Vorher loeste der Test echtes DNS auf
    # und schlug in Umgebungen ohne Internet fehl - ein Test darf davon nicht abhaengen.
    import ipaddress
    g.RESOLVER = lambda host: [ipaddress.ip_address("93.184.216.34")]   # oeffentlich
    try:
        g.pruefe("https://irgendeine-domain.test/")
        pruefe("erlaubt: oeffentliche IP (Resolver injiziert)", True)
    except g.Blocked as e:
        pruefe("erlaubt: oeffentliche IP (Resolver injiziert)", False, e)
    g.RESOLVER = lambda host: [ipaddress.ip_address("10.1.2.3")]        # DNS zeigt intern
    try:
        g.pruefe("https://sieht-oeffentlich-aus.test/")
        pruefe("blockiert: Hostname loest auf private IP auf", False, "durchgelassen")
    except g.Blocked:
        pruefe("blockiert: Hostname loest auf private IP auf", True)
    g.RESOLVER = lambda host: [ipaddress.ip_address("fd00::1")]         # privates IPv6
    try:
        g.pruefe("https://ipv6.test/")
        pruefe("blockiert: privates IPv6 aus DNS", False, "durchgelassen")
    except g.Blocked:
        pruefe("blockiert: privates IPv6 aus DNS", True)
    g.RESOLVER = None
    r = g.redigiere("https://a.de/x?gclid=ABC&email=max@test.de&page=2")
    pruefe("Redaction entfernt gclid und email", "ABC" not in r and "max@test.de" not in r, r)
    pruefe("Redaction behaelt unverfaengliche Parameter", "page=2" in r, r)


# ---------------------------------------------------------------- C: Kundenbericht
def test_bericht():
    print("\nC. Kundenbericht")
    renderer = ROOT / "skills/kundenbericht/scripts/render_report.mjs"
    beispiele = list((ROOT / "skills/kundenbericht/examples").glob("*.json"))
    pruefe("mindestens ein offizielles Beispiel vorhanden", bool(beispiele))
    for b in beispiele:
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(["node", str(renderer), str(b), "--out", d + "/r.html"],
                               capture_output=True, text=True, timeout=120, cwd=d)
            html = Path(d + "/r.html").read_text(encoding="utf-8") if Path(d + "/r.html").exists() else ""
            pruefe("Beispiel rendert: " + b.name, r.returncode == 0 and len(html) > 500,
                   (r.stdout + r.stderr).strip()[:150])
            if html:
                pruefe("HTML enthaelt den Kundennamen",
                       json.loads(b.read_text(encoding="utf-8")).get("kunde", "") in html)

    def rendere(audit, extra=None):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.json"
            f.write_text(json.dumps(audit), encoding="utf-8")
            r = subprocess.run(["node", str(renderer), str(f), "--out", d + "/r.html"] + (extra or []),
                               capture_output=True, text=True, timeout=60, cwd=d)
            html = Path(d + "/r.html").read_text(encoding="utf-8") if Path(d + "/r.html").exists() else ""
            return r, html

    basis = {"typ": "seogeo", "kunde": "K", "domain": "a.de", "scorecard": [], "findings": []}
    r, _ = rendere({**basis, "typ": "quatsch"})
    pruefe("unbekannter typ wird abgelehnt", r.returncode != 0)
    r, _ = rendere({**basis, "scorecard": [{"bereich": "T", "status": "unsinn"}]})
    pruefe("unbekannter status wird abgelehnt", r.returncode != 0)
    r, _ = rendere({**basis, "findings": [{"titel": "x", "prioritaet": "ultra"}]})
    pruefe("unbekannte prioritaet wird abgelehnt", r.returncode != 0)
    r, _ = rendere({k: v for k, v in basis.items() if k != "domain"})
    pruefe("fehlende domain wird abgelehnt", r.returncode != 0)
    r, _ = rendere({k: v for k, v in basis.items() if k != "kunde"})
    pruefe("fehlender kunde wird abgelehnt", r.returncode != 0)

    _, html = rendere({**basis, "scorecard": [{"bereich": "T", "status": "gut",
                                              "anzahl": "3</td><script>alert(1)</script>"}]})
    pruefe("HTML-Injection ueber scorecard.anzahl neutralisiert",
           "<script>alert(1)</script>" not in html)
    _, html = rendere({**basis, "findings": [{"titel": "<img src=x onerror=alert(1)>",
                                             "prioritaet": "hoch", "bereich": "T"}]})
    pruefe("HTML-Injection ueber findings.titel escapt",
           "<img src=x onerror=" not in html and "&lt;img" in html)

    # Ein vorbereitetes .part-Symlink darf nie verfolgt oder geloescht werden.
    if os.name != "nt":
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d) / "work"; cwd.mkdir()
            outside = Path(d) / "outside"; outside.mkdir()
            audit = cwd / "a.json"; audit.write_text(json.dumps(basis), encoding="utf-8")
            victim = outside / "victim.txt"; victim.write_text("UNVERAENDERT", encoding="utf-8")
            os.symlink(victim, cwd / "r.html.part")
            r = subprocess.run(["node", str(renderer), str(audit), "--out", str(cwd / "r.html")],
                               capture_output=True, text=True, timeout=60, cwd=cwd)
            pruefe("Report folgt keinem vorbereiteten .part-Symlink",
                   r.returncode != 0 and victim.read_text(encoding="utf-8") == "UNVERAENDERT",
                   (r.stdout + r.stderr)[-180:])
            pruefe("fremder .part-Symlink bleibt bei Abbruch unangetastet", (cwd / "r.html.part").is_symlink())

        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d) / "work"; cwd.mkdir()
            outside = Path(d) / "outside"; outside.mkdir()
            audit = cwd / "a.json"; audit.write_text(json.dumps(basis), encoding="utf-8")
            os.symlink(outside, cwd / "link")
            r = subprocess.run(["node", str(renderer), str(audit), "--out", str(cwd / "link" / "r.html")],
                               capture_output=True, text=True, timeout=60, cwd=cwd)
            pruefe("Report schreibt nicht durch symlinkten Ausgabeordner nach ausserhalb",
                   r.returncode != 0 and not (outside / "r.html").exists(), (r.stdout + r.stderr)[-180:])

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "a.json"; f.write_text(json.dumps(basis), encoding="utf-8")
        cfg = Path(d) / "c.json"
        cfg.write_text(json.dumps({"branding": {"logo": "http://127.0.0.1/logo.png"}}), encoding="utf-8")
        r = subprocess.run(["node", str(renderer), str(f), "--out", str(Path(d)/"r.html"),
                            "--config", str(cfg), "--remote-logo"],
                           capture_output=True, text=True, timeout=60, cwd=d)
        html = (Path(d)/"r.html").read_text(encoding="utf-8") if (Path(d)/"r.html").exists() else ""
        pruefe("privates Remote-Logo wird trotz Opt-in nicht eingebettet",
               r.returncode == 0 and "127.0.0.1/logo.png" not in html and "Netzwerkpolicy" in r.stderr,
               (r.stdout + r.stderr)[-180:])


# ---------------------------------------------------------------- D: Tracking-Builder
def test_builder():
    print("\nD. Tracking-Builder")
    gen = ROOT / "skills/tracking-audit/scripts/build_web_container.py"

    def baue(plan, extra=None):
        with tempfile.TemporaryDirectory() as d:
            Path(d + "/p.json").write_text(json.dumps(plan, default=str), encoding="utf-8")
            r = subprocess.run([sys.executable, str(gen), d + "/p.json", "-o", d + "/o.json"] + (extra or []),
                               capture_output=True, text=True, timeout=60)
            out = json.loads(Path(d + "/o.json").read_text(encoding="utf-8")) if Path(d + "/o.json").exists() else None
            return r, out

    gueltig = {"ga4": {"measurement_id": "G-ABCDE12345"},
               "consent": {"mode": "advanced", "update_event": "cookie_consent_update"},
               "meta": {"pixel_id": "987654321098765", "browser_pixel": True},
               "events": [{"name": "generate_lead", "meta_event": "Lead", "value": 50, "currency": "EUR"}]}
    r, out = baue(gueltig)
    pruefe("gueltiger Browser-Plan baut", r.returncode == 0 and out is not None,
           (r.stdout + r.stderr)[:140])
    if out:
        tags = out["containerVersion"]["tag"]
        basis = [t for t in tags if "Base" in t["name"]]
        trig = {t["triggerId"]: t for t in out["containerVersion"]["trigger"]}
        pruefe("Meta-Basis-Tag haengt am Consent-Ereignis",
               bool(basis) and any(trig.get(i, {}).get("type") == "CUSTOM_EVENT"
                                   for i in basis[0]["firingTriggerId"]))
        pruefe("Meta-Basis-Tag feuert hoechstens einmal je Seite",
               bool(basis) and basis[0]["tagFiringOption"] == "ONCE_PER_LOAD")
        html = " ".join(p["value"] for t in tags if t["type"] == "html"
                        for p in t["parameter"] if p["key"] == "html")
        pruefe("Ereignis-ID fuer Deduplizierung gesetzt", "eventID" in html)

    gen_mod = modul("skills/tracking-audit/scripts/build_web_container.py", "builder_server")
    server_plan = {**gueltig, "architecture": "server",
                   "server_container_url": "https://sgtm.example.test/metrics",
                   "google_ads": {"conversion_id": "AW-987654321"},
                   "events": [{"name": "purchase", "meta_event": "Purchase",
                               "ads_label": "XyZaBcDeFgH", "value": 9, "currency": "EUR"}]}
    try:
        b = gen_mod.Builder(server_plan, server_resolver=lambda host: ["93.184.216.34"])
        out = b.build(); errs = gen_mod.validate(out)
        pruefe("architecture=server baut hermetisch erfolgreich", not errs and out is not None, errs)
        pruefe("architecture=server erzeugt keine Browser-Ads-Conversion",
               not [t for t in out["containerVersion"]["tag"] if t["type"] == "awct"])
    except Exception as e:
        pruefe("architecture=server baut hermetisch erfolgreich", False, repr(e))

    try:
        gen_mod.pruefe_server_url("https://sgtm.example.test/x", resolver=lambda host: ["100.64.0.1"])
        pruefe("sGTM Shared Address Space wird abgelehnt", False, "100.64.0.1 wurde akzeptiert")
    except gen_mod.PlanError:
        pruefe("sGTM Shared Address Space wird abgelehnt", True)

    boese = [
        ("meta_event mit Code", {"events": [{"name": "e", "meta_event": "L'); alert(1); //"}]}),
        ("value als JS-Ausdruck", {"events": [{"name": "e", "meta_event": "Lead", "value": "1;alert(1)"}]}),
        ("value NaN", {"events": [{"name": "e", "meta_event": "Lead", "value": float("nan")}]}),
        ("ungueltige Waehrung", {"events": [{"name": "e", "meta_event": "Lead", "value": 1, "currency": "XXX"}]}),
        ("Platzhalter-ID", {"ga4": {"measurement_id": "G-XXXXXXXXXX"}}),
        ("browser + server_container_url", {"architecture": "browser",
                                            "server_container_url": "https://s.example.com/m"}),
        ("sGTM ohne https", {"architecture": "server", "server_container_url": "http://s.example.com/m"}),
        ("params mit E-Mail", {"events": [{"name": "e", "params": {"m": "user.email"}}]}),
        ("consent.mode fehlt", {"consent": {}}),
    ]
    for label, patch in boese:
        plan = json.loads(json.dumps(gueltig, default=str))
        plan.update(patch)
        r, out = baue(plan)
        pruefe("abgelehnt: " + label, r.returncode != 0 and out is None,
               "Exit %s" % r.returncode)
        pruefe("  ohne Traceback: " + label, "Traceback" not in r.stderr)


# ---------------------------------------------------------------- E: fill_template
def test_template():
    print("\nE. GTM-Master / fill_template")
    ft = ROOT / "skills/tracking-audit/scripts/fill_template.py"
    master = {"containerVersion": {"container": {"usageContext": ["SERVER"]}, "tag": [
        {"name": "Boese", "type": "html", "parameter": [
            {"key": "html", "value": "<script>eval(atob('eA=='))</script>"}]}], "variable": [
        {"name": "C - Meta CAPI Access Token", "type": "c",
         "parameter": [{"key": "value", "value": "EAAG-GEHEIM"}]},
        {"name": "C - GA4 Measurement ID", "type": "c",
         "parameter": [{"key": "value", "value": "G-ALT9999999"}]}]}}
    with tempfile.TemporaryDirectory() as d:
        m = Path(d) / "m.json"
        m.write_text(json.dumps(master), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ft), str(m), "--list"],
                           capture_output=True, text=True, timeout=60)
        pruefe("--list zeigt keinen Tokenwert", "EAAG-GEHEIM" not in r.stdout + r.stderr)
        pruefe("--list markiert Geheimnisse als redigiert", "<redigiert>" in r.stdout)
        pruefe("verdaechtiges Custom-HTML wird gemeldet",
               "eval(" in r.stderr or "atob(" in r.stderr or "WARNUNG" in r.stderr)
        v = Path(d) / "v.json"
        v.write_text(json.dumps({"C - GA4 Measurement ID": "G-NEU1234567"}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ft), str(m), str(v), "-o", d + "/out.json"],
                           capture_output=True, text=True, timeout=60)
        pruefe("Befuellen bricht bei nicht ersetztem Token ab", r.returncode != 0)
        pruefe("bei Abbruch wird nichts geschrieben", not Path(d + "/out.json").exists())


# ---------------------------------------------------------------- F: SiteOne
def test_siteone():
    print("\nF. SiteOne-Wrapper")
    so = ROOT / "skills/seogeo/scripts/siteone.py"
    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "fake"
        fake.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        fake.chmod(0o755)
        r = subprocess.run([sys.executable, str(so), "http://127.0.0.1/x", "--bin", str(fake)],
                           capture_output=True, text=True, timeout=60)
        pruefe("interne Ziel-URL wird abgelehnt", r.returncode != 0 and "intern" in (r.stdout + r.stderr))
        for arg, wert in (("--workers", "99"), ("--rps", "-5"), ("--timeout", "9999")):
            r = subprocess.run([sys.executable, str(so), "https://127.0.0.1", "--bin", str(fake), arg, wert],
                               capture_output=True, text=True, timeout=60)
            pruefe("Wertebereich erzwungen: %s %s" % (arg, wert), r.returncode != 0)
        # ACHTUNG: --crawler-arg MUSS mit "=" uebergeben werden. Mit Leerzeichen bricht
        # argparse vorher ab - in 0.7.6 hat genau das drei Tests scheinbestehen lassen.
        def crawl(*extra):
            return subprocess.run([sys.executable, str(so), "https://kunde.test", "--bin", str(fake)]
                                  + list(extra), capture_output=True, text=True, timeout=60)

        r = crawl("--crawler-arg=--allowed-domain-for-crawling=*")
        pruefe("Wildcard im Crawl-Scope abgelehnt",
               r.returncode != 0 and "Wildcard" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-120:])
        r = crawl("--crawler-arg=--allowed-domain-for-crawling=fremde-domain.test")
        pruefe("fremde Zusatzdomain -> REVIEW_REQUIRED",
               r.returncode != 0 and "REVIEW_REQUIRED" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-120:])
        # Scope-Logik hermetisch direkt testen; kein echter Resolver-Aufruf.
        so_mod = modul("skills/seogeo/scripts/siteone.py", "siteone_scope")
        seen = []
        got = so_mod.pruefe_crawl_domain("shop.kunde.test", "kunde.test", [],
                                         guard_fn=lambda u: seen.append(u))
        pruefe("Subdomain passiert die Scope-Pruefung hermetisch",
               got == "shop.kunde.test" and seen == ["https://shop.kunde.test"], (got, seen))
        r = crawl("--crawler-arg=--allowed-domain-for-crawling=192.168.1.5")
        pruefe("private Adresse als Crawl-Domain abgelehnt", r.returncode != 0)
        sichtbar = so_mod.redigiere_cmd(["siteone", "--http-auth=admin:geheim123", "--url=https://kunde.test"])
        aus = " ".join(sichtbar)
        pruefe("Zugangsdaten erscheinen nicht in der Ausgabe", "geheim123" not in aus, aus)
        pruefe("Zugangsdaten werden als [REDACTED] gezeigt", "--http-auth=[REDACTED]" in aus, aus)


def test_doctor():
    print("\nG. Doctor / Versionspruefung")
    d = modul("skills/setup/scripts/doctor.py", "doctor")
    pruefe("Mindestversionen zentral definiert",
           d.MIN_NODE == (20, 0) and d.MIN_PYTHON == (3, 10), (d.MIN_NODE, d.MIN_PYTHON))
    for text, erwartet in [("v18.20.4", False), ("v19.9.0", False), ("v20.0.0", True),
                           ("v20.11.1", True), ("v22.22.2", True), ("", False), ("kaputt", False)]:
        got = d.version_ok(d.parse_node_version(text), d.MIN_NODE)
        pruefe("Node %-12s -> %s" % (text or "(leer)", "ok" if erwartet else "zu alt"),
               got == erwartet, "erhalten %s" % got)
    for ver, erwartet in [((3, 9, 18), False), ((3, 10, 0), True), ((3, 12, 3), True), (None, False)]:
        got = d.version_ok(ver, d.MIN_PYTHON)
        pruefe("Python %-12s -> %s" % (str(ver), "ok" if erwartet else "zu alt"),
               got == erwartet, "erhalten %s" % got)
    pruefe("SiteOne-Version wird aus der Ausgabe gelesen",
           d.parse_siteone_version("SiteOne Crawler v2.5.1 (build 3)") == "2.5.1")
    pruefe("unlesbare SiteOne-Ausgabe ergibt None",
           d.parse_siteone_version("kein Versionsstring") is None)
    pruefe("Playwright-Pin gesetzt", bool(d.PLAYWRIGHT_VERSION))
    roots = d.playwright_roots({"CLAUDE_PLUGIN_ROOT": "/tmp/plugin", "MT_PLAYWRIGHT_DIR": "/tmp/pw"})
    pruefe("Doctor prueft MT_PLAYWRIGHT_DIR und CLAUDE_PLUGIN_ROOT",
           Path("/tmp/pw") in roots and Path("/tmp/plugin") in roots, roots)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "plugin"
        (root / "node_modules/playwright").mkdir(parents=True)
        (root / "node_modules/playwright/package.json").write_text("{}", encoding="utf-8")
        found = d.find_playwright_root({"CLAUDE_PLUGIN_ROOT": str(root)})
        pruefe("Doctor findet Playwright im Plugin-Root", found == root, found)


def test_dokumentation():
    print("\nH. Dokumentation gegen Code")
    import re as _re
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    d = modul("skills/setup/scripts/doctor.py", "doctor2")
    pruefe("README nennt dieselbe Node-Mindestversion wie doctor.py",
           "Node ≥ %d" % d.MIN_NODE[0] in readme, d.MIN_NODE)
    pruefe("README nennt dieselbe Python-Mindestversion",
           "Python ≥ %d.%d" % d.MIN_PYTHON in readme, d.MIN_PYTHON)
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pruefe("package.json engines.node passt zu MIN_NODE",
           str(d.MIN_NODE[0]) in pkg.get("engines", {}).get("node", ""), pkg.get("engines"))
    pruefe("Playwright-Pin in package.json == doctor.py",
           pkg["dependencies"]["playwright"] == d.PLAYWRIGHT_VERSION)
    versionen = {json.loads((ROOT / f).read_text(encoding="utf-8"))["version"]
                 for f in (".claude-plugin/plugin.json", "package.json", "package-lock.json")}
    pruefe("eine einzige Versionsnummer in allen Metadaten", len(versionen) == 1, versionen)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    fehlend = [m for m in _re.findall(r"`(docs/[^`]+)`", changelog) if not (ROOT / m).exists()]
    pruefe("CHANGELOG verweist auf keine fehlende Datei", not fehlend, fehlend)
    pruefe("keine unbelegten PageSpeed-Quoten mehr",
           "25.000" not in readme and "ohne Limit" not in readme)
    tracking_skill = (ROOT / "skills/tracking-audit/SKILL.md").read_text(encoding="utf-8")
    google_ref = (ROOT / "skills/tracking-audit/references/google.md").read_text(encoding="utf-8")
    pruefe("alte harte gcs!=G100-Regel aus Skill und Referenz entfernt",
           "gcs≠G100" not in tracking_skill and "gcs≠G100" not in google_ref
           and "G111 alles erteilt" not in google_ref)


def test_netzpolicy():
    print("\nI. Browser-Netzpolicy (ohne Browser, hermetisch)")
    skript = r"""
    import("%s/lib/netpolicy.mjs").then(async m => {
      const res = {};
      const oeff = async () => ["93.184.216.34"];
      for (const u of ["http://127.0.0.1/","http://localhost/","http://10.0.0.1/",
                       "http://172.16.5.5/","http://192.168.1.1/","http://169.254.169.254/",
                       "http://[::1]/","http://[fd00::1]/","http://[fe80::1]/",
                       "http://[::ffff:7f00:1]/","http://[::ffff:a00:1]/","http://[::ffff:c0a8:101]/",
                       "http://[::ffff:a9fe:a9fe]/","http://[::ffff:ac10:1]/",
                       "http://100.64.0.1/","http://198.18.0.1/","http://192.0.2.1/",
                       "http://198.51.100.1/","http://203.0.113.1/",
                       "http://[2002:7f00:1::]/","http://[2002:a00:1::]/",
                       "http://user:pw@a.example/","http://a.example:22/","file:///etc/passwd",
                       "http://metadata.google.internal/"]) {
        res[u] = (await m.pruefeZiel(u, oeff)).erlaubt;
      }
      res["OEFFENTLICH"] = (await m.pruefeZiel("https://www.google-analytics.com/g/collect", oeff)).erlaubt;
      res["CDN"] = (await m.pruefeZiel("https://cdn.example/x.js", oeff)).erlaubt;
      res["DNS_PRIVAT"] = (await m.pruefeZiel("https://x.example/", async () => ["10.1.2.3"])).erlaubt;
      res["DNS_V6_PRIVAT"] = (await m.pruefeZiel("https://y.example/", async () => ["fd00::5"])).erlaubt;
      res["172_32_OEFFENTLICH"] = (await m.pruefeZiel("http://172.32.0.1/", oeff)).erlaubt;
      console.log(JSON.stringify(res));
    });
    """ % ROOT
    r = subprocess.run(["node", "-e", skript], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        pruefe("Netzpolicy laedt", False, (r.stderr or "")[-160:])
        return
    res = json.loads(r.stdout.strip().splitlines()[-1])
    pruefe("Netzpolicy laedt und antwortet", True)
    for u, erlaubt in res.items():
        if u in ("OEFFENTLICH", "CDN", "172_32_OEFFENTLICH"):
            pruefe("durchgelassen: %s" % u, erlaubt is True, erlaubt)
        else:
            pruefe("blockiert: %s" % u[:38], erlaubt is False, erlaubt)

    quelle = (ROOT / "skills/tracking-audit/scripts/consent_test.mjs").read_text(encoding="utf-8")
    pruefe("consent_test prueft die Start-URL vor der Navigation", "await pruefeZiel(url)" in quelle)
    pruefe("consent_test haengt die Policy an den Context", "installiereNetzPolicy(ctx" in quelle)
    pruefe("Consent-Context blockiert Service Worker fuer Request-Interception", 'serviceWorkers: "block"' in quelle)
    netq = (ROOT / "lib/netpolicy.mjs").read_text(encoding="utf-8")
    pruefe("Netzpolicy routet WebSockets", "routeWebSocket" in netq and "connectToServer" in netq)
    pruefe("consent_test blockiert Collection statt Tracker-Loader",
           "shouldBlockTrackerDelivery" in quelle and "trackerAbbrechen" in quelle)
    pos_policy = quelle.index("installiereNetzPolicy(ctx")
    pos_goto = quelle.index("page.goto(url")
    pruefe("Policy wird vor der ersten Navigation gesetzt", pos_policy < pos_goto)


def test_skill_invocation():
    print("\nJ. Skill-Invocation")
    import re as _re
    MUTIEREND = {"seogeo", "tracking-audit", "launch", "kundenbericht", "setup", "start", "wissen-update"}
    for d in sorted((ROOT / "skills").iterdir()):
        if not (d / "SKILL.md").is_file():
            continue
        kopf = _re.match(r"^---\n(.*?)\n---", (d / "SKILL.md").read_text(encoding="utf-8"), _re.S)
        pruefe("Frontmatter lesbar: %s" % d.name, bool(kopf))
        if not kopf:
            continue
        felder = dict(_re.findall(r"^([a-z-]+):\s*(.*)$", kopf.group(1), _re.M))
        pruefe("  name == Verzeichnis: %s" % d.name, felder.get("name") == d.name, felder.get("name"))
        if d.name in MUTIEREND:
            pruefe("  mutierender Skill ist user-only: %s" % d.name,
                   felder.get("disable-model-invocation") == "true",
                   felder.get("disable-model-invocation", "(fehlt)"))



def test_consent_logic():
    print("\nK. Consent-Analyse (hermetisch)")
    skript = r"""
    import("%s/skills/tracking-audit/scripts/consent_logic.mjs").then(m => {
      const site = "https://kunde.test/";
      const out = {};
      out.gtmRole = m.requestRole("https://www.googletagmanager.com/gtm.js?id=GTM-X", "script", site);
      out.metaLoaderRole = m.requestRole("https://connect.facebook.net/en_US/fbevents.js", "script", site);
      out.metaPixelRole = m.requestRole("https://www.facebook.com/tr?id=1&ev=PageView", "image", site);
      out.blockLoader = m.shouldBlockTrackerDelivery("https://connect.facebook.net/en_US/fbevents.js", {resourceType:()=>"script"}, site);
      out.blockPixel = m.shouldBlockTrackerDelivery("https://www.facebook.com/tr?id=1&ev=PageView", {resourceType:()=>"image"}, site);
      out.delta = m.storageDelta({localStorage:["a"],sessionStorage:[],indexedDB:{databases:[]}},
                                 {localStorage:["a","_fbp"],sessionStorage:["_ga"],indexedDB:{databases:["analytics"]}});
      out.empty = m.emptyScenario("ablehnen");
      const bad = {scenario:"keine_interaktion",status:"unknown",abbruch:"BROWSER_FEHLER",errors:["x"],hits:[],cookies_after:[]};
      const ok = {scenario:"akzeptieren",status:"geprueft",abbruch:null,errors:[],hits:[],cookies_after:[],datalayer_consent:[]};
      const rej = {scenario:"ablehnen",status:"unknown",abbruch:"CMP_BUTTON_NICHT_GEFUNDEN",errors:["x"],hits:[],cookies_after:[]};
      out.findings = m.assess([bad,ok,rej]);
      console.log(JSON.stringify(out));
    });
    """ % ROOT
    r = subprocess.run(["node", "-e", skript], capture_output=True, text=True, timeout=60)
    pruefe("Consent-Logik laedt", r.returncode == 0, r.stderr[-160:])
    if r.returncode != 0:
        return
    x = json.loads(r.stdout.strip().splitlines()[-1])
    pruefe("GTM-Loader wird als Loader erkannt", x["gtmRole"] == "loader", x["gtmRole"])
    pruefe("Meta-Library wird nicht als Collection blockiert", x["metaLoaderRole"] == "loader" and x["blockLoader"] is False, x)
    pruefe("Meta-Pixel-Beacon wird als Collection blockiert", x["metaPixelRole"] == "collection" and x["blockPixel"] is True, x)
    pruefe("Storage-Delta erfasst neue Keys/DB", x["delta"]["localStorage_new"] == ["_fbp"] and x["delta"]["indexedDB_new"] == ["analytics"], x["delta"])
    pruefe("Consent-Szenario-Vertrag initialisiert Summary-Felder immer",
           x["empty"]["cookies_after"] == [] and x["empty"]["hits"] == []
           and x["empty"]["errors"] == [] and x["empty"]["status"] == "unknown", x["empty"])
    pruefe("Browserfehler wird nicht fachlich ausgewertet",
           any(v.startswith("NICHT GEPRUEFT (keine_interaktion)") for v in x["findings"])
           and not any("KRITISCH" in v for v in x["findings"]), x["findings"])


if __name__ == "__main__":
    print("meixner-toolkit Regressionstests")
    print("Plugin-Wurzel: %s\n" % ROOT)
    for fn in (test_launch, test_urlguard, test_bericht, test_builder, test_template,
               test_siteone, test_doctor, test_dokumentation,
               test_netzpolicy, test_skill_invocation, test_consent_logic):
        try:
            fn()
        except Exception as e:
            pruefe("%s ABGEBROCHEN" % fn.__name__, False, "%s: %s" % (type(e).__name__, e))
    bestanden = sum(1 for _, ok, _ in ERGEBNISSE if ok)
    print("\n%d Tests, %d bestanden, %d fehlgeschlagen"
          % (len(ERGEBNISSE), bestanden, len(ERGEBNISSE) - bestanden))
    sys.exit(0 if bestanden == len(ERGEBNISSE) else 1)
