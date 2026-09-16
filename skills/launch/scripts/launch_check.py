#!/usr/bin/env python3
"""Go-Live-Check einer Website (nur Standardbibliothek).

  python3 launch_check.py https://www.kunde.de [--alt https://alt-domain.de ...] [--paths /kontakt /impressum] [--max-urls 50] [--out launch-check.json]

Prüft: Host-Varianten (http/https, www/ohne) → eine kanonische Adresse per 301/308; alte Domains → 301 pfaderhaltend;
Startseite (Status, noindex, Title, Canonical, Staging-Reste, Impressum/Datenschutz-Links); robots.txt; Sitemap (Status der URLs,
Weiterleitungen, noindex); echte 404; SSL-Restlaufzeit; HSTS & Basis-Sicherheitsheader.
"""
import argparse, json, os, random, re, socket, ssl, string, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

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

UA = "Mozilla/5.0 (compatible; meixner-toolkit-launch/0.3)"
checks = []
ALLOWED_HOSTS = set()      # wird in main() aus URL + --alt gefuellt
MAX_BODY = 2_000_000
MAX_HOPS = 10


def add(level, cid, title, detail=""):
    """Sammelt einen Befund. Datenmodell unveraendert gegenueber 0.7.2:
    level/id/titel/detail - so konsumiert es der Kundenbericht ueber audit.json.
    Neu ist allein die Redaction: Detailtexte enthalten sonst vollstaendige URLs
    mit Click-IDs und Session-Parametern."""
    checks.append({"level": level, "id": cid, "titel": title,
                   "detail": guard.redigiere_fehler(detail) if detail else ""})


Blocked = guard.Blocked
MAX_BODY = guard.MAX_BODY
MAX_HOPS = guard.MAX_HOPS


def guard_url(url, allow_any_host=False):
    return guard.pruefe(url, None if allow_any_host else (ALLOWED_HOSTS or None))


def fetch(url, method="GET", limit=MAX_BODY, allow_any_host=False):
    hosts = None if allow_any_host else (ALLOWED_HOSTS or None)
    return guard.hole(url, hosts, methode=method, limit=limit, ua=UA)


def chain(url, max_hops=MAX_HOPS, allow_any_host=False):
    hosts = None if allow_any_host else (ALLOWED_HOSTS or None)
    return guard.kette(url, hosts, max_hops=max_hops, ua=UA)


def fmt(hops):
    return " → ".join("%s [%s]" % (h["url"], h["status"]) for h in hops)


def norm(u):
    p = urllib.parse.urlsplit(u)
    return "%s://%s%s" % (p.scheme, p.netloc.lower(), p.path or "/")


def robots_blocks_all(txt, agents=("*", "googlebot")):
    """Wertet robots.txt nach der Google-Spezifikation aus statt mit einem Einzelmuster.

    Beruecksichtigt: mehrere Gruppen, zusammengefasste User-agent-Zeilen, Allow-Regeln
    (laengere Regel gewinnt), Kommentare, CRLF. Gibt True zurueck, wenn "/" fuer einen
    der genannten Agenten gesperrt ist.
    Quelle: developers.google.com/crawling/docs/robots-txt/robots-txt-spec
    """
    groups, cur, expect_agent = [], None, True
    for raw in txt.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            if not expect_agent or cur is None:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
                expect_agent = True
            cur["agents"].append(value.lower())
        elif field in ("allow", "disallow"):
            if cur is None:
                continue
            expect_agent = False
            cur["rules"].append((field, value))
    for want in agents:
        rules = [r for g in groups if want in g["agents"] for r in g["rules"]]
        if not rules:
            continue
        best = None
        for kind, path in rules:
            if path == "" and kind == "disallow":
                continue          # "Disallow:" leer = alles erlaubt
            pat = path.rstrip("*")
            if "/".startswith(pat) or pat in ("/", ""):
                if best is None or len(pat) > best[1]:
                    best = (kind, len(pat))
        if best and best[0] == "disallow":
            return True
    return False


ROBOTS_META = re.compile(r"<meta[^>]+>", re.I)
NOINDEX_WORDS = ("noindex", "none")


