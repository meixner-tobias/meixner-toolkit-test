const TRACKERS = [
  ["ga4", /\/g\/collect\?|google-analytics\.com\/(g\/)?collect/],
  ["gtm_load", /googletagmanager\.com\/(gtm|gtag\/js)|\/gtm\.js\?id=|\/gtag\/js\?id=/],
  ["google_ads", /googleadservices\.com|googlesyndication|doubleclick\.net|google\.com\/(pagead|ccm)\//],
  ["meta", /facebook\.com\/tr|connect\.facebook\.net/],
  ["microsoft", /bat\.bing\.com|clarity\.ms/],
  ["tiktok", /analytics\.tiktok\.com/],
  ["linkedin", /px\.ads\.linkedin\.com|snap\.licdn\.com/],
  ["pinterest", /ct\.pinterest\.com|s\.pinimg\.com/],
  ["hotjar", /hotjar\.com|hotjar\.io/],
];

export const TRACK_COOKIES = /^(_ga|_gid|_gcl_|_gac_|FPID|FPLC|_fbp|_fbc|_uet|_clck|_clsk|_ttp|li_|_pin|_hj|IDE|test_cookie|gtmeec)/i;
export const TRACK_STORAGE = /^(_ga|_gid|_gcl_|_gac_|FPID|FPLC|_fbp|_fbc|_uet|_clck|_clsk|_ttp|li_|_pin|_hj|IDE|gtm|ga:|google|meta|facebook)/i;

export function emptyScenario(name, echtGesendet = false) {
  return {
    scenario: name, status: "unknown", abbruch: null, cmp_click: null, errors: [],
    datalayer_consent: null, cookies_before: [], cookies_after: [],
    speicher_before: null, speicher_after: null, speicher_delta: null,
    hits: [], blockiert: [], echt_gesendet: Boolean(echtGesendet),
  };
}

export function classify(url, siteUrl) {
  for (const [kind, re] of TRACKERS) if (re.test(url)) return kind;
  try {
    const x = new URL(url);
    const apex = new URL(siteUrl).host.replace(/^www\./, "").toLowerCase();
    const h = x.host.toLowerCase();
    if ((h === apex || h.endsWith("." + apex)) && /\/data\/?$/.test(x.pathname)) return "stape_data";
  } catch {}
  return null;
}

export function requestRole(url, resourceType, siteUrl) {
  const kind = classify(url, siteUrl);
  if (!kind) return null;
  if (kind === "gtm_load" || resourceType === "script") return "loader";
  return "collection";
}

export function shouldBlockTrackerDelivery(url, request, siteUrl) {
  const resourceType = typeof request?.resourceType === "function" ? request.resourceType() : request?.resourceType;
  return requestRole(url, resourceType, siteUrl) === "collection";
}

export function parseTracking(url, postData) {
  const q = new URL(url).searchParams;
  const body = new URLSearchParams(postData && !postData.startsWith("{") ? postData.split("\n")[0] : "");
  const g = k => q.get(k) ?? body.get(k);
  return { tid: g("tid") ?? g("id"), en: g("en") ?? g("ev"), gcs: g("gcs"), gcd: g("gcd"), eid: g("eid"), host: new URL(url).host };
}

export function storageDelta(before, after) {
  const b = before || {}, a = after || {};
  const diff = (x, y) => [...new Set(y || [])].filter(k => !(x || []).includes(k));
  return {
    localStorage_new: diff(b.localStorage, a.localStorage),
    sessionStorage_new: diff(b.sessionStorage, a.sessionStorage),
    indexedDB_new: diff(b.indexedDB?.databases, a.indexedDB?.databases),
  };
}

function collectionHits(r) {
  return (r.hits || []).filter(h => h.role === "collection");
}

export function assess(results) {
  const findings = [];
  const [none, acc, rej] = results;
  for (const r of results) {
    if (r.abbruch || r.status !== "geprueft" || (r.errors || []).length) {
      findings.push(`NICHT GEPRUEFT (${r.scenario}): ${r.abbruch || "BROWSER_FEHLER"} – aus diesem Szenario laesst sich nichts ableiten.`);
    }
  }
  const usable = r => r && !r.abbruch && r.status === "geprueft" && !(r.errors || []).length;
  const marketingKinds = new Set(["meta", "microsoft", "tiktok", "linkedin", "pinterest", "hotjar"]);

  for (const r of [none, rej].filter(usable)) {
    const where = r.scenario === "keine_interaktion" ? "ohne Interaktion" : "nach Ablehnen";
    const rel = collectionHits(r).filter(h => r.scenario === "keine_interaktion" || h.phase === "nach_klick");
    const marketing = rel.filter(h => marketingKinds.has(h.kind));
    if (marketing.length) {
      findings.push(`HOCH: Technischer Compliance-Risk – Marketing-Collection-Requests ${where}: ${[...new Set(marketing.map(h => h.kind + "@" + h.host))].join(", ")}. Rechtliche Einordnung separat pruefen.`);
    }

    const google = rel.filter(h => h.kind === "ga4" || h.kind === "google_ads");
    if (google.length) {
      const signale = [...new Set(google.map(h => `gcs=${h.gcs ?? "-"},gcd=${h.gcd ?? "-"}`))];
      findings.push(`BEOBACHTUNG: ${google.length} Google-Collection-Request(s) ${where}; codierte Consent-Signale: ${signale.join(" | ")}. Nicht als stabile Ja/Nein-Decodierung behandeln; mit Tag Assistant/aktueller Google-Doku verifizieren.`);
    }

    const cookies = (r.cookies_after || []).filter(c => !/^test_cookie/i.test(c));
    if (cookies.length) findings.push(`HOCH: Tracking-artige Cookies ${where}: ${cookies.join(", ")}. Technischen Zweck und Einwilligungsbedarf separat pruefen.`);

    const s = r.speicher_after || r.speicher_before;
    const local = (s?.localStorage || []).filter(k => TRACK_STORAGE.test(k));
    const session = (s?.sessionStorage || []).filter(k => TRACK_STORAGE.test(k));
    if (local.length || session.length) {
      findings.push(`HOCH: Tracking-artige Web-Storage-Schluessel ${where}: ${[...local.map(k => "local:" + k), ...session.map(k => "session:" + k)].join(", ")}.`);
    }
    if ((s?.indexedDB?.databases || []).length) {
      findings.push(`BEOBACHTUNG: IndexedDB-Datenbanken ${where}: ${s.indexedDB.databases.join(", ")}. Name allein beweist keinen Tracking-Zweck.`);
    }
  }

  if (usable(none) && none.datalayer_consent && !none.datalayer_consent.some(c => c.cmd === "default"))
    findings.push("MITTEL: Kein 'consent default' im dataLayer beobachtet; CMP kann Consent auch anders implementieren – manuell pruefen.");

  if (usable(acc)) {
    const after = collectionHits(acc).filter(h => h.phase === "nach_klick");
    const loaders = (acc.hits || []).filter(h => h.role === "loader");
    if (after.length === 0 && loaders.length)
      findings.push("MITTEL: Tracking-Bibliotheken wurden geladen, aber nach dem akzeptierten CMP-Klick keine Collection-Requests beobachtet. Falls Tags erwartet sind, Trigger/Consent-Konfiguration manuell pruefen.");

    const meta = after.filter(h => h.kind === "meta" && /facebook\.com\/tr/.test(h.url || ""));
    if (meta.length && meta.every(h => !h.eid))
      findings.push("MITTEL: Beobachtete Meta-Pixel-Collection-Requests ohne eventID (eid) – Browser/CAPI-Deduplizierung pruefen.");
    const sgtm = after.filter(h => h.kind === "ga4" && !/google-analytics\.com/.test(h.host || ""));
    findings.push(sgtm.length
      ? `INFO: Beobachtete GA4-Collection ueber eigenen Server-Endpunkt: ${[...new Set(sgtm.map(h => h.host))].join(", ")}`
      : "INFO: Kein eigener GA4-Server-Endpunkt in den beobachteten Collection-Requests erkannt.");
  }

  findings.push("HINWEIS: Locale de-DE und Zeitzone Europe/Berlin ersetzen keine IP-Geolokation. Service Worker werden fuer die Netzwerksicherheitsgrenze blockiert; dadurch kann sich das Verhalten von Websites mit Service-Worker-Logik vom Produktionsbrowser unterscheiden.");
  return findings;
}
