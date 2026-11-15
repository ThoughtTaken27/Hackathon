// One household's sync logic, independent of where it runs (Cloudflare Durable Object or the local dev server).
// It stores only what the Python app stores: the parent's choices (consent, pause, off), the family's checks, and window
// labels with times and scores. No audio ever reaches it; the kitchen page labels sound on the parent's own device.
import { CLASSES, HIDEABLE, KIND_NAMES, MEAL, actions, newState, tick, tzOffset, validateRules } from "../public/js/core.js";
import { SHOWN_SOUNDS } from "../public/js/sounds.js";
import { validSubscription } from "./push.js";

export const KEEP_DAYS = 8;            // labels older than this are deleted
const MAX_EVENTS_PER_POST = 60;
const MAX_NAME = 24;

export async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
export function randomId(n, alphabet = "abcdefghjkmnpqrstuvwxyz23456789") {
  const bytes = crypto.getRandomValues(new Uint8Array(n));
  return [...bytes].map((b) => alphabet[b % alphabet.length]).join("");
}
const cleanName = (s, fallback) => (typeof s === "string" && s.trim() ? s.trim().slice(0, MAX_NAME) : fallback);
const validTz = (tz) => { try { new Intl.DateTimeFormat("en-US", { timeZone: tz }); return true; } catch { return false; } };

const RELATION_IDS = ["parent", "grandparent", "partner", "relative", "friend", "self"];
const ROOM_IDS = ["kitchen", "living", "bedroom", "hallway", "bathroom", "home", "other"];
const cleanRelation = (r, fallback = "parent") => (RELATION_IDS.includes(r) ? r : fallback);
/** {type, name} for the room the device listens in (people.js ROOMS); a free name only for "other". */
function cleanRoom(room, fallback = { type: "kitchen", name: "" }) {
  if (!room || typeof room !== "object" || !ROOM_IDS.includes(room.type)) return fallback;
  return { type: room.type, name: room.type === "other" ? cleanName(room.name, "room").toLowerCase() : "" };
}

/** A new household's stored record, and its two keys (returned once, stored only as hashes).
 *  No name given = no name stored: screens say "Your parent" and "you" (people.js who()), never a made-up Mom or Dad. */
export async function create({ parent, caregiver, relation, room, tz } = {}, now) {
  const kitchenKey = randomId(24), familyKey = randomId(24);
  const state = { ...newState(), names: { parent: cleanName(parent, null), caregiver: cleanName(caregiver, null),
      relation: cleanRelation(relation), room: cleanRoom(room) },
    tz: validTz(tz) ? tz : "UTC", created: now, hop: 10,
    keys: { kitchen: await sha256(kitchenKey), family: await sha256(familyKey) } };
  return { state, kitchenKey, familyKey };
}

/** The state as either screen may see it (no key hashes). */
export function publicState(s) {
  const { keys, push, ...rest } = s;              // push endpoints are capability URLs: they never leave the server
  return { ...rest, pushCount: (push || []).length };
}

export function cleanEvent(e, now) {
  if (!e || typeof e !== "object") return null;
  const start = +e.start, end = +e.end;
  if (!(end > start) || end - start > 600 || end > now + 120 || end < now - 86400) return null;
  if (e.label === "private") {           // a label the parent keeps private: no scores, no sounds (plan D2)
    const probs = Object.fromEntries(CLASSES.map((c) => [c, 0]));
    return { start, end, label: "private", conf: 0, probs, novel: false, private: true, sounds: [], kinds: [] };
  }
  if (!CLASSES.includes(e.label)) return null;
  const probs = {};
  for (const c of CLASSES) { const v = +(e.probs || {})[c]; if (!(v >= 0 && v <= 1)) return null; probs[c] = Math.round(v * 1e4) / 1e4; }
  // only names on the allow-list are kept (kettle/evidence_labels.json): the server refuses anything else a client sends
  const sounds = Array.isArray(e.sounds) ? e.sounds.slice(0, 3).filter((x) => x && typeof x.name === "string" && SHOWN_SOUNDS.has(x.name))
    .map((x) => ({ name: x.name, score: Math.round((+x.score || 0) * 1000) / 1000 })) : [];
  const out = { start, end, label: e.label, conf: Math.round(probs[e.label] * 1000) / 1000, probs, novel: !!e.novel, sounds };
  // the second opinion: two scores and one of three kitchen words, nothing else
  const w = e.w;
  if (w && typeof w === "object" && MEAL.has(w.family) && w.k >= 0 && w.k <= 1 && w.v >= 0 && w.v <= 1)
  {
    out.w = { k: Math.round(w.k * 1000) / 1000, family: w.family, v: Math.round(w.v * 1000) / 1000 };
    // three evidence numbers for naming a kitchen stretch (core.js nameKitchen): cooking, running water, chewing
    for (const g of ["cook", "water", "mouth"]) if (w[g] != null && +w[g] >= 0 && +w[g] <= 1) out.w[g] = Math.round(+w[g] * 1000) / 1000;
  }
  // named household sound types: ids from the allow-list only (plan D1, A6); "taught" = helped by this kitchen's setup
  out.kinds = Array.isArray(e.kinds) ? [...new Set(e.kinds.filter((k) => Object.hasOwn(KIND_NAMES, k)))] : [];
  if (e.taught) out.taught = true;
  return out;
}

