#!/usr/bin/env node
// Automatischer Consent-Test: 3 Szenarien in jeweils frischem Browser-Kontext (keine Screenshots nötig).
//   1) keine Interaktion  2) "Alle akzeptieren"  3) "Ablehnen"
// Protokolliert Tracking-Requests (GA4/sGTM, Google Ads, Meta, Microsoft, TikTok, LinkedIn …), gcs/gcd-Werte,
// Meta-Event-IDs und gesetzte Cookies. Ergebnis als JSON + Kurzbewertung.
//
// Einmalig (in einem beliebigen Arbeitsordner):  npm i playwright && npx playwright install chromium
// Aufruf (aus diesem Arbeitsordner):             node <pfad>/consent_test.mjs https://www.kunde.de [--accept "css"] [--reject "css"] [--wait 6000] [--out consent-report.json] [--path /kontakt]
import { createRequire } from "module";
import fs from "fs";
import os from "os";
import path from "path";
import { fileURLToPath } from "url";
import { pruefeZiel, installiereNetzPolicy } from "../../../lib/netpolicy.mjs";
import { TRACK_COOKIES, classify, requestRole, shouldBlockTrackerDelivery, parseTracking, storageDelta, assess, emptyScenario } from "./consent_logic.mjs";

const PLAYWRIGHT_PIN = "1.56.1";

let chromium;
{
  // Playwright NUR aus kontrollierten Pfaden laden. Ein Kundenordner kann ein eigenes
  // node_modules/playwright enthalten - dessen Code liefe dann mit vollen Rechten.
  // Deshalb kein process.cwd()-Fallback.
  const roots = [process.env.MT_PLAYWRIGHT_DIR,
                 process.env.CLAUDE_PLUGIN_ROOT,
                 path.join(os.homedir(), ".cache", "mt-playwright")].filter(Boolean);
  const tried = [];
  for (const dir of roots) {
    let real;
    try { real = fs.realpathSync(dir); } catch { tried.push(`${dir} (nicht vorhanden)`); continue; }
    const mod = path.join(real, "node_modules", "playwright");
    try {
      if (fs.realpathSync(mod).startsWith(real + path.sep)) {
        ({ chromium } = createRequire(path.join(real, "/"))("playwright"));
        const v = JSON.parse(fs.readFileSync(path.join(mod, "package.json"), "utf8")).version;
        if (v !== PLAYWRIGHT_PIN) console.error(`WARNUNG: Playwright ${v} gefunden, erwartet ${PLAYWRIGHT_PIN}.`);
        break;
      }
      tried.push(`${dir} (Symlink zeigt nach draussen)`);
    } catch { tried.push(`${dir} (kein playwright)`); }
  }
}
if (!chromium) {
  console.error("Playwright nicht gefunden. Geprueft:\n  " + [process.env.MT_PLAYWRIGHT_DIR, process.env.CLAUDE_PLUGIN_ROOT, "~/.cache/mt-playwright"].filter(Boolean).join("\n  ")
              + "\nDer aktuelle Arbeitsordner wird bewusst NICHT durchsucht. Installation: /meixner-toolkit:setup");
  process.exit(2);
}

