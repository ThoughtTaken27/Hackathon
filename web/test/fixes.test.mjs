// Tests for the Sat Nov 14 evening fixes: the second opinion, "settle before showing", and the sound-name allow-list.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { CLASSES, MEAL, TAU_K, TAU_V, TAU_KD, TAU_KD_K, TAU_COOK, TAU_WATER, TAU_MOUTH, COOK_SHARE, nameKitchen, rawLabel, headLabel, bySounds, blocks, today, newState, actions, evaluateRules } from "../public/js/core.js";
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
  { const { kd, ...o } = opinion(web, as); assert.ok(kd >= 0 && kd <= 1); assert.deepEqual(o, { k: 0.61, family: "dishwashing", v: 0.2, cook: 0, water: 0, mouth: 0 }); }
  as[names.indexOf("Sizzle")] = 0.3; as[names.indexOf("Water tap, faucet")] = 0.07; as[names.indexOf("Crunch")] = 0.2;
  { const { kd, ...o } = opinion(web, as); assert.ok(kd >= 0 && kd <= 1); assert.deepEqual(o, { k: 0.61, family: "dishwashing", v: 0.2, cook: 0.3, water: 0.07, mouth: 0.2 }); }
});

test("rule 2f never fires without a kitchen tag heard (glass, clapping, birds, thunder)", () => {
  const w = { k: 0.01, family: "dishwashing", v: 0, cook: 0, water: 0, mouth: 0, kd: 0.99 };
  const ev = { probs: Object.fromEntries(CLASSES.map((c) => [c, c === "other" ? 0.5 : 0.5 / 8])), novel: true, w, sounds: [], kinds: [] };
  assert.notEqual(rawLabel(ev, 0.66), "kitchen");
  assert.equal(rawLabel({ ...ev, w: { ...w, k: 0.2 } }, 0.66), "kitchen");
});

test("rule 2f: TAU_KD and the detector match models/witness.json", () => {
  const cfg = read("models/witness.json"), web = read("web/public/model/witness.json");
  assert.equal(TAU_KD, cfg.detector.tau); assert.equal(TAU_KD_K, cfg.detector.tau_k); assert.equal(web.detector.tau, cfg.detector.tau); assert.deepEqual(web.detector.coef, cfg.detector.coef);
});

test("rule 2c thresholds match models/witness.json", () => {
  const cfg = read("models/witness.json"), names = read("models/audioset_labels.json"), web = read("web/public/model/witness.json");
  assert.equal(TAU_COOK, cfg.tau_cook); assert.equal(TAU_WATER, cfg.tau_water); assert.equal(TAU_MOUTH, cfg.tau_mouth); assert.equal(COOK_SHARE, cfg.cook_share);
  for (const g of ["cook", "water", "mouth"]) assert.deepEqual(web.evidence[g].map((i) => names[i]), cfg.evidence[g]);
});

