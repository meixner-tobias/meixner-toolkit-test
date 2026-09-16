#!/usr/bin/env python3
"""Prüft die Umgebung für meixner-toolkit und legt bei Bedarf die Konfiguration an.

  python3 doctor.py            # Prüfen
  python3 doctor.py --init     # Konfigurationsordner + config.json aus Vorlage anlegen (überschreibt nichts)
  python3 doctor.py --online   # zusätzlich PSI-API und Playwright-Start testen
Konfigurationsordner: $MEIXNER_TOOLKIT_HOME oder ~/.meixner-toolkit
"""
import json, os, re, shutil, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ.get("MEIXNER_TOOLKIT_HOME", Path.home() / ".meixner-toolkit"))
PW_FALLBACK = Path.home() / ".cache" / "mt-playwright"
# ---- Einzige Quelle der Wahrheit fuer Mindestversionen (README verweist hierauf) ----
MIN_NODE = (20, 0)          # aktive LTS-Linie; identisch mit engines.node in package.json
MIN_PYTHON = (3, 10)
PLAYWRIGHT_VERSION = "1.56.1"



def playwright_roots(env=None):
    """Kontrollierte Suchorte fuer Playwright, in Prioritaetsreihenfolge.

    Claude Code installiert Plugin-Abhaengigkeiten im Plugin-Verzeichnis; daneben
    bleibt der explizite MT_PLAYWRIGHT_DIR/fallback fuer manuelle Installationen.
    """
    env = os.environ if env is None else env
    kandidaten = [env.get("MT_PLAYWRIGHT_DIR"), env.get("CLAUDE_PLUGIN_ROOT"),
                  str(HERE.parents[2]), str(PW_FALLBACK)]
    out = []
    for x in kandidaten:
        if not x:
            continue
        p = Path(x).expanduser()
        if p not in out:
            out.append(p)
    return out


def find_playwright_root(env=None):
    for root in playwright_roots(env):
        if (root / "node_modules" / "playwright" / "package.json").is_file():
            return root
    return None

def parse_node_version(text):
    """'v20.11.1' -> (20, 11, 1). Gibt None zurueck, wenn nichts Sinnvolles drinsteht."""
    m = re.search(r"v?(\d+)\.(\d+)\.(\d+)", str(text or ""))
    return tuple(int(x) for x in m.groups()) if m else None


def parse_python_version(text):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", str(text or ""))
    return tuple(int(x) for x in m.groups()) if m else None


def version_ok(gefunden, minimum):
    """True, wenn gefunden >= minimum. None (= nicht ermittelbar) ist nie ok."""
    if gefunden is None:
        return False
    return tuple(gefunden[:len(minimum)]) >= tuple(minimum)


def parse_siteone_version(text):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", str(text or ""))
    return ".".join(m.groups()) if m else None  # festgeschrieben, siehe package.json im Plugin-Wurzelverzeichnis
rows = []


def add(status, check, detail="", fix=""):
    rows.append((status, check, detail, fix))


