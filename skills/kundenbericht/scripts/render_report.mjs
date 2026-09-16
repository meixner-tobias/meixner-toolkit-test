#!/usr/bin/env node
// Kundenbericht aus einer oder mehreren audit.json-Dateien – Brief + vollständige, aufklappbare Punkteliste.
// Gestaltung folgt meixner-tobias.com: Archivo (Überschriften), Newsreader (Text), Papier auf Ink, Signalfarbe Amber.
//   node render_report.mjs audit.json [weitere.json …] --out bericht.html [--pdf bericht.pdf] [--voll] [--teaser [--top 3]] [--config pfad]
// Standard: ALLE gefundenen Punkte, je Punkt Problem, Folge, Nachweis, Aufwand – aber keine Maßnahme.
//   --voll    zusätzlich „Was zu tun ist“ (für beauftragte Kunden)
//   --teaser  Kurzfassung für Erstkontakt: nur die wichtigsten N Punkte, Rest als Anzahl je Bereich
//   --pdf     dasselbe noch einmal als PDF (alles aufgeklappt, Seitenzahlen); braucht Playwright
import fs from "fs";
import path from "path";
import os from "os";
import { createRequire } from "module";
import { fileURLToPath } from "url";
import { pruefeZiel, installiereNetzPolicy } from "../../../lib/netpolicy.mjs";

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const valueFlags = ["--out", "--pdf", "--config", "--top"];
const flagVals = new Set(valueFlags.flatMap(k => { const i = args.indexOf(k); return i >= 0 ? [args[i + 1]] : []; }));
const inputs = args.filter(a => a.endsWith(".json") && !flagVals.has(a));
if (!inputs.length) { console.error("Aufruf: node render_report.mjs audit.json [...] --out bericht.html [--pdf bericht.pdf] [--voll] [--teaser [--top 3]]"); process.exit(2); }

const home = process.env.MEIXNER_TOOLKIT_HOME || path.join(os.homedir(), ".meixner-toolkit");
const cfgPath = opt("--config", path.join(home, "config.json"));
const cfg = fs.existsSync(cfgPath) ? JSON.parse(fs.readFileSync(cfgPath, "utf8")) : {};
const brand = cfg.branding || {}, offer = cfg.angebot || {};
const OUT = opt("--out", "kundenbericht.html"), PDF = opt("--pdf", null);
const FULL = args.includes("--voll");          // mit Maßnahmen
const TEASER = args.includes("--teaser");      // Kurzfassung
const TOP = Math.max(1, Number(opt("--top", 3)));

const audits = inputs.map(f => JSON.parse(fs.readFileSync(f, "utf8")));

// --- Schemapruefung: lieber abbrechen als einen halben Bericht an den Kunden geben ---
// Einzige Quelle der Wahrheit: references/audit-schema.md.
// In 0.7.5 standen hier erfundene Werte ("ok", "achtung"), die das eigene Beispiel
// beispiel-seogeo.json abgelehnt haetten. Die Listen unten sind woertlich aus dem
// Schema uebernommen und muessen mit WORT/PRIO_WORT weiter unten uebereinstimmen.
const TYP = new Set(["seogeo", "seo", "geo", "tracking", "launch"]);
const STATUS = new Set(["gut", "mittel", "kritisch", "nicht_geprueft"]);
const PRIO = new Set(["kritisch", "hoch", "mittel", "niedrig"]);
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
for (const [i, a] of audits.entries()) {
  const q = `${inputs[i]}`;
  if (!a.domain) { console.error(`ABBRUCH: ${q} hat kein Feld "domain".`); process.exit(2); }
  if (!a.kunde)  { console.error(`ABBRUCH: ${q} hat kein Feld "kunde".`); process.exit(2); }
  if (a.typ && !TYP.has(a.typ)) { console.error(`ABBRUCH: ${q}: unbekannter typ "${a.typ}". Erlaubt: ${[...TYP].join(", ")}`); process.exit(2); }
  for (const b of a.scorecard || []) if (b.status && !STATUS.has(b.status)) {
    console.error(`ABBRUCH: ${q}: unbekannter Status "${b.status}". Erlaubt: ${[...STATUS].join(", ")}`); process.exit(2); }
  for (const f of a.findings || []) if (f.prioritaet && !PRIO.has(f.prioritaet)) {
    console.error(`ABBRUCH: ${q}: unbekannte Prioritaet "${f.prioritaet}". Erlaubt: ${[...PRIO].join(", ")}`); process.exit(2); }
}

