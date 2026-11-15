// Kettle's on-device layers on top of the frozen head (head.js). Every constant comes from
// web/public/model/kinds.json and enrol.json, written by eval/beyond.py, which measures each layer first
// (results/beyond.json; the "Beyond the research home" section of How sure).
//
//   2. Teach-this-kitchen (A3): the nearest windows recorded during setup vote; near them, "unlike anything it
//      learned" is lifted for this kitchen only. Stored on this device only, never sent.
//   (Appliance hum and digital silence are handled by the second opinion and the silent-mic rule: core.js, kitchen.js.)
//   4. Sound types (A6, D1): 18 named household sounds (kettle, tap, doorbell, alarm...). Only these names leave
//      the device. Voices, body and bathroom sounds are never named or sent; when one of them is the loudest
//      thing in the window, nothing is named at all (the privacy veto).
import { CLASSES } from "./core.js";

export const THETA = 0.66;

/** kinds.json + enrol.json -> the constants refine() needs. */
export function prepareSense(kinds, enrolCfg) {
  return { ...kinds, enrol: enrolCfg, byId: Object.fromEntries(kinds.kinds.map((k) => [k.id, k])) };
}

/** RMS level of a window in dBFS (digital silence = -Infinity). */
export function levelDb(wave) {
  let s = 0;
  for (let i = 0; i < wave.length; i++) s += wave[i] * wave[i];
  return 10 * Math.log10(s / Math.max(1, wave.length));
}

/** The named sound types a window contains: [{id, name, score}] strongest first (score / its threshold). */
export function kindsOf(sense, as, off = []) {
  const out = [];
  let top = 0;
  for (const k of sense.kinds) {
    let s = 0;
    for (const i of k.index) s = Math.max(s, as[i]);
    if (s < k.tau) continue;
    top = Math.max(top, s);                                  // the veto compares with every type, even switched-off ones
    if (!off.includes(k.id)) out.push({ id: k.id, name: k.name, score: Math.round(s * 1000) / 1000, r: s / k.tau });
  }
  let sensitive = 0;
  for (const i of sense.veto) sensitive = Math.max(sensitive, as[i]);
  if (out.length && sensitive >= top) return [];            // a body or bathroom sound outscores them all: name nothing
  return out.sort((a, b) => b.r - a.r).map(({ r, ...k }) => k);
}

/** A Quiet window from the loudness gate: no model run, nothing named. */
export function quietWindow(db) {
  const probs = Object.fromEntries(CLASSES.map((c) => [c, c === "absence" ? 1 : 0]));
  return { label: "absence", conf: 1, probs, novel: false, sounds: [], kinds: [], why: "quiet", db: Math.round(db) };
}

const standardise = (head, emb) => Float64Array.from(emb, (v, i) => (v - head.mean[i]) / head.std[i]);
function dist(a, b) { let s = 0; for (let i = 0; i < a.length; i++) { const d = a[i] - b[i]; s += d * d; } return Math.sqrt(s); }

/** Build this kitchen's prototypes from setup windows [{c: class, emb: Float32Array}] -> stored record. */
export function buildEnrolment(head, samples, quietDbs = [], activeDbs = []) {
  const pts = samples.map((s) => ({ c: s.c, z: Array.from(standardise(head, s.emb), (v) => Math.round(v * 1000) / 1000) }));
  const nn = pts.map((p, i) => {
    let m = Infinity;
    pts.forEach((q, j) => { if (j !== i && q.c === p.c) m = Math.min(m, dist(p.z, q.z)); });
    return m;
  }).filter(Number.isFinite).sort((a, b) => a - b);
  const median = nn.length ? (nn.length % 2 ? nn[(nn.length - 1) / 2] : (nn[nn.length / 2 - 1] + nn[nn.length / 2]) / 2) : 0;
  const q = quietDbs.filter(Number.isFinite).sort((a, b) => a - b);
  const a = activeDbs.filter(Number.isFinite).sort((x, y) => x - y);
  let floor = null;
  if (q.length) {
    floor = q[Math.floor(q.length / 2)] + 3;                // the kitchen's own quiet, plus 3 dB
    if (a.length) floor = Math.min(floor, a[0] - 3);         // never above its quietest activity
  }
  return { v: 1, at: Date.now(), points: pts, median, floor: floor == null ? null : Math.round(floor * 10) / 10,
    counts: Object.fromEntries([...new Set(pts.map((p) => p.c))].map((c) => [c, pts.filter((p) => p.c === c).length])) };
}

/**
 * Apply this kitchen's prototypes (eval/beyond.py adapt()). Only a window the head could not name (unlike anything
 * it learned, or below theta) that lies near the setup windows is helped: the k nearest vote with weight alpha.
 * A confident head is never overridden.
 */
export function applyEnrolment(sense, head, enrolment, emb, r) {
  if (!enrolment || !enrolment.points || enrolment.points.length < 3) return r;
  if (!r.novel && r.conf >= THETA) return r;
  const { alpha, rho, knn } = sense.enrol;
  const z = standardise(head, emb);
  const ds = enrolment.points.map((p) => ({ c: p.c, d: dist(z, p.z) })).sort((a, b) => a.d - b.d);
  if (ds[0].d > rho * enrolment.median) return r;
  const near = ds.slice(0, knn), probs = {};
  for (const c of CLASSES) probs[c] = (1 - alpha) * r.probs[c] + (alpha * near.filter((x) => x.c === c).length) / near.length;
  let label = CLASSES[0];
  for (const c of CLASSES) if (probs[c] > probs[label]) label = c;
  for (const c of CLASSES) probs[c] = Math.round(probs[c] * 1e4) / 1e4;
  return { ...r, probs, label, conf: Math.round(probs[label] * 1000) / 1000, novel: false, taught: true };
}

/**
 * The whole on-device decision for one window, after head.js decide() (which already carries the second opinion w
 * and the allow-listed sound names). ctx = { head, enrolment, kindsOff }.
 * Adds: this kitchen's setup windows (only for windows the head couldn't name) and the named sound types.
 */
export function refine(sense, ctx, emb, as, r) {
  const out = applyEnrolment(sense, ctx.head, ctx.enrolment, emb, r);
  const named = kindsOf(sense, as, ctx.kindsOff || []);
  return { ...out, novel: !!out.novel, taught: !!out.taught, kinds: named.map((k) => k.id) };
}
