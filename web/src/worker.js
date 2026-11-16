// Cloudflare Worker: serves the static app (public/) and the sync API. One Durable Object per household holds its
// state and window labels in SQLite; one more holds short-lived pairing codes. Free plan compatible.
import { handle } from "./household.js";
import { route } from "./router.js";
import { makeVapidKeys } from "./push.js";
import { notify } from "./notify.js";

const SECURITY = {
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
  "permissions-policy": "microphone=(self), camera=(), geolocation=()",
};

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/")) {
      const codes = () => env.CODES.get(env.CODES.idFromName("codes"));
      return route(req, {
        // push notifications go out after the kitchen's request has its answer (the household DO sends them)
        notify: (id, n) => { ctx.waitUntil(env.HOUSEHOLD.get(env.HOUSEHOLD.idFromName(id)).notify(id, n)); },
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
          miss: (who, t) => env.CODES.get(env.CODES.idFromName("codes")).miss(who, t),
          misses: (who, since) => env.CODES.get(env.CODES.idFromName("codes")).misses(who, since),
          vapid: () => codes().vapid(),
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
  // One request at a time per home. handle() reads the state, awaits (the key hash), then writes it back; an await that isn't
  // storage lets another request in, so an alert and the 10-second labels sent the same second could erase each other.
  call(op) {
    const run = (this.queue || Promise.resolve()).then(() => this.callOne(op));
    this.queue = run.catch(() => {});
    return run;
  }
  async callOne(op) {
    const minute = Math.floor(Date.now() / 60000);
    if (this.hits.minute !== minute) this.hits = { minute, n: 0 };
    if (++this.hits.n > 300) return { status: 429, body: { error: "Too many requests. Kettle will try again shortly." } };
    return handle(this.store(), op);
  }
  async notify(home, n) {
    const keys = await this.env.CODES.get(this.env.CODES.idFromName("codes")).vapid();
    return (await notify(this.store(), home, n, keys)).length;
  }
}

export class Codes extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, v TEXT, exp REAL)");
    this.sql.exec("CREATE TABLE IF NOT EXISTS misses (who TEXT, t REAL)");
    this.sql.exec("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)");
  }
  /** The VAPID key pair for Web Push: made on first use and kept in this object's storage (no env secret, nothing in git). */
  async vapid() {
    const r = this.sql.exec("SELECT v FROM kv WHERE k = 'vapid'").toArray();
    if (r.length) return JSON.parse(r[0].v);
    const keys = await makeVapidKeys();
    this.sql.exec("INSERT OR IGNORE INTO kv (k, v) VALUES ('vapid', ?)", JSON.stringify(keys));
    return JSON.parse(this.sql.exec("SELECT v FROM kv WHERE k = 'vapid'").toArray()[0].v);
  }
  async miss(who, t) { this.sql.exec("DELETE FROM misses WHERE t < ?", t - 3600); this.sql.exec("INSERT INTO misses (who, t) VALUES (?, ?)", who, t); return true; }
  async misses(who, since) { return this.sql.exec("SELECT COUNT(*) AS n FROM misses WHERE who = ? AND t > ?", who, since).toArray()[0].n; }
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
