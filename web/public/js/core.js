// Kettle core: the same rules as the Python app (kettle/labels, timeline, rules, heartbeat, live, view), in plain JS.
// Used by both screens in the browser and by the sync worker. No DOM, no network. web/test/core.test.mjs checks every
// output against Python's own answers (web/test/fixtures.json, made by tools/export_web_fixtures.py).

// ---------------------------------------------------------------- labels
export const CLASSES = ["absence", "cooking", "dishwashing", "eating", "other", "social_activity", "vacuum_cleaner", "watching_tv", "working"];
export const DISPLAY = { absence: "Quiet", cooking: "Cooking", dishwashing: "Washing up", eating: "Eating", other: "Some activity",
  social_activity: "Conversation", vacuum_cleaner: "Vacuuming", watching_tv: "TV", working: "Typing" };
export const PHRASE = { absence: "quiet", cooking: "cooking", dishwashing: "washing up", eating: "eating", other: "some activity",
  social_activity: "conversation", vacuum_cleaner: "vacuuming", watching_tv: "TV", working: "typing" };
export const COLOUR = { absence: "--act-empty", cooking: "--act-cooking", dishwashing: "--act-washing", eating: "--act-eating",
  other: "--act-moving", social_activity: "--act-talk", vacuum_cleaner: "--act-vacuum", watching_tv: "--act-tv", working: "--act-working" };
export const MEAL = new Set(["cooking", "dishwashing", "eating"]);
export const ACTIVE = new Set(CLASSES.filter((c) => c !== "absence"));
const TALK_OR_TV_MARGIN = 0.15;
// The named household sound types (web/public/model/kinds.json, measured by eval/beyond.py). Order = display order.
export const KIND_NAMES = { kettle: "Kettle or a hot drink", frying: "Frying or sizzling", chopping: "Chopping", blender: "Blender",
  microwave: "Microwave", dishes: "Dishes and cutlery", tap: "Running water", cupboard: "Cupboards and drawers", door: "A door",
  doorbell: "Doorbell or knocking", phone: "Phone ringing", alarm: "An alarm or beeping", tv: "TV or radio", vacuum: "Vacuum cleaner",
  typing: "Typing", footsteps: "Footsteps", pet: "A dog or cat", glass: "Glass breaking" };
// Labels the parent may keep private (plan D2): they reveal visits and TV habits.
export const HIDEABLE = ["social_activity", "watching_tv"];
export const WHY_TEXT = { appliance: "only appliance hum, no kitchen sounds", novel: "a sound unlike anything it learned",
  close: "two activities sounded alike", mixed: "the sounds kept changing", low: "it wasn't sure enough" };
const WHY_ORDER = ["appliance", "novel", "close", "mixed", "low"];
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

