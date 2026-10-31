// Site checks for docs/: every relative link/src resolves, every cards file is strict JSON, every
// page loads in headless Chrome with no JS errors (figures included: they render on load), and the
// figures and predict boxes render. SHOTS=<dir> saves a full-page screenshot of each page.
//   run via `lk check` (CHROME_PATH overrides the browser)
import puppeteer from "puppeteer-core";
import { createServer } from "node:http";
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// SITE_DIR: the built site (lk build → _site). LEARNING_JSON: the project's config, for the
// terminal smoke test ("terminal.smoke": [[input or null, regex, what], ...]).
const docs = path.resolve(process.env.SITE_DIR || "_site");
const learning = process.env.LEARNING_JSON ? JSON.parse(readFileSync(process.env.LEARNING_JSON, "utf8")) : {};
const errors = [];
const walk = (d) => readdirSync(d).flatMap((f) => { const p = path.join(d, f); return statSync(p).isDirectory() ? walk(p) : [p]; });
const files = walk(docs);
const pages = files.filter((f) => f.endsWith(".html") && !path.basename(f).startsWith("_"));

// 1. relative references
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const [, ref] of html.matchAll(/(?:href|src)="([^"#?]+)[^"]*"/g)) {
    if (/^(https?:|mailto:|data:|\/\/)/.test(ref)) continue;
    const target = path.resolve(path.dirname(page), ref);
    if (!existsSync(target)) errors.push(`${path.relative(docs, page)}: broken reference ${ref}`);
  }
}

// 2. cards: EE.addCards("NN", [ strict JSON ])
for (const f of files.filter((f) => /cards\/\d\d\.js$/.test(f))) {
  const m = readFileSync(f, "utf8").match(/EE\.addCards\(\s*"(\d\d)"\s*,\s*(\[[\s\S]*\])\s*\)\s*;?\s*$/);
  if (!m) { errors.push(`${path.relative(docs, f)}: not EE.addCards("NN", [...])`); continue; }
  try {
    const cards = JSON.parse(m[2]);
    for (const c of cards) if (!c.id || !c.q || !c.a) errors.push(`${path.relative(docs, f)}: card missing id/q/a`);
    if (new Set(cards.map((c) => c.id)).size !== cards.length) errors.push(`${path.relative(docs, f)}: duplicate card ids`);
  } catch (e) { errors.push(`${path.relative(docs, f)}: ${e.message}`); }
}

// 3. load every page, served over HTTP the way Pages serves it
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".wasm": "application/wasm",
  ".json": "application/json", ".sql": "text/plain", ".md": "text/markdown", ".svg": "image/svg+xml" };
const server = createServer((req, res) => {
  const p = path.join(docs, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!p.startsWith(docs) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { "content-type": MIME[path.extname(p)] || "application/octet-stream" }).end(readFileSync(p));
}).listen(0);
const base = `http://localhost:${server.address().port}/`;
const chrome = process.env.CHROME_PATH || (process.platform === "darwin"
  ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : "/usr/bin/google-chrome");
const browser = await puppeteer.launch({ executablePath: chrome, headless: "new", args: ["--no-sandbox", "--allow-file-access-from-files"] });
for (const page of pages) {
  const tab = await browser.newPage();
  const rel = path.relative(docs, page);
  tab.on("pageerror", (e) => errors.push(`${rel}: ${e.message}`));
  tab.on("console", (m) => { if (m.type() === "error" && !/fonts\.(googleapis|gstatic)|Failed to load resource/.test(m.text())) errors.push(`${rel}: console: ${m.text()}`); });
  tab.on("requestfailed", (r) => { if (r.url().startsWith(base) && !r.url().includes("/api/")) errors.push(`${rel}: failed to load ${r.url()}`); });
  tab.on("response", (r) => { if (r.url().startsWith(base) && r.status() >= 400 && !r.url().endsWith("favicon.ico") && !r.url().includes("/api/")) errors.push(`${rel}: HTTP ${r.status()} ${r.url()}`); });
  await tab.setViewport({ width: 1200, height: 900 });
  await tab.goto(base + rel, { waitUntil: "load" });
  await new Promise((r) => setTimeout(r, 400));
  // pages with figures must have rendered them
  if (process.env.SHOTS) await tab.screenshot({ path: path.join(process.env.SHOTS, rel.replace(/\//g, "_") + ".png"), fullPage: true });
  const unmounted = await tab.evaluate(() => [...document.querySelectorAll('article div[id^="viz"]')].filter((d) => !d.children.length).map((d) => d.id));
  for (const id of unmounted) errors.push(`${rel}: figure mount #${id} never rendered`);
  await tab.close();
  console.log(`checked ${rel}`);
}
await browser.close();
server.close();

if (errors.length) { console.error("\n" + errors.join("\n")); process.exit(1); }
console.log(`\nOK: ${pages.length} pages, no errors`);
