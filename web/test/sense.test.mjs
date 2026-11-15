// The on-device layers (public/js/sense.js) and the new day features in core.js, on hand-made inputs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as core from "../public/js/core.js";
import { prepareSense, kindsOf, buildEnrolment, applyEnrolment } from "../public/js/sense.js";

const kinds = JSON.parse(readFileSync(new URL("../public/model/kinds.json", import.meta.url)));
const enrolCfg = JSON.parse(readFileSync(new URL("../public/model/enrol.json", import.meta.url)));
const S = prepareSense(kinds, enrolCfg);
const AS = (set = {}) => { const a = new Float32Array(527); for (const [i, v] of Object.entries(set)) a[+i] = v; return a; };
const probs = (top, p = 0.9) => Object.fromEntries(core.CLASSES.map((c) => [c, c === top ? p : (1 - p) / 8]));

test("kinds.json names match core.KIND_NAMES (the family view and the server use core's copy)", () => {
  assert.deepEqual(Object.fromEntries(kinds.kinds.map((k) => [k.id, k.name])), core.KIND_NAMES);
});

test("named sound types: strongest first; switched-off types are not named (device list, hidden ones included)", () => {
  const as = AS({ 456: 0.5, 370: 0.2, 443: 0.9, 74: 0.9 });       // boiling, tap, shatter; a dog is never named
  assert.deepEqual(kindsOf(S, as, [], true).map((k) => k.id), ["glass", "kettle", "tap"]);
  assert.deepEqual(kindsOf(S, as, ["glass"], true).map((k) => k.id), ["kettle", "tap"]);
});

test("handover 3.1: only sounds that passed the pre-registered bar are sent; core.KINDS_SHOWN matches kinds.json", () => {
  assert.deepEqual(new Set(kinds.kinds.filter((k) => k.shown).map((k) => k.id)), core.KINDS_SHOWN);
  assert.deepEqual(kindsOf(S, AS({ 367: 0.5, 524: 0.6 })).map((k) => k.id), ["tv"]);            // frying is computed but hidden
});

test("handover 3.1 context: frying with a hiss is not a kettle or a tap; a kettle louder than everything is", () => {
  const ids = (as) => kindsOf(S, as, [], true).map((k) => k.id);
  assert.ok(!ids(AS({ 367: 0.6, 456: 0.3, 370: 0.2 })).includes("kettle"));                     // frying louder than boiling
  assert.ok(!ids(AS({ 367: 0.6, 370: 0.3 })).includes("tap"));                                   // frying louder than the tap
  assert.ok(!ids(AS({ 449: 0.9, 452: 0.9 })).includes("kettle"));                               // pouring is not a kettle
  assert.ok(ids(AS({ 456: 0.6, 367: 0.1 })).includes("kettle"));
  assert.ok(!ids(AS({ 368: 0.4 })).includes("microwave"));                                      // microwave needs >= 0.5
  assert.ok(!ids(AS({ 368: 0.7, 377: 0.8 })).includes("microwave"));                            // ... and to beat a vacuum
  assert.ok(ids(AS({ 368: 0.7 })).includes("microwave"));
  assert.ok(!ids(AS({ 399: 0.9 })).includes("alarm"));                                         // a smoke alarm is never a family sound name
});

test("privacy veto: a toilet flush louder than every named type names nothing (plan D1)", () => {
  assert.deepEqual(kindsOf(S, AS({ 374: 0.6, 370: 0.3 }), [], true), []);
  assert.deepEqual(kindsOf(S, AS({ 374: 0.1, 370: 0.3 }), [], true).map((k) => k.id), ["tap"]);
});



test("teach-this-kitchen: helps only windows the head couldn't name, never overrides a confident head (plan A3)", () => {
  const head = { mean: new Array(4).fill(0), std: new Array(4).fill(1) };
  const near = (c, x) => ({ c, emb: Float32Array.from([x, x, 0, 0]) });
  const samples = [near("cooking", 1), near("cooking", 1.1), near("cooking", 0.9), near("dishwashing", -1), near("dishwashing", -1.1), near("dishwashing", -0.9)];
  const en = buildEnrolment(head, samples, [-60, -58], [-40, -35]);
  assert.equal(en.floor, -55);           // median quiet (-58) + 3 dB, below the quietest activity (-40) - 3 dB
  const unsure = { label: "other", conf: 0.4, probs: probs("other", 0.4), novel: true };
  const r = applyEnrolment(S, head, en, Float32Array.from([1.05, 1.05, 0, 0]), unsure);
  assert.equal(r.taught, true);
  assert.equal(r.novel, false);
  assert.equal(r.label, "cooking");
  const sure = { label: "eating", conf: 0.95, probs: probs("eating", 0.95), novel: false };
  assert.equal(applyEnrolment(S, head, en, Float32Array.from([1.05, 1.05, 0, 0]), sure), sure);
  const far = applyEnrolment(S, head, en, Float32Array.from([9, -9, 9, 9]), unsure);
  assert.equal(far, unsure);
});

