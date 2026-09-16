"""Zentraler URL-, DNS- und SSRF-Validator (Abschnitt 4).

Wird von launch_check.py, siteone.py und doctor.py verwendet, damit es genau EINE
Stelle gibt, an der entschieden wird, welche Adresse abgerufen werden darf.

Vorgehen nach OWASP SSRF Prevention Cheat Sheet:
Schema-Allowlist, Userinfo-Verbot, DNS-Aufloesung, Ablehnung interner Adressbereiche,
Host-Allowlist, Port-Allowlist, Redirects einzeln pruefen, Groessen- und Zeitgrenzen.

Nicht geloest: eine echte DNS-Rebinding-Sperre. Zwischen Pruefung und Verbindungsaufbau
loest urllib erneut auf. pin_and_open() prueft deshalb unmittelbar vor dem Aufbau erneut
und vergleicht mit dem Ergebnis der ersten Aufloesung - das erschwert Rebinding, schliesst
es aber nicht aus. Vollstaendig sicher waere nur ein Verbindungsaufbau auf die bereits
geprueften IP-Adressen mit gesetztem Host-Header.
"""
import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request

ERLAUBTE_SCHEMATA = ("http", "https")
ERLAUBTE_PORTS = (80, 443)
MAX_BODY = 2_000_000
MAX_HOPS = 10
TIMEOUT = 20