/**
 * Plan B3: a tiny per-day tally kept as windows arrive, so the family's week view needs no scan of 8 days of labels.
 * Per local day: windows heard, windows Kettle could name, first kitchen-activity window, first kettle sound,
 * TV windows. Single windows, before the timeline's smoothing; 9 days kept.
 */
export function tallyDays(s, evs) {
  const days = s.days || (s.days = {});
  for (const e of evs) {
    const off = tzOffset(s.tz || "UTC", e.end);
    const key = new Date((e.start + off) * 1000).toISOString().slice(0, 10);
    const d = days[key] || (days[key] = { n: 0, told: 0, meal: null, kettle: null, tv: 0, off });
    d.n++;
    const sure = !e.private && !e.novel && e.conf >= 0.66;
    if (sure) d.told++;
    if (sure && ["cooking", "dishwashing", "eating"].includes(e.label) && (d.meal == null || e.start < d.meal)) d.meal = e.start;
    if ((e.kinds || []).includes("kettle") && (d.kettle == null || e.start < d.kettle)) d.kettle = e.start;
    if (sure && e.label === "watching_tv") d.tv++;
  }
  for (const k of Object.keys(days).sort().slice(0, -9)) delete days[k];
}

/**
 * Handle one request for this household.
 * store: { getState(), putState(s), addEvents(evs), eventsSince(t), prune(before), wipe() }
 * Returns { status, body }.
 */
// Urgent safety alerts the kitchen device may raise (web/public/js/safety.js): smoke/CO alarm, a gunshot, a crash then a cry or
// stillness, screaming, shouting, repeated crying, and the "I need help" button. Only the kind, the time and the check-in state are
// stored; the family view shows a red banner until seen, and every subscribed family phone gets a push notification (notify.js).
export const SAFETY_TYPES = ["smoke", "co", "gunshot", "fall", "fall_still", "scream", "shout", "distress", "stillness", "help"];
// Handover v3.5, 3.2: the family is told at once ("asking": the kitchen screen is asking "Are you OK?" right now), then the same
// alert (same time, same id) is updated when the person answers ("ok", "help") or doesn't ("no_answer"). "none" = no check-in.
export const CHECKIN_STATES = ["asking", "ok", "help", "no_answer", "none"];
const MAX_ALERTS = 20, MAX_PUSH = 10;

