#!/usr/bin/env python3
"""Fail closed if shipped GTM reference/master assets contain live-looking customer values or unsafe defaults."""
from __future__ import annotations
import argparse, copy, json, re, sys
from pathlib import Path

META_REAL_TOKEN = re.compile(r"\bEAA[A-Za-z0-9]{40,}\b")
LIVE_GTM_ID = re.compile(r"\bGTM-(?!REFERENCE\b)[A-Z0-9]{5,}\b")
LIVE_GA4_ID = re.compile(r"\bG-[A-Z0-9]{6,}\b")
PLACEHOLDER = re.compile(r"^__[A-Z0-9_]+__$")
CUSTOMER_URL_KEYS = {"taggingServerUrls"}


def pval(obj, key):
    return next((p.get("value") for p in obj.get("parameter", []) if p.get("key") == key), None)


def _without_template_code(data):
    out = copy.deepcopy(data)
    cv = out.get("containerVersion") if isinstance(out, dict) else None
    if isinstance(cv, dict):
        for t in cv.get("customTemplate", []) or []:
            if "templateData" in t:
                t["templateData"] = "__OPAQUE_TEMPLATE_SOURCE__"
    return out


def _is_safe_reference_url(value):
    if not isinstance(value, str):
        return True
    if value.startswith("{{") or PLACEHOLDER.fullmatch(value):
        return True
    return value.startswith("https://sgtm.example.invalid") or value.startswith("https://tagmanager.google.com/")


def check_file(path):
    problems = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ["invalid JSON: %s" % e]
    if not isinstance(data, dict):
        return problems
    cv = data.get("containerVersion")
    safe_raw = json.dumps(_without_template_code(data), ensure_ascii=False)
    if META_REAL_TOKEN.search(safe_raw):
        problems.append("real-looking Meta access token outside opaque template source")
    for m in LIVE_GTM_ID.findall(safe_raw):
        problems.append("live-looking GTM public ID: %s" % m)
    for m in LIVE_GA4_ID.findall(safe_raw):
        problems.append("live-looking GA4 measurement ID: %s" % m)

    if cv:
        cont = cv.get("container") or {}
        if cont.get("accountId") not in (None, "__REFERENCE_ACCOUNT_ID__"):
            problems.append("container accountId not sanitized")
        if cont.get("containerId") not in (None, "__REFERENCE_CONTAINER_ID__"):
            problems.append("container containerId not sanitized")
        for u in cont.get("taggingServerUrls", []) or []:
            if not _is_safe_reference_url(u):
                problems.append("customer taggingServerUrl not sanitized")
        for v in cv.get("variable", []) or []:
            if v.get("type") != "c":
                continue
            name = str(v.get("name", "")); value = str(pval(v, "value") or "")
            if re.search(r"token|secret|password|credential|pixel|measurement|mess-id|mess id", name, re.I) and not PLACEHOLDER.fullmatch(value):
                problems.append("sensitive/id constant not placeholder: %s" % name)
            if META_REAL_TOKEN.search(value):
                problems.append("real-looking Meta token in constant: %s" % name)
        for t in cv.get("tag", []) or []:
            if t.get("type") == "sgtmadsct":
                for key in ("conversionId", "conversionLabel", "currencyCode"):
                    val = str(pval(t, key) or "")
                    if val and not PLACEHOLDER.fullmatch(val):
                        problems.append("server Ads %s not placeholder in %s" % (key, t.get("name")))
            # Customer transport URLs may occur in nested tag settings.
            def walk(x):
                if isinstance(x, dict):
                    if x.get("key") in {"parameterValue", "value"} and isinstance(x.get("value"), str):
                        val = x["value"]
                        if val.startswith(("http://", "https://")) and not _is_safe_reference_url(val):
                            problems.append("customer/live URL in tag parameter: %s" % t.get("name"))
                    for vv in x.values():
                        walk(vv)
                elif isinstance(x, list):
                    for vv in x:
                        walk(vv)
            walk(t.get("parameter") or [])
        if data.get("_meixnerMaster", {}).get("status") == "candidate_reference_only" and data.get("_meixnerMaster", {}).get("verified") is not False:
            problems.append("candidate core must explicitly remain unverified")
        ref = data.get("_meixnerReference")
        if "production-reference" in path.parts and path.name.endswith(".sanitized.json"):
            if not isinstance(ref, dict) or ref.get("sanitized") is not True:
                problems.append("sanitized reference marker missing")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1] / "masters"))
    a = ap.parse_args()
    root = Path(a.root); problems = []
    files = sorted(root.rglob("*.json"))
    for p in files:
        for problem in check_file(p):
            problems.append("%s: %s" % (p.relative_to(root), problem))
    required = [
        root / "REFERENCE-POLICY.md",
        root / "production-reference/web-reference.sanitized.json",
        root / "production-reference/server-reference.sanitized.json",
        root / "core/web-core.candidate.json",
        root / "core/server-core.candidate.json",
        root / "patterns/event-patterns.json",
    ]
    for p in required:
        if not p.exists():
            problems.append("required asset missing: %s" % p)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}, ensure_ascii=False, indent=2))
        sys.exit(2)
    print(json.dumps({"ok": True, "checked_json": len(files)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
