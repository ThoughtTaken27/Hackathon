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

/** kinds.json + enrol.json (+ sound_head.json) -> the constants refine() needs. */
export function prepareSense(kinds, enrolCfg, soundHead = null) {
  const heads = soundHead && soundHead.heads ? soundHead.heads : {};
  return { ...kinds, enrol: enrolCfg, heads, byId: Object.fromEntries(kinds.kinds.map((k) => [k.id, k])) };
}

/** The trained sound head's probability for one sound (eval/sound_head.py, pre-registered v2): logistic regression on the
 *  embedding [192], or the embedding plus the log-odds of the 527 AudioSet scores. */
export function headProb(h, emb, as) {
  let z = h.b;
  const n = emb.length;
  for (let i = 0; i < h.w.length; i++) {
    let x;
    if (i < n) x = emb[i];
    else { const p = Math.min(1 - 1e-4, Math.max(1e-4, as[i - n])); x = Math.log(p / (1 - p)); }
    z += h.w[i] * ((x - h.mean[i]) / h.std[i]);
  }
  return 1 / (1 + Math.exp(-z));
}

/** RMS level of a window in dBFS (digital silence = -Infinity). */
export function levelDb(wave) {
  let s = 0;
  for (let i = 0; i < wave.length; i++) s += wave[i] * wave[i];
  return 10 * Math.log10(s / Math.max(1, wave.length));
}

/** The named sound types a window contains: [{id, name, score}] strongest first.
 *  With the embedding and a trained head for a sound (sound_head.json), the head decides; otherwise the v1 threshold +
 *  context rules do. Either way the privacy veto compares AudioSet scores, as before. */
export function kindsOf(sense, as, off = [], withHidden = false, emb = null) {
  const out = [];
  let top = 0;
  for (const k of sense.kinds) {
    let s = 0;
    for (const i of k.index) s = Math.max(s, as[i]);
    const h = emb && sense.heads ? sense.heads[k.id] : null;
    if (h) {
      const p = headProb(h, emb, as);
      if (p < h.threshold) continue;
      top = Math.max(top, s);
      if (!off.includes(k.id) && (withHidden || h.shown)) out.push({ id: k.id, name: k.name, score: Math.round(p * 1000) / 1000, r: 1 + p });
      continue;
    }
    if (s < k.tau || s < (k.min || 0)) continue;
    let rival = 0;                                           // context: e.g. a kettle must be louder than frying, tap and dishes
    for (const i of k.beat || []) rival = Math.max(rival, as[i]);
    if (k.beat && s <= rival) continue;
    top = Math.max(top, s);                                  // the veto compares with every type, even switched-off or hidden ones
    if (!off.includes(k.id) && (withHidden || k.shown !== false)) out.push({ id: k.id, name: k.name, score: Math.round(s * 1000) / 1000, r: s / k.tau });
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

// Two on-device rules on top of the frozen head.
//   Quiet (any window, even one the head named): the window is no louder than this kitchen's own quiet as taught in setup (+3 dB), or, before setup, than
//   QUIET_DB (a near-silent room on a laptop microphone with gain control off). A real laptop's room hum is new to the model,
//   which learned one research home's quiet. (Not "the quietest recent windows": a dog barking for a minute would become Quiet.)
//   Voices (only windows the head could NOT name; a confident head is never changed): a person talking is the loudest thing Kettle can name (speech tags >= 0.5, above any body or bathroom sound).
//   The model learned conversation from people talking across a room, so one close voice reads as new to it.
export const QUIET_DB = -55, VOICE_MIN = 0.5;
/** The level (dBFS) at or below which a window counts as Quiet. */
export function quietLevel(enrolment) {
  return enrolment && Number.isFinite(enrolment.floor) ? enrolment.floor : QUIET_DB;
}
function lean(r, c, alpha = 0.6) {                          // move the head's scores toward one class, the way setup windows vote
  const probs = {};
  for (const k of CLASSES) probs[k] = Math.round(((1 - alpha) * r.probs[k] + (k === c ? alpha : 0)) * 1e4) / 1e4;
  return { ...r, probs, label: c, conf: Math.round(probs[c] * 1000) / 1000, novel: false };
}
export function roomRules(sense, ctx, as, db, r) {
  if (Number.isFinite(db) && db <= quietLevel(ctx.enrolment)) return { ...lean(r, "absence", 1), why: "quiet" };   // any window: a near-silent room is Quiet
  if (!r.novel && r.conf >= THETA) return r;
  if (sense.speech && sense.speech.length) {
    let sp = 0; for (const i of sense.speech) sp = Math.max(sp, as[i]);
    let body = 0; for (const i of sense.veto) body = Math.max(body, as[i]);
    if (sp >= VOICE_MIN && sp > body) return { ...lean(r, "social_activity"), why: "voices" };
  }
  return r;
}

/**
 * The whole on-device decision for one window, after head.js decide() (which already carries the second opinion w
 * and the allow-listed sound names). ctx = { head, enrolment, kindsOff }.
 * Adds: this kitchen's setup windows (only for windows the head couldn't name) and the named sound types.
 */
export function refine(sense, ctx, emb, as, r, db = NaN) {
  const out = roomRules(sense, ctx, as, db, applyEnrolment(sense, ctx.head, ctx.enrolment, emb, r));
  const named = kindsOf(sense, as, ctx.kindsOff || [], false, emb);
  // every name the device computed, including ones hidden for missing the accuracy bar: for on-device safety concerns only, never sent
  const device = kindsOf(sense, as, [], true, emb).map((k) => k.id);
  return { ...out, novel: !!out.novel, taught: !!out.taught, kinds: named.map((k) => k.id), kindsDevice: device };
}
