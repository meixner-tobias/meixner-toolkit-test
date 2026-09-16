#!/usr/bin/env python3
"""Deterministischer Agent-/Accessibility-Readiness-Check fuer HTML.

Prueft nur maschinenlesbare, beobachtbare Signale. Er behauptet keinen Rankingeffekt.
URL-Modus nutzt die zentrale SSRF-Policy; fuer Tests kann audit_html() direkt benutzt werden.
"""
import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from lib import urlguard  # noqa: E402

INTERACTIVE_ROLES = {"button", "link", "menuitem", "checkbox", "radio", "switch", "tab", "option"}
TEXT_INPUT_TYPES = {"text", "email", "tel", "url", "search", "password", "number", "date", "time", "datetime-local"}
BUTTON_INPUT_TYPES = {"button", "submit", "reset", "image"}


def _attrs(raw):
    return {str(k).lower(): ("" if v is None else str(v)) for k, v in raw}


def _name_from_attrs(a):
    for k in ("aria-label", "aria-labelledby", "title"):
        if a.get(k, "").strip():
            return a[k].strip()
    return ""


class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.landmarks = {"main": 0, "nav": 0}
        self.labels_for = set()
        self.controls = []
        self._stack = []
        self._label_depth = 0

    def _nearest_control(self):
        for _, rec in reversed(self._stack):
            if rec is not None:
                return rec
        return None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = _attrs(attrs)
        if tag == "html":
            self.lang = a.get("lang", "").strip()
        if tag in self.landmarks:
            self.landmarks[tag] += 1
        role = a.get("role", "").lower().strip()
        if role == "main": self.landmarks["main"] += 1
        if role == "navigation": self.landmarks["nav"] += 1
        if tag == "label":
            self._label_depth += 1
            if a.get("for"):
                self.labels_for.add(a["for"])

        # Image-Alt innerhalb eines Links/Buttons ist Teil des Accessible Names.
        if tag == "img" and a.get("alt", "").strip():
            rec = self._nearest_control()
            if rec is not None:
                rec["text"] = (rec["text"] + " " + a["alt"].strip()).strip()

        is_control = tag in {"button", "a", "input", "select", "textarea"} or role in INTERACTIVE_ROLES
        rec = None
        if is_control:
            rec = {"tag": tag, "attrs": a, "text": "", "role": role,
                   "wrapped_label": self._label_depth > 0}
            self.controls.append(rec)
        self._stack.append((tag, rec))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text:
            return
        rec = self._nearest_control()
        if rec is not None:
            rec["text"] = (rec["text"] + " " + text).strip()

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break
        if tag == "label" and self._label_depth:
            self._label_depth -= 1


def _accessible(control, labels_for):
    tag, a, text = control["tag"], control["attrs"], control["text"].strip()
    if a.get("aria-hidden", "").lower() == "true" or a.get("disabled") is not None:
        return True, "ignored"
    explicit = _name_from_attrs(a)
    if explicit:
        return True, "aria/title"
    if control.get("wrapped_label"):
        return True, "wrapped-label"
    if tag == "button":
        return bool(text), "text" if text else "missing"
    if tag == "a":
        if not a.get("href"):
            return True, "not-link"
        return bool(text), "text/image-alt" if text else "missing"
    if tag == "input":
        typ = a.get("type", "text").lower()
        if typ in {"hidden"}:
            return True, "ignored"
        if typ in BUTTON_INPUT_TYPES:
            name = a.get("value", "").strip() or a.get("alt", "").strip()
            return bool(name), "value/alt" if name else "missing"
        if typ in TEXT_INPUT_TYPES or typ in {"checkbox", "radio", "file", "range", "color"}:
            ident = a.get("id", "")
            ok = bool(ident and ident in labels_for)
            return ok, "label" if ok else "missing"
    if tag in {"select", "textarea"}:
        ident = a.get("id", "")
        ok = bool(ident and ident in labels_for)
        return ok, "label" if ok else "missing"
    if control.get("role") in INTERACTIVE_ROLES:
        return bool(text), "text" if text else "missing"
    return True, "not-applicable"

def audit_html(html, source="inline"):
    p = AuditParser()
    p.feed(html)
    missing = []
    checked = 0
    for c in p.controls:
        ok, why = _accessible(c, p.labels_for)
        if why == "ignored" or why == "not-link":
            continue
        checked += 1
        if not ok:
            a = c["attrs"]
            missing.append({
                "tag": c["tag"], "role": c.get("role") or None,
                "id": a.get("id") or None, "type": a.get("type") or None,
                "reason": "kein maschinenlesbarer Accessible Name/Label beobachtet"
            })
    findings = []
    if not p.lang:
        findings.append({"id": "AGENT-LANG", "level": "MITTEL", "detail": "html[lang] fehlt"})
    if p.landmarks["main"] == 0:
        findings.append({"id": "AGENT-MAIN", "level": "MITTEL", "detail": "kein <main> bzw. role=main beobachtet"})
    if missing:
        findings.append({"id": "AGENT-NAME", "level": "HOCH", "detail": "%d interaktive Elemente ohne beobachtbaren Namen/Label" % len(missing)})
    return {
        "source": source,
        "checked_controls": checked,
        "unnamed_controls": missing,
        "landmarks": p.landmarks,
        "html_lang": p.lang or None,
        "findings": findings,
        "interpretation": "Agent-/Accessibility-Kompatibilitaet; kein behaupteter Rankingfaktor"
    }


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--html", help="lokale HTML-Datei")
    g.add_argument("--url", help="oeffentliche URL; zentrale SSRF-Policy gilt")
    ap.add_argument("--out", help="JSON-Ausgabe")
    a = ap.parse_args()
    if a.html:
        path = Path(a.html)
        html = path.read_text(encoding="utf-8", errors="replace")
        rep = audit_html(html, str(path))
    else:
        _, _, body = urlguard.hole(a.url, max_bytes=4 * 1024 * 1024)
        rep = audit_html(body.decode("utf-8", "replace"), urlguard.redigiere(a.url))
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
