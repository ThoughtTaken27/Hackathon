// The sync API end to end on an in-memory host: pairing, the consent gate, who may do what, and deletion.
import { test } from "node:test";
import assert from "node:assert/strict";
import { handle } from "../src/household.js";
import { route } from "../src/router.js";

function memEnv() {
  const hs = {}, codes = {};
  const store = (id) => ({
    async getState() { return hs[id] ? structuredClone(hs[id].state) : null; },
    async putState(s) { hs[id].state = s; },
    async addEvents(evs) { hs[id].events.push(...evs); },
    async eventsSince(t) { return hs[id].events.filter((e) => e.end > t); },
    async prune() {}, async wipe() { delete hs[id]; },
  });
  return { hs, env: {
    household: (id) => ({ init: async (s) => { hs[id] = { state: s, events: [] }; }, call: async (op) => (hs[id] ? handle(store(id), op) : { status: 404, body: {} }) }),
    codes: { put: async (c, v) => { codes[c] = v; }, get: async (c) => codes[c] || null,
      miss: async (w, t) => { (codes.__m ||= []).push([w, t]); }, misses: async (w, since) => (codes.__m || []).filter(([x, t]) => x === w && t > since).length },
  } };
}
const call = async (env, method, path, body, key, now = 1_800_000_000) => {
  const r = await route(new Request("http://x" + path, { method, headers: key ? { authorization: `Bearer ${key}` } : {}, body: body && method !== "GET" ? JSON.stringify(body) : undefined }), env, now);
  return { status: r.status, body: await r.json() };
};
const ev = (end, label = "cooking") => ({ start: end - 10, end, label, conf: 0.9,
  probs: { absence: 0.01, cooking: 0.9, dishwashing: 0.02, eating: 0.02, other: 0.01, social_activity: 0.01, vacuum_cleaner: 0.01, watching_tv: 0.01, working: 0.01 },
  novel: false, sounds: [{ name: "Frying (food)", score: 0.4 }] });

test("pair, consent, hear, read, set checks, delete", async () => {
  const { env } = memEnv();
  const T = 1_800_000_000;
  const c = await call(env, "POST", "/api/households", { parent: "Papa", caregiver: "Asha", tz: "America/Chicago", as: "family" });
  assert.equal(c.status, 201);
  assert.equal(c.body.codeFor, "kitchen");
  const pair = await call(env, "POST", "/api/pair", { code: c.body.code.toLowerCase().replace(/(...)/, "$1 ") });
  assert.equal(pair.status, 200);
  assert.equal(pair.body.role, "kitchen");
  const K = pair.body.key, F = c.body.familyKey, id = c.body.id;

  // nothing can be sent before the parent says yes
  assert.equal((await call(env, "POST", `/api/h/${id}/events`, { events: [ev(T)] }, K)).status, 409);
  // the family screen can't say yes for the parent
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "consent" }, F)).status, 403);
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "consent" }, K)).status, 200);

  const sent = await call(env, "POST", `/api/h/${id}/events`, { events: [ev(T - 20), ev(T - 10), { bad: 1 }] }, K, T);
  assert.equal(sent.body.accepted, 2);
  assert.equal((await call(env, "POST", `/api/h/${id}/events`, { events: [ev(T)] }, F)).status, 403);

  const read = await call(env, "GET", `/api/h/${id}/state`, null, F, T + 1);
  assert.equal(read.status, 200);
  assert.equal(read.body.role, "family");
  assert.equal(read.body.events.length, 2);
  assert.equal(read.body.state.names.parent, "Papa");
  assert.equal(read.body.state.keys, undefined, "key hashes never leave the server");

  assert.equal((await call(env, "POST", `/api/h/${id}/rules`, { rules: [{ type: "kitchen_by", time: "09:30" }] }, K)).status, 403);
  const r = await call(env, "POST", `/api/h/${id}/rules`, { rules: [{ type: "kitchen_by", time: "09:30" }] }, F);
  assert.deepEqual(r.body.state.rules, [{ id: "r1", type: "kitchen_by", time: "09:30" }]);

  // paused: labels are refused
  await call(env, "POST", `/api/h/${id}/action`, { type: "pause", minutes: 15 }, K, T + 2);
  assert.equal((await call(env, "POST", `/api/h/${id}/events`, { events: [ev(T + 3)] }, K, T + 3)).status, 409);

  assert.equal((await call(env, "GET", `/api/h/${id}/state`, null, "wrong-key-wrong-key")).status, 403);
  assert.equal((await call(env, "DELETE", `/api/h/${id}`, null, F)).body.deleted, true);
  assert.equal((await call(env, "GET", `/api/h/${id}/state`, null, F)).status, 404);
});

