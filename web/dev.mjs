// Local server for Kettle web: the same static files and the same sync API as the Cloudflare Worker, with households
// kept in memory and saved to web/.data/dev.json so a restart loses nothing. No dependencies.
//   node dev.mjs            -> http://localhost:8787
import http from "node:http";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { handle } from "./src/household.js";
import { route } from "./src/router.js";
import { makeVapidKeys } from "./src/push.js";
import { notify } from "./src/notify.js";

const ROOT = fileURLToPath(new URL(".", import.meta.url));
const PUB = join(ROOT, "public");
const DATA = join(ROOT, ".data", "dev.json");
const PORT = +(process.env.PORT || 8787);
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2", ".wasm": "application/wasm",
  ".onnx": "application/octet-stream", ".flac": "audio/flac", ".wav": "audio/wav", ".txt": "text/plain", ".ico": "image/x-icon" };

let missLog = [];                       // wrong pairing codes per address (memory only)
const db = existsSync(DATA) ? JSON.parse(readFileSync(DATA, "utf8")) : { households: {}, codes: {} };
let saveTimer = null;
const save = () => { clearTimeout(saveTimer); saveTimer = setTimeout(async () => { await mkdir(join(ROOT, ".data"), { recursive: true }); await writeFile(DATA, JSON.stringify(db)); }, 300); };

function memStore(id) {
  const h = db.households[id];
  return {
    async getState() { return h ? structuredClone(h.state) : null; },
    async putState(s) { h.state = s; save(); },
    async addEvents(evs) { const m = new Map(h.events.map((e) => [e.end, e])); for (const e of evs) m.set(e.end, e); h.events = [...m.values()].sort((a, b) => a.end - b.end); save(); },
    async eventsSince(t) { return h.events.filter((e) => e.end > t); },
    async prune(before) { h.events = h.events.filter((e) => e.end >= before); save(); },
    async wipe() { delete db.households[id]; save(); },
  };
}
const env = {
  household: (id) => ({
    init: async (state) => { db.households[id] = { state, events: [] }; save(); },
    call: async (op) => (db.households[id] ? handle(memStore(id), op) : { status: 404, body: { error: "This Kettle link isn't valid any more. Ask for a new one." } }),
  }),
  codes: {
    put: async (code, value, ttl) => { db.codes[code] = { v: value, exp: Date.now() / 1000 + ttl }; save(); },
    get: async (code) => { const c = db.codes[code]; return c && c.exp > Date.now() / 1000 ? c.v : null; },
    miss: async (who, t) => { missLog.push([who, t]); missLog = missLog.filter(([, x]) => x > t - 3600); },
    misses: async (who, since) => missLog.filter(([w, x]) => w === who && x > since).length,
    vapid: async () => { if (!db.vapid) { db.vapid = await makeVapidKeys(); save(); } return db.vapid; },
  },
  // push notifications in the background, as the Worker does with waitUntil
  notify: (id, n) => { if (db.households[id]) env.codes.vapid().then((keys) => notify(memStore(id), id, n, keys)).then((r) => r.length && console.log(`push: ${r.filter((x) => x.ok).length}/${r.length} sent`)); },
};

async function file(path) {
  let p = normalize(join(PUB, decodeURIComponent(path)));
  if (!p.startsWith(PUB)) return null;
  for (const cand of [p, p + ".html", join(p, "index.html")]) {
    try { if ((await stat(cand)).isFile()) return cand; } catch {}
  }
  return null;
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (url.pathname.startsWith("/api/")) {
    const chunks = []; for await (const c of req) chunks.push(c);
    const r = await route(new Request(url, { method: req.method, headers: req.headers, body: ["GET", "HEAD"].includes(req.method) ? undefined : Buffer.concat(chunks) }), env);
    res.writeHead(r.status, Object.fromEntries(r.headers)); res.end(Buffer.from(await r.arrayBuffer()));
    return;
  }
  const f = await file(url.pathname);
  if (!f) { const nf = await file("/404"); res.writeHead(404, { "content-type": TYPES[".html"] }); res.end(nf ? await readFile(nf) : "Not found"); return; }
  res.writeHead(200, { "content-type": TYPES[extname(f)] || "application/octet-stream", "cache-control": "no-cache" });
  res.end(await readFile(f));
}).listen(PORT, () => console.log(`Kettle web on http://localhost:${PORT}`));
