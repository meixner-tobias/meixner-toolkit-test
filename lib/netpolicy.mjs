/**
 * Netzwerk-Policy fuer browsergestuetzte Audits.
 *
 * Ziel: Nur global routbare HTTP(S)- und WebSocket-Ziele duerfen den Browser
 * verlassen. Die reine Entscheidungslogik ist absichtlich browserunabhaengig,
 * damit sie hermetisch getestet werden kann.
 *
 * Grenzen: DNS-Rebinding zwischen Pruefung und Chromiums Verbindungsaufbau kann
 * ohne eigenes Socket-Pinning nicht vollstaendig ausgeschlossen werden. Deshalb
 * wird die Policy als starke Schutzschicht, nicht als formaler SSRF-Beweis,
 * dokumentiert.
 */
import dns from "dns/promises";
import net from "net";

export const ERLAUBTE_SCHEMATA = new Set(["http:", "https:", "ws:", "wss:"]);
export const ERLAUBTE_PORTS = new Set(["", "80", "443"]);

const LOKALE_NAMEN = new Set([
  "localhost", "localhost.localdomain", "ip6-localhost", "metadata.google.internal",
]);

function v4ToInt(ip) {
  if (net.isIP(ip) !== 4) return null;
  const p = ip.split(".").map(Number);
  return (((p[0] << 24) >>> 0) + (p[1] << 16) + (p[2] << 8) + p[3]) >>> 0;
}

function inV4Cidr(ip, base, prefix) {
  const x = v4ToInt(ip), b = v4ToInt(base);
  if (x === null || b === null) return false;
  if (prefix === 0) return true;
  const mask = prefix === 32 ? 0xffffffff : (0xffffffff << (32 - prefix)) >>> 0;
  return (x & mask) === (b & mask);
}

// Konservativ: special-use / nicht global routbare Bereiche werden fuer einen
// Audit-Browser geblockt. Dokumentations- und Benchmark-Netze sind keine
// sinnvollen Kundenziele und sollen nicht als "oeffentlich" gelten.
const NICHT_GLOBAL_V4 = [
  ["0.0.0.0", 8, "unspecified/current network 0.0.0.0/8"],
  ["10.0.0.0", 8, "privat 10.0.0.0/8"],
  ["100.64.0.0", 10, "Shared Address Space 100.64.0.0/10"],
  ["127.0.0.0", 8, "Loopback 127.0.0.0/8"],
  ["169.254.0.0", 16, "Link-local 169.254.0.0/16"],
  ["172.16.0.0", 12, "privat 172.16.0.0/12"],
  ["192.0.0.0", 24, "special-use 192.0.0.0/24"],
  ["192.0.2.0", 24, "Dokumentation 192.0.2.0/24"],
  ["192.88.99.0", 24, "special-use 192.88.99.0/24"],
  ["192.168.0.0", 16, "privat 192.168.0.0/16"],
  ["198.18.0.0", 15, "Benchmarking 198.18.0.0/15"],
  ["198.51.100.0", 24, "Dokumentation 198.51.100.0/24"],
  ["203.0.113.0", 24, "Dokumentation 203.0.113.0/24"],
  ["224.0.0.0", 4, "Multicast 224.0.0.0/4"],
  ["240.0.0.0", 4, "reserviert 240.0.0.0/4"],
];

export function istPrivateV4(ip) {
  if (net.isIP(ip) !== 4) return null;
  for (const [base, prefix, grund] of NICHT_GLOBAL_V4) {
    if (inV4Cidr(ip, base, prefix)) return grund;
  }
  return null;
}

function ipv6ToBigInt(input) {
  let ip = input.toLowerCase().replace(/^\[|\]$/g, "");
  const zone = ip.indexOf("%");
  if (zone >= 0) ip = ip.slice(0, zone);
  if (net.isIP(ip) !== 6) return null;

  // Eingebettetes IPv4 in zwei Hexgruppen umwandeln, z. B. ::ffff:127.0.0.1.
  if (ip.includes(".")) {
    const idx = ip.lastIndexOf(":");
    const v4 = ip.slice(idx + 1);
    const n = v4ToInt(v4);
    if (n === null) return null;
    const hi = ((n >>> 16) & 0xffff).toString(16);
    const lo = (n & 0xffff).toString(16);
    ip = ip.slice(0, idx + 1) + hi + ":" + lo;
  }

  const halves = ip.split("::");
  if (halves.length > 2) return null;
  const left = halves[0] ? halves[0].split(":").filter(Boolean) : [];
  const right = halves.length === 2 && halves[1] ? halves[1].split(":").filter(Boolean) : [];
  const missing = 8 - left.length - right.length;
  if (missing < 0 || (halves.length === 1 && missing !== 0)) return null;
  const groups = halves.length === 2 ? [...left, ...Array(missing).fill("0"), ...right] : [...left, ...right];
  if (groups.length !== 8 || groups.some(g => !/^[0-9a-f]{1,4}$/.test(g))) return null;
  return groups.reduce((acc, g) => (acc << 16n) | BigInt(parseInt(g, 16)), 0n);
}

function ipv6CidrBase(text) {
  const v = ipv6ToBigInt(text);
  if (v === null) throw new Error("ungueltige IPv6-Konstante: " + text);
  return v;
}

function inV6Cidr(value, base, prefix) {
  if (value === null) return false;
  if (prefix === 0) return true;
  const shift = 128n - BigInt(prefix);
  return (value >> shift) === (base >> shift);
}

