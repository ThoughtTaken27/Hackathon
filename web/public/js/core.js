// Kettle core: the same rules as the Python app (kettle/labels, timeline, rules, heartbeat, live, view), in plain JS.
// Used by both screens in the browser and by the sync worker. No DOM, no network. web/test/core.test.mjs checks every
// output against Python's own answers (web/test/fixtures.json, made by tools/export_web_fixtures.py).

// ---------------------------------------------------------------- labels
export const CLASSES = ["absence", "cooking", "dishwashing", "eating", "other", "social_activity", "vacuum_cleaner", "watching_tv", "working"];
export const DISPLAY = { absence: "Quiet", cooking: "Cooking", dishwashing: "Washing up", eating: "Eating", other: "Some activity",
  social_activity: "Conversation", vacuum_cleaner: "Vacuuming", watching_tv: "TV", working: "Typing", kitchen: "Kitchen activity" };
export const PHRASE = { absence: "quiet", cooking: "cooking", dishwashing: "washing up", eating: "eating", other: "some activity",
  social_activity: "conversation", vacuum_cleaner: "vacuuming", watching_tv: "TV", working: "typing", kitchen: "kitchen activity" };
export const COLOUR = { absence: "--act-empty", cooking: "--act-cooking", dishwashing: "--act-washing", eating: "--act-eating",
  other: "--act-moving", social_activity: "--act-talk", vacuum_cleaner: "--act-vacuum", watching_tv: "--act-tv", working: "--act-working", kitchen: "--act-kitchen" };
export const MEAL = new Set(["cooking", "dishwashing", "eating", "kitchen"]);   // "kitchen": a stretch heard as kitchen, not which activity
export const ACTIVE = new Set([...CLASSES, "kitchen"].filter((c) => c !== "absence"));
const TALK_OR_TV_MARGIN = 0.15;
// The named household sound types (web/public/model/kinds.json, measured by eval/beyond.py). Order = display order.
// No pets, phone or doorbell: the same choice as the sound-name allow-list (kettle/evidence_labels.json).
// Named sounds that passed the pre-registered bar (eval/PREREGISTER-SOUNDS.md -> results/sounds.json; kinds.json "shown").
// The others are never sent; a check on one says "Can't tell". web/test/fixes.test.mjs keeps this equal to kinds.json.
export const KINDS_SHOWN = new Set(["tv"]);
// A kettle check needs the kettle in 2 or more windows of one block (about 20 s), not one stray window (handover v3.2, 3.1).
export const KIND_MIN_WINDOWS = { kettle: 2 };
export const KIND_NAMES = { kettle: "Kettle or a hot drink", frying: "Frying or sizzling", chopping: "Chopping", blender: "Blender",
  microwave: "Microwave", dishes: "Dishes and cutlery", tap: "Running water", cupboard: "Cupboards and drawers", door: "A door",
  alarm: "Timer or appliance beep", tv: "TV or radio", vacuum: "Vacuum cleaner", typing: "Typing", footsteps: "Footsteps", glass: "Glass breaking" };
// Labels the parent may keep private (plan D2): they reveal visits and TV habits.
export const HIDEABLE = ["social_activity", "watching_tv"];
export const WHY_TEXT = { veto: "a machine or bathroom sound was louder than any kitchen sound", novel: "a sound unlike anything it learned",
  close: "two activities sounded alike", mixed: "the sounds kept changing", low: "it wasn't sure enough" };
const WHY_ORDER = ["veto", "novel", "close", "mixed", "low"];
export const WEEK_S = 7 * 86400;

// ---------------------------------------------------------------- Python-compatible number helpers
/** Python round(x): halves go to the even neighbour. */
export function pyRound(x) {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 ? 2 * Math.round(x / 2) : r;
}
/** Python round(x, 3): correctly rounded from the exact binary value (toFixed does the same), ties to even. */
const round3 = (x) => Number(x.toFixed(3));     // an exact 3-decimal tie can't be a binary double, so no tie rule needed
/** Python f"{x:.2f}" (ties to even only matter for exact binary halves like 0.125). */
function fmt2(x) {
  if (Number.isInteger(x * 8) && Math.abs((x * 100) % 1) === 0.5) return (pyRound(x * 100) / 100).toFixed(2);   // 0.125, 0.375, …
  return x.toFixed(2);
}

// ---------------------------------------------------------------- time in the kitchen's zone
/** Offset from UTC in seconds of IANA zone `tz` at unix time t (seconds). */
export function tzOffset(tz, t) {
  const f = new Intl.DateTimeFormat("en-US", { timeZone: tz, hourCycle: "h23", year: "numeric", month: "numeric", day: "numeric",
    hour: "numeric", minute: "numeric", second: "numeric" });
  const p = Object.fromEntries(f.formatToParts(new Date(t * 1000)).map((x) => [x.type, +x.value || 0]));
  const asUTC = Date.UTC(p.year, p.month - 1, p.day, p.hour % 24, p.minute, p.second) / 1000;
  return Math.round(asUTC - Math.floor(t));
}
/** Local midnight (unix s) of the day containing t, given the zone's offset. */
export function localMidnight(t, off) { return Math.floor((t + off) / 86400) * 86400 - off; }
export function clock(t, off) {
  const s = ((Math.trunc(t + off) % 86400) + 86400) % 86400;
  const mins = Math.floor(s / 60), h = Math.floor(mins / 60), m = mins % 60;
  return `${(h % 12) || 12}:${String(m).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`;
}
export function clockRange(a, z, off) {
  const ca = clock(a, off), cz = clock(z, off);
  return ca.slice(-2) === cz.slice(-2) ? `${ca.slice(0, -3)}–${cz}` : `${ca}–${cz}`;
}
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
function local(t, off) { return new Date((t + off) * 1000); }       // read with getUTC* only
export function dateText(t, off) { const d = local(t, off); return `${DAYS[d.getUTCDay()]}, ${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}`; }
function dayName(t, off) { return DAYS[local(t, off).getUTCDay()]; }

// ---------------------------------------------------------------- timeline (kettle/timeline.py)
export function staleS(hop) { return 2 * hop + 30; }
export const BRIDGE_S = 30;

