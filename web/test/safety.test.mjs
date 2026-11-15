// The safety layer (public/js/safety.js) must give exactly the Python twin's answers (kettle/safety.py) on shared cases
// (safety_fixtures.json, made by tools/export_safety_fixtures.py): every Urgent rule's positive case and the hard
// negatives (TV scream, dropped pan then cooking, microwave beep, doorbell, paused period), the T3/T4 alarm patterns,
// the envelope, the detectors and the cough comparison.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as S from "../public/js/safety.js";

const F = JSON.parse(readFileSync(new URL("./safety_fixtures.json", import.meta.url)));
const cfg = S.prepareSafety(JSON.parse(readFileSync(new URL("../public/model/safety.json", import.meta.url))));

function run(sc) {
  const st = S.newEngine(), out = [];
  const answers = sc.answers.slice().sort((a, b) => a.t - b.t);
  const o = { urgent: sc.opts.urgent ?? true, concern: sc.opts.concern ?? true, paused: !!sc.opts.paused, smokeWhilePaused: !!sc.opts.smokeWhilePaused };
  for (const w of sc.windows) {
    while (answers.length && answers[0].t <= w.t) {
      const a = answers.shift();
      const acts = a.reply === "ask_stillness" ? S.askStillness(st, a.t) : S.answer(st, a.t, a.reply);
      out.push(...acts.map((x) => ({ t: a.t, ...x })));
    }
    out.push(...S.step(st, w, o).map((x) => ({ t: w.t, ...x })));
  }
  return out;
}

for (const sc of F.scenarios) test(`scenario ${sc.name}: same actions as Python`, () => assert.deepEqual(run(sc), sc.expect));

test("every Urgent rule fires on its positive case and none on the hard negatives", () => {
  const by = Object.fromEntries(F.scenarios.map((s) => [s.name, s.expect]));
  for (const [name, acts] of Object.entries(by)) {
    if (name.endsWith("_no")) assert.equal(acts.filter((a) => a.tier === "urgent" || a.do === "checkin").length, 0, name);
  }
  assert.ok(by.smoke_alarm.some((a) => a.type === "smoke" && a.tier === "urgent"));
  assert.ok(by.co_alarm.some((a) => a.type === "co"));
  assert.ok(by.fall_groan_no_answer.some((a) => a.tier === "urgent" && a.checkin === "no_answer"));
  assert.ok(by.fall_groan_answer_ok.some((a) => a.tier === "concern" && a.checkin === "ok"));
  assert.ok(by.scream_tv_drama.every((a) => a.tier !== "urgent"));
});

test("alarm patterns (NFPA 72 T3/T4) match Python, and a kitchen timer is neither", () => {
  for (const p of F.patterns) {
    assert.deepEqual(S.alarmPattern(p.env), p.expect, `${p.kind} seed ${p.seed}`);
    if (p.kind === "timer" || p.kind === "none") assert.deepEqual(p.expect, { t3: 0, t4: 0 });
  }
  assert.ok(F.patterns.filter((p) => p.kind === "t3").every((p) => p.expect.t3 >= 1));
  assert.ok(F.patterns.filter((p) => p.kind === "t4").every((p) => p.expect.t4 >= 1));
});

test("envelope and detectors match Python", () => {
  const env = S.envelope(Float32Array.from(F.envelope.wave)).map((x) => Math.round(x * 1e6) / 1e6);
  env.forEach((v, i) => assert.ok(Math.abs(v - F.envelope.expect[i]) < 1e-3, `frame ${i}`));
  assert.deepEqual(S.detect(cfg, F.detect.scores), F.detect.expect);
});

test("unusual coughing (C11) compares with the device's own week", () => {
  for (const c of F.cough) assert.deepEqual(S.coughConcern(c.days, c.today), c.expect);
});