test("a bad pairing code says so plainly", async () => {
  const { env } = memEnv();
  const r = await call(env, "POST", "/api/pair", { code: "ZZZZZZ" });
  assert.equal(r.status, 404);
  assert.match(r.body.error, /didn't work/);
});

test("only allow-listed sound names and fields are stored (plan D1); private windows carry no scores", async () => {
  const { cleanEvent } = await import("../src/household.js");
  const T = 1_800_000_000;
  const e = cleanEvent({ ...ev(T), sounds: [{ name: "Cough", score: 0.9 }, { name: "Water tap, faucet", score: 0.3 }, { name: "Toilet flush", score: 0.5 }],
    kinds: ["tap", "cough", "kettle", "pet"], audio: [1, 2, 3], db: -30, emb: [0.1] }, T);
  assert.deepEqual(e.sounds, [{ name: "Water tap, faucet", score: 0.3 }]);
  assert.deepEqual(e.kinds, ["tap", "kettle"]);
  for (const k of ["audio", "db", "emb"]) assert.equal(k in e, false);
  const p = cleanEvent({ start: T - 10, end: T, label: "private", probs: { social_activity: 0.99 }, sounds: [{ name: "Running water", score: 1 }] }, T);
  assert.equal(p.private, true);
  assert.equal(Math.max(...Object.values(p.probs)), 0);
  assert.deepEqual(p.sounds, []);
});

test("pairing codes: 10 wrong tries from one address, then a 10-minute wait (plan D6)", async () => {
  const { env } = memEnv();
  const T = 1_800_000_000;
  const c = await call(env, "POST", "/api/households", { as: "family" }, null, T);
  for (let i = 0; i < 10; i++) assert.equal((await call(env, "POST", "/api/pair", { code: "ZZZZZZ" }, null, T + i)).status, 404);
  assert.equal((await call(env, "POST", "/api/pair", { code: c.body.code }, null, T + 20)).status, 429);
  assert.equal((await call(env, "POST", "/api/pair", { code: c.body.code }, null, T + 700)).status, 200);
});

test("guest pause and privacy choices are the parent's, and show on the family view", async () => {
  const { env } = memEnv();
  const T = 1_800_000_000;
  const c = await call(env, "POST", "/api/households", { as: "family", tz: "UTC" }, null, T);
  const pair = await call(env, "POST", "/api/pair", { code: c.body.code }, null, T);
  const K = pair.body.key, F = c.body.familyKey, id = c.body.id;
  await call(env, "POST", `/api/h/${id}/action`, { type: "consent" }, K, T);
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "privacy", hide: ["watching_tv"] }, F, T)).status, 403);
  const pr = await call(env, "POST", `/api/h/${id}/action`, { type: "privacy", hide: ["watching_tv", "cooking"], kindsOff: ["alarm", "nope"] }, K, T);
  assert.deepEqual(pr.body.state.hide, ["watching_tv"]);
  assert.deepEqual(pr.body.state.kinds_off, ["alarm"]);
  await call(env, "POST", `/api/h/${id}/action`, { type: "pause", minutes: 120, reason: "guest" }, K, T + 60);
  const r = await call(env, "POST", `/api/h/${id}/action`, { type: "resume" }, K, T + 600);
  assert.deepEqual(r.body.state.pauses.at(-1), [T + 60, T + 600, "guest"]);
});

test("handover 3.6: an Urgent alert from the kitchen reaches the family until they mark it seen; only kind and time are kept", async () => {
  const { env } = memEnv();
  const c = await call(env, "POST", "/api/households", { parent: "Papa", caregiver: "Asha", tz: "America/Chicago", as: "family" });
  const pair = await call(env, "POST", "/api/pair", { code: c.body.code });
  const K = pair.body.key, F = c.body.familyKey, id = c.body.id, T = 1_800_000_000;
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "smoke", at: T }, K)).status, 409);   // needs a yes first
  await call(env, "POST", `/api/h/${id}/action`, { type: "consent" }, K);
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "smoke", at: T }, F)).status, 403);   // family can't raise one
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "burglar", at: T }, K)).status, 400);
  const r = await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "scream", at: T - 5, checkin: "no_answer", scores: { scream: 0.9 } }, K);
  assert.equal(r.status, 200);
  const a = r.body.state.alerts[0];
  assert.deepEqual(Object.keys(a).sort(), ["at", "checkin", "id", "kind", "seen"]);
  assert.equal(a.seen, null);
  assert.equal((await call(env, "POST", `/api/h/${id}/seen`, { id: a.id }, K)).status, 403);
  const s = await call(env, "POST", `/api/h/${id}/seen`, { id: a.id }, F);
  assert.equal(s.status, 200);
  assert.ok(s.body.state.alerts[0].seen > 0);
});