// Second opinion (kettle/witness.py; numbers from models/witness.json, checked by web/test/core.test.mjs).
// Each window carries w = { k, family, v }: the strongest general kitchen tag, which activity it belongs to, and the
// strongest "motor or bathroom" tag, all made on the device. Two plain rules:
//   rescue: the head has no answer (unfamiliar sound, or below theta) and k >= TAU_K and k > v  -> show w.family
//   veto:   the head says a kitchen activity but v >= TAU_V and v > k                           -> show "Not sure"
export const TAU_K = 0.15, TAU_V = 0.3;
// Rule 2c (kettle/witness.py name_kitchen; models/witness.json "_evidence"; added Sun Nov 15 after a real-kitchen test showed
// pots while cooking as "washing up" and cutlery as "eating"). Rescued windows say only "kitchen"; each stretch of them is
// named from evidence across all its windows: each window votes for the louder of cooking sounds and running water;
// cooking if its votes are >= COOK_SHARE of the stretch and >= water's; else any water vote -> washing up;
// chewing -> eating; otherwise "kitchen activity". Windows from before carry no evidence numbers and keep the old family.
export const TAU_COOK = 0.05, TAU_WATER = 0.05, TAU_MOUTH = 0.1, COOK_SHARE = 0.1;
const FAMILIES = ["cooking", "dishwashing", "eating"];
export function nameKitchen(evs) {
  const ws = evs.map((e) => e.w || {});
  if (!ws.some((w) => "cook" in w)) {
    const fams = ws.map((w) => w.family).filter((f) => FAMILIES.includes(f));
    if (!fams.length) return "kitchen";
    let best = FAMILIES[0];
    for (const f of FAMILIES) if (fams.filter((x) => x === f).length > fams.filter((x) => x === best).length) best = f;
    return best;
  }
  // each window votes for the louder of its cooking and running-water evidence (a sink at 0.7 beats a faint "stir")
  const n = ws.length;
  const cook = ws.filter((w) => (w.cook || 0) >= TAU_COOK && (w.cook || 0) >= (w.water || 0)).length;
  const water = ws.filter((w) => (w.water || 0) >= TAU_WATER && (w.water || 0) > (w.cook || 0)).length;
  if (cook >= Math.max(1, COOK_SHARE * n) && cook >= water) return "cooking";
  if (water >= 1) return "dishwashing";
  if (ws.some((w) => (w.mouth || 0) >= TAU_MOUTH)) return "eating";
  return "kitchen";
}
export function nameStretches(labels, run) {
  const out = labels.slice();
  let i = 0;
  while (i < out.length) {
    if (out[i] !== "kitchen") { i++; continue; }
    let j = i;
    while (j + 1 < out.length && out[j + 1] === "kitchen") j++;
    const name = nameKitchen(run.slice(i, j + 1));
    for (let k = i; k <= j; k++) out[k] = name;
    i = j + 1;
  }
  return absorb(out, run);
}
// Rule 2d (kettle/timeline.py _absorb): a washing-up, eating or unnamed kitchen stretch with no evidence of its own (no running
// water, no chewing), at most SHORT_FLIP windows long, next to cooking, is cooking. The case: the head was 93% sure of
// "washing up" on plates and cutlery between frying, with no tap heard.
export const SHORT_FLIP = 3;
export function votes(evs) {
  const ws = evs.map((e) => e.w || {});
  return { cook: ws.filter((w) => (w.cook || 0) >= TAU_COOK && (w.cook || 0) >= (w.water || 0)).length,
    water: ws.filter((w) => (w.water || 0) >= TAU_WATER && (w.water || 0) > (w.cook || 0)).length,
    mouth: ws.filter((w) => (w.mouth || 0) >= TAU_MOUTH).length, has: ws.some((w) => "cook" in w) };
}
function unsupported(label, evs) {
  const v = votes(evs);
  if (!v.has) return false;
  return (label === "dishwashing" && v.water === 0) || (label === "eating" && v.mouth === 0) || label === "kitchen";
}
function absorb(labels, run) {
  const out = labels.slice(), segs = [];
  for (let i = 0; i < out.length;) { let j = i; while (j + 1 < out.length && out[j + 1] === out[i]) j++; segs.push([i, j]); i = j + 1; }
  segs.forEach(([i, j], n) => {
    const lab = out[i];
    if (!["dishwashing", "eating", "kitchen"].includes(lab) || !unsupported(lab, run.slice(i, j + 1))) return;
    const near = [n - 1, n + 1].filter((m) => m >= 0 && m < segs.length).map((m) => out[segs[m][0]]);
    if (j - i + 1 <= SHORT_FLIP && near.includes("cooking")) for (let k = i; k <= j; k++) out[k] = "cooking";
  });
  return out;
}
export function headLabel(ev, theta) {
  if (ev.novel) return "not_sure";
  const p = ev.probs;
  const top = Object.keys(p).sort((a, b) => p[b] - p[a]);
  const pair = new Set([top[0], top[1]]);
  if (pair.has("watching_tv") && pair.has("social_activity") && p[top[0]] - p[top[1]] < TALK_OR_TV_MARGIN && p[top[0]] + p[top[1]] >= theta)
    return "talk_or_tv";
  return p[top[0]] >= theta ? top[0] : "not_sure";
}
const rescues = (lab, w) => !!w && lab === "not_sure" && w.k >= TAU_K && w.k > w.v;
const vetoes = (lab, w) => !!w && MEAL.has(lab) && w.v >= TAU_V && w.v > w.k;
export function rawLabel(ev, theta) {
  if (ev.private) return "private";
  const lab = headLabel(ev, theta);
  if (vetoes(lab, ev.w)) return "not_sure";
  if (rescues(lab, ev.w)) return "cook" in ev.w ? "kitchen" : ev.w.family;
  return lab;
}
export const bySounds = (ev, theta) => rescues(headLabel(ev, theta), ev.w);
export function smooth(labels) {
  return labels.map((lab, i) => {
    if (i === 0 || i === labels.length - 1) return lab;
    const a = labels[i - 1], c = labels[i + 1];
    return lab === a || lab === c ? lab : a === c ? a : "not_sure";
  });
}
export function bridge(labels, run, maxS = BRIDGE_S) {
  const out = labels.slice();
  let i = 1;
  while (i < out.length) {
    if (out[i] !== "not_sure") { i++; continue; }
    let j = i;
    while (j + 1 < out.length && out[j + 1] === "not_sure") j++;
    const before = out[i - 1], after = j + 1 < out.length ? out[j + 1] : null;
    const short = run[j].end - run[i - 1].end <= maxS;
    let novel = false;
    for (let k = i; k <= j; k++) novel = novel || !!run[k].novel;
    if (before === after && before !== "not_sure" && before !== "talk_or_tv" && short && !novel) for (let k = i; k <= j; k++) out[k] = before;
    i = j + 1;
  }
  return out;
}
export function runs(events, gap) {
  const out = [];
  for (const ev of events) {
    const last = out.length ? out[out.length - 1] : null;
    if (last && ev.start - last[last.length - 1].end <= gap) last.push(ev); else out.push([ev]);
  }
  return out;
}
function stateOf(label) { return label === "absence" ? "empty" : ["not_sure", "talk_or_tv", "private"].includes(label) ? label : "activity"; }
/** Why a Not sure block couldn't be named, by majority of its windows (plan F10; kettle/timeline.py why_not_sure). */
export function whyNotSure(evs, theta) {
  const votes = Object.fromEntries(WHY_ORDER.map((k) => [k, 0]));
  for (const e of evs) {
    const p = Object.values(e.probs).sort((a, b) => b - a);
    if (vetoes(headLabel(e, theta), e.w)) votes.veto++;
    else if (e.novel) votes.novel++;
    else if (p[0] >= theta) votes.mixed++;
    else if (p[0] - p[1] < TALK_OR_TV_MARGIN) votes.close++;
    else votes.low++;
  }
  return WHY_ORDER.reduce((best, k) => (votes[k] > votes[best] ? k : best), WHY_ORDER[0]);
}
/** Named sound types in these windows: { id: { n, at } } (at = start of the first window naming it). */
function kindsIn(evs) {
  const out = {};
  for (const e of evs) for (const k of e.kinds || []) { if (!out[k]) out[k] = { n: 0, at: e.start }; out[k].n++; }
  return out;
}
export function mergeSounds(lists, k = 3) {
  const total = new Map();
  for (const lst of lists) for (const s of lst || []) total.set(s.name, (total.get(s.name) || 0) + s.score);
  const n = Math.max(1, lists.length);
  return [...total.entries()].sort((a, b) => b[1] - a[1]).slice(0, k).map(([name, v]) => ({ name, score: round3(v / n) }));
}
function makeBlock(evs, label, theta) {
  let conf;
  if (label === "not_sure" || label === "talk_or_tv") conf = evs.reduce((s, e) => s + Math.max(...Object.values(e.probs)), 0) / evs.length;
  else conf = evs.reduce((s, e) => s + (e.probs[label] || 0), 0) / evs.length;
  const guesses = {};
  for (const e of evs) for (const [k, v] of Object.entries(e.probs)) guesses[k] = (guesses[k] || 0) + v / evs.length;
  const top2 = Object.keys(guesses).sort((a, b) => guesses[b] - guesses[a]).slice(0, 2);
  const st = stateOf(label);
  return { start: evs[0].start, end: evs[evs.length - 1].end, state: st, activity: st === "activity" || st === "empty" ? label : null,
    conf: round3(conf), n_windows: evs.length, sounds: mergeSounds(evs.map((e) => e.sounds)),
    guesses: top2.map((g) => ({ activity: g, p: round3(guesses[g]) })),
    by_sounds: evs.reduce((n, e) => n + (bySounds(e, theta) ? 1 : 0), 0), kinds: kindsIn(evs),
    taught: evs.filter((e) => e.taught).length, ...(label === "not_sure" ? { why: whyNotSure(evs, theta) } : {}) };
}
function subtract(a, b, cuts) {
  let parts = [[a, b]];
  for (const [c0, c1] of cuts) {
    const nxt = [];
    for (const [p0, p1] of parts) {
      if (c1 <= p0 || c0 >= p1) { nxt.push([p0, p1]); continue; }
      if (c0 > p0) nxt.push([p0, c0]);
      if (c1 < p1) nxt.push([c1, p1]);
    }
    parts = nxt;
  }
  return parts.filter(([p0, p1]) => p1 - p0 > 1);
}
const emptyBlock = (start, end, state, extra = {}) => ({ start, end, state, activity: null, conf: null, n_windows: 0, sounds: [], guesses: [], kinds: {}, ...extra });

