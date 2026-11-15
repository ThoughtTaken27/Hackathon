// Kettle's safety layer (plan v3.1, Workstream E): danger detectors on the AudioSet scores CED-tiny already computes for
// every window, a smoke/CO alarm pattern detector on the loudness envelope, and a small sequence engine that turns
// detections plus time into "Urgent" or "Worth a look" alerts. Runs on the listening device only: no audio, no words.
// Thresholds come from web/public/model/safety.json, written by eval/safety.py (picked on development clips, reported
// once on held-out clips; results/safety.json). kettle/safety.py is the Python twin; web/test/safety.test.mjs checks
// both give the same answers on shared fixtures (web/test/safety_fixtures.json, made by tools/export_web_fixtures.py).
//
// Urgent rules (notify the family at once; person-related ones ask "Are you OK?" on the screen first):
//   U1 smoke or fire alarm   smoke detector score in 2 of the last 3 windows, or 2 T3 beep cycles in one window
//   U2 carbon monoxide alarm T4 beep pattern in 2 separate windows within 40 s
//   U3 possible fall         impact or breaking glass, then within 60 s a distress voice; or 10 min of stillness
//                            after it (2 stray windows allowed) when the person had been active in the 30 min before (cancelled by normal
//                            kitchen sounds within 2 min: a dropped pan, then cooking)
//   U4 screaming             a scream in 2 separate windows within 2 min, or a scream and a distress voice
//                            (any TV, radio or music in the last 3 windows makes this a "Worth a look" note instead)
//   U5 distress after quiet  a distress voice 3+ separate times in 5 min with nothing else going on
//   U6 "I need help"         the button on the screen, or "I need help" in a check-in
//   U7 stillness             too quiet for hours (core.js C1) and no answer to the check-in
// Worth-a-look notes made here (core.js makes the timeline ones): C6 stove maybe left on, C7 beeping ignored,
// C8 "said they were OK" after a check-in, C9 water left running, scream heard with the TV on.

export const CHECKIN_S = { fall: 60, scream: 30, distress: 60, stillness: 60 };
const FALL_DISTRESS_S = 60, FALL_STILL_S = 600, FALL_CANCEL_S = 120, ACTIVE_BEFORE_S = 1800;
const SCREAM_S = 120, DISTRESS_S = 300, SEPARATE_S = 10, MEDIA_WINDOWS = 3;
const COOLDOWN_S = 600, SMOKE_CLEAR_S = 300;
const STOVE_S = 2400, STOVE_GAP_S = 180, BEEP_S = 300, BEEP_GAP_S = 120, WATER_S = 1200, WATER_SHARE = 0.8;
const KEEP_S = 2 * 3600, STRAY = 2;          // stillness allows 2 stray windows (a false door or cupboard name)
export const COOKING_KINDS = ["frying", "kettle", "boiling"];
export const OTHER_KITCHEN = ["dishes", "cutlery", "tap", "chopping", "cupboard", "drawer", "microwave", "blender", "pouring", "stirring"];

export const TEXT = {
  smoke: "a smoke alarm", co: "what sounds like a carbon monoxide alarm", fall: "a crash, then a groan or cry", fall_still: "a crash, then no movement for 10 minutes",
  scream: "screaming", distress: "repeated groaning or crying", help: "the I need help button", stillness: "no activity for hours",
  stove: "frying or boiling for 40 minutes with nothing else heard", beep: "a timer or appliance beeping for 5 minutes", water: "running water for 20 minutes",
  scream_tv: "screaming while the TV or music was on", test: "a test alert",
};

/** safety.json -> the constants the detectors need. */
export function prepareSafety(cfg) {
  return { ...cfg, byId: Object.fromEntries(cfg.detectors.map((d) => [d.id, d])) };
}

const r3 = (x) => Math.round(x * 1000) / 1000;

/** One window's detections: { scores: {id: max score}, hits: [ids at or above their threshold], media } */
export function detect(cfg, as) {
  const scores = {}, hits = [];
  for (const d of cfg.detectors) {
    let s = 0;
    for (const i of d.index) s = Math.max(s, as[i] || 0);
    scores[d.id] = r3(s);
    if (s >= d.tau) hits.push(d.id);
  }
  let m = 0;
  for (const i of cfg.media.index) m = Math.max(m, as[i] || 0);
  return { scores, hits, media: m >= cfg.media.tau };
}

/**
 * Loudness envelope of a window in dB, one value per frame (50 ms). The signal is first-differenced, a cheap high-pass
 * that keeps a 3 kHz alarm tone and drops most hum and speech energy, so the beeps stand out from the room.
 */
