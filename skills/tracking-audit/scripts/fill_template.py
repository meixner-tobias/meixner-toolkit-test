#!/usr/bin/env python3
"""Befüllt einen exportierten Master-Container (Web ODER Server) mit kundenspezifischen Werten.

Idee: Du baust dein Standard-Setup (z. B. Server-Container mit GA4-Client, Stape-Meta-CAPI-Tag,
Google-Ads-Tags, Cookie-Keeper-Einstellungen) einmal sauber in GTM, exportierst es und legst es ab.
Pro Kunde werden nur die Konstanten (Variablen vom Typ "Konstante") ersetzt.

  Konstanten anzeigen:  python3 fill_template.py master.json --list
                        (zeigt nur Namen; Werte nur mit --show-value NAME, nie fuer Geheimnisse)
  Befüllen:             python3 fill_template.py master.json values.json -o kunde-import.json

values.json = {"C - GA4 Measurement ID": "G-ABC123", "C - Meta Pixel ID": "123", ...}
Nur Standardbibliothek.
"""
import argparse, json, os, sys, datetime, tempfile, hashlib

SECRET_HINTS = ("token", "secret", "key", "password", "passwort", "credential",
                "access", "api", "auth", "bearer", "signature")
PLACEHOLDER_HINTS = ("XXXX", "YYYY", "YOUR ", "REPLACE", "TODO", "PLATZHALTER", "<", "CHANGEME")
PLACEHOLDER_RE = __import__("re").compile(r"^__[A-Z0-9_]+__$")


def is_secret(name):
    n = name.lower()
    return any(h in n for h in SECRET_HINTS)


def looks_like_placeholder(val):
    text = str(val).strip()
    return bool(PLACEHOLDER_RE.fullmatch(text)) or any(h in text.upper() for h in PLACEHOLDER_HINTS)


def write_atomic(path, data):
    """Schreibt ohne bestehende Datei zu zerstoeren, falls der Lauf abbricht."""
    if os.path.exists(path):
        sys.exit("FEHLER: %s existiert bereits. Anderen Namen mit -o waehlen "
                 "oder die Datei vorher selbst verschieben." % path)
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.path.exists(tmp) and os.unlink(tmp)
        raise


