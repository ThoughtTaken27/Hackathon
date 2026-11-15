// Tests for the Sat Nov 14 evening fixes: the second opinion, "settle before showing", and the sound-name allow-list.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { CLASSES, MEAL, TAU_K, TAU_V, rawLabel, headLabel, bySounds, blocks, today, newState, actions, evaluateRules } from "../public/js/core.js";
import { opinion } from "../public/js/head.js";
import { SHOWN_SOUNDS } from "../public/js/sounds.js";
import * as H from "../src/household.js";

const root = new URL("../../", import.meta.url);
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, root)));
const ev = (start, label, conf = 0.9, extra = {}) => {
  const rest = (1 - conf) / (CLASSES.length - 1), probs = Object.fromEntries(CLASSES.map((c) => [c, rest]));
  probs[label] = conf;
  return { start, end: start + 10, label, conf, probs, novel: false, sounds: [], ...extra };
};

test("thresholds and tag positions match models/witness.json", () => {
  const cfg = read("models/witness.json"), names = read("models/audioset_labels.json"), web = read("web/public/model/witness.json");
  assert.equal(TAU_K, cfg.tau_k); assert.equal(TAU_V, cfg.tau_v);
  assert.equal(web.tau_k, cfg.tau_k); assert.equal(web.tau_v, cfg.tau_v);
  for (const f of ["cooking", "dishwashing", "eating"]) assert.deepEqual(web.kitchen[f].map((i) => names[i]), cfg.kitchen[f]);
  assert.deepEqual(web.veto.map((i) => names[i]), cfg.veto);
});

test("opinion(): three numbers from the listed tags only", () => {
  const web = read("web/public/model/witness.json"), names = read("models/audioset_labels.json");
  const as = new Float32Array(527);
  as[names.indexOf("Dishes, pots, and pans")] = 0.61; as[names.indexOf("Vacuum cleaner")] = 0.2;
  as[names.indexOf("Blender")] = 0.99; as[names.indexOf("Speech")] = 0.99;         // neither is kitchen evidence
  assert.deepEqual(opinion(web, as), { k: 0.61, family: "dishwashing", v: 0.2 });
});

test("second opinion: rescue, veto, and a confident head is left alone", () => {
  const TH = 0.66, w = (k, family, v) => ({ w: { k, family, v } });
  assert.equal(rawLabel(ev(0, "cooking"), TH), "cooking");                                                   // no second opinion: old rule
  assert.equal(rawLabel(ev(0, "watching_tv", 0.9, { novel: true, ...w(0.6, "dishwashing", 0) }), TH), "dishwashing");   // unfamiliar room, clear kitchen tags
  assert.ok(bySounds(ev(0, "watching_tv", 0.9, { novel: true, ...w(0.6, "dishwashing", 0) }), TH));
  assert.equal(rawLabel(ev(0, "other", 0.4, w(0.5, "eating", 0)), TH), "eating");                             // head not confident
  assert.equal(rawLabel(ev(0, "other", 0.4, { novel: true, ...w(TAU_K - 0.01, "cooking", 0) }), TH), "not_sure");
  assert.equal(rawLabel(ev(0, "other", 0.4, { novel: true, ...w(0.4, "cooking", 0.7) }), TH), "not_sure");      // a motor is louder
  assert.equal(rawLabel(ev(0, "watching_tv", 0.95, w(0.8, "cooking", 0)), TH), "watching_tv");                // cooking show on TV stays TV
  assert.equal(rawLabel(ev(0, "cooking", 0.72, w(0.05, "cooking", 0.6)), TH), "not_sure");                    // the reviewer's vacuum cleaner
  assert.equal(rawLabel(ev(0, "cooking", 0.72, w(0.7, "cooking", 0.4)), TH), "cooking");
  assert.equal(rawLabel(ev(0, "vacuum_cleaner", 0.99, w(0, "cooking", 0.95)), TH), "vacuum_cleaner");
  assert.equal(headLabel(ev(0, "cooking", 0.72, w(0.05, "cooking", 0.6)), TH), "cooking");
});

const kitchenCheck = (evs, now) => evaluateRules([{ id: "r1", type: "kitchen_by", time: "10:00" }], blocks(evs, 0.66, { now, listeningNow: true, holdLast: true }), now, 0, 0)[0].state;