def robots_directives(html, headers, agents=("robots", "googlebot")):
    """Sammelt ALLE robots-Meta-Tags und den X-Robots-Tag-Header (Gross/Kleinschreibung egal).

    Der bisherige Einzelabgleich fand nur das erste Meta-Tag, kannte content="none" nicht
    und suchte den Header nur in exakter Schreibweise.
    Quelle: developers.google.com/search/docs/crawling-indexing/robots-meta-tag
    """
    found = []
    for tag in ROBOTS_META.findall(html or ""):
        n = re.search(r'name\s*=\s*["\']([^"\']+)', tag, re.I)
        c = re.search(r'content\s*=\s*["\']([^"\']*)', tag, re.I)
        if n and c and n.group(1).strip().lower() in agents:
            found.append(("meta[%s]" % n.group(1).strip().lower(), c.group(1)))
    for k, v in (headers or {}).items():
        if k.lower() == "x-robots-tag":
            found.append(("X-Robots-Tag", v))
    return found


def is_noindex(html, headers):
    for quelle, wert in robots_directives(html, headers):
        parts = [p.strip().lower() for p in re.split(r"[,;]", wert)]
        if any(p in NOINDEX_WORDS for p in parts):
            return "%s: %s" % (quelle, wert.strip())
    return None


def meta(body, name):
    m = re.search(r'<meta[^>]+name=["\']%s["\'][^>]*content=["\']([^"\']*)' % name, body, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*name=["\']%s["\']' % name, body, re.I)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--alt", nargs="*", default=[], help="alte Domains/URLs, die dauerhaft weiterleiten sollen")
    ap.add_argument("--paths", nargs="*", default=["/impressum", "/datenschutz", "/kontakt"], help="Pfade für Weiterleitungstests alter Domains")
    ap.add_argument("--max-urls", type=int, default=50)
    ap.add_argument("--out", default="launch-check.json")
    a = ap.parse_args()

    base = a.url.rstrip("/") + "/"
    sp = urllib.parse.urlsplit(base)
    host = (sp.hostname or "").lower()
    apex = host[4:] if host.startswith("www.") else host

    # Nur die vom Nutzer genannten Domains duerfen abgerufen werden. Alles andere -
    # Sitemap-Eintraege, Redirect-Ziele, <loc>-Elemente - wird geblockt und im Bericht vermerkt.
    ALLOWED_HOSTS.add(apex)
    for alt in a.alt:
        h = (urllib.parse.urlsplit(alt if "//" in alt else "//" + alt).hostname or "").lower()
        if h:
            ALLOWED_HOSTS.add(h[4:] if h.startswith("www.") else h)
    print("Geprueft werden ausschliesslich: %s" % ", ".join(sorted(ALLOWED_HOSTS)), file=sys.stderr)

    # 1) Startseite + kanonische Adresse
    hops, headers, body = chain(base)
    final = hops[-1]
    canon_url = norm(final["url"])
    if final["status"] != 200:
        add("KRITISCH", "HOME-STATUS", "Startseite nicht erreichbar", fmt(hops))
    html = body.decode("utf-8", "replace")
    nd = is_noindex(html, headers)
    if nd:
        add("KRITISCH", "HOME-NOINDEX", "Startseite ist von der Indexierung ausgeschlossen", nd)
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not title or not title.group(1).strip():
        add("HOCH", "HOME-TITLE", "Startseite ohne <title>", "")
    c = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html, re.I)
    if c and urllib.parse.urlsplit(c.group(1)).netloc.lower() not in ("", urllib.parse.urlsplit(canon_url).netloc):
        add("HOCH", "HOME-CANONICAL", "Canonical zeigt auf anderen Host", c.group(1))
    leftovers = sorted(set(re.findall(r'https?://(?:localhost|127\.0\.0\.1|[a-z0-9-]*(?:staging|stage|dev|test)[a-z0-9-]*\.[^\s"\'<>/]+)', html, re.I)))
    leftovers = [l for l in leftovers if urllib.parse.urlsplit(l).netloc.lower() not in (host, urllib.parse.urlsplit(canon_url).netloc)]
    if leftovers:
        add("HOCH", "HOME-STAGING", "Verweise auf Staging/Dev-Adressen im HTML", ", ".join(leftovers[:5]))
    for word, cid in (("impressum", "LEGAL-IMPRESSUM"), ("datenschutz", "LEGAL-DATENSCHUTZ")):
        if not re.search(r'<a[^>]+href=["\'][^"\']*%s' % word, html, re.I) and word not in html.lower():
            add("HOCH", cid, "Kein Link zu %s auf der Startseite gefunden" % word.capitalize(), "DE/AT/CH: Pflichtangaben prüfen")

    # 2) Host-Varianten
    variants = {"http://" + apex + "/", "http://www." + apex + "/", "https://" + apex + "/", "https://www." + apex + "/"}
    for v in sorted(variants):
        vh, _, _ = chain(v)
        if norm(vh[-1]["url"]) != canon_url and vh[-1]["status"] is not None:
            add("HOCH", "HOST-VARIANTE", "Variante landet nicht auf der kanonischen Adresse", fmt(vh))
        elif any(h["status"] in (302, 303, 307) for h in vh[:-1]):
            add("HOCH", "HOST-302", "Variante leitet temporär statt dauerhaft weiter", fmt(vh))
        elif len(vh) > 3:
            add("MITTEL", "HOST-KETTE", "Weiterleitungskette mit mehr als 2 Sprüngen", fmt(vh))
        elif vh[-1]["status"] is None:
            add("INFO", "HOST-NA", "Variante nicht erreichbar (DNS/Zertifikat?)", v)

    # 3) Alte Domains
    for old in a.alt:
        old = old.rstrip("/")
        for path in ["/"] + a.paths:
            oh, _, _ = chain(old + path)
            first = oh[0]["status"]
            target = norm(oh[-1]["url"])
            if first not in (301, 308):
                add("HOCH" if first in (302, 303, 307) else "KRITISCH", "ALT-REDIRECT", "Alte Domain leitet nicht dauerhaft weiter", fmt(oh))
            elif urllib.parse.urlsplit(target).netloc != urllib.parse.urlsplit(canon_url).netloc:
                add("HOCH", "ALT-ZIEL", "Alte Domain leitet auf falschen Host", fmt(oh))
            elif path != "/" and urllib.parse.urlsplit(target).path.rstrip("/") in ("", "/") :
                add("MITTEL", "ALT-PFAD", "Unterseite der alten Domain landet auf der Startseite (nicht pfaderhaltend)", fmt(oh))
            elif oh[-1]["status"] == 404:
                add("MITTEL", "ALT-404", "Weiterleitung endet auf 404 – Pfad-Mapping nötig", fmt(oh))

    # 4) robots.txt
    root = "%s://%s" % (urllib.parse.urlsplit(canon_url).scheme, urllib.parse.urlsplit(canon_url).netloc)
    rs, _, rb = fetch(root + "/robots.txt")
    robots = rb.decode("utf-8", "replace") if rs == 200 else ""
    sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
    if rs != 200:
        add("NIEDRIG", "ROBOTS-FEHLT", "robots.txt nicht erreichbar",
            "Status %s – ohne robots.txt darf alles gecrawlt werden; nur ein Mangel, "
            "wenn Bereiche ausgeschlossen werden sollen" % rs)
    else:
        if robots_blocks_all(robots):
            add("KRITISCH", "ROBOTS-SPERRE", "robots.txt sperrt die gesamte Website",
                "Gruppe fuer * (bzw. Googlebot) enthaelt Disallow: / ohne wirksames Allow – typischer Staging-Rest")
        if not sitemaps:
            add("NIEDRIG", "ROBOTS-SITEMAP", "Kein Sitemap-Verweis in robots.txt", "")

    # 5) Sitemap
    candidates = sitemaps or [root + p for p in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/wp-sitemap.xml")]
    urls, seen = [], set()
    queue = list(candidates)
    while queue and len(urls) < a.max_urls and len(seen) < 20:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        st, sh, sb = fetch(sm)
        if sh.get("blocked"):
            add("HOCH", "SITEMAP-FREMD", "Sitemap-Verweis zeigt nach ausserhalb der geprueften Domains",
                "%s – %s" % (sm, sh.get("error")))
            continue
        if st != 200:
            continue
        import html as _html
        locs = [_html.unescape(x) for x in
                re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sb.decode("utf-8", "replace"))]
        if b"<sitemapindex" in sb:
            queue.extend(locs)
        else:
            urls.extend(locs)
    if not urls:
        add("MITTEL", "SITEMAP-FEHLT", "Keine Sitemap mit URLs gefunden",
            "Geprueft: %s – bei kleinen Websites verzichtbar, bei groesseren ein echter Mangel"
            % ", ".join(candidates[:4]))
    bad = []
    for u in urls[: a.max_urls]:
        st, h, b = fetch(u)
        nd_u = is_noindex(b.decode("utf-8", "replace"), h)
        if st != 200:
            bad.append("%s [%s]" % (u, st))
        elif nd_u:
            bad.append("%s [noindex]" % u)
        time.sleep(0.3)
    if bad:
        add("HOCH", "SITEMAP-URLS", "%d Sitemap-URLs nicht 200/indexierbar" % len(bad), "; ".join(bad[:10]))

    # 6) Echte 404
    rnd = "/" + "".join(random.choices(string.ascii_lowercase, k=12)) + "-mt404"
    st, _, _ = fetch(root + rnd)
    if st == 200:
        add("HOCH", "SOFT-404", "Nicht existierende Seite liefert 200 (Soft-404)", root + rnd)
    elif st not in (404, 410):
        add("MITTEL", "404-STATUS", "Nicht existierende Seite liefert Status %s" % st, root + rnd)

    # 7) SSL & Header
    if urllib.parse.urlsplit(canon_url).scheme == "https":
        hostname = urllib.parse.urlsplit(canon_url).hostname
        try:
            # Auch der rohe TLS-Socket muss durch dieselbe Netzgrenze. Nicht erneut per
            # Hostname verbinden (DNS-Rebinding), sondern eine unmittelbar zuvor vom
            # zentralen Guard verifizierte IP pinnen; SNI/Zertifikatspruefung bleibt
            # auf dem urspruenglichen Hostnamen.
            ips = guard.pruefe(canon_url, ALLOWED_HOSTS or None, nur_https=True)
            ctx = ssl.create_default_context()
            letzter_fehler = None
            exp = None
            for ip in ips:
                try:
                    with socket.create_connection((str(ip), 443), timeout=10) as sock, ctx.wrap_socket(sock, server_hostname=hostname) as ss:
                        exp = datetime.strptime(ss.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    break
                except Exception as e:  # noqa - naechste verifizierte Adresse versuchen
                    letzter_fehler = e
            if exp is None:
                raise letzter_fehler or RuntimeError("keine verifizierte IP erreichbar")
            days = (exp - datetime.now(timezone.utc)).days
            if days < 14:
                add("KRITISCH" if days < 3 else "HOCH", "SSL-ABLAUF", "Zertifikat läuft in %d Tagen ab" % days, str(exp.date()))
            else:
                add("INFO", "SSL-OK", "Zertifikat gültig", "noch %d Tage" % days)
        except Exception as e:  # noqa
            add("INFO", "SSL-NA", "SSL-Prüfung nicht möglich (z. B. Proxy)", str(e)[:120])
        hl = {k.lower() for k in headers}
        if "strict-transport-security" not in hl:
            add("NIEDRIG", "HSTS", "Kein HSTS-Header", "Nach stabilem HTTPS-Betrieb ergänzen")
    else:
        add("KRITISCH", "KEIN-HTTPS", "Kanonische Adresse ist nicht HTTPS", canon_url)

    order = {"KRITISCH": 0, "HOCH": 1, "MITTEL": 2, "NIEDRIG": 3, "INFO": 4}
    checks.sort(key=lambda c: order[c["level"]])
    report = {"url": a.url, "kanonisch": canon_url, "datum": datetime.now().isoformat(timespec="seconds"),
              "sitemap_urls_geprueft": min(len(urls), a.max_urls), "checks": checks}
    import os, tempfile
    if os.path.exists(a.out):
        sys.exit("FEHLER: %s existiert bereits. Anderen Namen mit --out waehlen." % a.out)
    _d = os.path.dirname(os.path.abspath(a.out)) or "."
    _fd, _tmp = tempfile.mkstemp(dir=_d, suffix=".part")
    with os.fdopen(_fd, "w", encoding="utf-8") as _f:
        json.dump(report, _f, ensure_ascii=False, indent=2)
    os.replace(_tmp, a.out)
    print("Kanonisch: %s | Sitemap-URLs geprüft: %d | Bericht: %s" % (canon_url, report["sitemap_urls_geprueft"], a.out))
    for c in checks:
        print("%-8s %-18s %s%s" % (c["level"], c["id"], c["titel"], (" – " + c["detail"]) if c["detail"] else ""))
    sys.exit(1 if any(c["level"] == "KRITISCH" for c in checks) else 0)


if __name__ == "__main__":
    main()
