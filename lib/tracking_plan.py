"""Deterministisches Completeness Gate fuer Tracking-Plaene.

Das Gate entscheidet nicht, *welche* Marketingstrategie richtig ist. Es erzwingt nur,
dass architekturrelevante Entscheidungen vor dem GTM-Build explizit geklaert und mit
konkreter Evidenz belegt wurden. Fehlende Angaben werden als Rueckfragen geliefert.
"""
import re

GATE_VERSION = 1
SITE_TYPES = {"mpa", "spa", "hybrid"}
EVENT_SOURCES = {"dataLayer", "listener", "hybrid", "native_gtag"}
INTERNAL_TRAFFIC = {"filter", "keep", "not_applicable"}
REFUND_STRATEGIES = {"tracked", "manual", "not_applicable"}
SPA_STRATEGIES = {"dataLayer_page_view"}
UNVERIFIED_WORDS = ("unknown", "unbekannt", "unklar", "todo", "annahme", "vermut", "placeholder", "platzhalter")


def _domain_ok(value):
    """Hostname validieren, inkl. IDN/Punycode, aber ohne URL/Port/Wildcard."""
    if not isinstance(value, str):
        return False
    host = value.strip().rstrip(".")
    if not host or len(host) > 253 or "://" in host or "/" in host or ":" in host or "*" in host:
        return False
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except (UnicodeError, ValueError):
        return False
    labels = ascii_host.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not 1 <= len(label) <= 63 or label.startswith("-") or label.endswith("-"):
            return False
        if not re.fullmatch(r"[A-Za-z0-9-]+", label):
            return False
    return len(labels[-1]) >= 2


def _ask(out, field, question):
    out.append({"field": field, "question": question})


def _verified(req, key):
    return req.get(key) is True


def _evidence_ok(value):
    if not isinstance(value, str) or len(value.strip()) < 8:
        return False
    low = value.casefold()
    return not any(word in low for word in UNVERIFIED_WORDS)


def _need_evidence(out, req, key, question):
    evidence = req.get("evidence")
    value = evidence.get(key) if isinstance(evidence, dict) else None
    if not _evidence_ok(value):
        _ask(out, "requirements.evidence.%s" % key, question)