export function envelope(wave, sr = 16000, frameS = 0.05) {
  const n = Math.floor(sr * frameS), frames = Math.floor(wave.length / n), out = new Array(frames);
  for (let f = 0; f < frames; f++) {
    let s = 0;
    for (let i = f * n + 1; i < (f + 1) * n; i++) { const d = wave[i] - wave[i - 1]; s += d * d; }
    out[f] = s > 0 ? 10 * Math.log10(s / n) : -120;
  }
  return out;
}

/**
 * NFPA 72 temporal patterns in an envelope (dB per frame of frameS seconds):
 *   T3 (smoke): three ~0.5-s beeps with ~0.5-s gaps, then ~1.5 s off.   T4 (CO): four ~0.1-s beeps, ~0.1-s gaps, then ~5 s off.
 * A frame is "on" when it is 12 dB or more above the window's 20th-percentile level. Returns complete cycles found.
 */
export function alarmPattern(env, frameS = 0.05) {
  if (!env.length) return { t3: 0, t4: 0 };
  const sorted = env.slice().sort((a, b) => a - b);
  const floor = sorted[Math.floor(0.2 * (sorted.length - 1))];
  if (sorted[sorted.length - 1] - floor < 12) return { t3: 0, t4: 0 };
  const on = env.map((v) => v >= floor + 12);
  const segs = [];                                    // [isOn, seconds, summed dB, frames]
  on.forEach((v, f) => { const g = segs[segs.length - 1]; if (g && g[0] === v) { g[1] += frameS; g[2] += env[f]; g[3]++; } else segs.push([v, frameS, env[f], 1]); });
  const steady = (ks) => { const lv = ks.map((k) => segs[k][2] / segs[k][3]); return Math.max(...lv) - Math.min(...lv) <= 6; };   // an alarm beeps at one level
  const near = (x, lo, hi) => x >= lo - 1e-9 && x <= hi + 1e-9;
  let t3 = 0, t4 = 0;
  for (let i = 0; i < segs.length; i++) {
    if (!segs[i][0]) continue;
    // T3: on, off, on, off, on, then a long off
    if (i + 5 < segs.length + 0 && [0, 2, 4].every((k) => segs[i + k] && segs[i + k][0] && near(segs[i + k][1], 0.35, 0.7))
      && [1, 3].every((k) => segs[i + k] && near(segs[i + k][1], 0.3, 0.7)) && segs[i + 5] && near(segs[i + 5][1], 1.1, 2.2) && steady([i, i + 2, i + 4])) t3++;
    // T4: four short beeps with short gaps, then a long off
    if ([0, 2, 4, 6].every((k) => segs[i + k] && segs[i + k][0] && near(segs[i + k][1], 0.05, 0.2))
      && [1, 3, 5].every((k) => segs[i + k] && near(segs[i + k][1], 0.05, 0.2)) && segs[i + 7] && segs[i + 7][1] >= 2.5 && steady([i, i + 2, i + 4, i + 6])) t4++;
  }
  return { t3, t4 };
}

// ---------------------------------------------------------------- the sequence engine
export function newEngine() {
  return { hist: [], lastActive: null, pending: null, checkin: null, last: {}, smokeSince: null, coSince: null, stoveFrom: null, stoveSeen: null,
    beepFrom: null, beepSeen: null, waterFrom: null, waterN: 0, waterHit: 0 };
}

/** Was something going on in this window (a sound above the room's quiet, a named sound, or an activity label)? */
export function isActive(w) {
  if ((w.kinds || []).length) return true;
  if (w.floor != null && w.db != null) return w.db >= w.floor + 3;
  return !!w.label && w.label !== "absence";
}
const cooks = (w) => ["cooking", "dishwashing", "eating"].includes(w.label) || (w.kinds || []).some((k) => COOKING_KINDS.includes(k) || OTHER_KITCHEN.includes(k));
const has = (w, id) => (w.hits || []).includes(id);
function separate(ws, id, since) {   // windows with this detection, counted only when 10 s or more apart (windows overlap)
  let n = 0, prev = -Infinity;
  for (const w of ws) if (w.t >= since && has(w, id) && w.t - prev >= SEPARATE_S) { n++; prev = w.t; }
  return n;
}
function alert(st, t, tier, type, extra = {}) {
  st.last[type] = t;
  return { do: "alert", tier, type, at: t, text: TEXT[type], ...extra };
}
const cool = (st, type, t) => st.last[type] == null || t - st.last[type] >= COOLDOWN_S;
function startCheckin(st, t, rule, type, evidence) {
  st.checkin = { rule, type, at: t, deadline: t + CHECKIN_S[rule], evidence };
  st.last[type] = t;
  return { do: "checkin", rule, type, at: t, deadline: st.checkin.deadline, text: TEXT[type] };
}

