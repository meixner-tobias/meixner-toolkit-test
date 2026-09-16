#!/usr/bin/env python3
"""Sanitize a real GTM export for architecture-reference use.

The output preserves GTM component *shape* but removes account/container metadata,
customer domains, advertising/analytics identifiers, credentials and site-specific
trigger operands. It is intentionally a reference, not a VERIFIED master.
"""
from __future__ import annotations
import argparse, copy, json, re, sys
from pathlib import Path

META_KEYS = {"accountId", "containerId", "containerVersionId", "fingerprint", "path", "tagManagerUrl"}
SECRET_NAME = re.compile(r"(token|secret|password|credential|api\s*key|access\s*key)", re.I)
META_TOKEN = re.compile(r"\bEAA[A-Za-z0-9]{40,}\b")
GTM_PUBLIC = re.compile(r"\bGTM-[A-Z0-9]{5,}\b")
GA4_PUBLIC = re.compile(r"\bG-[A-Z0-9]{6,}\b")
PLACEHOLDER = re.compile(r"^__[A-Z0-9_]+__$")


def slug(value: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", value or "ITEM").strip("_").upper()
    return s[:48] or "ITEM"


def param_value(params, key):
    for p in params or []:
        if p.get("key") == key:
            return p.get("value")
    return None


def set_param(params, key, value):
    for p in params or []:
        if p.get("key") == key:
            p["value"] = value


def scrub_metadata(obj):
    if isinstance(obj, dict):
        for k in list(obj):
            if k in META_KEYS:
                if k == "accountId": obj[k] = "__REFERENCE_ACCOUNT_ID__"
                elif k == "containerId": obj[k] = "__REFERENCE_CONTAINER_ID__"
                elif k == "containerVersionId": obj[k] = "0"
                elif k == "fingerprint": obj[k] = "0"
                elif k == "path": obj[k] = "__REFERENCE_GTM_PATH__"
                elif k == "tagManagerUrl": obj[k] = "https://tagmanager.google.com/"
            else:
                scrub_metadata(obj[k])
    elif isinstance(obj, list):
        for x in obj:
            scrub_metadata(x)


def _walk_params_replace_urls(obj):
    """Replace customer transport URLs in tag parameters; leave GTM macros untouched."""
    if isinstance(obj, dict):
        if obj.get("key") in {"parameterValue", "value"} and isinstance(obj.get("value"), str):
            val = obj["value"].strip()
            if val.startswith(("http://", "https://")) and "tagmanager.google.com" not in val:
                obj["value"] = "https://sgtm.example.invalid"
        for v in obj.values():
            _walk_params_replace_urls(v)
    elif isinstance(obj, list):
        for v in obj:
            _walk_params_replace_urls(v)


def _scrub_form_ids(obj):
    if isinstance(obj, dict):
        mp = obj.get("map")
        if isinstance(mp, list):
            pv = next((p for p in mp if p.get("key") == "parameter"), None)
            vv = next((p for p in mp if p.get("key") == "parameterValue"), None)
            if pv and vv and pv.get("value") == "form_id":
                vv["value"] = "__FORM_ID__"
        for v in obj.values():
            _scrub_form_ids(v)
    elif isinstance(obj, list):
        for v in obj:
            _scrub_form_ids(v)


def _sanitize_constant(variable):
    name = str(variable.get("name", ""))
    if variable.get("type") != "c":
        return
    low = name.casefold()
    replacement = None
    if "meta" in low and "pixel" in low:
        replacement = "__META_PIXEL_ID__"
    elif "meta" in low and SECRET_NAME.search(name):
        replacement = "__META_CAPI_ACCESS_TOKEN__"
    elif "meta" in low and "test" in low:
        replacement = "__META_TEST_EVENT_CODE__"
    elif "google" in low and ("mess" in low or "measurement" in low or "ga4" in low):
        replacement = "__GA4_MEASUREMENT_ID__"
    elif SECRET_NAME.search(name):
        replacement = "__SECRET_VALUE__"
    if replacement:
        set_param(variable.get("parameter"), "value", replacement)


def sanitize(export):
    out = copy.deepcopy(export)
    cv = out.get("containerVersion")
    if not isinstance(cv, dict):
        raise ValueError("containerVersion fehlt")
    usage = (cv.get("container") or {}).get("usageContext") or []
    ctype = "server" if "SERVER" in usage else "web" if "WEB" in usage else None
    if not ctype:
        raise ValueError("WEB/SERVER usageContext fehlt")

    scrub_metadata(out)
    out["exportTime"] = "SANITIZED_REFERENCE"
    out["_meixnerReference"] = {
        "schema": 1,
        "sanitized": True,
        "type": ctype,
        "purpose": "architecture_reference_only"
    }
    container = cv.setdefault("container", {})
    container["name"] = "Production Reference || " + ctype.title()
    container["publicId"] = "GTM-REFERENCE-" + ctype.upper()
    container["tagIds"] = ["GTM-REFERENCE-" + ctype.upper()]
    if "taggingServerUrls" in container or ctype == "server":
        container["taggingServerUrls"] = ["https://sgtm.example.invalid"]

    for v in cv.get("variable", []) or []:
        _sanitize_constant(v)
        # Data-layer variable definitions are structural; their display names can expose customer semantics.
        if v.get("type") == "v" and str(v.get("name", "")).strip():
            v["name"] = "DLV - Reference Value"

    # Tags: preserve type/configuration shape, neutralize customer values/names.
    for idx, t in enumerate(cv.get("tag", []) or [], 1):
        params = t.get("parameter") or []
        typ = t.get("type")
        if typ == "sgtmadsct":
            set_param(params, "conversionId", "__GOOGLE_ADS_CONVERSION_ID__")
            set_param(params, "conversionLabel", "__GOOGLE_ADS_CONVERSION_LABEL__")
            if param_value(params, "currencyCode") is not None:
                set_param(params, "currencyCode", "__CURRENCY_ISO_4217__")
        if typ == "googtag":
            t["name"] = "Google Tag - Reference"
        elif typ == "gclidw":
            t["name"] = "Conversion Linker - Reference"
        elif typ == "sgtmadscl":
            t["name"] = "Server Conversion Linker - Reference"
        else:
            t["name"] = "Reference Tag %02d (%s)" % (idx, typ or "unknown")
        _walk_params_replace_urls(params)
        _scrub_form_ids(params)
        # Event names embedded in event-tag settings are business semantics, not reusable defaults.
        for p in params:
            if p.get("key") == "eventName" and isinstance(p.get("value"), str) and not p["value"].startswith("{{"):
                p["value"] = "__EVENT_NAME__"

    # Triggers: preserve trigger types/operators but neutralize site/event operands and labels.
    for idx, tr in enumerate(cv.get("trigger", []) or [], 1):
        tr["name"] = "Reference Trigger %02d (%s)" % (idx, tr.get("type") or "unknown")
        groups = (tr.get("filter") or []) + (tr.get("customEventFilter") or [])
        for group in groups:
            typ = group.get("type")
            serialized = json.dumps(group, ensure_ascii=False)
            for p in group.get("parameter", []) or []:
                if p.get("key") != "arg1" or not isinstance(p.get("value"), str):
                    continue
                if typ == "CSS_SELECTOR":
                    p["value"] = "__CSS_SELECTOR__"
                elif "{{Page Path}}" in serialized:
                    p["value"] = "__SUCCESS_PATH__"
                elif "{{Click Text}}" in serialized:
                    p["value"] = "__CLICK_TEXT__"
                elif "{{_event}}" in serialized:
                    p["value"] = "__SOURCE_EVENT_NAME__"
                elif "{{DLV" in serialized or "{{Data Layer" in serialized:
                    p["value"] = "__DATA_LAYER_MATCH_VALUE__"
                else:
                    p["value"] = "__TRIGGER_MATCH_VALUE__"

    # Last structured token safety pass, excluding opaque custom-template source where examples/base64 may occur.
    def scrub_tokens(obj, inside_template_data=False):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "templateData":
                    continue
                if isinstance(v, str):
                    value = META_TOKEN.sub("__META_CAPI_ACCESS_TOKEN__", v)
                    value = GTM_PUBLIC.sub("GTM-REFERENCE", value)
                    value = GA4_PUBLIC.sub("__GA4_MEASUREMENT_ID__", value)
                    obj[k] = value
                else:
                    scrub_tokens(v)
        elif isinstance(obj, list):
            for v in obj:
                scrub_tokens(v)
    scrub_tokens(out)
    return out, ctype


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            src = json.load(f)
        out, ctype = sanitize(src)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        sys.exit("ABBRUCH: %s" % e)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(p, "x", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except FileExistsError:
        sys.exit("ABBRUCH: %s existiert bereits" % p)
    print("OK: sanitized %s reference -> %s" % (ctype, p))

if __name__ == "__main__":
    main()
