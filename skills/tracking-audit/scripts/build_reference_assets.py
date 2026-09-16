#!/usr/bin/env python3
"""Derive neutral core candidates and a pattern catalog from sanitized GTM references.

Inputs MUST already be sanitized. Output is architecture guidance / GTM candidate material,
never a VERIFIED master. A real GTM import->preview->re-export is still required before registry promotion.
"""
from __future__ import annotations
import argparse, copy, json, re, sys
from pathlib import Path

def load(path, kind):
    data = json.load(open(path, encoding="utf-8"))
    marker = data.get("_meixnerReference") if isinstance(data, dict) else None
    if not isinstance(marker, dict) or marker.get("sanitized") is not True or marker.get("purpose") != "architecture_reference_only":
        raise ValueError("Input ist keine durch sanitize_gtm_reference.py markierte Referenz")
    usage = ((data.get("containerVersion") or {}).get("container") or {}).get("usageContext") or []
    if kind.upper() not in usage:
        raise ValueError("%s ist kein %s-Container" % (path, kind))
    return data


def write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2); f.write("\n")


def deep_replace(obj, old, new):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, str): obj[k] = v.replace(old, new)
            else: deep_replace(v, old, new)
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            if isinstance(v, str): obj[i] = v.replace(old, new)
            else: deep_replace(v, old, new)


def core_web(web):
    out = copy.deepcopy(web); cv = out["containerVersion"]
    cv["container"]["name"] = "Meixner Toolkit || Web Core Candidate"
    cv["tag"] = [t for t in cv.get("tag", []) if t.get("type") in {"gclidw", "googtag"}]
    cv["trigger"] = []
    cv["variable"] = [v for v in cv.get("variable", []) if v.get("name") == "Const - Google Mess ID"]
    # Add reusable sGTM URL constant and route the Google Tag through it.
    cv["variable"].append({
        "accountId":"__REFERENCE_ACCOUNT_ID__", "containerId":"__REFERENCE_CONTAINER_ID__",
        "variableId":"9001", "name":"Const - sGTM URL", "type":"c",
        "parameter":[{"type":"TEMPLATE","key":"value","value":"__SGTM_URL__"}], "formatValue":{}
    })
    deep_replace(cv["tag"], "https://sgtm.example.invalid", "{{Const - sGTM URL}}")
    cv["builtInVariable"] = []
    out["_meixnerMaster"] = {
        "schema":1, "status":"candidate_reference_only", "type":"web-core",
        "source":"sanitized production reference", "verified":False,
        "warning":"Nicht als VERIFIED behandeln. Vor Kundeneinsatz GTM Import -> Preview -> Re-Export -> gtm_master_verify.py."
    }
    return out


def core_server(server):
    out = copy.deepcopy(server); cv = out["containerVersion"]
    cv["container"]["name"] = "Meixner Toolkit || Server Core Candidate"
    cv["tag"] = [t for t in cv.get("tag", []) if t.get("type") == "sgtmadscl"]
    cv["trigger"] = []
    cv["variable"] = [v for v in cv.get("variable", []) if v.get("name") in {
        "Const - Meta Pixel ID", "Const - Meta Access Token", "Const - Meta Test Event Code"}]
    cv["builtInVariable"] = [v for v in cv.get("builtInVariable", []) if v.get("type") == "EVENT_NAME"]
    cv["client"] = [c for c in cv.get("client", []) if c.get("type") == "gaaw_client"]
    # Keep the real installed Stape template as reference material for future event patterns,
    # but no Meta tag is enabled in the core itself.
    cv["customTemplate"] = [t for t in cv.get("customTemplate", []) if t.get("name") == "Facebook Conversion API"]
    out["_meixnerMaster"] = {
        "schema":1, "status":"candidate_reference_only", "type":"server-core",
        "source":"sanitized production reference", "verified":False,
        "warning":"Community-Template ist versioniert und muss vor neuem Release gegen Gallery/Stape geprueft werden. Echter GTM Roundtrip bleibt Pflicht."
    }
    return out