export async function handle(store, { method, route, key, body, now }) {
  const s = await store.getState();
  if (!s) return { status: 404, body: { error: "This Kettle link isn't valid any more. Ask for a new one." } };
  const h = key ? await sha256(key) : "";
  const role = h && h === s.keys.kitchen ? "kitchen" : h && h === s.keys.family ? "family" : null;
  if (!role) return { status: 403, body: { error: "This link doesn't match this home." } };

  let changed = tick(s, now);
  const done = async (status, extra = {}) => {
    if (changed) await store.putState(s);
    return { status, body: { now, role, state: publicState(s), ...extra } };
  };

  if (method === "GET" && route === "state") {
    const since = Math.max(+body?.since || 0, now - 36 * 3600);
    return done(200, { events: await store.eventsSince(since) });
  }
  if (method === "POST" && route === "events") {
    if (role !== "kitchen") return { status: 403, body: { error: "Only the kitchen laptop sends what it hears." } };
    if (!s.consent || s.off_at || (s.paused_until && now < s.paused_until)) return done(409, { error: "Kettle isn't listening right now." });
    const evs = (Array.isArray(body?.events) ? body.events : []).slice(0, MAX_EVENTS_PER_POST).map((e) => cleanEvent(e, now)).filter(Boolean);
    if (evs.length) {
      await store.addEvents(evs);
      tallyDays(s, evs);
      s.last_window_t = Math.max(s.last_window_t || 0, ...evs.map((e) => e.end));
      if (s.mic !== "ok") { s.mic = "ok"; s.mic_at = now; }
      changed = true;
      if (Math.random() < 0.02) await store.prune(now - KEEP_DAYS * 86400);
    }
    if (body?.tz && validTz(body.tz) && body.tz !== s.tz) { s.tz = body.tz; changed = true; }
    return done(200, { accepted: evs.length });
  }
  if (method === "POST" && route === "action") {
    if (role !== "kitchen") return { status: 403, body: { error: "Only the person at the kitchen laptop can do this." } };
    const type = body?.type;
    if (!["consent", "off", "start", "pause", "resume", "keep_on", "mic", "device", "privacy", "alert"].includes(type)) return { status: 400, body: { error: "unknown action" } };
    if (type === "device") {            // allowed before consent: it says what the device is, nothing about the room
      if (!["phone", "tablet", "laptop"].includes(body.kind)) return { status: 400, body: { error: "bad device" } };
      const level = body.level >= 0 && body.level <= 1 ? Math.round(body.level * 100) / 100 : null;
      const ms = body.ms > 0 && body.ms < 600000 ? Math.round(body.ms) : null;
      actions.device(s, now, { kind: body.kind, charging: typeof body.charging === "boolean" ? body.charging : null, level, ms });
      changed = true;
      return done(200);
    }
    if (type !== "consent" && !s.consent) return { status: 409, body: { error: "Kettle needs a yes first." } };
    if (type === "pause") {
      const minutes = body.minutes == null ? null : Math.max(1, Math.min(24 * 60, +body.minutes || 15));
      actions.pause(s, now, { minutes, reason: body.reason === "guest" ? "guest" : "parent", off: tzOffset(s.tz, now) });
    } else if (type === "privacy") {
      const hide = Array.isArray(body.hide) ? body.hide.filter((h) => HIDEABLE.includes(h)) : [];
      const kindsOff = Array.isArray(body.kindsOff) ? body.kindsOff.filter((k) => Object.hasOwn(KIND_NAMES, k)) : [];
      actions.privacy(s, now, { hide, kindsOff });
    } else if (type === "alert") {     // handover v3.5, 3.2: an Urgent safety alert from the kitchen device (no audio, no scores)
      const checkin = body.checkin || "none";
      if (!SAFETY_TYPES.includes(body.kind) || !CHECKIN_STATES.includes(checkin)) return { status: 400, body: { error: "bad alert" } };
      const at = Math.min(now, Math.max(now - 3600, +body.at || now));
      const id = `a${Math.round(at)}`;
      const old = (s.alerts || []).find((x) => x.id === id);
      if (old) {                        // the same alert, answered (or not): update it in place, never a second banner
        if (old.checkin === checkin) return done(200);                  // a retry: nothing new, nobody is told twice
        if (old.checkin === "help" || (old.checkin === "no_answer" && checkin === "asking")) return done(200);   // never step back
        old.checkin = checkin; old.answered = now;
      } else s.alerts = [...(s.alerts || []), { id, kind: body.kind, at, checkin, seen: null }].slice(-MAX_ALERTS);
      changed = true;
      const a = s.alerts.find((x) => x.id === id);
      const r = await done(200);
      return { ...r, notify: { alert: { ...a }, tz: s.tz, names: s.names } };
    } else if (type === "mic") {
      if (!["ok", "blocked", "none"].includes(body.state)) return { status: 400, body: { error: "bad mic state" } };
      actions.mic(s, now, { state: body.state });
    } else actions[type](s, now);
    changed = true;
    return done(200);
  }
  if (method === "POST" && route === "rules") {
    if (role !== "family") return { status: 403, body: { error: "Checks are set from the family view." } };
    try { s.rules = validateRules(body?.rules); } catch (e) { return { status: 400, body: { error: String(e.message || e) } }; }
    changed = true;
    return done(200);
  }
  if (method === "POST" && route === "seen") {
    if (role !== "family") return { status: 403, body: { error: "Alerts are acknowledged from the family view." } };
    const a = (s.alerts || []).find((x) => x.id === body?.id);
    if (!a) return { status: 404, body: { error: "no such alert" } };
    a.seen = now;
    changed = true;
    return done(200);
  }
  // Web Push (docs/PUSH-INTEGRATION.md): the family's phones subscribe here; the server keeps at most 10, deduped by endpoint.
  if (route === "push" && (method === "POST" || method === "DELETE")) {
    if (role !== "family") return { status: 403, body: { error: "Alerts are turned on from the family view." } };
    if (method === "DELETE") {
      s.push = (s.push || []).filter((p) => p.endpoint !== body?.endpoint);
      changed = true;
      return done(200, { subscribed: s.push.length });
    }
    const sub = validSubscription(body?.subscription);
    if (!sub) return { status: 400, body: { error: "That browser's alert subscription isn't one Kettle can use." } };
    s.push = [...(s.push || []).filter((p) => p.endpoint !== sub.endpoint), { ...sub, at: now }].slice(-MAX_PUSH);
    changed = true;
    return done(200, { subscribed: s.push.length });
  }
  if (method === "POST" && route === "pushtest") {          // "Send a test alert": proves the phone really gets notifications
    if (role !== "family") return { status: 403, body: { error: "Test alerts are sent from the family view." } };
    if (!(s.push || []).length) return { status: 409, body: { error: "Turn on alerts on this phone first." } };
    const r = await done(200, { subscribed: s.push.length });
    return { ...r, notify: { test: true, at: now, tz: s.tz, names: s.names } };
  }
  if (method === "POST" && route === "names") {
    s.names = { parent: cleanName(body?.parent, s.names.parent), caregiver: cleanName(body?.caregiver, s.names.caregiver),
      relation: cleanRelation(body?.relation, s.names.relation || "parent"), room: cleanRoom(body?.room, s.names.room || { type: "kitchen", name: "" }) };
    changed = true;
    return done(200);
  }
  if (method === "DELETE" && route === "") {
    await store.wipe();
    return { status: 200, body: { deleted: true } };
  }
  return { status: 404, body: { error: "not found" } };
}