// ---------------------------------------------------------------- handover v3.5: red at once, updated in place, pushed to phones
import { notify, payloadFor } from "../src/notify.js";
import { b64uEncode, makeVapidKeys } from "../src/push.js";

async function fakeSub(host = "fcm.googleapis.com") {
  const pair = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", pair.publicKey));
  return { endpoint: `https://${host}/fcm/send/${Math.random().toString(36).slice(2)}`, keys: { p256dh: b64uEncode(pub), auth: b64uEncode(crypto.getRandomValues(new Uint8Array(16))) } };
}
async function pairedHome() {
  const m = memEnv(), notices = [];
  m.env.notify = async (id, n) => { notices.push({ id, n }); };
  const c = await call(m.env, "POST", "/api/households", { parent: "Papa", caregiver: "Asha", tz: "America/Chicago", as: "family" });
  const pair = await call(m.env, "POST", "/api/pair", { code: c.body.code });
  const K = pair.body.key, F = c.body.familyKey, id = c.body.id;
  await call(m.env, "POST", `/api/h/${id}/action`, { type: "consent" }, K);
  return { ...m, notices, K, F, id };
}

test("v3.5: a scream goes red at once (asking), then the same alert turns amber when they press I'm OK; retries tell nobody twice", async () => {
  const { env, notices, K, F, id } = await pairedHome();
  const T = 1_800_000_000;
  assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "scream", at: T, checkin: "maybe" }, K, T)).status, 400);
  const r1 = await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "scream", at: T, checkin: "asking" }, K, T);
  assert.equal(r1.status, 200);
  assert.equal(r1.body.state.alerts.length, 1);
  assert.equal(r1.body.state.alerts[0].checkin, "asking");
  assert.equal(notices.length, 1, "the family is told at the moment of the scream, not after the check-in");
  assert.equal(notices[0].n.alert.checkin, "asking");
  assert.equal(r1.body.notify, undefined, "the notice never goes back to the client");
  await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "scream", at: T, checkin: "asking" }, K, T + 2);   // a retry
  assert.equal(notices.length, 1);
  const r2 = await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "scream", at: T, checkin: "ok" }, K, T + 20);
  assert.equal(r2.body.state.alerts.length, 1, "same time, same id: updated, not a second banner");
  assert.equal(r2.body.state.alerts[0].checkin, "ok");
  assert.equal(r2.body.state.alerts[0].answered, T + 20);
  assert.equal(notices.length, 2);
  // "I need help" is never undone by a late "asking"
  await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "fall", at: T + 100, checkin: "help" }, K, T + 130);
  await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "fall", at: T + 100, checkin: "asking" }, K, T + 131);
  const s = await call(env, "GET", `/api/h/${id}/state`, null, F, T + 140);
  assert.equal(s.body.state.alerts.find((a) => a.id === `a${T + 100}-fall`).checkin, "help");
  // a smoke and a CO alarm in the same second are two alerts, not one
  await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "smoke", at: T + 150 }, K, T + 160);
  const two = await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind: "co", at: T + 150 }, K, T + 160);
  assert.equal(two.body.state.alerts.filter((a) => a.at === T + 150).length, 2);
  // new kinds are accepted (gunshot, shout, CO, crying)
  for (const kind of ["gunshot", "shout", "co", "distress"]) assert.equal((await call(env, "POST", `/api/h/${id}/action`, { type: "alert", kind, at: T + 200 + kind.length * 20 }, K, T + 300)).status, 200);
});

test("v3.5: push subscriptions are the family's, validated, deduped, capped, and never shown to either screen", async () => {
  const { env, K, F, id } = await pairedHome();
  const sub = await fakeSub();
  assert.equal((await call(env, "POST", `/api/h/${id}/push`, { subscription: sub }, K)).status, 403);
  assert.equal((await call(env, "POST", `/api/h/${id}/push`, { subscription: { ...sub, endpoint: "https://evil.example/x" } }, F)).status, 400);
  assert.equal((await call(env, "POST", `/api/h/${id}/pushtest`, {}, F)).status, 409);
  const r = await call(env, "POST", `/api/h/${id}/push`, { subscription: sub }, F);
  assert.equal(r.status, 200);
  assert.equal(r.body.subscribed, 1);
  assert.equal((await call(env, "POST", `/api/h/${id}/push`, { subscription: sub }, F)).body.subscribed, 1, "same phone twice = one");
  const st = await call(env, "GET", `/api/h/${id}/state`, null, K);
  assert.equal(st.body.state.push, undefined);
  assert.equal(st.body.state.pushCount, 1);
  for (let i = 0; i < 12; i++) await call(env, "POST", `/api/h/${id}/push`, { subscription: await fakeSub() }, F);
  assert.equal((await call(env, "GET", `/api/h/${id}/state`, null, F)).body.state.pushCount, 10);
  const d = await call(env, "DELETE", `/api/h/${id}/push`, { endpoint: sub.endpoint }, F);
  assert.equal(d.body.subscribed, 10);
});

