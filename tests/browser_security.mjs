import { chromium } from "playwright";
import { installiereNetzPolicy } from "../lib/netpolicy.mjs";

function assert(name, cond, detail = "") {
  if (!cond) throw new Error(`${name}: FAIL ${detail}`);
  console.log(`${name}: PASS`);
}

const browser = await chromium.launch({ headless: true });
try {
  const ctx = await browser.newContext({ serviceWorkers: "block" });
  const blocked = [];
  await installiereNetzPolicy(ctx, { onBlock: x => blocked.push(x) });
  const page = await ctx.newPage();
  await page.setContent("<html><body>fixture</body></html>");

  // HTTP fetch auf Loopback muss die Context-Route erreichen und geblockt werden.
  await page.evaluate(async () => {
    try { await fetch("http://127.0.0.1/"); } catch {}
  });
  assert("private HTTP request blocked", blocked.some(x => x.art === "netzbereich" && x.url.includes("127.0.0.1")), JSON.stringify(blocked));

  // Derselbe Angriff in IPv4-mapped IPv6-Notation.
  await page.evaluate(async () => {
    try { await fetch("http://[::ffff:7f00:1]/"); } catch {}
  });
  assert("mapped IPv6 loopback blocked", blocked.some(x => x.art === "netzbereich" && x.url.includes("ffff")), JSON.stringify(blocked));

  // 6to4 kann eingebettete IPv4-Ziele transportieren und wird fuer diesen Auditbrowser
  // konservativ als Transition-Mechanismus blockiert.
  await page.evaluate(async () => {
    try { await fetch("http://[2002:7f00:1::]/"); } catch {}
  });
  assert("6to4 transition blocked", blocked.some(x => x.art === "netzbereich" && x.url.includes("2002:")), JSON.stringify(blocked));

  // WebSocket-Pfad wird separat geroutet; es darf kein Verbindungsversuch zum privaten Ziel erfolgen.
  await page.evaluate(() => new Promise(resolve => {
    const ws = new WebSocket("ws://127.0.0.1/");
    const done = () => resolve();
    ws.addEventListener("close", done, { once: true });
    ws.addEventListener("error", done, { once: true });
    setTimeout(done, 1000);
  }));
  assert("private WebSocket blocked", blocked.some(x => x.art === "websocket" && x.url.includes("127.0.0.1")), JSON.stringify(blocked));

  await ctx.close();
} finally {
  await browser.close();
}