// Mehrere Audits duerfen nur zusammengefuehrt werden, wenn sie denselben Kunden betreffen.
{
  const norm = v => String(v ?? "").trim().toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/$/, "");
  const doms = [...new Set(audits.map(a => norm(a.domain)).filter(Boolean))];
  const kunden = [...new Set(audits.map(a => norm(a.kunde)).filter(Boolean))];
  if (doms.length > 1 || kunden.length > 1) {
    console.error("ABBRUCH: Die uebergebenen Audits gehoeren nicht zusammen.");
    if (doms.length > 1) console.error("  Domains: " + doms.join(", "));
    if (kunden.length > 1) console.error("  Kunden : " + kunden.join(", "));
    console.error("  Ein Bericht je Kunde erzeugen.");
    process.exit(2);
  }
}
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------- Kontextgerechte Validierung (Phase 7) ----------
// Alles aus audit.json und config.json ist ungeprueft, bis es hier durchgelaufen ist.
const warn = m => console.error("WARNUNG: " + m);

// Ganze Zahl oder nichts – fuer scorecard[].anzahl
const zahlOderNichts = v => (Number.isInteger(v) && v >= 0 && v < 100000) ? String(v) : null;

// CSS: nur Schriftlisten aus Namen, Anfuehrungszeichen und generischen Familien
const CSS_FONT = /^[\w\s"'-]{1,120}$/;
const safeFontStack = (v, fallback) => {
  if (!v) return fallback;
  if (!CSS_FONT.test(v) || /[;{}()@\\]|url|import|expression/i.test(v)) {
    warn(`branding.schrift enthaelt unerlaubte Zeichen und wird ignoriert: ${JSON.stringify(v)}`);
    return fallback;
  }
  return v;
};

// URLs: nur http/https bzw. mailto/tel, nie javascript:/data:
const safeUrl = (v, { allowMail = false } = {}) => {
  if (!v) return null;
  const raw = String(v).trim();
  const withScheme = /^[a-z][a-z0-9+.-]*:/i.test(raw) ? raw : "https://" + raw;
  let u;
  try { u = new URL(withScheme); } catch { warn(`Unlesbare URL verworfen: ${raw}`); return null; }
  const ok = ["http:", "https:"].concat(allowMail ? ["mailto:", "tel:"] : []);
  if (!ok.includes(u.protocol)) { warn(`URL mit unerlaubtem Schema verworfen: ${u.protocol}`); return null; }
  return u.href;
};

// Pfade: nur unterhalb erlaubter Wurzeln einbetten
const IMG_EXT = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]);
const ROOTS = [home, process.cwd()].map(r => path.resolve(r));
const ROOTS_REAL = ROOTS.map(r => { try { return fs.realpathSync(r); } catch { return null; } }).filter(Boolean);
const unterWurzel = (p, roots = ROOTS) => roots.some(r => p === r || p.startsWith(r + path.sep));

function sichereAusgabe(zielRaw, data, { force = false, mode = 0o600 } = {}) {
  const ziel = path.resolve(zielRaw);
  if (!unterWurzel(ziel)) throw new Error(`Ausgabe ${ziel} liegt ausserhalb von ${ROOTS.join(" / ")}.`);
  let parentReal;
  try { parentReal = fs.realpathSync(path.dirname(ziel)); }
  catch { throw new Error(`Ausgabeordner von ${ziel} ist nicht aufloesbar.`); }
  if (!unterWurzel(parentReal, ROOTS_REAL))
    throw new Error(`Ausgabeordner ${parentReal} liegt nach Symlink-Aufloesung ausserhalb der erlaubten Wurzeln.`);

  if (fs.existsSync(ziel)) {
    const st = fs.lstatSync(ziel);
    if (st.isSymbolicLink()) throw new Error(`Ausgabe ${ziel} ist ein Symlink/Junction und wird nicht ueberschrieben.`);
    if (!force) throw new Error(`${ziel} existiert bereits. Anderen Namen waehlen oder --force setzen.`);
  }
  const tmp = ziel + ".part";
  // Exklusive Erstellung: ein vorbereiteter .part-Symlink darf niemals verfolgt werden.
  let fd = null, created = false;
  try {
    fd = fs.openSync(tmp, "wx", mode);
    created = true;
    fs.writeFileSync(fd, data);
    fs.fsyncSync(fd);
    fs.closeSync(fd); fd = null;
    if (process.platform !== "win32") fs.chmodSync(tmp, mode);
    try {
      fs.renameSync(tmp, ziel);
    } catch (e) {
      // Windows ersetzt bestehende Dateien per rename nicht immer atomar. --force darf
      // nur eine zuvor gepruefte regulaere Datei entfernen, niemals einen Symlink.
      if (force && ["EEXIST", "EPERM", "EACCES"].includes(e.code) && fs.existsSync(ziel)) {
        if (fs.lstatSync(ziel).isSymbolicLink()) throw e;
        fs.unlinkSync(ziel);
        fs.renameSync(tmp, ziel);
      } else throw e;
    }
    created = false;
    if (process.platform !== "win32") fs.chmodSync(ziel, mode);
    return ziel;
  } finally {
    if (fd !== null) try { fs.closeSync(fd); } catch {}
    if (created) try { fs.unlinkSync(tmp); } catch {}
  }
}