// holdLast (timeline rule 5, "settle before showing"): while Kettle is listening, the newest window is left off until the
// next one arrives, because 2-of-3 smoothing can still change it. Nothing on the bar, in the summary or in a check is ever
// taken back: a check that reads "Met" stays met.
export function blocks(events, theta, { pauses = [], listeningFrom = null, now = null, listeningNow = false, gap = staleS(2), bridgeS = BRIDGE_S, holdLast = false } = {}) {
  const evs = events.slice().sort((a, b) => a.end - b.end);
  const out = [];
  const allRuns = runs(evs, gap);
  allRuns.forEach((full, r) => {
    let labs = smooth(full.map((e) => rawLabel(e, theta))), run = full;
    if (holdLast && r === allRuns.length - 1) { labs = labs.slice(0, -1); run = full.slice(0, -1); }
    labs = nameStretches(bridge(labs, run, bridgeS), run);
    let i = 0;
    while (i < run.length) {
      let j = i;
      while (j + 1 < run.length && labs[j + 1] === labs[i]) j++;
      out.push(makeBlock(run.slice(i, j + 1), labs[i], theta));
      i = j + 1;
    }
  });
  for (const p of pauses) out.push(emptyBlock(p[0], p[1], "paused", { kind: p.length > 2 ? p[2] : "pause" }));
  const cuts = pauses.map((p) => [p[0], p[1]]);
  const heard = out.filter((b) => b.state !== "paused").map((b) => [b.start, b.end]).sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  const edges = [];
  for (let k = 0; k + 1 < heard.length; k++) if (heard[k + 1][0] - heard[k][1] > gap) edges.push([heard[k][1], heard[k + 1][0]]);
  if (heard.length && now != null && !listeningNow && now - heard[heard.length - 1][1] > gap) edges.push([heard[heard.length - 1][1], now]);
  if (listeningFrom != null && heard.length && heard[0][0] - listeningFrom > gap + 10) edges.push([listeningFrom, heard[0][0]]);
  for (const [a, b] of edges) for (const [p0, p1] of subtract(a, b, cuts)) out.push(emptyBlock(p0, p1, "not_listening"));
  return out.sort((x, y) => x.start - y.start);
}

const round5 = (t) => pyRound(t / 300) * 300;      // 5 minutes, so the summary agrees with the bar and the checks
function span(b, off) {
  const a = round5(b.start), z = round5(b.end), name = PHRASE[b.activity];
  if (b.activity === "watching_tv" && z - a >= 3600) return `TV from about ${clock(a, off)}`;
  if (z - a < 600) return `${name} around ${clock(a, off)}`;
  return `${name} around ${clockRange(a, z, off)}`;
}
export function summary(blks, off, listeningSince = null) {
  const merged = [];
  for (const b of blks.filter((x) => x.state === "activity")) {
    const last = merged[merged.length - 1];
    if (last && last.activity === b.activity && b.start - last.end <= 900) merged[merged.length - 1] = { ...last, end: b.end };
    else merged.push({ ...b });
  }
  if (!merged.length) {
    const unsure = blks.filter((b) => b.state === "not_sure").reduce((s, b) => s + b.end - b.start, 0);
    if (unsure >= 20 * 60) return `Kettle wasn't sure about ${Math.floor(unsure / 60)} minutes of sound today.`;
    if (listeningSince != null) return `No kitchen activity heard yet today. Kettle has been listening since ${clock(listeningSince, off)}.`;
    return "";
  }
  const last3 = merged.slice(-3);
  const items = last3.map((b, i) => {
    let text = span(b, off);
    if (i && last3[i - 1].activity === b.activity) text = "again " + text.split(" ").slice(1).join(" ");
    return text;
  });
  const more = merged.length - 3;
  let text = "So far today: " + items.slice(0, -1).join(", ") + (items.length > 1 ? " and " : "") + items[items.length - 1] + ".";
  if (more > 0) text += ` ${more === 1 ? "One earlier activity is" : `${more} earlier activities are`} on the bar.`;
  return text;
}
export function displayName(b) {
  return { not_sure: "Not sure", talk_or_tv: "Talking or TV", not_listening: "Not listening", paused: "Paused", private: "Private" }[b.state] || DISPLAY[b.activity];
}