test("v3.5: an urgent alert is encrypted and sent to every phone; dead subscriptions are dropped; no key or score in the payload", async () => {
  const { env, hs, K, F, id } = await pairedHome();
  const keys = await makeVapidKeys();
  const a = await fakeSub(), b = await fakeSub("updates.push.services.mozilla.com");
  await call(env, "POST", `/api/h/${id}/push`, { subscription: a }, F);
  await call(env, "POST", `/api/h/${id}/push`, { subscription: b }, F);
  const store = { async getState() { return structuredClone(hs[id].state); }, async putState(s) { hs[id].state = s; } };
  const sent = [];
  const fetchImpl = async (url, init) => { sent.push({ url, init }); return { status: url === b.endpoint ? 410 : 201 }; };
  const T = 1_800_000_000;
  const n = { alert: { id: `a${T}`, kind: "smoke", at: T, checkin: "none", seen: null }, tz: "America/Chicago", names: { parent: "Papa", room: { type: "kitchen" } } };
  const res = await notify(store, id, n, keys, fetchImpl);
  assert.deepEqual(res.map((x) => x.ok), [true, false]);
  assert.equal(sent.length, 2);
  assert.match(sent[0].init.headers.Authorization, /^vapid t=.+, k=/);
  assert.equal(sent[0].init.headers.Urgency, "high");
  assert.equal(sent[0].init.headers["Content-Encoding"], "aes128gcm");
  assert.equal(hs[id].state.push.length, 1, "the 410 subscription is deleted");
  const p = payloadFor(id, n);
  assert.equal(p.tier, "urgent");
  assert.match(p.body, /smoke alarm at \d+:\d\d (AM|PM)/);
  assert.equal(p.url, `/family?h=${id}`);
  assert.ok(!JSON.stringify(p).includes(F) && !JSON.stringify(p).includes(K), "no key in a lock-screen payload");
  const ok = payloadFor(id, { ...n, alert: { ...n.alert, kind: "scream", checkin: "ok", answered: T + 30 } });
  assert.equal(ok.tier, "update");
  assert.match(ok.body, /pressed "I'm OK" at/);
  assert.equal(payloadFor(id, { test: true, at: T, tz: "UTC" }).tier, "test");
});

test("v3.5: the server makes one push key and serves only its public half", async () => {
  const { env } = memEnv();
  assert.equal((await call(env, "GET", "/api/push/key")).status, 503);
  const keys = await makeVapidKeys();
  env.codes.vapid = async () => keys;
  const r = await call(env, "GET", "/api/push/key");
  assert.equal(r.body.publicKey, keys.publicKey);
  assert.equal(r.body.privateJwk, undefined);
});

test("one code connects several devices; each is recorded under the name it was given", async () => {
  const { env } = memEnv();
  const c = await call(env, "POST", "/api/households", { parent: "Papa", caregiver: "Asha", tz: "UTC", as: "family" });
  const a = await call(env, "POST", "/api/pair", { code: c.body.code, name: "Kitchen laptop" });
  const b = await call(env, "POST", "/api/pair", { code: c.body.code, name: "  Living room tablet with a very long name indeed  " });
  const old = await call(env, "POST", "/api/pair", { code: c.body.code });                  // an older client: no name, still pairs
  assert.equal(a.status, 200); assert.equal(b.status, 200); assert.equal(old.status, 200);
  assert.equal(a.body.key, b.body.key, "same home, same role");
  assert.ok(a.body.deviceId && b.body.deviceId && a.body.deviceId !== b.body.deviceId);
  const st = await call(env, "GET", `/api/h/${c.body.id}/state`, null, c.body.familyKey);
  assert.deepEqual(st.body.state.devices.map((d) => [d.name, d.role]), [["Kitchen laptop", "kitchen"], ["Living room tablet with", "kitchen"]]);
  assert.equal((await call(env, "POST", `/api/h/${c.body.id}/joined`, { name: " " }, a.body.key)).status, 400);
});