def missing_requirements(plan):
    out = []
    req = plan.get("requirements")
    if not isinstance(req, dict):
        return [{"field": "requirements", "question": "Vor dem Build den Requirements-Block aus der Audit-/Plan-Runde ausfuellen und belegen."}]

    if req.get("gate_version") != GATE_VERSION:
        _ask(out, "requirements.gate_version", "Requirements-Schema bestaetigen (aktuell gate_version=%d)." % GATE_VERSION)
    if req.get("open_questions") != []:
        _ask(out, "requirements.open_questions", "Alle offenen Tracking-Fragen klaeren; Build erst mit leerer Liste starten.")
    site_type = req.get("site_type")
    if site_type not in SITE_TYPES:
        _ask(out, "requirements.site_type", "Ist die Website MPA, SPA oder hybrid?")
    domain = req.get("primary_domain")
    if not _domain_ok(domain):
        _ask(out, "requirements.primary_domain", "Welche kanonische Produktionsdomain wird gemessen? (nur Hostname; IDN ist erlaubt)")

    if req.get("event_source") not in EVENT_SOURCES:
        _ask(out, "requirements.event_source", "Woher kommen Conversion-Events: dataLayer, Listener, hybrid oder native_gtag?")
    if not _verified(req, "event_source_verified"):
        _ask(out, "requirements.event_source_verified", "Eventquelle am echten Erfolgsfall verifizieren (nicht nur Button-Klick vermuten).")
    else:
        _need_evidence(out, req, "event_source", "Konkrete Evidenz fuer die Eventquelle angeben (z. B. GTM Preview/dataLayer/Codepfad).")

    events = [e for e in (plan.get("events") or []) if isinstance(e, dict)]
    if events and not _verified(req, "conversion_success_verified"):
        _ask(out, "requirements.conversion_success_verified", "Fuer die geplanten Events den tatsaechlichen Ausloesepunkt verifizieren (Danke-Seite/dataLayer/Callback).")
    elif events:
        _need_evidence(out, req, "conversion_success", "Evidenz fuer den verifizierten Erfolgs-/Ausloesepunkt angeben.")
        ev_evidence = req.get("event_evidence")
        if not isinstance(ev_evidence, dict):
            _ask(out, "requirements.event_evidence", "Fuer jedes geplante Event die beobachtete Quelle/Evidenz dokumentieren.")
        else:
            for ev in events:
                name = ev.get("name")
                if isinstance(name, str) and name and not _evidence_ok(ev_evidence.get(name)):
                    _ask(out, "requirements.event_evidence.%s" % name,
                         "Event %s am echten oder reproduzierbaren Erfolgs-/Interaktionspfad belegen." % name)

    if not _verified(req, "consent_strategy_verified"):
        _ask(out, "requirements.consent_strategy_verified", "CMP, Basic/Advanced Consent Mode und Update-Ereignis am echten Setup verifizieren.")
    else:
        _need_evidence(out, req, "consent_strategy", "Evidenz fuer CMP/Consent-Mode/Update-Ereignis angeben (Messung oder Nutzerbestaetigung + Konfiguration).")

    cross = req.get("cross_domain")
    if cross == "not_required":
        pass
    elif isinstance(cross, list) and cross and all(_domain_ok(x) for x in cross):
        # Der Direktgenerator implementiert Cross-Domain bewusst nicht; Routing erfolgt spaeter.
        impl = req.get("cross_domain_implementation")
        if impl not in {"verified_master"}:
            _ask(out, "requirements.cross_domain_implementation",
                 "Cross-Domain ist erforderlich: einen real verifizierten GTM-Master verwenden (cross_domain_implementation='verified_master').")
    else:
        _ask(out, "requirements.cross_domain", "Cross-Domain-Tracking entscheiden: 'not_required' oder Liste der beteiligten Domains.")

    if req.get("internal_traffic") not in INTERNAL_TRAFFIC:
        _ask(out, "requirements.internal_traffic", "Interne/Test-Zugriffe entscheiden: filter, keep oder not_applicable.")

    ecommerce = any(bool(e.get("ecommerce")) for e in events)
    if ecommerce:
        if not _verified(req, "ecommerce_contract_verified"):
            _ask(out, "requirements.ecommerce_contract_verified", "E-Commerce-dataLayer am echten Kauf verifizieren: transaction_id, value, currency und items.")
        else:
            _need_evidence(out, req, "ecommerce_contract", "Evidenz fuer transaction_id/value/currency/items des E-Commerce-Vertrags angeben.")
        if req.get("refund_strategy") not in REFUND_STRATEGIES:
            _ask(out, "requirements.refund_strategy", "Wie werden Refunds/Stornos behandelt: tracked, manual oder not_applicable?")
        elif req.get("refund_strategy") == "tracked" and not any(e.get("name") == "refund" for e in events):
            _ask(out, "events.refund", "refund_strategy='tracked' verlangt ein explizites refund-Event im Plan.")
        pay = req.get("payment_referrals")
        if pay == "not_required":
            pass
        elif isinstance(pay, list) and pay and all(_domain_ok(x) for x in pay):
            pass
        else:
            _ask(out, "requirements.payment_referrals", "Payment-/Checkout-Referrals entscheiden: 'not_required' oder Liste auszuschliessender Domains.")

    ads = plan.get("google_ads") or {}
    if ads.get("enhanced_conversions"):
        if not _verified(req, "enhanced_conversions_verified"):
            _ask(out, "requirements.enhanced_conversions_verified", "Quelle und Einwilligungsweg der Enhanced-Conversion-Nutzerdaten verifizieren.")
        else:
            _need_evidence(out, req, "enhanced_conversions", "Evidenz fuer Quelle und Consent-Pfad der Enhanced-Conversion-Daten angeben.")
        src = req.get("enhanced_conversions_source")
        if not isinstance(src, str) or not src.strip():
            _ask(out, "requirements.enhanced_conversions_source", "Welche verifizierte Quelle liefert user_data (Formular/Shop/dataLayer)?")

    if plan.get("architecture") in {"server", "browser+server"}:
        if not _verified(req, "server_strategy_verified"):
            _ask(out, "requirements.server_strategy_verified", "Server-Transport, Ziel-Domain und Zuständigkeit von Browser-vs-Server-Conversions verifizieren.")
        else:
            _need_evidence(out, req, "server_strategy", "Evidenz fuer sGTM-Ziel, Transport und Browser-vs-Server-Zustaendigkeit angeben.")

    if site_type in {"spa", "hybrid"}:
        strategy = req.get("spa_pageview_strategy")
        if strategy not in SPA_STRATEGIES:
            _ask(out, "requirements.spa_pageview_strategy", "SPA/Hybrid: unterstuetzt ist aktuell 'dataLayer_page_view' nach verifiziertem virtuellen Seitenwechsel.")
        elif not any(e.get("name") == "page_view" for e in events):
            _ask(out, "events.page_view", "spa_pageview_strategy='dataLayer_page_view' verlangt ein page_view-Event im Plan.")

    return out


def direct_builder_blockers(plan):
    """Faelle, die der direkte Web-JSON-Generator absichtlich nicht still approximiert."""
    req = plan.get("requirements") or {}
    out = []
    cross = req.get("cross_domain")
    if isinstance(cross, list) and cross:
        out.append("Cross-Domain-Konfiguration wird vom Direktgenerator nicht erzeugt; real verifizierten GTM-Master verwenden.")
    return out


def assert_direct_build_supported(plan):
    blockers = direct_builder_blockers(plan)
    if blockers:
        raise ValueError("DIREKT-BUILD NICHT UNTERSTUETZT:\n- " + "\n- ".join(blockers))
    return True


def assert_complete(plan):
    missing = missing_requirements(plan)
    if missing:
        lines = ["TRACKING-PLAN UNVOLLSTAENDIG – vor dem Build Rueckfragen klaeren:"]
        lines += ["- %s: %s" % (m["field"], m["question"]) for m in missing]
        raise ValueError("\n".join(lines))
    return True