def patterns():
    return {
      "schema": 1,
      "status": "reference_patterns_not_defaults",
      "principles": [
        "Erst den realen Erfolgs-/Interaktionspunkt verifizieren, dann Event benennen und Tagging erzeugen.",
        "Production Reference ist Evidenz fuer ein funktionierendes Muster, keine Soll-Konfiguration fuer andere Kunden.",
        "Kunden-IDs, Domains, Labels, Consent-Entscheidungen, Waehrungen, CSS/Pfade und Business-Events nie uebernehmen.",
        "Google Ads bei serverseitiger Conversion-Messung nicht parallel als gleichartige Browser-Conversion doppeln.",
        "Meta Browser + CAPI nur mit identischem event_name und stabil gleicher event_id zur Deduplizierung.",
        "Marketing-Consent nie aus dem Referenzsetup erben; pro Kunde/CMP/Region verifizieren."
      ],
      "patterns": {
        "purchase": {
          "canonical_ga4_event": "purchase",
          "source": "verified purchase-success event/dataLayer; source event name is site-specific",
          "required_fields": ["transaction_id", "value", "currency", "items"],
          "web": ["GA4 event tag", "send ecommerce from verified dataLayer", "route through verified sGTM transport when architecture=server"],
          "server": ["GA4 client receives purchase", "Google Ads conversion tag may read ecommerce fields automatically", "Meta CAPI Purchase only when requested/consented"],
          "defaults_forbidden": ["fixed EUR", "copied transaction IDs", "copied Ads label", "copied Meta Pixel/Token"]
        },
        "start_trial": {
          "canonical_ga4_event": "start_trial",
          "source": "verified trial activation/success, not a guessed CTA click",
          "server_destinations": "business decision; do not automatically create Ads/Meta conversions",
          "note": "Production reference used a differently cased event. New plans prefer canonical lowercase GA4 naming when semantics match."
        },
        "lead_or_booking": {
          "canonical_ga4_event": "generate_lead",
          "source": "verified successful lead/booking submission",
          "meta_event": "Choose standard event from real semantics (e.g. Lead or Schedule); do not infer from button text alone.",
          "server_destinations": "only destinations explicitly selected in plan"
        },
        "newsletter_signup": {
          "canonical_ga4_event": "newsletter_signup",
          "source": "verified successful newsletter subscription",
          "note": "Do not misuse GA4 sign_up unless the action really creates/registers a user account."
        },
        "scroll_50": {
          "canonical_ga4_event": "scroll_50",
          "source": "GTM scroll trigger or dataLayer, if this measurement is actually useful",
          "default_destinations": ["GA4 optional"],
          "do_not_default": ["Google Ads conversion", "Meta conversion/CAPI"]
        },
        "custom_completion": {
          "canonical_ga4_event": "site-specific custom event",
          "source": "verified completion callback/dataLayer preferred over brittle CSS/text click",
          "server_destinations": "only if business value and ad-platform mapping are explicitly defined"
        }
      }
    }


def architecture_catalog():
    return {
      "schema":1,
      "status":"sanitized_production_reference",
      "purpose":"Architecture evidence only; never copy customer configuration blindly.",
      "reusable_core": {
        "web":["Conversion Linker", "Google Tag routed to sGTM", "GA4 event tags built from per-customer plan"],
        "server":["GA4 client", "Server Conversion Linker", "server-side Google Ads conversion pattern", "Stape Meta CAPI template pattern"]
      },
      "parameterize_every_customer":[
        "GTM/container/account IDs", "GA4 Measurement ID", "sGTM domain", "Google Ads conversion IDs/labels",
        "Meta Pixel ID", "Meta Access Token", "Meta test code", "currency strategy", "event names",
        "form IDs", "paths", "CSS selectors", "button text", "consent/CMP strategy"
      ],
      "observed_but_not_default":[
        "single-currency EUR", "Meta CAPI adStorageConsent=optional/send-always", "Meta event-name inheritance",
        "scroll-depth forwarded to ad platforms", "page/click triggers for business conversions"
      ],
      "preferred_new-build_rules":[
        "Use stable success dataLayer/callbacks over click/text selectors when available.",
        "Use recommended GA4 event names when semantics exactly match; custom otherwise.",
        "For server-side Google Ads, avoid duplicate equivalent browser conversion tags.",
        "For hybrid Meta browser+CAPI, use the same event_id across channels.",
        "Consent behavior is a per-customer verified requirement, never inherited from the reference."
      ]
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--web", required=True); ap.add_argument("--server", required=True); ap.add_argument("--outdir", required=True)
    a=ap.parse_args(); out=Path(a.outdir)
    try:
        w=load(a.web,"WEB"); s=load(a.server,"SERVER")
    except (OSError,json.JSONDecodeError,ValueError) as e: sys.exit("ABBRUCH: %s"%e)
    write(out/"core"/"web-core.candidate.json", core_web(w))
    write(out/"core"/"server-core.candidate.json", core_server(s))
    write(out/"patterns"/"event-patterns.json", patterns())
    write(out/"production-reference"/"architecture.json", architecture_catalog())
    print("OK: Core candidates + pattern catalog derived")

if __name__ == "__main__": main()