const args = process.argv.slice(2);
// Vorher: args.find(a => /^https?:\/\//.test(a)) - damit wurde auch ein Wert wie
// --out https://... als Ziel-URL genommen. Jetzt: nur echte Positionsargumente.
const FLAGS_MIT_WERT = new Set(["--accept", "--reject", "--wait", "--out", "--path"]);
const positional = [];
for (let i = 0; i < args.length; i++) {
  if (FLAGS_MIT_WERT.has(args[i])) { i++; continue; }
  if (args[i].startsWith("--")) continue;
  positional.push(args[i]);
}
if (positional.length > 1) { console.error(`Mehrdeutig: ${positional.length} Positionsargumente (${positional.join(", ")}). Genau eine URL angeben.`); process.exit(2); }
const url = positional[0];
if (url && !/^https:\/\//i.test(url)) { console.error("Nur https-URLs erlaubt: " + url); process.exit(2); }
try { const u = new URL(url); if (u.username || u.password) { console.error("URLs mit Benutzername/Passwort sind nicht erlaubt."); process.exit(2); } } catch {}

const ECHT_SENDEN = args.includes("--echt-senden");
if (ECHT_SENDEN) console.error("WARNUNG: --echt-senden ist aktiv. Trackeraufrufe gehen tatsaechlich "
  + "an Google, Meta und den sGTM-Endpunkt und erzeugen dort echte Events. "
  + "Nur gegen Staging oder mit Test-IDs verwenden.");

// Schicht A: Start-URL pruefen, BEVOR ein Browser startet.
{
  const { erlaubt, grund } = await pruefeZiel(url);
  if (!erlaubt) {
    console.error(`ABBRUCH: Ziel-URL abgelehnt - ${grund}.`);
    console.error("Ein Audit darf nicht als Zugang zu internen Systemen dienen.");
    process.exit(2);
  }
}
if (!url) { console.error("Aufruf: node consent_test.mjs <url> [--accept css] [--reject css] [--wait ms] [--out datei] [--path /pfad]"); process.exit(2); }
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const WAIT = Number(opt("--wait", 6000));
const OUT = opt("--out", "consent-report.json");
const EXTRA_PATH = (() => {
  const v = opt("--path", null);
  if (v === null) return null;
  // Eine absolute Fremd-URL hier wuerde den Test auf eine andere Domain umlenken.
  if (!v.startsWith("/") || v.startsWith("//")) { console.error(`--path muss ein Pfad auf derselben Domain sein, beginnend mit / (erhalten: ${v})`); process.exit(2); }
  return v;
})();

const ACCEPT = [opt("--accept", null),
  "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll", "#CybotCookiebotDialogBodyButtonAccept",   // Cookiebot
  "[data-testid='uc-accept-all-button']",                                                          // Usercentrics
  "[data-borlabs-cookie-actions='accept-all']", "a._brlbs-btn-accept-all",                         // Borlabs
  ".cmplz-accept", "#cookie_action_close_header", ".cky-btn-accept",                               // Complianz, CookieYes
].filter(Boolean);
const REJECT = [opt("--reject", null),
  "#CybotCookiebotDialogBodyButtonDecline",
  "[data-testid='uc-deny-all-button']",
  "[data-borlabs-cookie-actions='accept-essential']", "a._brlbs-refuse-btn",
  ".cmplz-deny", ".cky-btn-reject",
].filter(Boolean);
const ACCEPT_TEXT = /^(alle akzeptieren|alles akzeptieren|alle zulassen|alle cookies akzeptieren|akzeptieren|zustimmen|einverstanden|accept all|allow all|accept)$/i;
const REJECT_TEXT = /^(ablehnen|alle ablehnen|nur notwendige|nur essenzielle|nur erforderliche|nur notwendige cookies|reject all|decline|deny)$/i;

// Trackingadressen enthalten Nutzerkennungen (cid, uid, em, gclid, fbp...). Der Bericht geht
// an den Kunden - deshalb werden Werte entfernt und nur die Parameternamen behalten.
const KEEP = new Set(["tid", "id", "en", "ev", "gcs", "gcd", "gtm", "v", "t"]);
function redact(u) {
  try {
    const x = new URL(u);
    for (const k of [...x.searchParams.keys()]) if (!KEEP.has(k)) x.searchParams.set(k, "<redigiert>");
    return (x.origin + x.pathname + "?" + x.searchParams.toString()).slice(0, 220);
  } catch { return "<unlesbare URL>"; }
}

// Ein Klick auf irgendeinen sichtbaren Button mit dem Wort "Akzeptieren" kann alles Moegliche
// treffen - ein Newsletter-Feld, eine Anzeige in einem fremden iframe. Der Texttreffer gilt
// deshalb nur innerhalb eines Containers, der wie ein CMP-Dialog aussieht.
const CMP_CONTAINER = [
  "#CybotCookiebotDialog", "#usercentrics-root", "#uc-center-container", "[id*='borlabs-cookie']",
  "#cmplz-cookiebanner-container", ".cky-consent-container", "#cookiescript_injected",
  "[id*='cookie' i][role='dialog']", "[class*='cookie' i][role='dialog']", "[aria-label*='consent' i]",
  "[aria-label*='cookie' i]", "[id*='consent' i]",
];

async function clickCmp(page, selectors, textRe) {
  // 1) bekannter Selektor - eindeutig, gilt in jedem Frame
  for (const frame of page.frames()) {
    for (const s of selectors) {
      try {
        const el = frame.locator(s).first();
        if (await el.isVisible({ timeout: 300 })) { await el.click({ timeout: 2000 }); return { how: `selector ${s}`, scoped: true }; }
      } catch {}
    }
  }
  // 2) Texttreffer nur innerhalb eines CMP-Containers
  for (const frame of page.frames()) {
    for (const c of CMP_CONTAINER) {
      try {
        const box = frame.locator(c).first();
        if (!(await box.isVisible({ timeout: 200 }))) continue;
        for (const role of ["button", "link"]) {
          const el = role === "button"
            ? box.getByRole("button").filter({ hasText: textRe }).first()
            : box.locator("a").filter({ hasText: textRe }).first();
          if (await el.isVisible({ timeout: 300 })) {
            const t = (await el.innerText()).trim();
            await el.click({ timeout: 2000 });
            return { how: `${role} "${t}" in ${c}`, scoped: true };
          }
        }
      } catch {}
    }
  }
  return null;
}

async function leseSpeicher(page) {
  try {
    return await page.evaluate(async () => {
      const dbs = (typeof indexedDB !== "undefined" && typeof indexedDB.databases === "function")
        ? await indexedDB.databases().then(xs => xs.map(x => x?.name).filter(Boolean)).catch(() => null)
        : null;
      return {
        localStorage: Object.keys(window.localStorage || {}).slice(0, 80),
        sessionStorage: Object.keys(window.sessionStorage || {}).slice(0, 80),
        indexedDB: { api_available: typeof indexedDB !== "undefined", databases: dbs, inspected: dbs !== null },
      };
    });
  } catch { return null; }
}

async function scenario(browser, name) {
  const ctx = await browser.newContext({ locale: "de-DE", timezoneId: "Europe/Berlin", serviceWorkers: "block" });

  // Schicht B: jeder Browserrequest laeuft durch die Policy - Navigation, Subressourcen,
  // XHR/fetch, Frames und Redirects. Dritte wie Google, Meta, CMPs und CDNs bleiben
  // erlaubt; blockiert werden ausschliesslich nicht oeffentliche Netzbereiche.
  const blockiert = [];
  await installiereNetzPolicy(ctx, {
    onBlock: e => blockiert.push(e),
    trackerAbbrechen: ECHT_SENDEN ? null : ((u, req) => shouldBlockTrackerDelivery(u, req, url)),
  });
  // Kein fester User Agent mehr: "Chrome/128.0" auf macOS passte weder zur tatsaechlichen
  // Chromium-Version noch zum Betriebssystem. CMPs und Tag-Manager werten den UA aus,
  // ein erfundener Stand kann das Messergebnis verfaelschen. Playwright setzt den UA
  // passend zur eingesetzten Engine.
  const page = await ctx.newPage();
  const hits = []; let phase = "vor_klick";
  page.on("response", r => { const h = hits.find(x => x.url && r.url().startsWith(x.url.split("?")[0]) && x.antwort === undefined);
    if (h) h.antwort = r.status(); });
  page.on("requestfailed", r => { const h = hits.find(x => x.url && r.url().startsWith(x.url.split("?")[0]) && x.antwort === undefined);
    if (h) h.antwort = "fehlgeschlagen: " + (r.failure()?.errorText || "unbekannt"); });
  page.on("request", r => {
    const u = r.url();
    const k = classify(u, url);
    const role = requestRole(u, r.resourceType(), url);
    if (k) hits.push({ phase, role, kind: k, method: r.method(), resourceType: r.resourceType(), ...parseTracking(u, r.postData()), url: redact(u) });
  });
  const res = emptyScenario(name, ECHT_SENDEN);
  try {
    const nav = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    if (!nav || !nav.ok()) {
      res.abbruch = "NAVIGATION_FEHLGESCHLAGEN";
      res.errors.push(`Seite antwortete mit ${nav ? nav.status() : "keiner Antwort"}`);
      res.hits = hits; await ctx.close(); return res;
    }
    await page.waitForTimeout(WAIT);
    res.datalayer_consent = await page.evaluate(() => (window.dataLayer || []).filter(e => e && e[0] === "consent")
      .map(e => ({ cmd: e[1], state: e[2] })).slice(0, 6)).catch(() => null);
    res.cookies_before = (await ctx.cookies()).filter(c => TRACK_COOKIES.test(c.name)).map(c => `${c.name}@${c.domain}`);
    res.speicher_before = await leseSpeicher(page);
    if (name !== "keine_interaktion") {
      phase = "nach_klick"; // vor dem Klick setzen: Requests, die der Klick synchron auslöst, zählen als "nach Klick"
      res.cmp_click = await clickCmp(page, name === "akzeptieren" ? ACCEPT : REJECT, name === "akzeptieren" ? ACCEPT_TEXT : REJECT_TEXT);
      if (!res.cmp_click) {
        res.abbruch = "CMP_BUTTON_NICHT_GEFUNDEN";
        res.errors.push("CMP-Button nicht gefunden – Selektor mit --accept/--reject angeben. "
                        + "Das Szenario wurde NICHT geprueft.");
        res.hits = hits; await ctx.close(); return res;
      }
      await page.waitForTimeout(WAIT);
      if (EXTRA_PATH) { await page.goto(new URL(EXTRA_PATH, url).href, { waitUntil: "domcontentloaded" }); await page.waitForTimeout(WAIT / 2); }
    }
  } catch (e) {
    res.abbruch = res.abbruch || "BROWSER_FEHLER";
    res.errors.push(String(e).slice(0, 200));
  }
  try {
    res.cookies_after = (await ctx.cookies()).filter(c => TRACK_COOKIES.test(c.name)).map(c => `${c.name}@${c.domain}${c.httpOnly ? " (HttpOnly)" : ""}`);
  } catch { res.cookies_after = []; }
  res.speicher_after = await leseSpeicher(page);
  res.speicher_delta = storageDelta(res.speicher_before, res.speicher_after);
  res.hits = hits;
  res.blockiert = blockiert.slice(0, 50);
  res.echt_gesendet = ECHT_SENDEN;
  res.status = (!res.abbruch && !res.errors.length) ? "geprueft" : "unknown";
  await ctx.close();
  return res;
}

const browser = await chromium.launch({ headless: true });
const results = [];
for (const s of ["keine_interaktion", "akzeptieren", "ablehnen"]) { process.stderr.write(`Szenario ${s} …\n`); results.push(await scenario(browser, s)); }
await browser.close();
const report = { url, datum: new Date().toISOString(), wartezeit_ms: WAIT, bewertung: assess(results), szenarien: results };
if (fs.existsSync(OUT) && !args.includes("--force")) {
  console.error(`ABBRUCH: ${OUT} existiert bereits. Anderen Namen mit --out waehlen oder --force setzen.`);
  process.exit(2);
}
const part = OUT + ".part";
if (fs.existsSync(part)) {
  console.error(`ABBRUCH: ${part} existiert bereits. Stale .part-Datei entfernen oder anderes --out waehlen.`);
  process.exit(2);
}
try {
  fs.writeFileSync(part, JSON.stringify(report, null, 2), { encoding: "utf8", mode: 0o600, flag: "wx" });
  fs.renameSync(part, OUT);
  if (process.platform !== "win32") fs.chmodSync(OUT, 0o600);
} catch (e) {
  try { if (fs.existsSync(part)) fs.unlinkSync(part); } catch {}
  throw e;
}
console.log(`Bericht: ${OUT}\n` + report.bewertung.map(x => "- " + x).join("\n"));
for (const r of results) {
  const hitsN = Array.isArray(r.hits) ? r.hits.length : 0;
  const cookies = Array.isArray(r.cookies_after) ? r.cookies_after : [];
  const errors = Array.isArray(r.errors) ? r.errors : [];
  console.log(`\n[${r.scenario}] Status: ${r.abbruch ? "NICHT GEPRUEFT (" + r.abbruch + ")" : r.status} | CMP-Klick: ${r.cmp_click ? r.cmp_click.how : "-"} | Hits: ${hitsN} | Cookies: ${cookies.join(", ") || "keine"}${errors.length ? " | Fehler: " + errors.join("; ") : ""}`);
}