// ---------------------------------------------------------------- rules (kettle/rules.py)
export const MAX_RULES = 8;          // plan v3.1: up to 8 checks, including the "Worth a look" concerns
const CANT_TELL_SHARE = 0.25, WINDOW_START_H = 6;
export const DEFAULT_RULES = [{ id: "r1", type: "kitchen_by", time: "10:00" }, { id: "r2", type: "tv_over", hours: 4 }];
function hhmm(s) { const [h, m] = s.split(":").map(Number); return `${(h % 12) || 12}:${String(m).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`; }
export function ruleTitle(r) {
  if (r.type === "concern") return concernTitle(r);
  if (r.type === "kind_by") return `${KIND_NAMES[r.kind] || r.kind} by ${hhmm(r.time)}`;
  if (r.type === "tv_over") return `TV on for more than ${r.hours} hour${r.hours !== 1 ? "s" : ""}`;
  return `${r.type === "kitchen_by" ? "Kitchen activity" : "Activity"} by ${hhmm(r.time)}`;
}
function counts(r, b) {
  if (r.type === "kind_by") return !!(b.kinds && b.kinds[r.kind] && b.kinds[r.kind].n >= (KIND_MIN_WINDOWS[r.kind] || 1));
  if (r.type === "kitchen_by") return b.state === "activity" && MEAL.has(b.activity);
  return (b.state === "activity" && ACTIVE.has(b.activity)) || b.state === "talk_or_tv";
}
function unheard(blks, a, z) {
  const heard = blks.filter((b) => b.state !== "not_listening" && b.state !== "paused" && b.end > a && b.start < z)
    .map((b) => [Math.max(a, b.start), Math.min(z, b.end)]).sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  const gaps = []; let t = a;
  for (const [s, e] of heard) { if (s > t + 1) gaps.push([t, s]); t = Math.max(t, e); }
  if (z > t + 1) gaps.push([t, z]);
  return gaps;
}
function dur(seconds) {
  let m = pyRound(seconds / 60); const h = Math.floor(m / 60); m = m % 60;
  return h && m ? `${h} h ${m} min` : h ? `${h} h` : `${m} min`;
}
const byStart = (blks) => blks.slice().sort((a, b) => a.start - b.start);
function ruleOne(r, blks, now, day0, off, hidden = [], ctx = {}) {
  if (r.type === "concern") return concernOne(r, blks, now, day0, off, hidden, ctx);
  if (r.type === "tv_over") return ruleTv(r, blks, now, day0, off, hidden);
  if (r.type === "kind_by" && !KINDS_SHOWN.has(r.kind))
    return { state: "cant_tell", at: null, detail: `Can't tell: Kettle can't name "${(KIND_NAMES[r.kind] || r.kind).toLowerCase()}" reliably yet (it missed our accuracy bar), so this check is paused.`, note: null };
  const [h, m] = r.time.split(":").map(Number);
  const deadline = day0 + h * 3600 + m * 60;
  const start = Math.min(day0 + WINDOW_START_H * 3600, deadline - 3600);
  const first = byStart(blks).find((b) => counts(r, b) && b.end > start && b.start < deadline && b.start <= now);
  if (first && r.type === "kind_by") {
    const at = Math.max(first.kinds[r.kind].at, first.start);
    return { state: "met", at, detail: `Met at ${clock(at, off)} (${KIND_NAMES[r.kind].toLowerCase()} heard)`, note: null };
  }
  if (first) {
    const what = first.activity ? PHRASE[first.activity] : "talking or TV";
    const sure = (first.conf || 0) >= 0.8 ? "high" : "medium";
    return { state: "met", at: first.start, detail: `Met at ${clock(first.start, off)} (${what}, how sure: ${sure})`, note: null };
  }
  const end = Math.min(now, deadline);
  const gaps = end > start ? unheard(blks, start, end) : [];
  const missing = gaps.reduce((s, [a, b]) => s + b - a, 0);
  if (now < deadline) return { state: "not_yet", at: null, detail: `Not yet · checks in ${dur(deadline - now)}`, note: null };
  if (missing > CANT_TELL_SHARE * (deadline - start)) {
    const heard = blks.filter((b) => b.state !== "not_listening" && b.state !== "paused");
    const f = heard.length ? Math.min(...heard.map((b) => b.start)) : null;
    if (f == null) return { state: "cant_tell", at: null, detail: "Can't tell: Kettle hasn't heard anything yet today.", note: null };
    if (f >= deadline) return { state: "cant_tell", at: null, detail: `Can't tell: Kettle started at ${clock(f, off)}, after this check's time.`, note: null };
    const [a, b] = gaps.reduce((best, g) => (g[1] - g[0] > best[1] - best[0] ? g : best));
    return { state: "cant_tell", at: null, detail: `Can't tell: Kettle wasn't listening from ${clockRange(a, b, off)}.`, note: null };
  }
  const later = byStart(blks).find((b) => counts(r, b) && b.start >= deadline);
  const whole = missing < 60 ? "Kettle was listening the whole time." : `Kettle was listening for ${pyRound(100 * (1 - missing / (deadline - start)))}% of that time.`;
  const unsure = blks.filter((b) => (b.state === "not_sure" || b.state === "talk_or_tv") && b.start < deadline && b.end > start);
  const note = (later ? `First heard at ${clock(later.start, off)}. ` : "") + "You might call to say hello.";
  if (unsure.length && r.type !== "kind_by") {
    const mins = unsure.reduce((s, b) => s + Math.min(b.end, deadline) - Math.max(b.start, start), 0);
    return { state: "missed", at: deadline, detail: `No clear kitchen activity by ${hhmm(r.time)}. Kettle heard sounds it couldn't name for ${dur(mins)} before then.`, note };
  }
  return { state: "missed", at: deadline, detail: `Not heard by ${hhmm(r.time)}. ${whole}`, note };
}
function ruleTv(r, blks, now, day0, off, hidden = []) {
  if (hidden.includes("watching_tv")) return { state: "cant_tell", at: null, detail: "Can't tell: TV is kept private on the kitchen device.", note: null };
  const tv = blks.filter((b) => b.state === "activity" && b.activity === "watching_tv");
  const total = tv.reduce((s, b) => s + b.end - b.start, 0);
  if (total > r.hours * 3600) return { state: "over", at: null, detail: `TV for ${dur(total)} today (from ${clock(tv[0].start, off)})`, note: null };
  const start = day0 + WINDOW_START_H * 3600;
  const gaps = now > start ? unheard(blks, start, now) : [];
  const missing = gaps.reduce((s, [a, b]) => s + b - a, 0);
  if (now > start && missing > CANT_TELL_SHARE * (now - start)) {
    const heard = blks.filter((b) => b.state !== "not_listening" && b.state !== "paused");
    const f = heard.length ? Math.min(...heard.map((b) => b.start)) : null;
    const lead = f == null ? "Can't tell: Kettle hasn't heard anything yet today."
      : f - start > 0.5 * (now - start) ? `Can't tell yet: Kettle has only been listening since ${clock(f, off)}.`
        : `Can't tell: Kettle wasn't listening for ${dur(missing)} today.`;
    return { state: "cant_tell", at: null, detail: lead, note: total ? `TV heard for ${dur(total)}.` : null };
  }
  // plan S7/F2: when Kettle couldn't name the sound for more than a quarter of the time it listened, it may have missed
  // the TV. Say "Can't tell", never "No TV heard today".
  const listened = blks.filter((b) => LISTENED.includes(b.state) && b.end > start).reduce((s, b) => s + b.end - Math.max(b.start, start), 0);
  const unnamed = blks.filter((b) => (b.state === "not_sure" || b.state === "talk_or_tv") && b.end > start).reduce((s, b) => s + b.end - Math.max(b.start, start), 0);
  if (listened > 0 && unnamed > CANT_TELL_SHARE * listened)
    return { state: "cant_tell", at: null, detail: `Can't tell: Kettle couldn't name the sound for ${dur(unnamed)} of the ${dur(listened)} it listened today.`,
      note: total ? `TV heard for ${dur(total)}.` : null };
  return { state: "under", at: null, detail: total ? `TV for ${dur(total)} so far today` : "No TV heard today", note: null };
}
const LISTENED = ["activity", "empty", "not_sure", "talk_or_tv", "private"];