const safeLocalImage = (v, feld) => {
  if (!v) return null;
  const abs = path.resolve(String(v).replace(/^~(?=$|[/\\])/, os.homedir()));
  if (!ROOTS.some(r => abs === r || abs.startsWith(r + path.sep))) {
    warn(`${feld}: ${abs} liegt ausserhalb von ${ROOTS.join(" und ")} – nicht eingebettet.`);
    return null;
  }
  if (!IMG_EXT.has(path.extname(abs).toLowerCase())) {
    warn(`${feld}: ${path.extname(abs) || "(ohne Endung)"} ist kein erlaubtes Bildformat – nicht eingebettet.`);
    return null;
  }
  if (!fs.existsSync(abs)) { warn(`${feld}: ${abs} nicht gefunden.`); return null; }
  try {
    if (fs.lstatSync(abs).isSymbolicLink()) { warn(`${feld}: ${abs} ist ein Symlink/Junction - abgelehnt.`); return null; }
    const real = fs.realpathSync(abs);
    if (!ROOTS.some(r => real === r || real.startsWith(r + path.sep))) {
      warn(`${feld}: ${real} liegt nach Aufloesung ausserhalb der erlaubten Ordner - abgelehnt.`); return null; }
  } catch { warn(`${feld}: Pfad nicht aufloesbar.`); return null; }
  const bytes = fs.statSync(abs).size;
  if (bytes > 2_000_000) { warn(`${feld}: ${Math.round(bytes / 1024)} KB ist zu gross (max. 2 MB).`); return null; }
  return abs;
};
const mime = f => "image/" + path.extname(f).slice(1).toLowerCase().replace("jpg", "jpeg").replace("svg", "svg+xml");

// ---------- Schriften (OFL, eingebettet – keine externen Aufrufe) ----------
const FONT_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "fonts");
const fontFace = (fam, file, weight, style) => { const f = path.join(FONT_DIR, file); return fs.existsSync(f)
  ? `@font-face{font-family:"${fam}";src:url(data:font/woff;base64,${fs.readFileSync(f).toString("base64")}) format("woff");font-weight:${weight};font-style:${style};font-display:swap}` : ""; };
const faces = safeFontStack(brand.schrift, null) ? "" : [
  fontFace("MT Serif", "nr-400.woff", "400", "normal"), fontFace("MT Serif", "nr-600.woff", "600 800", "normal"),
  fontFace("MT Serif", "nr-italic.woff", "400", "italic"), fontFace("MT Display", "nr-display.woff", "400", "normal"),
  fontFace("MT Sans", "ar-580.woff", "500 700", "normal"),
].join("");
const serif = safeFontStack(brand.schrift, '"MT Serif", "Newsreader", "Charter", "Georgia", serif');
const sans = '"MT Sans", "Archivo", "Helvetica Neue", "Segoe UI", Arial, sans-serif';
const signal = /^#[0-9a-f]{6}$/i.test(brand.farbe || "") ? brand.farbe : "#7d5310"; // Amber auf Papier

// ---------- Wortlisten ----------
const BEREICH_TYP = { seogeo: "Google & KI-Suche", seo: "Google-Suche", geo: "KI-Suche", tracking: "Tracking & Datenschutz", launch: "Livegang" };
const WORT = { gut: "solide", mittel: "ausbaufähig", kritisch: "dringend", nicht_geprueft: "nicht geprüft" };
const PRIO_WORT = { kritisch: "dringend", hoch: "wichtig", mittel: "sinnvoll", niedrig: "Feinschliff" };
const PRIO_KL = { kritisch: "p-krit", hoch: "p-hoch", mittel: "p-mit", niedrig: "p-nied" };
const AUFWAND = { S: "gering", M: "mittel", L: "größer" };
const order = ["kritisch", "hoch", "mittel", "niedrig"];
// Feste Bereichsnamen (references/audit-schema.md) – bestimmen Reihenfolge in Übersicht und Punkteliste
const KANON = ["Technik", "Ladezeit", "Inhalte", "KI-Suche", "Google-Profil & Einträge", "Messung", "Werbekonten", "Recht & Einwilligung"];
const kanonIdx = b => { const i = KANON.indexOf(b); return i < 0 ? 99 : i; };
const ANLASS = {
  seogeo: "die Technik dahinter, die Inhalte und wie gut Sie bei Google und in KI-Assistenten wie ChatGPT gefunden werden",
  seo: "die Technik dahinter, die Inhalte und wie gut Sie bei Google gefunden werden",
  geo: "wie gut Sie in KI-Assistenten wie ChatGPT, Perplexity oder Googles KI-Übersichten auftauchen",
  tracking: "wie Ihre Website Besucher und Anfragen misst und ob dabei der Datenschutz eingehalten wird",
  launch: "ob beim Livegang alles sauber gelaufen ist",
};

