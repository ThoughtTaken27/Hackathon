// The frozen head on CED-tiny's outputs, exactly as kettle/model.py + kettle/live.py classify():
// standardise -> logistic regression -> softmax(/T) -> top label; Mahalanobis novelty; top 3 shown household sounds;
// and the second opinion w = { k, family, v } from the encoder's general tags (kettle/witness.py).
import { CLASSES } from "./core.js";

/** head.json + evidence.json -> flat arrays for speed. */
export function prepare(head, ev, wit = null) {
  const nov = head.novelty;
  return { head, D: head.mean.length, K: CLASSES.length, shown: ev.shown, index: ev.index, wit,
    coef: head.coef.map((r) => Float64Array.from(r)), mean: Float64Array.from(head.mean), std: Float64Array.from(head.std),
    nMeans: nov ? nov.means.map((r) => Float64Array.from(r)) : null, prec: nov ? nov.precision.map((r) => Float64Array.from(r)) : null,
    novThr: nov ? nov.threshold : Infinity, T: head.temperature || 1 };
}

/** 527 AudioSet probabilities -> { k, family, v, cook, water, mouth }: six numbers, no tag names (same as kettle/witness.py opinion()). */
export function opinion(wit, as) {
  let k = -1, family = null;
  for (const f of ["cooking", "dishwashing", "eating"]) { let m = 0; for (const i of wit.kitchen[f]) m = Math.max(m, as[i]); if (m > k) { k = m; family = f; } }
  let v = 0; for (const i of wit.veto) v = Math.max(v, as[i]);
  const out = { k: Math.round(k * 1000) / 1000, family, v: Math.round(v * 1000) / 1000 };
  // cooking, running-water and chewing evidence for naming a kitchen stretch (core.js nameKitchen; kettle/witness.py)
  if (wit.evidence) for (const g of ["cook", "water", "mouth"]) { let m = 0; for (const i of wit.evidence[g]) m = Math.max(m, as[i]); out[g] = Math.round(m * 1000) / 1000; }
  // the kitchen detector (kettle/witness.py detector): logistic regression on the log-odds of all 527 tags
  if (wit.detector) {
    let z = wit.detector.intercept;
    for (let i = 0; i < as.length; i++) { const a = Math.min(Math.max(as[i], 1e-4), 1 - 1e-4); z += Math.log(a / (1 - a)) * wit.detector.coef[i]; }
    out.kd = Math.round(1000 / (1 + Math.exp(-z))) / 1000;
  }
  return out;
}

/** embedding [192] + AudioSet probabilities [527] -> { label, conf, probs, novel, w, sounds } */
export function decide(m, emb, as) {
  const z = new Float64Array(m.D);
  for (let i = 0; i < m.D; i++) z[i] = (emb[i] - m.mean[i]) / m.std[i];
  const L = new Float64Array(m.K);
  for (let k = 0; k < m.K; k++) { let s = 0; const c = m.coef[k]; for (let i = 0; i < m.D; i++) s += z[i] * c[i]; L[k] = (s + m.head.intercept[k]) / m.T; }
  let mx = -Infinity; for (const v of L) mx = Math.max(mx, v);
  let sum = 0; const e = Array.from(L, (v) => { const x = Math.exp(v - mx); sum += x; return x; });
  const probs = {}; let best = 0;
  CLASSES.forEach((c, k) => { probs[c] = Math.round((e[k] / sum) * 1e4) / 1e4; if (e[k] > e[best]) best = k; });
  let novel = false;
  if (m.nMeans) {
    let dmin = Infinity; const d = new Float64Array(m.D);
    for (const mu of m.nMeans) {
      for (let i = 0; i < m.D; i++) d[i] = z[i] - mu[i];
      let q = 0;
      for (let i = 0; i < m.D; i++) { const r = m.prec[i]; let s = 0; for (let j = 0; j < m.D; j++) s += r[j] * d[j]; q += d[i] * s; }
      if (q < dmin) dmin = q;
    }
    novel = Math.sqrt(Math.max(dmin, 0)) > m.novThr;
  }
  const sounds = m.index.map((ix, i) => ({ name: m.shown[i], score: as[ix] })).sort((a, b) => b.score - a.score).slice(0, 3)
    .map((s) => ({ name: s.name, score: Math.round(s.score * 1000) / 1000 }));
  const label = CLASSES[best];
  return { label, conf: Math.round((e[best] / sum) * 1000) / 1000, probs, novel, w: m.wit ? opinion(m.wit, as) : undefined, sounds };
}