def consts(cv):
    for v in cv.get("variable", []):
        if v.get("type") == "c":
            val = next((p.get("value") for p in v.get("parameter", []) if p.get("key") == "value"), "")
            yield v, val


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("master")
    ap.add_argument("values", nargs="?")
    ap.add_argument("-o", "--out", default="gtm-import.json")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--erwarteter-typ", choices=["web", "server"],
                    help="bricht ab, wenn der Master nicht diesen usageContext hat")
    ap.add_argument("--show-value", action="append", default=[],
                    help="Wert EINER Konstante anzeigen (nicht moeglich bei Token/Key/Secret/Password)")
    ap.add_argument("--allow-inherited", action="store_true",
                    help="bestehende Werte nicht ersetzter Konstanten bewusst uebernehmen")
    ap.add_argument("--name", help="neuer Containername im Import (optional)")
    ap.add_argument("--verified-manifest", help="Manifest aus gtm_master_verify.py; Hash und Typ muessen zum Master passen")
    ap.add_argument("--candidate-only", action="store_true", help="nur zum erstmaligen GTM-Importkandidaten; erlaubt Server-Master ohne Verified-Manifest")
    a = ap.parse_args()

    def _sha(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    manifest = None
    if a.verified_manifest:
        manifest = json.load(open(a.verified_manifest, encoding="utf-8"))
        if manifest.get("status") != "verified_by_gtm_import_roundtrip":
            sys.exit("ABBRUCH: Verified-Manifest hat keinen gueltigen Status.")
        if manifest.get("candidate_sha256") != _sha(a.master) and manifest.get("roundtrip_sha256") != _sha(a.master):
            sys.exit("ABBRUCH: Verified-Manifest gehoert nicht zu diesem Master (SHA-256 abweichend).")

    export = json.load(open(a.master, encoding="utf-8"))
    cv = export.get("containerVersion") or sys.exit("Keine GTM-Exportdatei (containerVersion fehlt).")
    usage = (cv.get("container") or {}).get("usageContext")
    actual_type = "server" if "SERVER" in (usage or []) else "web" if "WEB" in (usage or []) else "unknown"
    if a.erwarteter_typ and actual_type != a.erwarteter_typ:
        sys.exit("ABBRUCH: Master ist Typ %s, erwartet %s." % (actual_type, a.erwarteter_typ))
    if manifest and manifest.get("container_type") != actual_type:
        sys.exit("ABBRUCH: Verified-Manifest-Typ passt nicht zum Master.")
    marker = export.get("_meixnerMaster") if isinstance(export, dict) else None
    if isinstance(marker, dict) and marker.get("status") == "candidate_reference_only" and not manifest and not a.candidate_only and not (a.list or not a.values):
        sys.exit("ABBRUCH: Dieser mitgelieferte Core-Master ist nur candidate_reference_only. "
                 "Fuer den Bootstrap bewusst --candidate-only verwenden; fuer Wiederverwendung zuerst echten GTM Import->Re-Export und Verified-Manifest erzeugen.")
    if actual_type == "server" and not manifest and not a.candidate_only and not (a.list or not a.values):
        sys.exit("ABBRUCH: Server-Master braucht ein Verified-Manifest aus echtem GTM Import->Re-Export. "
                 "Fuer den allerersten Importkandidaten bewusst --candidate-only verwenden.")

    # Der Master ist eine Datei, die niemand validiert. Ein manipuliertes Custom-HTML-Tag
    # darin wanderte bisher unbesehen in den Kundencontainer. Der Scan laeuft immer,
    # also auch bei --list - sonst sieht ihn niemand vor dem Befuellen.
    verdaechtig = []
    for t in cv.get("tag", []):
        if t.get("type") != "html":
            continue
        code = next((pp.get("value", "") for pp in t.get("parameter", []) if pp.get("key") == "html"), "")
        for muster in ("eval(", "atob(", "document.write", "innerHTML", "fromCharCode",
                       "XMLHttpRequest", "fetch(", "new Function", "<iframe"):
            if muster in code:
                verdaechtig.append("%s: %s" % (t.get("name", "?"), muster))
    if verdaechtig:
        print("WARNUNG: Custom-HTML im Master enthaelt auffaellige Muster. Vor dem Import pruefen:",
              file=sys.stderr)
        for v in verdaechtig[:12]:
            print("  - " + v, file=sys.stderr)

    if a.list or not a.values:
        print("Container-Typ:", usage)
        for v, val in consts(cv):
            name = v["name"]
            if name in a.show_value and is_secret(name):
                shown = "<gesperrt: Name deutet auf ein Geheimnis hin>"
            elif name in a.show_value:
                shown = repr(val)
            elif is_secret(name):
                shown = "<redigiert>"
            elif looks_like_placeholder(val):
                shown = "<Platzhalter>"
            else:
                shown = "<gesetzt>" if str(val).strip() else "<leer>"
            print("  %-45s %s" % (name, shown))
        print("\nWerte werden nicht angezeigt. Einzelwert: --show-value \"<Name>\" "
              "(bei Token/Key/Secret/Password gesperrt).")
        return

    values = json.load(open(a.values, encoding="utf-8"))
    all_names = [v["name"] for v, _ in consts(cv)]
    found = set()
    for v, _ in consts(cv):
        if v["name"] in values:
            for p in v["parameter"]:
                if p.get("key") == "value":
                    p["value"] = str(values[v["name"]])
            found.add(v["name"])
    missing = set(values) - found
    if missing:
        sys.exit("FEHLER: Diese Konstanten gibt es im Master nicht: %s" % sorted(missing))

    # Nicht ersetzte Konstanten: Werte des Vorkunden wuerden sonst stillschweigend mitwandern.
    inherited = [n for n in all_names if n not in values]
    inherited_secret = [n for n in inherited if is_secret(n)]
    if inherited_secret:
        sys.exit("ABBRUCH: Diese Konstanten sehen nach Geheimnissen aus und wurden nicht "
                 "ersetzt: %s\nJeden Wert in values.json setzen - ein uebernommenes Token "
                 "gehoert zum vorherigen Konto." % sorted(inherited_secret))
    if inherited and not a.allow_inherited:
        sys.exit("ABBRUCH: Nicht ersetzte Konstanten: %s\nEntweder in values.json aufnehmen "
                 "oder bewusst mit --allow-inherited uebernehmen." % sorted(inherited))

    # Umgebungsspezifische Felder entfernen – GTM vergibt sie beim Import neu
    for key in ("fingerprint", "tagManagerUrl", "path"):
        cv.pop(key, None)
    for coll in ("tag", "trigger", "variable", "folder", "client", "customTemplate", "builtInVariable", "transformation"):
        for item in cv.get(coll, []):
            for key in ("fingerprint", "path", "tagManagerUrl"):
                item.pop(key, None)
    if a.name:
        cv.setdefault("container", {})["name"] = a.name
    export["exportTime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    leftovers = [v["name"] for v, val in consts(cv) if looks_like_placeholder(val)]
    if leftovers:
        sys.exit("ABBRUCH: Noch Platzhalter in: %s\nEs wurde nichts geschrieben." % ", ".join(leftovers))
    write_atomic(a.out, export)
    print("OK: %s (%s) – %d Konstanten ersetzt" % (a.out, usage, len(found)))
    if inherited:
        print("HINWEIS: bewusst uebernommen (--allow-inherited):", ", ".join(inherited))


if __name__ == "__main__":
    main()