// ---------------------------------------------------------------- "Worth a look" concerns (plan v3.1, Workstream C; kettle/concerns.py)
// Not urgent, but worth a call. Each reads the same blocks as the checks; the family can change the numbers or remove it.
// Device-side ones (stove, beep, water, cough) are measured on the listening device (safety.js) and arrive as alerts.
export const CONCERNS = {
  too_quiet: { hours: 4, from: "08:00", to: "20:00", escalate: 6 },     // C1
  no_meal: { time: "14:00" },                                           // C2
  tv_long: { hours: 8 },                                                // C3
  tv_night: { hours: 1 },                                               // C4
  night: { minutes: 30 },                                               // C5
  stove: {}, beep: {}, water: {},                                       // C6, C7, C9 (on the device)
  device_off: { hours: 2 },                                             // C10
  cough: {},                                                            // C11 (opt-in, on the device)
  unusual: {},                                                          // C12
};
export const DEVICE_CONCERNS = ["stove", "beep", "water", "cough"];
const HEARD = ["activity", "talk_or_tv", "not_sure", "private"];
const heardBlock = (b) => HEARD.includes(b.state) && !(b.state === "activity" && b.activity === "absence");
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
export function concernTitle(r) {
  const c = { ...CONCERNS[r.cid], ...r };
  return {
    too_quiet: `No activity for ${plural(c.hours, "hour")} (${hhmm(c.from)}–${hhmm(c.to)})`,
    no_meal: `No kitchen activity by ${hhmm(c.time)}`,
    tv_long: `TV on for more than ${plural(c.hours, "hour")}`,
    tv_night: `TV on between 1 and 5 AM for more than ${plural(c.hours, "hour")}`,
    night: `Up at night (midnight to 5 AM) for more than ${c.minutes} min`,
    stove: "Stove maybe left on (40 min of frying or boiling, nothing else)",
    beep: "A timer or appliance beeping for 5 minutes",
    water: "Water left running for 20 minutes",
    device_off: `The listening device off for ${plural(c.hours, "hour")} during the day`,
    cough: "Unusual coughing (counted on the device only)",
    unusual: "A day unlike their usual (after a week)",
  }[r.cid] || "A check";
}
function validConcern(r, id) {
  const cid = r.cid || r.id;
  if (!Object.hasOwn(CONCERNS, cid)) throw new Error("unknown concern");
  const out = { id, type: "concern", cid };
  const num = (k, lo, hi) => { if (r[k] == null) return; const v = Number(r[k]); if (!(v >= lo && v <= hi)) throw new Error(`bad ${k}`); out[k] = v; };
  const time = (k) => { if (r[k] == null) return; const [h, m] = String(r[k]).split(":").map(Number); if (!(h >= 0 && h < 24 && m >= 0 && m < 60)) throw new Error("bad time");
    out[k] = `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`; };
  if (cid === "too_quiet") { num("hours", 1, 12); num("escalate", 2, 16); time("from"); time("to"); }
  if (cid === "no_meal") time("time");
  if (cid === "tv_long") num("hours", 2, 16);
  if (cid === "tv_night") num("hours", 0.5, 4);
  if (cid === "night") num("minutes", 10, 240);
  if (cid === "device_off") num("hours", 1, 12);
  return out;
}
const atClock = (day0, s) => { const [h, m] = s.split(":").map(Number); return day0 + h * 3600 + m * 60; };
function overlap(blks, pred, a, z) {
  let total = 0, first = null, last = null;
  for (const b of blks) {
    if (!pred(b)) continue;
    const s0 = Math.max(a, b.start), s1 = Math.min(z, b.end);
    if (s1 > s0) { total += s1 - s0; first = first == null ? s0 : Math.min(first, s0); last = last == null ? s1 : Math.max(last, s1); }
  }
  return { total, first, last };
}
const secOfDay = (t, off) => (((t + off) % 86400) + 86400) % 86400;
function concernOne(r, blks, now, day0, off, hidden, ctx) {
  const c = { ...CONCERNS[r.cid], ...r };
  const B = byStart(blks);
  const res = (state, detail, extra = {}) => ({ state, at: null, detail, note: null, ...extra });
  const alerts = (ctx.alerts || []).filter((a) => a.type === r.cid && a.at >= day0);
  if (DEVICE_CONCERNS.includes(r.cid)) {
    if (alerts.length) return res("note", `Heard at ${clock(alerts[alerts.length - 1].at, off)}: ${alerts[alerts.length - 1].text || "see the note"}.`, { at: alerts[alerts.length - 1].at });
    return res("watching", "Kettle listens for this on the listening device.");
  }
  if (r.cid === "no_meal") {
    const x = ruleOne({ type: "kitchen_by", time: c.time }, blks, now, day0, off, hidden);
    return { ...x, state: { met: "ok", missed: "note" }[x.state] || x.state };
  }
  if (r.cid === "tv_long") {
    const x = ruleTv({ type: "tv_over", hours: c.hours }, blks, now, day0, off, hidden);
    return { ...x, state: { over: "note", under: "ok" }[x.state] || x.state };
  }
  if (r.cid === "tv_night" || r.cid === "night") {
    if (r.cid === "tv_night" && hidden.includes("watching_tv")) return res("cant_tell", "Can't tell: TV is kept private on the listening device.");
    const a = day0 + (r.cid === "tv_night" ? 3600 : 0), z = day0 + 5 * 3600;
    if (now < a) return res("not_yet", `Checks from ${clock(a, off)}`);
    const pred = r.cid === "tv_night" ? (b) => b.state === "activity" && b.activity === "watching_tv" : heardBlock;
    const o = overlap(B, pred, a, Math.min(now, z));
    const limit = r.cid === "tv_night" ? c.hours * 3600 : c.minutes * 60;
    if (o.total > limit) {
      const what = r.cid === "tv_night" ? "TV on" : "Activity";
      return res("note", `${what} for ${dur(o.total)} between ${clock(a, off)} and ${clock(z, off)} (${clockRange(o.first, o.last, off)}).`, { at: o.first });
    }
    if (r.cid === "night") {
      const keys = Object.keys(ctx.days || {}).sort().slice(-8, -1);
      const nights = keys.filter((k) => ((ctx.days[k].night || 0) * (ctx.hop || 10)) >= limit).length;
      if (nights >= 3) return res("note", `Activity after midnight on ${nights} of the last ${keys.length} nights.`);
    }
    const gaps = unheard(B, a, Math.min(now, z)).reduce((s2, [x, y]) => s2 + y - x, 0);
    if (gaps > CANT_TELL_SHARE * (Math.min(now, z) - a)) return res("cant_tell", `Can't tell: Kettle wasn't listening for ${dur(gaps)} of that time.`);
    return res("ok", o.total ? `${dur(o.total)} so far, under ${dur(limit)}.` : "Nothing heard.");
  }
  if (r.cid === "device_off") {
    const a = atClock(day0, "08:00"), z = Math.min(now, atClock(day0, "20:00"));
    if (z <= a) return res("not_yet", `Checks from ${clock(a, off)}`);
    const o = overlap(B, (b) => b.state === "not_listening", a, z);
    if (o.total >= c.hours * 3600) return res("note", `Kettle couldn't listen for ${dur(o.total)} today: the device was off, asleep or disconnected.`, { at: o.first });
    return res("ok", o.total ? `Not listening for ${dur(o.total)} today.` : "Listening all day so far.");
  }
  if (r.cid === "too_quiet") {
    const a = atClock(day0, c.from), z = Math.min(now, atClock(day0, c.to));
    if (now < a) return res("not_yet", `Checks from ${clock(a, off)}`);
    const heard = B.filter(heardBlock);
    if (!heard.some((b) => b.start < z)) return res("ok", "Waiting for the first activity today.");
    // quiet stretches between sounds, counting only time Kettle was listening (paused and not-listening time don't count)
    let best = { quiet: 0, from: null, to: null, open: false }, prevEnd = null;
    const stretch = (x, y, open) => {
      const s0 = Math.max(x, a), s1 = Math.min(y, z);
      if (s1 <= s0) return;
      const lost = overlap(B, (b) => b.state === "not_listening" || b.state === "paused", s0, s1).total;
      const quiet = s1 - s0 - lost;
      if (quiet > best.quiet) best = { quiet, from: x, to: y, open };
    };
    for (const b of heard) { if (prevEnd != null && b.start > prevEnd) stretch(prevEnd, b.start, false); prevEnd = Math.max(prevEnd ?? b.end, b.end); }
    if (prevEnd != null && now > prevEnd) stretch(prevEnd, now, true);
    if (best.quiet >= c.hours * 3600) {
      const escalate = best.open && best.quiet >= c.escalate * 3600;
      return res("note", best.open ? `No activity heard for ${dur(best.quiet)}, since ${clock(best.from, off)}.`
        : `No activity heard for ${dur(best.quiet)} (${clockRange(best.from, best.to, off)}).`, { at: best.from, escalate });
    }
    return res("ok", best.quiet >= 1800 ? `Longest quiet stretch so far: ${dur(best.quiet)}.` : "Activity heard through the day.");
  }
  if (r.cid === "unusual") {
    const keys = Object.keys(ctx.days || {}).sort();
    const todayKey = new Date((now + off) * 1000).toISOString().slice(0, 10);
    const past = keys.filter((k) => k < todayKey).slice(-7).map((k) => ctx.days[k]).filter((d) => d && d.meal != null).map((d) => secOfDay(d.meal, d.off ?? off));
    if (past.length < 5) return res("not_yet", `Kettle needs about a week of days to learn what's usual (${past.length} so far).`);
    const lo = Math.min(...past), hi = Math.max(...past), usual = `${clock(day0 + lo, 0)}–${clock(day0 + hi, 0)}`.replace(/^(.*) (AM|PM)–(.*) \2$/, "$1–$3 $2");
    const first = B.find((b) => b.state === "activity" && MEAL.has(b.activity));
    if (first && first.start - day0 > hi + 3600) return res("note", `First kitchen activity at ${clock(first.start, off)}, later than usual (${usual} on recent days).`, { at: first.start });
    if (!first && now - day0 > hi + 3600) return res("note", `No kitchen activity yet. On recent days it was by ${clock(day0 + hi, 0)}.`);
    return res(first ? "ok" : "not_yet", first ? `Within the usual range (${usual}).` : `Usually between ${usual}.`);
  }
  return res("ok", "");
}

