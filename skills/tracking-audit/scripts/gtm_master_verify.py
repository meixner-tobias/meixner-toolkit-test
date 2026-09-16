#!/usr/bin/env python3
"""Verifiziert einen GTM-Master durch echten Import->Re-Export-Roundtrip.

Ein Master gilt im Toolkit erst dann als VERIFIED, wenn Google Tag Manager ihn importiert
hat und der danach exportierte Workspace semantisch dieselben Komponenten enthaelt.
Das Skript ersetzt keinen GTM-Import und behauptet ohne Re-Export keinen Erfolg.
"""
import argparse, copy, datetime, hashlib, json, re, sys
from pathlib import Path

DYNAMIC_KEYS = {"accountId", "containerId", "containerVersionId", "fingerprint", "path", "tagManagerUrl"}
COLLECTIONS = ("tag", "trigger", "variable", "client", "transformation", "customTemplate", "folder", "builtInVariable")
CVT = re.compile(r"^cvt_[0-9]+_([0-9]+)$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_export(path, expected=None):
    data = json.load(open(path, encoding="utf-8"))
    cv = data.get("containerVersion")
    if not isinstance(cv, dict):
        raise ValueError("containerVersion fehlt")
    usage = (cv.get("container") or {}).get("usageContext") or []
    typ = "server" if "SERVER" in usage else "web" if "WEB" in usage else "unknown"
    if expected and typ != expected:
        raise ValueError("Container-Typ ist %s, erwartet %s" % (typ, expected))
    return data, cv, typ


def _canon(value):
    if isinstance(value, dict):
        return {k: _canon(v) for k, v in sorted(value.items()) if k not in DYNAMIC_KEYS and k not in {"exportTime"}}
    if isinstance(value, list):
        vals = [_canon(v) for v in value]
        if all(isinstance(v, dict) for v in vals):
            def key(v):
                return (str(v.get("key", "")), str(v.get("name", "")), str(v.get("type", "")), json.dumps(v, sort_keys=True, ensure_ascii=False))
            return sorted(vals, key=key)
        return vals
    return value


def snapshot(data):
    cv = data["containerVersion"]
    trigger_names = {str(t.get("triggerId")): t.get("name") for t in cv.get("trigger", []) if t.get("triggerId") is not None}
    custom_by_id = {str(t.get("templateId")): t.get("name") for t in cv.get("customTemplate", []) if t.get("templateId") is not None}

    def norm_type(t):
        if not isinstance(t, str): return t
        m = CVT.match(t)
        if m and m.group(1) in custom_by_id:
            return "cvt:" + str(custom_by_id[m.group(1)])
        return t

    out = {"usageContext": (cv.get("container") or {}).get("usageContext") or []}
    for coll in COLLECTIONS:
        rows = []
        for raw in cv.get(coll, []) or []:
            item = copy.deepcopy(raw)
            for k in list(item):
                if k in DYNAMIC_KEYS or k.endswith("Id") and k in {"tagId", "triggerId", "variableId", "clientId", "transformationId", "templateId", "folderId"}:
                    item.pop(k, None)
            if coll == "tag":
                item["type"] = norm_type(item.get("type"))
                for key in ("firingTriggerId", "blockingTriggerId"):
                    if key in item:
                        item[key] = sorted(trigger_names.get(str(x), "builtin:" + str(x)) for x in item.get(key, []))
            rows.append(_canon(item))
        rows.sort(key=lambda x: (str(x.get("name", "")), str(x.get("type", "")), json.dumps(x, sort_keys=True, ensure_ascii=False)))
        out[coll] = rows
    return _canon(out)


def diff(a, b):
    diffs = []
    if a.get("usageContext") != b.get("usageContext"):
        diffs.append("usageContext unterscheidet sich")
    for coll in COLLECTIONS:
        aa, bb = a.get(coll, []), b.get(coll, [])
        if aa != bb:
            names_a = [x.get("name", x.get("type", "?")) for x in aa]
            names_b = [x.get("name", x.get("type", "?")) for x in bb]
            if names_a != names_b:
                diffs.append("%s: Komponenten unterscheiden sich (vorher=%s, nachher=%s)" % (coll, names_a, names_b))
            else:
                diffs.append("%s: gleich benannte Komponenten haben unterschiedliche Konfiguration" % coll)
    return diffs


def verify(candidate, roundtrip, expected):
    cdata, _, ctype = load_export(candidate, expected)
    rdata, _, rtype = load_export(roundtrip, expected)
    cs, rs = snapshot(cdata), snapshot(rdata)
    problems = diff(cs, rs)
    return problems, ctype, cs



def write_manifest_exclusive(path, manifest):
    """Write a verified manifest without following or overwriting an existing path/symlink."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out, "x", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write("\n")
        try:
            out.chmod(0o600)
        except OSError:
            pass
    except FileExistsError:
        raise FileExistsError("%s existiert bereits" % out)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", help="JSON, das in GTM importiert wurde")
    ap.add_argument("roundtrip", help="direkt danach aus demselben GTM-Workspace exportiertes JSON")
    ap.add_argument("--type", required=True, choices=["web", "server"])
    ap.add_argument("--out", required=True, help="Verified-Manifest")
    ap.add_argument("--name", required=True, help="stabiler Master-Name")
    ap.add_argument("--notes", default="")
    a = ap.parse_args()
    try:
        problems, typ, snap = verify(a.candidate, a.roundtrip, a.type)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        sys.exit("ABBRUCH: %s" % e)
    if problems:
        print("NICHT VERIFIZIERT:", file=sys.stderr)
        for p in problems: print("- " + p, file=sys.stderr)
        sys.exit(2)
    manifest = {
        "schema": 1,
        "status": "verified_by_gtm_import_roundtrip",
        "name": a.name,
        "container_type": typ,
        "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate_sha256": sha256(a.candidate),
        "roundtrip_sha256": sha256(a.roundtrip),
        "component_counts": {k: len(snap.get(k, [])) for k in COLLECTIONS},
        "notes": a.notes,
        "verification": "Manueller GTM-Import + Re-Export; semantischer Vergleich ohne umgebungsspezifische IDs/Fingerprints."
    }
    try:
        out = write_manifest_exclusive(a.out, manifest)
    except FileExistsError as e:
        sys.exit("ABBRUCH: %s" % e)
    print("VERIFIED: %s -> %s" % (a.name, out))


if __name__ == "__main__":
    main()