const ev0 = (t) => ev(t, "other", 0.3);
// Parth's own kitchen, Sun Nov 15: pots and cutlery while his mom cooked were shown as "washing up" and "eating".
test("rule 2c: a kitchen stretch is named from evidence across all its windows", () => {
  const TH = 0.66;
  const win = (t, fam, ev) => ({ ...ev0(t), novel: true, w: { k: 0.4, family: fam, v: 0, cook: 0, water: 0, mouth: 0, ...ev } });
  // pots clanking (tags say "Dishes, pots, and pans" = old washing up) and cutlery (old eating), sizzle in 2 of 12 windows, no water
  const cooking = Array.from({ length: 12 }, (_, i) => win(i * 10, i % 3 ? "dishwashing" : "eating", i === 4 || i === 9 ? { cook: 0.2 } : {}));
  const b1 = blocks(cooking, TH).filter((b) => b.state === "activity");
  assert.equal(b1.length, 1); assert.equal(b1[0].activity, "cooking");
  // the same clatter with no cooking sound and no water: "kitchen activity", not a guess
  const clatter = Array.from({ length: 6 }, (_, i) => win(i * 10, "dishwashing", {}));
  assert.deepEqual(blocks(clatter, TH).filter((b) => b.state === "activity").map((b) => b.activity), ["kitchen"]);
  // running water in the stretch, no cooking sounds: washing up
  const wash = Array.from({ length: 6 }, (_, i) => win(i * 10, "dishwashing", i === 2 ? { water: 0.3 } : {}));
  assert.deepEqual(blocks(wash, TH).filter((b) => b.state === "activity").map((b) => b.activity), ["dishwashing"]);
  // chewing, nothing else: eating
  const eat = Array.from({ length: 6 }, (_, i) => win(i * 10, "eating", i === 3 ? { mouth: 0.3 } : {}));
  assert.deepEqual(blocks(eat, TH).filter((b) => b.state === "activity").map((b) => b.activity), ["eating"]);
  // windows from before the change (no evidence numbers) keep the old answer
  const old = Array.from({ length: 4 }, (_, i) => ({ ...ev0(i * 10), novel: true, w: { k: 0.4, family: "eating", v: 0 } }));
  assert.deepEqual(blocks(old, TH).filter((b) => b.state === "activity").map((b) => b.activity), ["eating"]);
  // rule 2d: the head 93% sure of "washing up" for 2 windows of plates between frying, no tap: one cooking block
  const fry = (t) => win(t, "cooking", { cook: 0.4 });
  const head = (t) => ({ ...ev(t, "dishwashing", 0.93), w: { k: 0.5, family: "dishwashing", v: 0, cook: 0.09, water: 0.001, mouth: 0 } });
  const mix = [fry(0), fry(10), fry(20), head(30), head(40), fry(50), fry(60), fry(70)];
  assert.deepEqual(blocks(mix, TH).filter((b) => b.state === "activity").map((b) => b.activity), ["cooking"]);
  // the same with a tap running: real washing up stays
  const tap = (t) => ({ ...ev(t, "dishwashing", 0.93), w: { k: 0.5, family: "dishwashing", v: 0, cook: 0, water: 0.3, mouth: 0 } });
  assert.deepEqual(blocks([fry(0), fry(10), fry(20), tap(30), tap(40), fry(50), fry(60), fry(70)], TH).filter((b) => b.state === "activity").map((b) => b.activity), ["cooking", "dishwashing", "cooking"]);
  assert.ok(MEAL.has("kitchen"));                                   // a kitchen stretch still meets "kitchen activity by 10"
  assert.equal(nameKitchen([win(0, "eating", { cook: 0.06 })]), "cooking");
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

test("credits page: every dataset and model the code uses is credited, links are https, disclaimer is present", () => {
  const html = fs.readFileSync(new URL("web/public/credits.html", root), "utf8");
  for (const name of ["SINS", "DESED", "Kitchen20", "ESC-50", "AudioSet", "CED-tiny", "CED-small", "Audio Spectrogram Transformer", "CLAP", "Apple Sound Recognition",
    "ONNX Runtime", "qrcode-generator", "Cloudflare", "Geist", "Instrument Serif", "transitions.dev", "Claude Code", "Aside", "REA", "Administration for Community Living"]) {
    assert.ok(html.includes(name), `credits page is missing ${name}`);
  }
  assert.match(html, /Prototype, not medical advice/);
  const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map((m) => m[1]);
  for (const h of hrefs) assert.ok(h.startsWith("https://") || h.startsWith("/") || h.startsWith("#"), `unexpected link ${h}`);
  for (const id of hrefs.filter((h) => h.startsWith("#")).map((h) => h.slice(1))) assert.ok(html.includes(`id="${id}"`), `anchor #${id} has no target`);
  for (const local of hrefs.filter((h) => h.startsWith("/") && !h.includes("?")).map((h) => h.split("#")[0]).filter((h) => /\.(txt|css|js)$/.test(h))) {
    assert.ok(fs.existsSync(new URL("web/public" + local, root)), `${local} is linked but missing`);
  }
  for (const page of ["index.html", "how-sure.html"]) assert.match(fs.readFileSync(new URL("web/public/" + page, root), "utf8"), /href="\/credits"/, `${page} does not link to /credits`);
});

test("handover 3.5: no voice tag is on the sound-name allow-list, so the server never stores one", () => {
  for (const v of ["Speech", "Conversation", "Chatter", "Hubbub, speech noise, speech babble", "Narration, monologue"]) assert.ok(!SHOWN_SOUNDS.has(v), v);
  const shown = read("web/public/model/evidence.json").shown;
  assert.ok(!shown.includes("Speech") && shown.includes("Frying (food)"));
});

test("handover 3.1: a check on a hidden sound says Can't tell, never missed; a kettle needs 2 windows", async () => {
  const { evaluateRules: ev2, KINDS_SHOWN, KIND_MIN_WINDOWS } = await import("../public/js/core.js");
  assert.ok(!KINDS_SHOWN.has("frying") && KIND_MIN_WINDOWS.kettle === 2);
  const day0 = 1_800_000_000 - (1_800_000_000 % 86400);
  const blk = (kinds) => ({ start: day0 + 7 * 3600, end: day0 + 7 * 3600 + 60, state: "activity", activity: "cooking", conf: 0.9, kinds });
  const r = [{ id: "r1", type: "kind_by", kind: "frying", time: "09:00" }];
  const out = ev2(r, [blk({ frying: { n: 3, at: day0 + 7 * 3600 } })], day0 + 10 * 3600, day0, 0);
  assert.equal(out[0].state, "cant_tell");
  // the kettle passed the v2 bar (results/sound_head.json): one stray window is not enough, two are
  const k = [{ id: "r2", type: "kind_by", kind: "kettle", time: "09:00" }];
  assert.notEqual(ev2(k, [blk({ kettle: { n: 1, at: day0 + 7 * 3600 } })], day0 + 7.5 * 3600, day0, 0)[0].state, "met");
  assert.equal(ev2(k, [blk({ kettle: { n: 2, at: day0 + 7 * 3600 } })], day0 + 7.5 * 3600, day0, 0)[0].state, "met");
});