export function rawLabel(ev, theta) {
  if (ev.private) return "private";
  if (ev.novel || ev.hold) return "not_sure";
  const p = ev.probs;
  const top = Object.keys(p).sort((a, b) => p[b] - p[a]);
  const pair = new Set([top[0], top[1]]);
  if (pair.has("watching_tv") && pair.has("social_activity") && p[top[0]] - p[top[1]] < TALK_OR_TV_MARGIN && p[top[0]] + p[top[1]] >= theta)
    return "talk_or_tv";
  return p[top[0]] >= theta ? top[0] : "not_sure";
}
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
    if (e.hold === "appliance") votes.appliance++;
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
function makeBlock(evs, label, theta = 0.66) {
  let conf;
  if (label === "not_sure" || label === "talk_or_tv") conf = evs.reduce((s, e) => s + Math.max(...Object.values(e.probs)), 0) / evs.length;
  else conf = evs.reduce((s, e) => s + (e.probs[label] || 0), 0) / evs.length;
  const guesses = {};
  for (const e of evs) for (const [k, v] of Object.entries(e.probs)) guesses[k] = (guesses[k] || 0) + v / evs.length;
  const top2 = Object.keys(guesses).sort((a, b) => guesses[b] - guesses[a]).slice(0, 2);
  const st = stateOf(label);
  return { start: evs[0].start, end: evs[evs.length - 1].end, state: st, activity: st === "activity" || st === "empty" ? label : null,
    conf: round3(conf), n_windows: evs.length, sounds: mergeSounds(evs.map((e) => e.sounds)),
    guesses: top2.map((g) => ({ activity: g, p: round3(guesses[g]) })), kinds: kindsIn(evs),
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

export function blocks(events, theta, { pauses = [], listeningFrom = null, now = null, listeningNow = false, gap = staleS(2), bridgeS = BRIDGE_S } = {}) {
  const evs = events.slice().sort((a, b) => a.end - b.end);
  const out = [];
  for (const run of runs(evs, gap)) {
    const labs = bridge(smooth(run.map((e) => rawLabel(e, theta))), run, bridgeS);
    let i = 0;
    while (i < run.length) {
      let j = i;
      while (j + 1 < run.length && labs[j + 1] === labs[i]) j++;
      out.push(makeBlock(run.slice(i, j + 1), labs[i], theta));
      i = j + 1;
    }
  }
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

function span(b, off) {       // exact block edges, the same times the timeline shows (never rounded)
  const a = b.start, z = b.end, name = PHRASE[b.activity];
  if (b.activity === "watching_tv" && z - a >= 3600) return `TV from ${clock(a, off)}`;
  if (clock(a, off) === clock(z, off)) return `${name} at ${clock(a, off)}`;
  return `${name} ${clockRange(a, z, off)}`;
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
    if (i && last3[i - 1].activity === b.activity) { const name = PHRASE[b.activity]; text = `${name} again ${text.slice(name.length + 1)}`; }
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
export const MAX_RULES = 3;
const CANT_TELL_SHARE = 0.25, WINDOW_START_H = 6;
export const DEFAULT_RULES = [{ id: "r1", type: "kitchen_by", time: "10:00" }, { id: "r2", type: "tv_over", hours: 4 }];
function hhmm(s) { const [h, m] = s.split(":").map(Number); return `${(h % 12) || 12}:${String(m).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`; }
export function ruleTitle(r) {
  if (r.type === "kind_by") return `${KIND_NAMES[r.kind]} by ${hhmm(r.time)}`;
  if (r.type === "tv_over") return `TV on for more than ${r.hours} hour${r.hours !== 1 ? "s" : ""}`;
  return `${r.type === "kitchen_by" ? "Kitchen activity" : "Some sound of activity"} by ${hhmm(r.time)}`;
}
function counts(r, b) {
  if (r.type === "kind_by") return !!(b.kinds && b.kinds[r.kind]);
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
function ruleOne(r, blks, now, day0, off, hidden = []) {
  if (r.type === "tv_over") return ruleTv(r, blks, now, day0, off, hidden);
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
  if (hidden.includes("watching_tv")) return { state: "cant_tell", at: null, detail: "Can't tell: TV is kept private on the kitchen laptop.", note: null };
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
  return { state: "under", at: null, detail: total ? `TV for ${dur(total)} so far today` : "No TV heard today", note: null };
}
export function evaluateRules(rules, blks, now, day0, off, hidden = []) {
  return rules.slice(0, MAX_RULES).map((r) => ({ id: r.id, type: r.type, title: ruleTitle(r), ...ruleOne(r, blks, now, day0, off, hidden) }));
}
export function validateRules(rules) {
  if (!Array.isArray(rules) || rules.length > MAX_RULES) throw new Error("up to 3 checks");
  return rules.map((r, i) => {
    if (!r || typeof r !== "object") throw new Error("each check is an object");
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
export function heartbeatLine(hb, now, off, names) {
  const P = names.parent, c = (t) => (t ? clock(t, off) : "");
  const { state: st, since, until } = hb;
  let text = "";
  if (st === "never") text = `Kettle isn't on yet. It starts when ${P} chooses to turn it on.`;
  else if (st === "off") text = `Turned off by ${P} at ${c(since)}.`;
  else if (st === "starting") text = "Starting… the first label appears in about 10 seconds.";
  else if (st === "listening") { const a = now - hb.last_heard; text = a < 10 ? "Listening · last heard just now" : `Listening · last heard ${ago(a)} ago`; }
  else if (st === "stale") text = since ? `Not listening since ${c(since)} (laptop asleep, closed or off). Nothing is known after that.` : "Not listening. Nothing is known about today yet.";
  else if (st === "paused") {
    const tomorrow = localMidnight(until, off) !== localMidnight(now, off);
    let tail = tomorrow ? `until tomorrow at ${c(until)} at the latest` : `resumes at ${c(until)}`;
    if (until - now > 300 * 86400) tail = `until ${P} answers the weekly question`;
    text = `Paused by ${P} at ${c(since)} · ${tail}`;
  } else if (st === "mic_blocked") text = "Not listening: the microphone is blocked on the kitchen laptop.";
  else if (st === "no_mic") text = "Not listening: no microphone was found on the kitchen laptop.";
  return { state: st, text, since, until, last_heard: hb.last_heard, since_text: c(since), until_text: c(until) };
}
export function blockView(b, off, names) {
  const rng = clockRange(b.start, b.end, off);
  const out = { ...b, label: displayName(b), range: rng };
  if (b.state === "activity" || b.state === "empty") {
    const how = b.conf >= 0.8 ? "high" : "medium";
    out.how_sure = how;
    out.card = b.state === "empty" ? `Quiet · ${rng} · Kettle was listening; the kitchen was quiet.`
      : `${DISPLAY[b.activity]} · ${rng} · ${b.n_windows} windows · how sure: ${how}`;
  } else if (b.state === "not_sure") {
    const g = b.guesses.map((x) => `${DISPLAY[x.activity]} ${fmt2(x.p)}`).join(" · ");
    out.card = `Not sure · ${rng} · Kettle heard something but couldn't tell what: ${WHY_TEXT[b.why || "low"]}. Closest guesses: ${g}.`;
  } else if (b.state === "talk_or_tv") out.card = `Talking or TV · ${rng} · Kettle heard voices and can't tell talking from the TV here. It never keeps words.`;
  else if (b.state === "not_listening") out.card = `Not listening · ${rng} · Kettle can't say what happened here.`;
  else if (b.state === "private") out.card = `Private · ${rng} · ${names.parent} chose not to share this kind of sound.`;
  else if (b.state === "paused") {
    out.label = b.kind === "off" ? `Turned off by ${names.parent}` : b.kind === "guest" ? `Paused for a guest` : `Paused by ${names.parent}`;
    out.card = `${out.label} · ${rng}`;
  }
  out.heard = Object.keys(KIND_NAMES).filter((k) => b.kinds && b.kinds[k]).map((k) => KIND_NAMES[k]);
  return out;
}
export function chipText(ev, theta, now, live) {
  if (!ev || !live || now - ev.end > 15) return null;
  const p = ev.probs, top = Object.keys(p).sort((a, b) => p[b] - p[a]);
  if (ev.novel || ev.conf < theta) return "Not sure what that is";
  if (ev.label === "absence") return "Quiet";
  const pair = new Set([top[0], top[1]]);
  if (pair.has("watching_tv") && pair.has("social_activity") && p[top[0]] - p[top[1]] < TALK_OR_TV_MARGIN) return "Sounds like talking or TV";
  return `Sounds like ${PHRASE[ev.label]}`;
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
    if (!Object.hasOwn(KIND_NAMES, k)) continue;
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
  const blks = blocks(evs, theta, { pauses, now, listeningNow: liveNow, listeningFrom: started, gap: staleS(hop) });
  if (["stale", "mic_blocked", "no_mic"].includes(hb.state) && !blks.some((b) => b.state !== "paused")) {
    const a = Math.max(day0, hb.since || day0);
    if (now - a > 1) blks.push(emptyBlock(a, now, "not_listening"));
  }
  const listeningSince = evs.length ? Math.min(...evs.map((e) => e.start)) : null;
  let sum = summary(blks, off, liveNow ? listeningSince : null);
  const since = hb.since || hb.last_heard;
  if (["paused", "stale", "off", "mic_blocked", "no_mic"].includes(hb.state) && since && sum) sum += ` Nothing is known after ${clock(since, off)}.`;
  const last = evs.length ? evs[evs.length - 1] : null;
  return {
    now, now_text: clock(now, off), day0, tz_offset: off, date_text: dateText(now, off), names,
    heartbeat: heartbeatLine(hb, now, off, names),
    blocks: blks.map((b) => blockView(b, off, names)),
    summary: sum,
    rules: evaluateRules(s.rules || DEFAULT_RULES, blks, now, day0, off, s.hide || []),
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
}
