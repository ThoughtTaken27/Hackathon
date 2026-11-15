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
    codes: { put: async (c, v) => { codes[c] = v; }, get: async (c) => codes[c] || null },
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