/**
 * The status strip above the family summary (plan 2d): red "Urgent" for an open urgent alert today, amber
 * "Worth a look" for notes, grey "Can't tell" when Kettle could tell what happened for under 75% of the day or isn't
 * listening, green "All OK so far today" only when none of these. Never green when coverage is low.
 */
export function statusStrip({ alerts = [], rules = [], coverage: cov = null, heartbeat: hb = null, day0 = 0 }) {
  const open = alerts.filter((a) => a.tier === "urgent" && a.at >= day0 && !a.acked);
  if (open.length) return { level: "urgent", text: open.length === 1 ? "Urgent: tap to see" : `Urgent: ${open.length} alerts, tap to see`, n: open.length };
  const notes = rules.filter((r) => r.type === "concern" && r.state === "note").length
    + alerts.filter((a) => a.tier === "concern" && a.at >= day0 && !a.dismissed && !rules.some((r) => r.concern === a.type && r.state === "note")).length;
  if (notes) return { level: "look", text: `Worth a look: ${plural(notes, "note")}`, n: notes };
  const st = hb ? hb.state : null;
  if (st && !["listening", "starting"].includes(st)) return { level: "cant_tell", text: st === "paused" ? "Can't tell: Kettle is paused" : "Can't tell: Kettle isn't listening right now", n: 0 };
  if (!cov) return { level: "cant_tell", text: "Can't tell yet: Kettle has heard too little today", n: 0 };
  if (cov.pct < 75) return { level: "cant_tell", text: `Can't tell: Kettle could only tell what was happening for ${cov.pct}% of the day`, n: 0 };
  return { level: "ok", text: "All OK so far today", n: 0 };
}

export function evaluateRules(rules, blks, now, day0, off, hidden = [], ctx = {}) {
  return rules.slice(0, MAX_RULES).map((r) => ({ id: r.id, type: r.type, ...(r.type === "concern" ? { concern: r.cid } : {}), title: ruleTitle(r),
    ...ruleOne(r, blks, now, day0, off, hidden, ctx) }));
}
export function validateRules(rules) {
  if (!Array.isArray(rules) || rules.length > MAX_RULES) throw new Error(`up to ${MAX_RULES} checks`);
  return rules.map((r, i) => {
    if (!r || typeof r !== "object") throw new Error("each check is an object");
    if (r.type === "concern") return validConcern(r, `r${i + 1}`);
    if (r.type === "activity_by") r = { ...r, type: "any_by" };
    if (r.type === "kitchen_by" || r.type === "any_by") {
      const [h, m] = String(r.time).split(":").map(Number);
      if (!(h >= 0 && h < 24 && m >= 0 && m < 60)) throw new Error("bad time");
      return { id: `r${i + 1}`, type: r.type, time: `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}` };
    }
    if (r.type === "kind_by") {
      const [h, m] = String(r.time).split(":").map(Number);
      if (!(h >= 0 && h < 24 && m >= 0 && m < 60)) throw new Error("bad time");
      if (!Object.hasOwn(KIND_NAMES, r.kind)) throw new Error("unknown sound");
      return { id: `r${i + 1}`, type: r.type, kind: r.kind, time: `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}` };
    }
    if (r.type === "tv_over") {
      const h = Number(r.hours);
      if (!(h >= 0.5 && h <= 16)) throw new Error("bad hours");
      return { id: `r${i + 1}`, type: r.type, hours: h };
    }
    throw new Error("unknown check");
  });
}

// ---------------------------------------------------------------- the parent's controls (kettle/live.py)
export function newState() {
  return { consent: false, consent_at: null, last_confirm: null, off_at: null, paused_at: null, paused_until: null, pause_reason: null,
    pauses: [], started_at: null, last_window_t: null, mic: null, mic_at: null, rules: DEFAULT_RULES.map((r) => ({ ...r })), log: [] };
}
const log = (s, now, type, extra = {}) => { const rec = { t: now, type, ...extra }; s.log = (s.log || []).slice(-200); s.log.push(rec); return rec; };
export function isPaused(s, now) { return !!s.paused_until && now < s.paused_until; }
function closePause(s, now) {
  if (s.paused_at != null) s.pauses.push(s.pause_reason === "guest" ? [s.paused_at, Math.min(now, s.paused_until || now), "guest"] : [s.paused_at, Math.min(now, s.paused_until || now)]);
}
export function nextMorning(now, off, hour = 8) {
  const t8 = localMidnight(now, off) + hour * 3600;
  return t8 > now ? t8 : t8 + 86400;
}
export const actions = {
  consent(s, now) { Object.assign(s, { consent: true, consent_at: now, last_confirm: now, off_at: null, started_at: now }); return log(s, now, "consent"); },
  off(s, now) { closePause(s, now); Object.assign(s, { off_at: now, paused_at: null, paused_until: null }); return log(s, now, "off"); },
  start(s, now) { if (s.off_at) s.pauses.push([s.off_at, now, "off"]); Object.assign(s, { off_at: null, started_at: now }); return log(s, now, "start"); },
  pause(s, now, { minutes = null, reason = "parent", off = 0 } = {}) {
    const until = minutes ? now + minutes * 60 : nextMorning(now, off);
    if (!isPaused(s, now)) s.paused_at = now;
    Object.assign(s, { paused_until: until, pause_reason: reason });
    return log(s, now, "pause", { until, reason });
  },
  resume(s, now) { closePause(s, now); Object.assign(s, { paused_at: null, paused_until: null, pause_reason: null, started_at: now }); return log(s, now, "resume"); },
  keep_on(s, now) { s.last_confirm = now; if (s.pause_reason === "weekly") actions.resume(s, now); return log(s, now, "keep_on"); },
  privacy(s, now, { hide = [], kindsOff = [] }) {
    Object.assign(s, { hide: hide.filter((h) => HIDEABLE.includes(h)), kinds_off: kindsOff.filter((k) => Object.hasOwn(KIND_NAMES, k)) });
    return log(s, now, "privacy", { hide: s.hide, kinds_off: s.kinds_off });
  },
  mic(s, now, { state }) { Object.assign(s, { mic: state, mic_at: now }); if (state === "ok") s.started_at = now; return log(s, now, "mic", { state }); },
  // what the kitchen device is and whether it's plugged in: so the family hears "on battery, 41%" before it goes quiet
  device(s, now, { kind, charging = null, level = null, ms = null } = {}) { s.device = { kind, charging, level, ms, at: now }; return null; },
};
export function weeklyDue(s, now) { return !!s.consent && !s.off_at && s.last_confirm != null && now - s.last_confirm >= WEEK_S; }
export function tick(s, now) {
  let changed = false;
  if (s.paused_until && now >= s.paused_until) {
    s.pauses.push(s.pause_reason === "guest" ? [s.paused_at, s.paused_until, "guest"] : [s.paused_at, s.paused_until]);
    log(s, s.paused_until, "resume", { auto: true });
    Object.assign(s, { paused_at: null, paused_until: null, pause_reason: null, started_at: now });
    changed = true;
  }
  if (weeklyDue(s, now) && now - s.last_confirm > WEEK_S + 86400 && !isPaused(s, now)) {
    s.paused_at = now;
    Object.assign(s, { paused_until: now + 365 * 86400, pause_reason: "weekly" });
    log(s, now, "pause", { until: s.paused_until, reason: "weekly" });
    changed = true;
  }
  return changed;
}
export function canListen(s, now) { return !!s.consent && !s.off_at && !isPaused(s, now); }

