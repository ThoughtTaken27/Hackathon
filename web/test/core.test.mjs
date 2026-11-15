// The browser core must say exactly what the Python app says, for every state in fixtures.json.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as core from "../public/js/core.js";

const F = JSON.parse(readFileSync(new URL("./fixtures.json", import.meta.url)));

for (const c of F.cases) {
  test(`parity: ${c.case}`, () => {
    const { events, ...state } = c.state;
    const got = core.today(state, events, c.now, { theta: F.theta, off: c.tz, day0: c.day0, hop: 2 });
    const e = c.expect;
    assert.equal(got.heartbeat.state, e.heartbeat.state);
    assert.equal(got.heartbeat.text, e.heartbeat.text);
    assert.equal(got.summary, e.summary);
    assert.equal(got.blocks.length, e.blocks.length, "block count");
    got.blocks.forEach((b, i) => {
      const x = e.blocks[i];
      for (const k of ["start", "end", "state", "activity", "label", "range", "n_windows", "card"]) assert.deepEqual(b[k], x[k], `block ${i} ${k}`);
      if (x.conf != null) assert.ok(Math.abs(b.conf - x.conf) < 1e-9, `block ${i} conf ${b.conf} vs ${x.conf}`);
    });
    assert.deepEqual(got.rules.map((r) => ({ id: r.id, state: r.state, title: r.title, detail: r.detail, note: r.note })), e.rules);
  });
}

test("tzOffset reads a zone correctly", () => {
  const t = Date.UTC(2026, 10, 10, 15, 0, 0) / 1000;
  assert.equal(core.tzOffset("America/Chicago", t), -6 * 3600);
  assert.equal(core.tzOffset("Asia/Kolkata", t), 5.5 * 3600);
  assert.equal(core.tzOffset("UTC", t), 0);
});

test("pause, resume and the consent gate", () => {
  const s = core.newState();
  assert.equal(core.canListen(s, 100), false);
  core.actions.consent(s, 100);
  assert.equal(core.canListen(s, 101), true);
  core.actions.pause(s, 200, { minutes: 15 });
  assert.equal(core.canListen(s, 300), false);
  core.tick(s, 200 + 15 * 60 + 1);
  assert.equal(core.canListen(s, 200 + 15 * 60 + 2), true);
  assert.equal(s.pauses.length, 1);
  core.actions.off(s, 5000);
  assert.equal(core.canListen(s, 5001), false);
});

test("rules validation", () => {
  assert.deepEqual(core.validateRules([{ type: "kitchen_by", time: "9:5" }]), [{ id: "r1", type: "kitchen_by", time: "09:05" }]);
  assert.throws(() => core.validateRules([{ type: "tv_over", hours: 99 }]));
  assert.throws(() => core.validateRules([1, 2, 3, 4]));
});