class Blocked(Exception):
    """Eine Adresse wurde bewusst nicht abgerufen."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(NoRedirect)
# urllib kennt von Haus aus FileHandler und FTPHandler. Beide werden entfernt,
# damit eine file:- oder ftp:-URL nicht doch noch durchkommt.
_opener.handlers = [h for h in _opener.handlers
                    if type(h).__name__ not in ("FileHandler", "FTPHandler", "DataHandler")]


# Fuer hermetische Tests injizierbar: ein Test darf nicht von echtem DNS abhaengen.
RESOLVER = None

# Transition-/Translation-Mechanismen werden fuer Audit-SSRF konservativ geblockt.
# Das ist absichtlich strenger als reine IANA-Global-Reachability: ein lokaler
# NAT64/6to4-Pfad soll nicht zur Umgehung der IPv4-Pruefung dienen. Explizite
# Netze halten das Verhalten auch unter aelteren unterstuetzten Python-Versionen stabil.
_KONSERVATIV_V6 = tuple(ipaddress.ip_network(x) for x in (
    "64:ff9b::/96", "64:ff9b:1::/48", "2002::/16",
))


def aufloesen(host):
    if RESOLVER is not None:
        return RESOLVER(host)
    try:
        # Nach Version getrennt sortieren - ipaddress vergleicht IPv4 und IPv6 nicht miteinander.
        adressen = {ipaddress.ip_address(ai[4][0]) for ai in socket.getaddrinfo(host, None)}
        return sorted(adressen, key=lambda ip: (ip.version, ip.packed))
    except OSError as e:
        raise Blocked("DNS-Aufloesung fehlgeschlagen: %s" % e)


def ist_intern(ip):
    """True fuer Adressen, die ein Audit-Browser nicht als oeffentlich behandeln soll.

    is_global ist fuer SSRF-Zwecke passender als nur is_private: dadurch werden auch
    Shared Address Space, Dokumentations- und Benchmark-Netze geblockt. Bei
    IPv4-mapped IPv6 pruefen wir die eingebettete IPv4-Adresse ausdruecklich, damit
    ::ffff:7f00:1 nicht als Umgehung fuer 127.0.0.1 dienen kann.
    """
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        return not mapped.is_global
    if ip.version == 6 and any(ip in netz for netz in _KONSERVATIV_V6):
        return True
    return not ip.is_global


def pruefe(url, erlaubte_hosts=None, nur_https=False):
    """Prueft eine Adresse. Gibt die aufgeloesten IPs zurueck oder wirft Blocked."""
    teile = urllib.parse.urlsplit(url)
    if teile.scheme not in ERLAUBTE_SCHEMATA:
        raise Blocked("Schema %r nicht erlaubt (nur %s)"
                      % (teile.scheme or "(keines)", "/".join(ERLAUBTE_SCHEMATA)))
    if nur_https and teile.scheme != "https":
        raise Blocked("Nur https erlaubt, nicht %s" % teile.scheme)
    if teile.username or teile.password:
        raise Blocked("Adressen mit Benutzername oder Passwort sind nicht erlaubt")
    host = (teile.hostname or "").lower()
    if not host:
        raise Blocked("Kein Host in der Adresse")
    try:
        port = teile.port or (443 if teile.scheme == "https" else 80)
    except ValueError:
        raise Blocked("Ungueltige Portangabe")
    if port not in ERLAUBTE_PORTS:
        raise Blocked("Port %d nicht erlaubt (nur %s)" % (port, ", ".join(map(str, ERLAUBTE_PORTS))))
    if erlaubte_hosts and not any(host == h or host.endswith("." + h) for h in erlaubte_hosts):
        raise Blocked("Host %s steht nicht auf der Liste der freigegebenen Domains" % host)
    ips = aufloesen(host)
    for ip in ips:
        if ist_intern(ip):
            raise Blocked("%s zeigt auf eine interne Adresse (%s)" % (host, ip))
    return ips


def hole(url, erlaubte_hosts=None, methode="GET", limit=MAX_BODY, timeout=TIMEOUT,
         nur_https=False, ua="meixner-toolkit"):
    """Einzelner Abruf ohne Redirect-Verfolgung. Gibt (status, headers, body) zurueck."""
    try:
        ips_vorher = pruefe(url, erlaubte_hosts, nur_https)
    except Blocked as e:
        return None, {"error": str(e), "blocked": True}, b""
    # Zweite Aufloesung unmittelbar vor dem Verbindungsaufbau (Rebinding erschweren).
    try:
        host = urllib.parse.urlsplit(url).hostname.lower()
        ips_jetzt = aufloesen(host)
        if any(ist_intern(ip) for ip in ips_jetzt):
            return None, {"error": "DNS zeigt jetzt auf eine interne Adresse", "blocked": True}, b""
        if set(ips_jetzt) != set(ips_vorher):
            return None, {"error": "DNS-Antwort hat sich zwischen Pruefung und Abruf geaendert "
                                   "(moegliches Rebinding)", "blocked": True}, b""
    except Blocked as e:
        return None, {"error": str(e), "blocked": True}, b""

    req = urllib.request.Request(url, method=methode, headers={
        "User-Agent": ua, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    try:
        with _opener.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(limit)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(limit)
    except Exception as e:
        return None, {"error": redigiere_fehler(str(e))}, b""


def kette(url, erlaubte_hosts=None, max_hops=MAX_HOPS, **kw):
    """Folgt Weiterleitungen. JEDES Ziel wird erneut geprueft."""
    hops, gesehen = [], set()
    for _ in range(max_hops):
        status, headers, body = hole(url, erlaubte_hosts, **kw)
        eintrag = {"url": redigiere(url), "status": status}
        if headers.get("blocked"):
            eintrag["blockiert"] = headers["error"]
            hops.append(eintrag)
            return hops, {}, b""
        hops.append(eintrag)
        loc = next((v for k, v in headers.items() if k.lower() == "location"), None)
        if status in (301, 302, 303, 307, 308) and loc:
            naechste = urllib.parse.urljoin(url, loc)
            if naechste in gesehen:
                hops.append({"url": redigiere(naechste), "status": "SCHLEIFE"})
                return hops, {}, b""
            gesehen.add(url)
            url = naechste
            continue
        return hops, headers, body
    hops.append({"url": redigiere(url), "status": "ABBRUCH nach %d Spruengen" % max_hops})
    return hops, {}, b""


# ---------- Redaction ----------
BEHALTEN = {"page", "p", "lang", "id"}


def redigiere(url):
    """Entfernt Query- und Fragmentwerte. Query-Strings enthalten Click-IDs, Session-IDs
    und teils E-Mail-Adressen - die gehoeren in keinen Bericht und in kein Log."""
    try:
        t = urllib.parse.urlsplit(url)
        if not t.query and not t.fragment:
            return url
        paare = urllib.parse.parse_qsl(t.query, keep_blank_values=True)
        neu = [(k, v if k.lower() in BEHALTEN else "<redigiert>") for k, v in paare]
        return urllib.parse.urlunsplit((t.scheme, t.netloc, t.path,
                                        urllib.parse.urlencode(neu),
                                        "<redigiert>" if t.fragment else ""))
    except Exception:
        return "<unlesbare URL>"


def redigiere_fehler(text):
    """Fehlermeldungen enthalten oft die vollstaendige URL samt Query."""
    import re
    return re.sub(r"https?://\S+", lambda m: redigiere(m.group(0)), str(text))[:300]
