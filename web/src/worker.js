// Cloudflare Worker: serves the static app (public/) and the sync API. One Durable Object per household holds its
// state and window labels in SQLite; one more holds short-lived pairing codes. Free plan compatible.
import { handle } from "./household.js";
import { route } from "./router.js";

const SECURITY = {
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
  "permissions-policy": "microphone=(self), camera=(), geolocation=()",
};

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/")) {
      return route(req, {
        household: (id) => {
          const stub = env.HOUSEHOLD.get(env.HOUSEHOLD.idFromName(id));
          return {
            init: (state) => stub.init(state),
            call: (op) => stub.call(op),
          };
        },
        codes: {
          put: (code, value, ttl) => env.CODES.get(env.CODES.idFromName("codes")).put(code, value, ttl),
          get: (code) => env.CODES.get(env.CODES.idFromName("codes")).take(code),
        },
      });
    }
    const res = await env.ASSETS.fetch(req);
    const out = new Response(res.body, res);
    for (const [k, v] of Object.entries(SECURITY)) out.headers.set(k, v);
    if (/\.(onnx|wasm)$/.test(url.pathname)) out.headers.set("cache-control", "public, max-age=604800, immutable");
    return out;
  },
};

import { DurableObject } from "cloudflare:workers";

export class Household extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)");
    this.sql.exec("CREATE TABLE IF NOT EXISTS ev (end REAL PRIMARY KEY, j TEXT)");
    this.hits = { minute: 0, n: 0 };
  }
  store() {
    const sql = this.sql, ctx = this.ctx;
    return {
      async getState() {        // a deleted home has no tables left: that's "not found", not an error
        try { const r = sql.exec("SELECT v FROM kv WHERE k = 'state'").toArray(); return r.length ? JSON.parse(r[0].v) : null; } catch { return null; }
      },
      async putState(s) { sql.exec("INSERT OR REPLACE INTO kv (k, v) VALUES ('state', ?)", JSON.stringify(s)); },
      async addEvents(evs) { for (const e of evs) sql.exec("INSERT OR REPLACE INTO ev (end, j) VALUES (?, ?)", e.end, JSON.stringify(e)); },
      async eventsSince(t) { return sql.exec("SELECT j FROM ev WHERE end > ? ORDER BY end LIMIT 20000", t).toArray().map((r) => JSON.parse(r.j)); },
      async prune(before) { sql.exec("DELETE FROM ev WHERE end < ?", before); },
      async wipe() { await ctx.storage.deleteAll(); },
    };
  }
  async init(state) { await this.store().putState(state); return true; }
  async call(op) {
    const minute = Math.floor(Date.now() / 60000);
    if (this.hits.minute !== minute) this.hits = { minute, n: 0 };
    if (++this.hits.n > 300) return { status: 429, body: { error: "Too many requests. Kettle will try again shortly." } };
    return handle(this.store(), op);
  }
}

export class Codes extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, v TEXT, exp REAL)");
  }
  async put(code, value, ttl) {
    const now = Date.now() / 1000;
    this.sql.exec("DELETE FROM codes WHERE exp < ?", now);
    this.sql.exec("INSERT OR REPLACE INTO codes (code, v, exp) VALUES (?, ?, ?)", code, JSON.stringify(value), now + ttl);
    return true;
  }
  async take(code) {
    const r = this.sql.exec("SELECT v, exp FROM codes WHERE code = ?", code).toArray();
    if (!r.length || r[0].exp < Date.now() / 1000) return null;
    return JSON.parse(r[0].v);
  }
}