test("settle before showing: the reviewer's sequence never flips the check back", () => {
  const seq = ["working", "cooking", "working", "cooking", "cooking", "cooking"], evs = [], states = [];
  seq.forEach((lab, i) => { evs.push(ev(8 * 3600 + i * 10, lab)); states.push(kitchenCheck(evs, evs.at(-1).end + 1)); });
  const met = states.map((s) => s === "met");
  assert.deepEqual(met, met.slice().sort(), states.join(","));
  assert.ok(met.at(-1));
});

test("settle before showing: 300 random days never take back a met check", () => {
  let seed = 7; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  const labs = ["absence", "cooking", "working", "other", "dishwashing", "watching_tv"];
  for (let d = 0; d < 300; d++) {
    const n = 3 + Math.floor(rnd() * 38), evs = []; let was = false;
    for (let i = 0; i < n; i++) {
      evs.push(ev(7 * 3600 + i * 10, labs[Math.floor(rnd() * labs.length)], [0.5, 0.7, 0.9][Math.floor(rnd() * 3)]));
      const met = kitchenCheck(evs, evs.at(-1).end + 1) === "met";
      assert.ok(met || !was, `day ${d} window ${i}`);
      was = met;
    }
  }
});

test("every frame of every sample day: checks never un-meet, and the summary only names activities on the bar", () => {
  const days = read("web/public/data/sample-days.json");
  for (const [sid, d] of Object.entries(days)) {
    const s = newState(); actions.consent(s, d.started);
    const evs = []; const metAt = {};
    for (const e of d.events) {
      evs.push(e); s.last_window_t = e.end;
      const t = today(s, evs, e.end + 1, { theta: 0.66, off: 0, day0: 0, hop: 2 });
      for (const r of t.rules) {
        if (metAt[r.id]) assert.equal(r.state, "met", `${sid}: check ${r.id} was met and then read "${r.detail}"`);
        if (r.state === "met") metAt[r.id] = true;
      }
      const onBar = new Set(t.blocks.filter((b) => b.state === "activity").map((b) => b.activity));
      for (const [act, word] of [["cooking", "cooking around"], ["working", "typing around"], ["eating", "eating around"], ["dishwashing", "washing up around"]])
        if (t.summary.includes(word)) assert.ok(onBar.has(act), `${sid}: summary says "${word}" but the bar has no such block: ${t.summary}`);
    }
  }
});

test("the server keeps only allow-listed sound names and a well-formed second opinion", async () => {
  let state = null, events = [];
  const store = { async getState() { return state; }, async putState(s) { state = s; }, async addEvents(evs) { events.push(...evs); },
    async eventsSince() { return events; }, async prune() {}, async wipe() { state = null; events = []; } };
  const now = 1_800_000_000;
  const made = await H.create({ parent: "Dad", caregiver: "Meera", tz: "America/Chicago" }, now);
  state = made.state;
  await H.handle(store, { method: "POST", route: "action", key: made.kitchenKey, body: { type: "consent" }, now });
  const e = { ...ev(now - 10, "cooking"), w: { k: 0.5, family: "cooking", v: 0.1, extra: "x" },
    sounds: [{ name: "Frying (food)", score: 0.5 }, { name: "Cough", score: 0.9 }, { name: "Toilet flush", score: 0.8 }] };
  const bad = { ...ev(now - 20, "cooking"), w: { k: 2, family: "Speech", v: 0 }, sounds: [{ name: "Laughter", score: 0.9 }] };
  const r = await H.handle(store, { method: "POST", route: "events", key: made.kitchenKey, body: { events: [e, bad] }, now });
  assert.equal(r.status, 200);
  const a = events.find((x) => x.end === e.end), b = events.find((x) => x.end === bad.end);
  assert.deepEqual(a.sounds, [{ name: "Frying (food)", score: 0.5 }]);
  assert.deepEqual(a.w, { k: 0.5, family: "cooking", v: 0.1 });
  assert.deepEqual(b.sounds, []); assert.equal(b.w, undefined);
  for (const x of events) for (const s of x.sounds) assert.ok(SHOWN_SOUNDS.has(s.name));
  for (const banned of ["Chewing, mastication", "Laughter", "Cat", "Dog", "Cough", "Toilet flush", "Doorbell", "Telephone"]) assert.ok(!SHOWN_SOUNDS.has(banned), banned);
});