const day = (labels, t0 = 8 * 3600, step = 10, extra = () => ({})) =>
  labels.map((l, i) => ({ start: t0 + i * step, end: t0 + (i + 1) * step, label: l, conf: 0.9, probs: probs(l), novel: false, sounds: [], ...extra(i) }));

test("coverage line and named sounds today (plans F1, A6)", () => {
  const evs = [...day(Array(60).fill("cooking"), 8 * 3600, 10, (i) => ({ kinds: i === 3 ? ["frying"] : i > 50 ? ["tv"] : [] })),
    ...day(Array(30).fill("other"), 8 * 3600 + 600, 10, () => ({ novel: true }))];
  const s = core.newState(); core.actions.consent(s, 8 * 3600 - 60); s.last_window_t = evs.at(-1).end;
  const t = core.today(s, evs, evs.at(-1).end + 1, { theta: 0.66, off: 0, day0: 0, hop: 10 });
  assert.equal(t.coverage.pct, 67);
  assert.match(t.coverage.text, /67% of the time it listened/);
  assert.deepEqual(t.heard.map((h) => [h.id, h.text]), [["tv", "at 8:08 AM"]]);          // frying missed the bar: never listed
  const ns = t.blocks.find((b) => b.state === "not_sure");
  assert.match(ns.card, /a sound unlike anything it learned/);
});

test("a 'sound heard by' check (plan A6/F9): met for a shown sound, Can't tell for a hidden one (handover 3.1)", () => {
  const rules = core.validateRules([{ type: "kind_by", kind: "tv", time: "9:00" }]);
  assert.throws(() => core.validateRules([{ type: "kind_by", kind: "speech", time: "9:00" }]));
  const s = core.newState(); core.actions.consent(s, 6 * 3600); s.rules = rules;
  const evs = day(Array(12).fill("cooking"), 7 * 3600, 10, (i) => ({ kinds: i === 5 ? ["tv", "frying"] : [] }));
  s.last_window_t = evs.at(-1).end;
  let t = core.today(s, evs, evs.at(-1).end + 1, { theta: 0.66, off: 0, day0: 0, hop: 10 });
  assert.equal(t.rules[0].title, "Talking / TV by 9:00 AM");
  assert.equal(t.rules[0].state, "met");
  assert.match(t.rules[0].detail, /Met at 7:00 AM \(talking \/ TV heard\)/);
  s.rules = core.validateRules([{ type: "kind_by", kind: "frying", time: "9:00" }]);
  assert.equal(core.today(s, evs, evs.at(-1).end + 1, { theta: 0.66, off: 0, day0: 0, hop: 10 }).rules[0].state, "cant_tell");
  const none = day(Array(400).fill("absence"), 6 * 3600, 10);
  s.last_window_t = 9 * 3600 + 30;
  t = core.today(s, [...none, ...day(Array(200).fill("absence"), 6 * 3600 + 4000, 10)], 9 * 3600 + 60, { theta: 0.66, off: 0, day0: 0, hop: 10 });
  assert.notEqual(t.rules[0].state, "met");
});

test("private windows are drawn as Private and the TV check says it can't tell", () => {
  const evs = day(Array(12).fill("watching_tv"), 9 * 3600, 10, () => ({ private: true }));
  const s = core.newState(); core.actions.consent(s, 9 * 3600 - 10); s.hide = ["watching_tv"]; s.last_window_t = evs.at(-1).end;
  const t = core.today(s, evs, evs.at(-1).end + 1, { theta: 0.66, off: 0, day0: 0, hop: 10, names: { parent: "Dad", caregiver: "Meera" } });
  assert.equal(t.blocks[0].state, "private");
  assert.match(t.blocks[0].card, /Dad chose not to share/);
  assert.equal(t.rules.find((r) => r.type === "tv_over").state, "cant_tell");
  assert.equal(t.summary.includes("TV"), false);
});