const host = u => { try { return new URL(/^https?:/.test(u) ? u : "https://" + u).host.replace(/^www\./, ""); } catch { return u; } };
const url = u => (/^https?:/.test(u) ? u : "https://" + u);
const tel = t => String(t).replace(/[^+0-9]/g, "");
const fmtDate = d => { try { return new Date(d).toLocaleDateString("de-DE", { day: "numeric", month: "long", year: "numeric" }); } catch { return d; } };
const zahl = k => ["keinen", "einen", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf"][k] ?? String(k);
const Zahl = k => zahl(k).replace(/^./, c => c.toUpperCase());
const punkte = k => (k === 1 ? "einen Punkt" : `${zahl(k)} Punkte`);

// ---------- Daten ----------
const a0 = audits[0];
const domain = host(a0.domain);
const datum = audits.map(a => a.datum).sort().at(-1);
const findings = audits.flatMap(a => (a.findings || []).map(f => ({ ...f, _typ: a.typ })))
  .sort((x, y) => order.indexOf(x.prioritaet) - order.indexOf(y.prioritaet));
findings.forEach(f => { f._bereich = f.bereich || BEREICH_TYP[f._typ] || "Sonstiges"; });
const n = findings.length;
const dringend = findings.filter(f => f.prioritaet === "kritisch" || f.prioritaet === "hoch").length;
const top = findings.slice(0, TOP), rest = findings.slice(TOP);

// Nicht geprueft bleibt sichtbar - sonst sieht es aus, als waere dort alles in Ordnung
// (eigene Regel: references/audit-schema.md).
const bereiche = audits.flatMap(a => a.scorecard || [])
  .sort((a, b) => kanonIdx(a.bereich) - kanonIdx(b.bereich));
const typen = new Set(audits.map(a => a.typ).flatMap(t => t === "seogeo" ? ["seogeo", "seo", "geo"] : [t]));
const leistungen = (offer.leistungen || []).filter(l => !l.typen || l.typen.some(t => typen.has(t)));

// Gruppen in der Reihenfolge der Übersicht, danach der Rest
const scoreOrder = [...new Set(audits.flatMap(a => (a.scorecard || []).map(b => b.bereich)))];
const gruppen = [...new Set(findings.map(f => f._bereich))]
  .sort((a, b) => kanonIdx(a) - kanonIdx(b)
    || (scoreOrder.indexOf(a) + 1 || 99) - (scoreOrder.indexOf(b) + 1 || 99)
    || a.localeCompare(b, "de"));
const fremd = [...new Set([...findings.map(f => f._bereich), ...bereiche.map(b => b.bereich)])].filter(b => !KANON.includes(b));
if (fremd.length) console.error(`Hinweis: Bereich nicht in der festen Liste (references/audit-schema.md): ${fremd.join(", ")} – Bericht wird trotzdem erzeugt, Gruppe steht am Ende.`);
// Nummern in Lesereihenfolge vergeben (Teaser: nach Dringlichkeit, sonst nach Gruppen)
(TEASER ? findings : gruppen.flatMap(g => findings.filter(f => f._bereich === g)))
  .forEach((f, i) => { f._nr = String(i + 1).padStart(2, "0"); });

// Teaser: Rest nur als Anzahl je Bereich
const restByArea = {};
for (const f of rest) restByArea[f._bereich] = (restByArea[f._bereich] || 0) + 1;
const areas = Object.keys(restByArea);
const areaList = areas.length > 1 ? areas.slice(0, -1).join(", ") + " und " + areas.at(-1) : areas[0];
const restDringend = rest.filter(f => f.prioritaet === "kritisch" || f.prioritaet === "hoch").length;
const restSatz = rest.length === 1 ? `Dazu kommt ein weiterer Punkt aus dem Bereich ${areaList}.`
  : `Dazu kommen ${zahl(rest.length)} weitere Punkte aus ${areas.length > 1 ? "den Bereichen" : "dem Bereich"} ${areaList}.`;

// ---------- Textbausteine ----------
const gruss = a0.ansprechpartner ? `Hallo ${esc(a0.ansprechpartner)},` : "Guten Tag,";
const anlass = [...new Set(audits.map(a => ANLASS[a.typ]).filter(Boolean))].join(", außerdem ");
const intro = a0.anschreiben ? esc(a0.anschreiben)
  : `ich habe mir ${esc(domain)} am ${esc(fmtDate(datum))} genauer angesehen: ${esc(anlass)}. Hier steht, was mir aufgefallen ist und womit ich an Ihrer Stelle anfangen würde.`;
const bilanz = n === 0 ? "Ich habe keine nennenswerten Probleme gefunden."
  : `Insgesamt sind mir ${punkte(n)} aufgefallen.` + (dringend ? ` ${dringend === 1 ? "Einen davon" : Zahl(dringend) + " davon"} würde ich zeitnah angehen.` : "")
    + (TEASER ? "" : " Alle stehen unten, jeder Punkt lässt sich aufklappen.");

// ---------- Bausteine ----------
let sig = "";
{ const p = safeLocalImage(brand.unterschrift, "branding.unterschrift");
  if (p) sig = `<img class="sig" src="data:${mime(p)};base64,${fs.readFileSync(p).toString("base64")}" alt="">`; }
let logo = "";
if (brand.logo) {
  if (/^https?:\/\//i.test(brand.logo) && !args.includes("--remote-logo")) {
    warn(`branding.logo ist eine externe Adresse und wird NICHT eingebettet. `
       + `Der Betreiber der Adresse saehe sonst, wann der Kunde den Bericht oeffnet, `
       + `und das PDF-Rendern wuerde die Datei nachladen. Lokale Datei hinterlegen oder --remote-logo setzen.`);
  } else if (/^https?:\/\//i.test(brand.logo)) {
    // Ein Remote-Logo laedt beim Oeffnen des Berichts UND beim PDF-Rendern nach.
    // Vor dem Einbetten muss auch dieser opt-in Netzwerkpfad durch dieselbe Public-Network-Policy.
    const u = safeUrl(brand.logo);
    if (u) {
      const netz = await pruefeZiel(u);
      if (!netz.erlaubt) warn(`branding.logo wurde von der Netzwerkpolicy abgelehnt: ${netz.grund}.`);
      else {
        warn(`branding.logo ist eine externe Adresse (${u}). Der Bericht laedt sie beim Oeffnen nach. Fuer einen geschlossenen Bericht eine lokale Datei hinterlegen.`);
        logo = `<img class="logo" src="${esc(u)}" alt="">`;
      }
    }
  } else {
    const p = safeLocalImage(brand.logo, "branding.logo");
    if (p) logo = `<img class="logo" src="data:${mime(p)};base64,${fs.readFileSync(p).toString("base64")}" alt="">`;
  }
}

let sec = 0;
const NAV = [];
const h2 = (t, extra = "") => { const id = `abschnitt-${++sec}`; NAV.push([id, t]);
  return `<div class="head" id="${id}"><h2><span class="no">${sec}</span>${esc(t)}</h2>${extra}</div>`; };

// Ein Punkt: zugeklappt eine Zeile, aufgeklappt Problem, Folge, Nachweis, (Maßnahme)
const punkt = f => `<details class="f" id="punkt-${f._nr}">
  <summary><span class="nr">${f._nr}</span><span class="ti">${esc(f.titel)}</span><span class="chip ${PRIO_KL[f.prioritaet] || ""}">${esc(PRIO_WORT[f.prioritaet] || "")}</span></summary>
  <div class="fb">
    <p>${esc(f.problem)}${f.auswirkung ? ` <span class="folge">${esc(f.auswirkung)}</span>` : ""}</p>
    ${FULL && f.massnahme ? `<p class="fix"><span>Was zu tun ist:</span> ${esc(f.massnahme)}</p>` : ""}
    ${(f.nachweis || f.aufwand) ? `<p class="meta">${f.nachweis ? `<span class="k">Geprüft</span> ${esc(f.nachweis)}` : ""}${f.aufwand && AUFWAND[f.aufwand] ? `${f.nachweis ? "<br>" : ""}<span class="k">Aufwand</span> ${esc(AUFWAND[f.aufwand])}` : ""}</p>` : ""}
  </div>
</details>`;

const gruppe = g => { const list = findings.filter(f => f._bereich === g);
  return `<div class="grp"><p class="grp-h">${esc(g)}<span>${list.length} ${list.length === 1 ? "Punkt" : "Punkte"}</span></p>${list.map(punkt).join("")}</div>`; };

const startBlock = (!TEASER && n > 6) ? `<div class="start"><p class="start-h">Womit ich anfangen würde</p><ol>${
  findings.slice(0, 3).map(f => `<li><a href="#punkt-${f._nr}">${esc(f.titel)}</a></li>`).join("")}</ol></div>` : "";

const html = `<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Website-Check ${esc(domain)} · ${esc(fmtDate(datum))}</title>
<style>
${faces}
:root{--signal:${signal};--ink:#0c1315;--paper:#faf8f3;--text:#14191a;--soft:#4e5658;--line:#ded7c9;--line-2:#c6bdad;--krit:#a8341f}
*{box-sizing:border-box}
html{background:var(--ink);scroll-behavior:smooth}
body{margin:0;color:var(--text);font:10.5pt/1.65 ${serif};-webkit-font-smoothing:antialiased}
.sheet{max-width:210mm;margin:30px auto;background:var(--paper);padding:16mm 22mm 18mm;border-top:3px solid var(--signal)}
h1,h2,h3,.grp-h,.chip,.label,.k,.start-h,.toggle,.toc,.w,.sub,.letterhead,.fine{font-family:${sans}}
.letterhead{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;font-size:8.5pt;line-height:1.5;color:var(--soft);padding-bottom:9px;border-bottom:1px solid var(--line)}
.letterhead strong{color:var(--text);font-weight:600;letter-spacing:-.01em}
.letterhead a{color:inherit;text-decoration:none;border-bottom:1px solid transparent}
.letterhead a:hover{color:var(--signal);border-color:var(--line-2)}
.logo{max-height:26px;max-width:140px;display:block;margin-bottom:6px}
.label{font-size:7.5pt;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--signal);margin:30px 0 8px}
h1{font-size:26pt;font-weight:600;line-height:1.05;letter-spacing:-.03em;margin:0;color:var(--ink)}
.sub{font-size:9pt;color:var(--soft);margin:7px 0 28px}
.letter p{max-width:70ch;margin:0 0 10px}
.head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:30px 0 12px;padding-top:12px;border-top:1px solid var(--line-2);break-after:avoid}
h2{font-size:12.5pt;font-weight:600;letter-spacing:-.015em;margin:0;color:var(--ink)}
h2 .no{display:inline-block;width:20px;color:var(--signal)}
.toggle{font-size:8.5pt;color:var(--soft);background:none;border:0;border-bottom:1px solid var(--line-2);padding:0 0 1px;cursor:pointer}
.toggle:hover{color:var(--signal);border-color:var(--signal)}
table{border-collapse:collapse;width:100%;font-size:10.5pt}
td{padding:6px 0;border-bottom:1px solid var(--line);vertical-align:top}
td.w{font-size:9pt;color:var(--soft);text-align:right;white-space:nowrap}
td.w.d{color:var(--krit);font-weight:600}
.start{margin:16px 0 0;padding:12px 16px;background:#f2eee5;border-left:2px solid var(--signal);max-width:70ch}
.start-h{font-size:8pt;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--soft);margin:0 0 6px}
.start ol{margin:0;padding-left:18px}.start li{margin:2px 0}
.start a{color:var(--text);text-decoration:none;border-bottom:1px solid var(--line-2)}
.start a:hover{color:var(--signal);border-color:var(--signal)}
.grp{margin:0 0 18px}
.grp-h{display:flex;justify-content:space-between;align-items:baseline;font-size:8pt;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--soft);margin:18px 0 0;padding-bottom:5px;border-bottom:1px solid var(--line-2);break-after:avoid}
.grp-h span{letter-spacing:0;text-transform:none;font-weight:500;color:var(--soft)}
details.f{border-bottom:1px solid var(--line);break-inside:avoid}
details.f>summary{display:flex;gap:10px;align-items:baseline;padding:8px 0;cursor:pointer;list-style:none}
details.f>summary::-webkit-details-marker{display:none}
details.f>summary:hover .ti{color:var(--signal)}
.nr{font-size:8.5pt;font-weight:600;color:var(--line-2);min-width:18px;font-variant-numeric:tabular-nums}
.ti{flex:1;font-family:${sans};font-size:10pt;font-weight:600;letter-spacing:-.01em;line-height:1.35;color:var(--ink)}
details.f[open] .nr{color:var(--signal)}
.chip{font-size:7pt;font-weight:600;letter-spacing:.11em;text-transform:uppercase;color:var(--soft);white-space:nowrap}
.chip.p-krit{color:var(--krit)}.chip.p-hoch{color:var(--signal)}
.fb{padding:0 0 12px 28px;max-width:70ch}
.fb p{margin:0 0 6px}
.folge{color:var(--soft)}
.fix{font-size:10pt}.fix span{font-style:italic;color:var(--soft)}
.meta{font-size:8.5pt;line-height:1.5;color:var(--soft)}
.meta .k{font-family:${sans};font-size:7pt;font-weight:600;letter-spacing:.11em;text-transform:uppercase;margin-right:6px}
.weitere{margin:14px 0;padding:10px 16px;background:#f2eee5;border-left:2px solid var(--signal);max-width:70ch}
.weitere>summary{cursor:pointer;list-style:none;font-family:${sans};font-size:9pt;color:var(--soft);display:flex;gap:6px}
.weitere>summary::-webkit-details-marker{display:none}
.weitere>summary:before{content:"+";color:var(--signal);font-weight:600}
.weitere[open]>summary:before{content:"–"}
.weitere p{margin:6px 0 0}
ul.plain{list-style:none;padding:0;margin:0;max-width:70ch}ul.plain li{padding-left:14px;position:relative;margin:3px 0}
ul.plain li:before{content:"–";position:absolute;left:0;color:var(--line-2)}
.offer td:last-child{text-align:right;white-space:nowrap;color:var(--soft)}
.close{margin-top:24px;break-inside:avoid}.close p{margin:0}
.sig{height:42px;display:block;margin:6px 0 2px}
.fine{margin-top:30px;font-size:7.5pt;line-height:1.55;color:var(--soft);max-width:70ch}
.toc{font-size:9pt;line-height:1.9;color:var(--soft);margin:0 0 24px}
.toc a{color:var(--soft);text-decoration:none;border-bottom:1px solid var(--line)}
.toc a:hover{color:var(--signal);border-color:var(--signal)}
.toc i{color:var(--line-2);font-style:normal;margin:0 3px}
a{color:var(--signal)}
:focus-visible{outline:2px solid var(--signal);outline-offset:2px}
@page{size:A4;margin:16mm 0}
@media print{html{background:#fff}body{font-size:10pt}
  .sheet{margin:0;max-width:none;padding:0 20mm;background:none;border-top:0}
  .toc,.toggle{display:none}
  details::details-content{content-visibility:visible!important}
  details.f>summary,.weitere>summary{cursor:auto}.weitere>summary:before,.weitere[open]>summary:before{content:""}
  details.f[open] .nr{color:var(--line-2)}
  details.f{break-inside:auto}details.f>summary{break-after:avoid}.fb{break-inside:auto}
  .start,.weitere{background:none}
  a{text-decoration:none}}
@media (max-width:640px){.sheet{padding:22px 18px;margin:0;border-top-width:2px}
  .letterhead{flex-direction:column;align-items:flex-start;gap:6px}.letterhead>div:last-child{text-align:left!important}
  h1{font-size:21pt}.fb{padding-left:0}
  details.f>summary{flex-wrap:wrap}.chip{width:100%;padding-left:28px}}
</style></head><body><div class="sheet">

<div class="letterhead">
  <div>${logo}<strong>${esc(brand.firma || brand.name || "")}</strong></div>
  <div style="text-align:right">${[
    brand.website && `<a href="${esc(url(brand.website))}">${esc(host(brand.website))}</a>`,
    brand.email && `<a href="mailto:${esc(brand.email)}">${esc(brand.email)}</a>`,
    brand.telefon && `<a href="tel:${esc(tel(brand.telefon))}">${esc(brand.telefon)}</a>`,
  ].filter(Boolean).join("<br>")}</div>
</div>

<p class="label">Website-Check</p>
<h1>${esc(domain)}</h1>
<p class="sub">für ${esc(a0.kunde || domain)} · ${esc(fmtDate(datum))}</p>

<div class="letter"><p>${gruss}</p><p>${intro}</p><p>${esc(bilanz)}</p></div>

<!--NAV-->

${bereiche.length ? `${h2("Auf einen Blick")}
<table>${bereiche.map(b => { const anz = zahlOderNichts(b.anzahl); return `<tr><td>${esc(b.bereich)}</td><td class="w${b.status === "kritisch" ? " d" : ""}">${esc(WORT[b.status] || b.status)}${anz ? ` · ${esc(anz)}` : ""}</td></tr>`; }).join("")}</table>
${startBlock}` : ""}

${n ? (TEASER
  ? `${h2(top.length === 1 ? "Der wichtigste Punkt" : `Die ${zahl(top.length)} wichtigsten Punkte`)}
${top.map(punkt).join("")}
${rest.length ? `<details class="weitere"><summary>${esc(restSatz)}</summary><p>${
  esc(areas.length > 1 ? "Verteilung: " + areas.map(a => `${a} ${restByArea[a]}`).join(" · ") + "." : `Alle ${zahl(rest.length)} betreffen ${areaList}.`)} ${
  esc(restDringend ? (restDringend === 1 ? "Einer davon ist zeitkritisch." : `${Zahl(restDringend)} davon sind zeitkritisch.`) : "Keiner davon ist zeitkritisch.")} Die vollständige Liste gehe ich gern mit Ihnen gemeinsam durch.</p></details>` : ""}`
  : `${h2(`Alle Punkte (${n})`, `<button class="toggle" type="button" id="alle">Alle aufklappen</button>`)}
${gruppen.map(gruppe).join("")}`) : ""}

${(() => { const good = [...new Set(audits.flatMap(a => a.positiv || []))]; return good.length ? `${h2("Was schon gut ist")}<ul class="plain">${good.map(g => `<li>${esc(g)}</li>`).join("")}</ul>` : ""; })()}

${h2("Wie es weitergehen kann")}
<div class="letter"><p>${FULL ? "Wenn Sie möchten, setze ich die Punkte der Reihe nach für Sie um, beginnend mit den dringenden."
  : "Wenn Sie mögen, gehen wir die Liste gemeinsam durch: Ich sage Ihnen zu jedem Punkt, was dahintersteckt, wie viel Aufwand er macht und was er bringt. Kostenlos und ohne Verpflichtung."}</p></div>
${leistungen.length ? `<table class="offer">${leistungen.map(l => `<tr><td>${esc(l.name)}</td><td>${esc(l.preis)}</td></tr>`).join("")}</table>` : ""}

<div class="close">
  <p style="margin-bottom:14px">Melden Sie sich einfach, per Mail${brand.telefon ? " oder Telefon" : ""} oder direkt über den Link unten. Ich freue mich auf das Gespräch.</p>
  <p>Viele Grüße</p>${sig}
  <p style="margin-top:${sig ? "0" : "14px"}">${esc(brand.name || "")}</p>
  ${safeUrl(offer.cta_link) ? `<p class="sub" style="margin:4px 0 0"><a href="${esc(safeUrl(offer.cta_link))}">${esc(offer.cta || safeUrl(offer.cta_link))}</a>${brand.telefon ? ` · <a href="tel:${esc(tel(brand.telefon))}">${esc(brand.telefon)}</a>` : ""}</p>` : ""}
</div>

<p class="fine">Stand ${esc(fmtDate(datum))}. Grundlage ist eine technische Prüfung der öffentlich erreichbaren Website${a0.umfang ? " (" + esc(a0.umfang) + ")" : ""}. Platzierungen bei Google oder in KI-Assistenten lassen sich nicht garantieren. Hinweise zu Datenschutz und Recht ersetzen keine Rechtsberatung.</p>

<script>
(function(){
  var alle=document.getElementById("alle");
  if(alle) alle.addEventListener("click",function(){
    var ds=document.querySelectorAll("details.f"), zu=[].filter.call(ds,function(d){return !d.open});
    var auf=zu.length>0;
    [].forEach.call(ds,function(d){d.open=auf});
    alle.textContent=auf?"Alle zuklappen":"Alle aufklappen";
  });
  function hash(){var el=location.hash.length>1&&document.getElementById(location.hash.slice(1));
    if(el&&el.tagName==="DETAILS"){el.open=true;el.scrollIntoView({block:"center"});}}
  addEventListener("hashchange",hash);hash();
  addEventListener("beforeprint",function(){[].forEach.call(document.querySelectorAll("details"),function(d){d.dataset.o=d.open?"1":"";d.open=true})});
  addEventListener("afterprint",function(){[].forEach.call(document.querySelectorAll("details"),function(d){d.open=d.dataset.o==="1"})});
})();
</script>
</div></body></html>`;

const nav = NAV.length > 1 ? `<p class="toc">${NAV.map(([id, t]) => `<a href="#${id}">${esc(t)}</a>`).join('<i>·</i>')}</p>` : "";
try {
  sichereAusgabe(OUT, html.replace("<!--NAV-->", nav), { force: args.includes("--force") });
} catch (e) {
  console.error(`ABBRUCH: ${e.message}`);
  process.exit(2);
}
console.log(`HTML: ${OUT} (${TEASER ? "Teaser" : FULL ? "vollständig mit Maßnahmen" : "alle Punkte"}, ${n} Punkte, davon ${TEASER ? top.length : n} im Detail)`);

if (PDF) {
  let chromium;
  // Kein process.cwd(): ein Kundenordner darf keine Quelle fuer ausfuehrbaren Code sein.
  for (const dir of [process.env.MT_PLAYWRIGHT_DIR, process.env.CLAUDE_PLUGIN_ROOT, path.join(os.homedir(), ".cache", "mt-playwright")].filter(Boolean)) {
    try { const real = fs.realpathSync(dir);
          if (!fs.realpathSync(path.join(real, "node_modules", "playwright")).startsWith(real + path.sep)) continue;
          ({ chromium } = createRequire(path.join(real, "/"))("playwright")); break; } catch {}
  }
  if (!chromium) { console.error("PDF übersprungen: Playwright nicht gefunden (siehe /setup)."); process.exit(0); }
  const b = await chromium.launch();
  const pdfCtx = await b.newContext({ serviceWorkers: "block" });
  await installiereNetzPolicy(pdfCtx);
  const p = await pdfCtx.newPage();
  // "load" wartet auf externe Bilder. Ein explizit erlaubtes Remote-Logo wird auch
  // beim PDF-Rendern erneut durch die Browser-Netzpolicy kontrolliert.
  await p.setContent(fs.readFileSync(OUT, "utf8"), { waitUntil: "load" });
  await p.evaluate(() => document.querySelectorAll("details").forEach(d => { d.open = true; }));
  const pdfData = await p.pdf({ format: "A4", printBackground: true, displayHeaderFooter: true, headerTemplate: "<span></span>",
    footerTemplate: `<div style="width:100%;font:7px Helvetica,Arial,sans-serif;color:#8a8a8a;padding:0 20mm;display:flex;justify-content:space-between"><span>Website-Check ${esc(domain)}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
    margin: { top: "16mm", bottom: "16mm", left: "0", right: "0" } });
  try {
    sichereAusgabe(PDF, pdfData, { force: args.includes("--force") });
  } catch (e) {
    await b.close();
    console.error(`ABBRUCH: ${e.message}`);
    process.exit(2);
  }
  await b.close(); console.log("PDF:", PDF);
}