// ---------------------------------------------------------------- heartbeat (kettle/heartbeat.py)
const FIRST_LABEL_S = 10;
export function heartbeat(s, now, hop = 2) {
  const last = s.last_window_t, base = { since: null, until: null, last_heard: last };
  if (!s.consent) return { ...base, state: "never" };
  if (s.off_at) return { ...base, state: "off", since: s.off_at };
  if (s.paused_until && now < s.paused_until) return { ...base, state: "paused", since: s.paused_at, until: s.paused_until };
  if (s.mic === "blocked") return { ...base, state: "mic_blocked", since: s.mic_at };
  if (s.mic === "none") return { ...base, state: "no_mic", since: s.mic_at };
  const started = s.started_at;
  if (last == null || (started && last < started)) {
    if (started && now - started <= FIRST_LABEL_S + staleS(hop)) return { ...base, state: "starting", since: started };
    return { ...base, state: "stale", since: started || last };
  }
  if (now - last <= staleS(hop)) return { ...base, state: "listening", since: started };
  return { ...base, state: "stale", since: last };
}
function ago(sec) {
  const s = Math.max(0, Math.trunc(sec));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} min`;
  return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} min`;
}

// ---------------------------------------------------------------- what both screens show (kettle/view.py)
/** How the kitchen device reads in a sentence. dev = { kind: "phone" | "tablet" | "laptop", charging, level } or null (older homes: a laptop). */
export function deviceWord(dev) { return dev && ["phone", "tablet", "laptop"].includes(dev.kind) ? dev.kind : "laptop"; }
/** A calm warning before the kitchen device runs out: "The kitchen phone is on battery (41%). Plug it in to keep Kettle listening." */
export function batteryLine(dev) {
  if (!dev || dev.charging !== false || !(dev.level >= 0)) return "";
  return `The kitchen ${deviceWord(dev)} is on battery (${Math.round(dev.level * 100)}%). Plug it in to keep Kettle listening.`;
}
export function heartbeatLine(hb, now, off, names, dev = null) {
  const P = names.parent, c = (t) => (t ? clock(t, off) : ""), D = deviceWord(dev);
  const asleep = D === "laptop" ? "laptop asleep, closed or off" : `${D} asleep, off, or Kettle isn't on its screen`;
  const { state: st, since, until } = hb;
  let text = "";
  if (st === "never") text = `Kettle isn't on yet. It starts when ${P} chooses to turn it on.`;
  else if (st === "off") text = `Turned off by ${P} at ${c(since)}.`;
  else if (st === "starting") text = "Starting… the first label appears in about 10 seconds.";
  else if (st === "listening") { const a = now - hb.last_heard; text = a < 10 ? "Listening · last heard just now" : `Listening · last heard ${ago(a)} ago`; }
  else if (st === "stale") text = since ? `Not listening since ${c(since)} (${asleep}). Nothing is known after that.` : "Not listening. Nothing is known about today yet.";
  else if (st === "paused") {
    const tomorrow = localMidnight(until, off) !== localMidnight(now, off);
    let tail = tomorrow ? `until tomorrow at ${c(until)} at the latest` : `resumes at ${c(until)}`;
    if (until - now > 300 * 86400) tail = `until ${P} answers the weekly question`;
    text = `Paused by ${P} at ${c(since)} · ${tail}`;
  } else if (st === "mic_blocked") text = `Not listening: the microphone is blocked or silent on the kitchen ${D}.`.replace(" or silent on the kitchen laptop", " on the kitchen laptop");
  else if (st === "no_mic") text = `Not listening: no microphone was found on the kitchen ${D}.`;
  const battery = st === "listening" || st === "starting" ? batteryLine(dev) : "";
  return { state: st, text, since, until, last_heard: hb.last_heard, since_text: c(since), until_text: c(until), battery };
}
export function blockView(b, off, names) {
  const rng = clockRange(b.start, b.end, off);
  const out = { ...b, label: displayName(b), range: rng };
  if (b.state === "activity" || b.state === "empty") {
    const how = b.conf >= 0.8 ? "high" : "medium";
    out.how_sure = how;
    out.card = b.state === "empty" ? `Quiet · ${rng} · Kettle was listening; the kitchen was quiet.`
      : `${DISPLAY[b.activity]} · ${rng} · ${b.n_windows} windows · how sure: ${how}`;
    if (2 * (b.by_sounds || 0) > b.n_windows) {       // most of this block was named by the second opinion
      out.how_sure = "medium";
      out.card = `${DISPLAY[b.activity]} · ${rng} · ${b.n_windows} windows · how sure: medium · named from general kitchen sounds, because this room sounds unlike the home Kettle learned in`;
    }
  } else if (b.state === "not_sure") {
    const g = b.guesses.map((x) => `${DISPLAY[x.activity]} ${fmt2(x.p)}`).join(" · ");
    out.card = `Not sure · ${rng} · Kettle heard something but couldn't tell what: ${WHY_TEXT[b.why || "low"]}. Closest guesses: ${g}.`;
  } else if (b.state === "talk_or_tv") out.card = `Talking or TV · ${rng} · Kettle heard voices and can't tell talking from the TV here. It never keeps words.`;
  else if (b.state === "not_listening") out.card = `Not listening · ${rng} · Kettle can't say what happened here.`;
  else if (b.state === "private") out.card = `Private · ${rng} · ${names.parent} chose not to share this kind of sound.`;
  else if (b.state === "paused") {
    out.label = b.kind === "off" ? `Turned off by ${names.parent}` : b.kind === "guest" ? "Paused for a guest" : `Paused by ${names.parent}`;
    out.card = `${out.label} · ${rng}`;
  }
  out.heard = Object.keys(KIND_NAMES).filter((k) => KINDS_SHOWN.has(k) && b.kinds && b.kinds[k]).map((k) => KIND_NAMES[k]);
  return out;
}
export function chipText(ev, theta, now, live) {
  if (!ev || !live || now - ev.end > 15) return null;
  let lab = rawLabel(ev, theta);               // the same rule as the day bar, so the chip never disagrees with it
  if (lab === "kitchen") lab = nameKitchen([ev]);   // rule 2c on this one window
  return { not_sure: "Not sure what that is", absence: "Quiet", talk_or_tv: "Sounds like talking or TV" }[lab] || `Sounds like ${PHRASE[lab]}`;
}