/**
 * One window (5-s hop): w = { t (window end, s), hits, scores, media, pattern: {t3, t4}, db, floor, kinds, label }.
 * opts = { urgent: bool, concern: bool (the parent's consent per tier), paused: bool, smokeWhilePaused: bool }.
 * Returns a list of actions: { do: "alert", tier, type, at, ... } | { do: "checkin", rule, type, deadline } | { do: "cancel" }.
 */
export function step(st, w, opts = {}) {
  const { urgent = true, concern = true, paused = false, smokeWhilePaused = false } = opts;
  const t = w.t, out = [];
  st.hist.push({ t, hits: w.hits || [], media: !!w.media || w.label === "watching_tv", active: isActive(w), cooks: cooks(w), kinds: w.kinds || [], label: w.label || null });
  st.hist = st.hist.filter((h) => h.t > t - KEEP_S);
  const h = st.hist, me = h[h.length - 1];
  if (me.active) st.lastActive = t;
  out.push(...timeouts(st, t));
  if (!urgent && !concern) return out;
  const last3 = h.slice(-3);
  // U1 smoke or fire alarm, U2 CO alarm: no check-in; also while paused if the parent chose that
  const pat = w.pattern || { t3: 0, t4: 0 };
  me.t3 = pat.t3; me.t4 = pat.t4;
  if (urgent && (!paused || smokeWhilePaused)) {
    const smoke = last3.filter((x) => has(x, "smoke_alarm")).length >= 2 || pat.t3 >= 2;
    if (smoke) { if (st.smokeSince == null) { st.smokeSince = t - 10; out.push(alert(st, t, "urgent", "smoke", { since: st.smokeSince, evidence: ev(w, ["smoke_alarm"], pat) })); } }
    else if (st.smokeSince != null && !h.some((x) => x.t > t - SMOKE_CLEAR_S && (has(x, "smoke_alarm") || x.t3))) st.smokeSince = null;
    const co = separate(h.map((x) => ({ ...x, hits: x.t4 >= 1 ? ["t4"] : [] })), "t4", t - 40) >= 2;      // two separate windows in 40 s
    if (co) { if (st.coSince == null) { st.coSince = t - 10; out.push(alert(st, t, "urgent", "co", { since: st.coSince, evidence: ev(w, ["smoke_alarm"], pat) })); } }
    else if (st.coSince != null && !h.some((x) => x.t > t - SMOKE_CLEAR_S && x.t4)) st.coSince = null;
  }
  if (paused) return out;
  const media = h.slice(-MEDIA_WINDOWS).some((x) => x.media);
  // U3 possible fall: an impact or breaking glass starts a 10-minute watch
  if (urgent && (has(me, "impact") || has(me, "glass")) && !media && !st.pending && !st.checkin) {
    const before = h.some((x) => x.t < t - 5 && x.t >= t - ACTIVE_BEFORE_S && x.active);
    st.pending = { at: t, before, evidence: ev(w, ["impact", "glass"]) };
  }
  if (st.pending && !st.checkin) {
    const p = st.pending;
    const after = h.filter((x) => x.t > p.at + 5);
    if (after.some((x) => x.t <= p.at + FALL_CANCEL_S && x.cooks)) st.pending = null;                       // a dropped pan, then cooking
    else if (after.some((x) => x.t <= p.at + FALL_DISTRESS_S && (has(x, "distress") || has(x, "scream")))) {
      st.pending = null; out.push(startCheckin(st, t, "fall", "fall", { ...p.evidence, ...ev(w, ["distress", "scream"]) }));
    } else if (t - p.at >= FALL_STILL_S) {
      st.pending = null;
      if (p.before && after.filter((x) => x.active).length <= STRAY) out.push(startCheckin(st, t, "fall", "fall_still", p.evidence));
    }
  }
  // U4 screaming (with TV, radio or music on: only a note)
  if (!st.checkin && (separate(h, "scream", t - SCREAM_S) >= 2 || (has(me, "scream") && h.some((x) => x.t > t - SCREAM_S && has(x, "distress"))))) {
    if (media) { if (concern && cool(st, "scream_tv", t)) out.push(alert(st, t, "concern", "scream_tv", { evidence: ev(w, ["scream"]) })); }
    else if (urgent && cool(st, "scream", t)) out.push(startCheckin(st, t, "scream", "scream", ev(w, ["scream", "distress"])));
  }
  // U5 distress voice again and again with nothing else going on
  if (urgent && !st.checkin && !media && cool(st, "distress", t) && separate(h, "distress", t - DISTRESS_S) >= 3
    && !h.some((x) => x.t > t - DISTRESS_S && x.cooks)) out.push(startCheckin(st, t, "distress", "distress", ev(w, ["distress"])));
  if (concern) out.push(...deviceConcerns(st, w, t));
  return out;
}

