// The sync API, written once for both hosts. `env` provides:
//   household(id).call(op) -> {status, body}      one household's store + handle()
//   household(id).init(state)                       store a new household
//   codes.put(code, value, ttlS) / codes.get(code)  short pairing codes ("K7P 4QX") -> {id, role, key}
//   codes.vapid()                                   this server's Web Push key pair, made once and kept (never in git)
//   notify(id, notice)                              optional: send push notifications in the background (notify.js)
import { create, randomId } from "./household.js";

const CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
const CODE_TTL_S = 48 * 3600;
export const PAIR_MISSES = 10, PAIR_WINDOW_S = 600;   // wrong codes allowed per address per 10 minutes (plan D6)
const json = (status, body) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" } });

async function readBody(req) {
  const text = await req.text();
  if (text.length > 256 * 1024) throw new Error("too large");
  return text ? JSON.parse(text) : {};
}
export const normCode = (c) => String(c || "").toUpperCase().replace(/[^A-Z0-9]/g, "");

export async function route(req, env, now = Date.now() / 1000) {
  const url = new URL(req.url);
  const p = url.pathname.replace(/\/+$/, "");
  try {
    if (p === "/api/health") return json(200, { ok: true, now });
    if (p === "/api/push/key" && req.method === "GET") {
      const k = env.codes.vapid ? await env.codes.vapid() : null;
      return k ? json(200, { publicKey: k.publicKey }) : json(503, { error: "Alerts aren't set up on this server." });
    }

    if (p === "/api/households" && req.method === "POST") {
      const b = await readBody(req);
      const as = b.as === "kitchen" ? "kitchen" : "family";
      const { state, kitchenKey, familyKey } = await create(b, now);
      const id = randomId(12);
      await env.household(id).init(state);
      const other = as === "kitchen" ? { role: "family", key: familyKey } : { role: "kitchen", key: kitchenKey };
      const code = randomId(6, CODE_ALPHABET);
      await env.codes.put(code, { id, ...other }, CODE_TTL_S);
      return json(201, { id, kitchenKey, familyKey, as, code, codeFor: other.role, codeExpires: now + CODE_TTL_S });
    }

    if (p === "/api/pair" && req.method === "POST") {
      const who = req.headers.get("cf-connecting-ip") || req.headers.get("x-forwarded-for") || "local";
      if ((await env.codes.misses(who, now - PAIR_WINDOW_S)) >= PAIR_MISSES)
        return json(429, { error: "Too many wrong codes. Wait 10 minutes, then try again." });
      const b = await readBody(req);
      const v = await env.codes.get(normCode(b.code));
      if (!v) { await env.codes.miss(who, now); return json(404, { error: "That code didn't work. Check the letters, or ask for a new code." }); }
      // the code stays valid (48 h) so more devices can join with it; each one is recorded under the name it was given
      if (typeof b.name === "string" && b.name.trim()) {
        const r = await env.household(v.id).call({ method: "POST", route: "joined", key: v.key, body: { name: b.name }, now });
        if (r.status !== 200) return json(r.status, r.body);
        return json(200, { ...v, deviceId: r.body.deviceId, name: b.name.trim().slice(0, 24).trim() });
      }
      return json(200, v);
    }

    const m = p.match(/^\/api\/h\/([a-z0-9]{6,24})(?:\/([a-z]+))?$/);
    if (m) {
      const [, id, sub = ""] = m;
      const key = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
      if (sub === "code" && req.method === "POST") {         // a fresh pairing code for the other screen
        const b = await readBody(req);
        const r = await env.household(id).call({ method: "GET", route: "state", key, body: { since: now }, now });
        if (r.status !== 200) return json(r.status, r.body);
        const role = b.for === "kitchen" ? "kitchen" : "family";
        const keyFor = b.key;                                  // the caller passes the other screen's key it holds
        if (typeof keyFor !== "string" || keyFor.length < 16) return json(400, { error: "missing key" });
        const code = randomId(6, CODE_ALPHABET);
        await env.codes.put(code, { id, role, key: keyFor }, CODE_TTL_S);
        return json(201, { code, codeFor: role, codeExpires: now + CODE_TTL_S });
      }
      const body = req.method === "GET" ? { since: +url.searchParams.get("since") || 0 } : await readBody(req);
      const r = await env.household(id).call({ method: req.method, route: sub, key, body, now });
      if (r.notify && env.notify) await env.notify(id, r.notify);     // hosts hand this to the background (waitUntil)
      return json(r.status, r.body);
    }
    return json(404, { error: "not found" });
  } catch (e) {
    return json(400, { error: "Bad request" });
  }
}