/**
 * Plan B3: the last 7 days, descriptive only (never an alarm): for each day whether kitchen activity was heard
 * before the morning check's time, from the server's per-day tally (household.js tallyDays).
 */
export function week(s, now, { tz = "UTC", hop = 10 } = {}) {
  const r = (s.rules || DEFAULT_RULES).find((x) => x.type === "kitchen_by") || { time: "10:00" };
  const [h, m] = r.time.split(":").map(Number);
  const rows = [];
  const off = tzOffset(tz, now);
  for (let i = 6; i >= 0; i--) {
    const t = now - i * 86400, key = new Date((t + off) * 1000).toISOString().slice(0, 10);
    const d = (s.days || {})[key];
    const day0 = localMidnight(t, off), deadline = day0 + h * 3600 + m * 60;
    const heardMin = d ? Math.round((d.n * hop) / 60) : 0;
    let state = "unknown";
    if (d && d.meal != null && d.meal < deadline) state = "yes";
    else if (d && heardMin >= 60 && (i > 0 || now >= deadline)) state = "no";
    rows.push({ key, day: DAYS[local(day0, off).getUTCDay()].slice(0, 3), state, at: d && d.meal != null ? clock(d.meal, off) : null,
      kettle: d && d.kettle != null ? clock(d.kettle, off) : null, heard_min: heardMin, told_pct: d && d.n ? pyRound((100 * d.told) / d.n) : null });
  }
  const known = rows.filter((x) => x.state !== "unknown");
  const yes = rows.filter((x) => x.state === "yes").length;
  const text = known.length ? `Kitchen activity before ${hhmm(r.time)} was heard on ${yes} of the last ${known.length} day${known.length === 1 ? "" : "s"} Kettle was listening.` : "";
  return { rows, text, time: hhmm(r.time) };
}

/** Plan F1: how much of the listened time Kettle could put a name to, so a day of Not sure never reads as quiet. */
export function coverage(blks) {
  const heard = ["activity", "empty", "not_sure", "talk_or_tv", "private"];
  let listened = 0, told = 0;
  for (const b of blks) if (heard.includes(b.state)) { listened += b.end - b.start; if (b.state !== "not_sure") told += b.end - b.start; }
  if (listened < 600) return null;
  const pct = pyRound((100 * told) / listened);
  return { pct, listened_s: listened, text: `Kettle could tell what was happening for ${pct}% of the time it listened today.` };
}
/** Named sound types heard today: [{ id, name, n, first, last, text }] in display order. */
export function heardToday(evs, off) {
  const agg = {};
  for (const e of evs) for (const k of e.kinds || []) {
    if (!Object.hasOwn(KIND_NAMES, k) || !KINDS_SHOWN.has(k)) continue;     // older stored windows may carry a now-hidden name
    const a = agg[k] || (agg[k] = { id: k, name: KIND_NAMES[k], n: 0, first: e.start, last: e.start });
    a.n++; a.first = Math.min(a.first, e.start); a.last = Math.max(a.last, e.start);
  }
  return Object.keys(KIND_NAMES).filter((k) => agg[k]).map((k) => {
    const a = agg[k];
    return { ...a, text: a.n === 1 || a.last - a.first < 120 ? `at ${clock(a.first, off)}` : `${clock(a.first, off)} to ${clock(a.last, off)}` };
  });
}

/**
 * The full picture both screens draw, from the household's raw state and its window events.
 * opts: { theta, tz (IANA zone of the kitchen) or off (seconds), hop (seconds between windows), names: {parent, caregiver} }
 */
export function today(s, events, now, { theta, tz = null, off = null, day0 = null, hop = 2, names = { parent: "Dad", caregiver: "Meera" } } = {}) {
  off = off ?? tzOffset(tz || "UTC", now);
  day0 = day0 ?? localMidnight(now, off);
  const hb = heartbeat(s, now, hop);
  const liveNow = hb.state === "listening" || hb.state === "starting";
  const evs = events.filter((e) => e.end >= day0);
  const pauses = (s.pauses || []).filter((p) => p[1] >= day0).map((p) => [Math.max(p[0], day0), ...p.slice(1)]);
  if (s.paused_at != null && isPaused(s, now)) pauses.push([Math.max(s.paused_at, day0), now]);
  if (s.off_at) pauses.push([Math.max(s.off_at, day0), now, "off"]);
  const started = s.started_at ? Math.max(s.started_at, day0) : null;
  const blks = blocks(evs, theta, { pauses, now, listeningNow: liveNow, listeningFrom: started, gap: staleS(hop), holdLast: liveNow });
  if (["stale", "mic_blocked", "no_mic"].includes(hb.state) && !blks.some((b) => b.state !== "paused")) {
    const a = Math.max(day0, hb.since || day0);
    if (now - a > 1) blks.push(emptyBlock(a, now, "not_listening"));
  }
  const listeningSince = evs.length ? Math.min(...evs.map((e) => e.start)) : null;
  let sum = summary(blks, off, liveNow ? listeningSince : null);
  const since = hb.since || hb.last_heard;
  if (["paused", "stale", "off", "mic_blocked", "no_mic"].includes(hb.state) && since && sum) sum += ` Nothing is known after ${clock(since, off)}.`;
  const last = evs.length ? evs[evs.length - 1] : null;
  const out = {
    now, now_text: clock(now, off), day0, tz_offset: off, date_text: dateText(now, off), names,
    heartbeat: heartbeatLine(hb, now, off, names, s.device || null),
    device: s.device || null,
    blocks: blks.map((b) => blockView(b, off, names)),
    summary: sum,
    rules: evaluateRules(s.rules || DEFAULT_RULES, blks, now, day0, off, s.hide || [], { alerts: s.alerts || [], days: s.days || {}, hop }),
    coverage: coverage(blks),
    heard: heardToday(evs, off),
    rule_defs: s.rules || DEFAULT_RULES,
    chip: chipText(last, theta, now, liveNow),
    last_event: last,
    kitchen: { consent: !!s.consent, off: !!s.off_at, paused: isPaused(s, now), pause_reason: isPaused(s, now) ? s.pause_reason : null,
      weekly_due: weeklyDue(s, now), consent_text: s.consent_at ? clock(s.consent_at, off) : "", consent_day: s.consent_at ? dayName(s.consent_at, off) : null,
      listening_since_text: s.started_at ? clock(s.started_at, off) : "", hide: s.hide || [], kinds_off: s.kinds_off || [] },
    theta,
  };
  out.alerts = (s.alerts || []).filter((a) => a.at >= day0 - 86400).map((a) => ({ ...a, at_text: clock(a.at, off), since_text: a.since ? clock(a.since, off) : null }));
  out.status = statusStrip({ alerts: out.alerts, rules: out.rules, coverage: out.coverage, heartbeat: out.heartbeat, day0 });
  return out;
}
