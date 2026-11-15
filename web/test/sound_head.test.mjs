// The trained sound head (eval/sound_head.py, pre-registered in eval/PREREGISTER-SOUNDS-V2.md): sense.js must name the same
// sounds as Python's kettle/kinds.py named() on real tune-half windows (tools/export_sound_head_fixtures.py).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as core from "../public/js/core.js";
import { prepareSense, kindsOf } from "../public/js/sense.js";

const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url)));
const kinds = read("../public/model/kinds.json"), head = read("../public/model/sound_head.json");
const S = prepareSense(kinds, read("../public/model/enrol.json"), head);
const cases = read("./sound_head_fixtures.json");

test("trained sound head: JS names exactly what Python names (shown and device-only lists)", () => {
  for (const c of cases) {
    const emb = Float32Array.from(c.emb), as = Float32Array.from(c.as);
    assert.deepEqual(kindsOf(S, as, [], false, emb).map((k) => k.id), c.shown, c.lab);
    assert.deepEqual(kindsOf(S, as, [], true, emb).map((k) => k.id), c.all, c.lab);
  }
});

test("shown sounds: kinds.json, sound_head.json and core.KINDS_SHOWN agree", () => {
  const fromKinds = new Set(kinds.kinds.filter((k) => k.shown).map((k) => k.id));
  const fromHead = new Set(Object.entries(head.heads).filter(([, h]) => h.shown).map(([k]) => k));
  assert.deepEqual(fromKinds, fromHead);
  assert.deepEqual(fromKinds, core.KINDS_SHOWN);
});

test("a switched-off sound is never named, even when the head is sure", () => {
  const c = cases.find((x) => x.shown.length);
  const off = c.shown[0];
  assert.ok(!kindsOf(S, Float32Array.from(c.as), [off], false, Float32Array.from(c.emb)).some((k) => k.id === off));
});