def run(cmd, cwd=None, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:  # noqa
        return 1, str(e)


def main():
    init, online = "--init" in sys.argv, "--online" in sys.argv

    if init:
        for d in (HOME, HOME / "kunden", HOME / "master", HOME / "audits"):
            d.mkdir(parents=True, exist_ok=True, mode=0o700)
            if os.name != "nt":
                try: d.chmod(0o700)
                except OSError: pass
        if not (HOME / "config.json").exists():
            ziel = HOME / "config.json"
            shutil.copy(HERE.parent / "examples" / "config.json", ziel)
            if os.name != "nt":
                try: ziel.chmod(0o600)
                except OSError: pass
            print("Angelegt:", ziel)

    # Konfiguration
    cfg_path = HOME / "config.json"
    if not cfg_path.exists():
        add("❌", "Konfiguration", str(cfg_path) + " fehlt", "python3 doctor.py --init, danach /setup Branding abfragen lassen")
        cfg = {}
    else:
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            b = cfg.get("branding", {})
            missing = [k for k in ("name", "website", "email") if not b.get(k)]
            add("⚠️" if missing else "✅", "Konfiguration", str(cfg_path) + (" – fehlt: " + ", ".join(missing) if missing else ""),
                "Werte in config.json ergänzen" if missing else "")
            if not b.get("farbe"):
                add("⚠️", "Branding-Farbe", "nicht gesetzt → Bericht nutzt neutrales Dunkelgrau", "branding.farbe als Hex setzen, z. B. aus der eigenen Website")
        except json.JSONDecodeError as e:
            add("❌", "Konfiguration", "ungültiges JSON: %s" % e, "config.json reparieren")
            cfg = {}

    kunden = sorted((HOME / "kunden").glob("*.json")) if (HOME / "kunden").exists() else []
    add("✅" if kunden else "⚠️", "Kundenliste", "%d Kunden in %s" % (len(kunden), HOME / "kunden"),
        "" if kunden else "Kunden werden beim ersten Audit automatisch angelegt")
    for k in kunden:
        try:
            json.loads(k.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            add("❌", "Kunde " + k.name, "ungültiges JSON", "Datei reparieren")

    # Master-Container + echte GTM-Roundtrip-Manifeste
    import hashlib
    def _sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    for typ in ("web", "server"):
        mc = cfg.get("master_container") or {}
        raw = mc.get(typ)
        manifest_raw = mc.get(typ + "_manifest")
        if not raw:
            add("⚠️", "Master-Container " + typ, "nicht hinterlegt", "GTM-Export in ~/.meixner-toolkit/master ablegen; Pfad in config.json → master_container.%s" % typ)
            continue
        mp = Path(os.path.expanduser(raw))
        try:
            usage = json.loads(mp.read_text(encoding="utf-8"))["containerVersion"]["container"].get("usageContext")
            erwartet = "WEB" if typ == "web" else "SERVER"
            if erwartet not in (usage or []):
                add("❌", "Master-Container " + typ, "%s enthaelt %s, erwartet wurde %s" % (mp, usage, erwartet), "Pfad web/server pruefen")
                continue
            if not manifest_raw:
                add("⚠️", "Master-Container " + typ, "%s – Candidate, kein GTM-Roundtrip-Manifest" % mp, "Importieren, re-exportieren, gtm_master_verify.py ausfuehren und Manifest hinterlegen")
                continue
            manp = Path(os.path.expanduser(manifest_raw))
            man = json.loads(manp.read_text(encoding="utf-8"))
            hashes = {man.get("candidate_sha256"), man.get("roundtrip_sha256")}
            ok = man.get("status") == "verified_by_gtm_import_roundtrip" and man.get("container_type") == typ and _sha256(mp) in hashes
            add("✅" if ok else "❌", "Master-Container " + typ, "%s – %s" % (mp, "GTM-Roundtrip verifiziert" if ok else "Manifest passt nicht"), "" if ok else "Manifest/Hash/Typ mit gtm_master_verify.py neu pruefen")
        except Exception as e:  # noqa
            add("❌", "Master-Container " + typ, "%s: %s" % (mp, e), "Pfad/Datei/Manifest pruefen")

    # PageSpeed-Key
    key = os.environ.get("PSI_API_KEY")
    if not key:
        add("⚠️", "PSI_API_KEY", "nicht gesetzt → /seogeo ohne Performance-Messung",
            'In ~/.claude/settings.json: {"env": {"PSI_API_KEY": "…"}} und Claude Code neu starten')
    elif online:
        # Key als kodierter Parameter, nie per Stringverkettung. Die vollstaendige URL
        # wird nirgends ausgegeben - sie enthaelt den Schluessel.
        import urllib.parse
        qs = urllib.parse.urlencode({"url": "https://example.com", "key": key, "category": "performance"})
        url = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed?" + qs
        add("ℹ️", "PageSpeed-Testabfrage", "1 Abruf gegen die Google-API. Google protokolliert "
            "den Aufruf. Das tatsaechliche Kontingent haengt am Google-Cloud-Projekt und ist "
            "dort unter APIs & Dienste > Kontingente einzusehen.")
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                add("✅" if r.status == 200 else "❌", "PSI_API_KEY", "Testabfrage HTTP %d" % r.status)
        except urllib.error.HTTPError as e:
            hinweis = {403: "API im Cloud-Projekt nicht aktiviert oder Key zu eng eingeschraenkt",
                       400: "Key ungueltig"}.get(e.code, "")
            add("❌", "PSI_API_KEY", "Testabfrage HTTP %d" % e.code, hinweis)
        except Exception as e:
            add("❌", "PSI_API_KEY", "Testabfrage fehlgeschlagen: %s" % str(e)[:60].replace(key, "<key>"))

    # ---- Laufzeiten: Version pruefen, nicht blosse Anwesenheit ----
    code, out = run(["node", "-v"])
    nv = parse_node_version(out) if code == 0 else None
    if nv is None:
        add("❌", "Node.js", "nicht gefunden oder Version nicht lesbar",
            "Node %d.%d+ installieren (nodejs.org)" % MIN_NODE)
    else:
        add("✅" if version_ok(nv, MIN_NODE) else "❌", "Node.js",
            "v%d.%d.%d" % nv,
            "" if version_ok(nv, MIN_NODE) else "Mindestens Node %d.%d noetig" % MIN_NODE)

    pv = sys.version_info[:3]
    add("✅" if version_ok(pv, MIN_PYTHON) else "❌", "Python", "%d.%d.%d" % pv,
        "" if version_ok(pv, MIN_PYTHON) else "Mindestens Python %d.%d noetig" % MIN_PYTHON)

    pw_root = find_playwright_root()
    # Vier getrennte Aussagen statt einer vermischten:
    # 1 Paket da, 2 Version passend, 3/4 Chromium vorhanden und startbar.
    if pw_root:
        add("✅", "Playwright-Paket", "gefunden in %s" % pw_root)
        code, out = run(["node", "-e",
                         "console.log(require('playwright/package.json').version)"], cwd=pw_root)
        gefunden = (out or "").strip() if code == 0 else None
        if gefunden == PLAYWRIGHT_VERSION:
            add("✅", "Playwright-Version", gefunden)
        elif gefunden:
            add("⚠️", "Playwright-Version", "%s gefunden, festgeschrieben ist %s"
                % (gefunden, PLAYWRIGHT_VERSION), "npm i playwright@%s" % PLAYWRIGHT_VERSION)
        else:
            add("⚠️", "Playwright-Version", "nicht ermittelbar")
    else:
        gesucht = ", ".join(str(x) for x in playwright_roots())
        add("❌", "Playwright-Paket", "nicht gefunden; geprueft: %s" % gesucht,
            "Im Plugin-Ordner npm ci && npx playwright install chromium ausfuehren "
            "oder MT_PLAYWRIGHT_DIR auf eine kontrollierte Installation setzen")

    if pw_root and online:
        code, out = run(["node", "-e", "require('playwright').chromium.launch().then(b=>b.close()).then(()=>console.log('ok'))"], cwd=pw_root, timeout=90)
        add("✅" if code == 0 and "ok" in out else "❌", "Playwright + Chromium", "Start OK" if code == 0 and "ok" in out else out[-200:],
            "" if code == 0 and "ok" in out else "cd %s && npx playwright install chromium" % pw_root)
    elif pw_root:
        add("⚠️", "Playwright + Chromium", "Paket vorhanden; Browserstart nur mit --online verifiziert",
            "python3 doctor.py --online fuer echten Chromium-Start")

    w = max(len(r[1]) for r in rows)
    for s, c, d, f in rows:
        print("%s  %-*s  %s" % (s, w, c, d))
        if f:
            print("   %s→ %s" % (" " * w, f))
    sys.exit(1 if any(r[0] == "❌" for r in rows) else 0)


if __name__ == "__main__":
    main()