function ev(w, ids, pat = null) {
  const e = {};
  for (const id of ids) if (w.scores && w.scores[id] != null) e[id] = w.scores[id];
  if (pat && (pat.t3 || pat.t4)) Object.assign(e, { t3: pat.t3, t4: pat.t4 });
  return e;
}

/** C6 stove maybe left on, C7 beeping ignored, C9 water left running: sustained named sounds, measured on the device. */
function deviceConcerns(st, w, t) {
  const out = [], k = w.kinds || [];
  // C6: frying or boiling heard at least every 3 minutes for 40 minutes, and no other kitchen sound or footsteps
  if (k.some((x) => COOKING_KINDS.includes(x))) {
    if (st.stoveFrom == null || t - st.stoveSeen > STOVE_GAP_S) st.stoveFrom = t;
    st.stoveSeen = t;
  }
  if (k.some((x) => OTHER_KITCHEN.includes(x) || x === "footsteps")) st.stoveFrom = st.stoveSeen != null ? t : null;
  if (st.stoveFrom != null && t - st.stoveSeen <= STOVE_GAP_S && t - st.stoveFrom >= STOVE_S && cool(st, "stove", t)) out.push(alert(st, t, "concern", "stove", { since: st.stoveFrom }));
  // C7: a timer or appliance beep again and again for 5 minutes
  if ((w.hits || []).includes("beep") || k.includes("timer")) {
    if (st.beepFrom == null || t - st.beepSeen > BEEP_GAP_S) st.beepFrom = t;
    st.beepSeen = t;
  }
  if (st.beepFrom != null && t - st.beepSeen <= BEEP_GAP_S && t - st.beepFrom >= BEEP_S && cool(st, "beep", t)) out.push(alert(st, t, "concern", "beep", { since: st.beepFrom }));
  // C9: running water in 80% of windows for 20 minutes
  const tap = k.includes("tap");
  if (tap && st.waterFrom == null) { st.waterFrom = t; st.waterN = 0; st.waterHit = 0; }
  if (st.waterFrom != null) {
    st.waterN++; if (tap) st.waterHit++;
    if (st.waterHit / st.waterN < WATER_SHARE) st.waterFrom = null;
    else if (t - st.waterFrom >= WATER_S && cool(st, "water", t)) out.push(alert(st, t, "concern", "water", { since: st.waterFrom }));
  }
  return out;
}

/** Check-ins nobody answered: the alert goes to the family. Call with the time even when no window arrives. */
export function timeouts(st, t) {
  if (!st.checkin || t < st.checkin.deadline) return [];
  const c = st.checkin; st.checkin = null;
  return [{ do: "alert", tier: "urgent", type: c.type, at: t, since: c.at, text: TEXT[c.type], checkin: "no_answer", evidence: c.evidence }];
}

/** The person answered on the screen (or by voice): "ok" -> a Worth-a-look note; "help" -> Urgent. */
export function answer(st, t, reply) {
  if (!st.checkin) return reply === "help" ? [help(st, t)] : [];
  const c = st.checkin; st.checkin = null;
  if (reply === "help") return [{ do: "alert", tier: "urgent", type: "help", at: t, since: c.at, text: TEXT.help, checkin: "help", after: c.type, evidence: c.evidence }];
  return [{ do: "alert", tier: "concern", type: c.type, at: t, since: c.at, text: TEXT[c.type], checkin: "ok", evidence: c.evidence }];
}
/** U6: the always-visible button. */
export function help(st, t) { st.last.help = t; return { do: "alert", tier: "urgent", type: "help", at: t, since: t, text: TEXT.help, checkin: "help" }; }
/** U7: core.js said "too quiet for hours" (C1 at its escalation point): ask on the screen first. */
export function askStillness(st, t) {
  if (st.checkin || !cool(st, "stillness", t)) return [];
  return [startCheckin(st, t, "stillness", "stillness", {})];
}

/** C11 (opt-in): today's cough count against this device's own last 7 days. Only the comparison ever leaves the device. */
export function coughConcern(days, today) {
  const v = days.filter(Number.isFinite).slice(-7).sort((a, b) => a - b);
  if (v.length < 3) return null;
  const med = v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2;
  return today > 3 * Math.max(med, 2) ? { ratio: Math.round((today / Math.max(med, 1)) * 10) / 10 } : null;
}