const NICHT_GLOBAL_V6 = [
  [ipv6CidrBase("::"), 96, "IPv4-kompatibel/unspecified ::/96"],
  [ipv6CidrBase("::ffff:0:0"), 96, "IPv4-mapped ::ffff:0:0/96"],
  [ipv6CidrBase("64:ff9b::"), 96, "NAT64 well-known prefix 64:ff9b::/96 (Audit-Policy konservativ blockiert)"],
  [ipv6CidrBase("64:ff9b:1::"), 48, "NAT64 local-use prefix 64:ff9b:1::/48"],
  [ipv6CidrBase("100::"), 64, "Discard-only 100::/64"],
  [ipv6CidrBase("2001::"), 23, "IETF special-purpose 2001::/23"],
  [ipv6CidrBase("2001:db8::"), 32, "Dokumentation 2001:db8::/32"],
  [ipv6CidrBase("2002::"), 16, "6to4-Transition 2002::/16"],
  [ipv6CidrBase("3fff::"), 20, "Dokumentation 3fff::/20"],
  [ipv6CidrBase("fc00::"), 7, "IPv6 Unique-local fc00::/7"],
  [ipv6CidrBase("fe80::"), 10, "IPv6 Link-local fe80::/10"],
  [ipv6CidrBase("ff00::"), 8, "IPv6 Multicast ff00::/8"],
];

export function istPrivateV6(ip) {
  const x = ip.toLowerCase().replace(/^\[|\]$/g, "");
  if (net.isIP(x) !== 6) return null;
  const value = ipv6ToBigInt(x);
  // Global Unicast liegt primaer in 2000::/3. Fuer einen Audit-Browser ist es
  // sicherer, andere IPv6-Arten abzulehnen als exotische Transition-Mechanismen
  // unbemerkt als "oeffentlich" durchzulassen.
  const globalBase = ipv6CidrBase("2000::");
  if (!inV6Cidr(value, globalBase, 3)) return "nicht global routbarer IPv6-Bereich";
  for (const [base, prefix, grund] of NICHT_GLOBAL_V6) {
    if (inV6Cidr(value, base, prefix)) return grund;
  }
  return null;
}

export function istPrivateAdresse(ip) {
  const roh = ip.replace(/^\[|\]$/g, "");
  const typ = net.isIP(roh);
  if (typ === 4) return istPrivateV4(roh);
  if (typ === 6) return istPrivateV6(roh);
  return null;
}

/**
 * Entscheidet ueber ein Netzwerkziel.
 * @param {string} rohUrl
 * @param {(host:string)=>Promise<string[]>} [resolver] injizierbar fuer hermetische Tests
 * @returns {Promise<{erlaubt:boolean, grund?:string}>}
 */
export async function pruefeZiel(rohUrl, resolver) {
  let u;
  try { u = new URL(rohUrl); } catch { return { erlaubt: false, grund: "unlesbare Adresse" }; }

  if (!ERLAUBTE_SCHEMATA.has(u.protocol))
    return { erlaubt: false, grund: `Schema ${u.protocol} nicht erlaubt` };
  if (u.username || u.password)
    return { erlaubt: false, grund: "Adresse enthaelt Zugangsdaten" };
  if (!ERLAUBTE_PORTS.has(u.port))
    return { erlaubt: false, grund: `Port ${u.port} nicht erlaubt` };

  const host = u.hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (LOKALE_NAMEN.has(host))
    return { erlaubt: false, grund: `lokaler Name ${host}` };

  const ipTyp = net.isIP(host);
  if (ipTyp) {
    const grund = istPrivateAdresse(host);
    return grund ? { erlaubt: false, grund } : { erlaubt: true };
  }

  let adressen;
  try {
    adressen = resolver ? await resolver(host)
                        : (await dns.lookup(host, { all: true })).map(a => a.address);
  } catch {
    return { erlaubt: false, grund: `DNS-Aufloesung von ${host} fehlgeschlagen` };
  }
  if (!adressen.length) return { erlaubt: false, grund: `keine Adresse fuer ${host}` };
  for (const a of adressen) {
    const grund = istPrivateAdresse(a);
    if (grund) return { erlaubt: false, grund: `${host} loest auf ${a} auf (${grund})` };
  }
  return { erlaubt: true };
}

/**
 * Installiert HTTP(S)- und WebSocket-Schutz auf einem Playwright BrowserContext.
 * Fuer request interception sollte der Context mit serviceWorkers:'block' erzeugt
 * werden; Playwright empfiehlt das, weil Service Worker sonst Routing umgehen
 * koennen. Nur nach dieser Funktion erzeugte WebSockets werden erfasst.
 */
export async function installiereNetzPolicy(ctx, { onBlock, resolver, trackerAbbrechen } = {}) {
  await ctx.route("**/*", async route => {
    const req = route.request();
    const url = req.url();
    const { erlaubt, grund } = await pruefeZiel(url, resolver);
    if (!erlaubt) {
      onBlock && onBlock({ url, grund, art: "netzbereich" });
      return route.abort("blockedbyclient");
    }
    if (trackerAbbrechen && trackerAbbrechen(url, req)) {
      onBlock && onBlock({ url, grund: "Tracking-Collection erfasst, aber nicht gesendet", art: "tracker" });
      return route.abort("blockedbyclient");
    }
    return route.continue();
  });

  if (typeof ctx.routeWebSocket === "function") {
    await ctx.routeWebSocket(/.*/, async ws => {
      const url = ws.url();
      const { erlaubt, grund } = await pruefeZiel(url, resolver);
      if (!erlaubt) {
        onBlock && onBlock({ url, grund, art: "websocket" });
        await ws.close({ code: 1008, reason: "network policy" });
        return;
      }
      ws.connectToServer();
    });
  }
}
