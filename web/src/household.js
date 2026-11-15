// One household's sync logic, independent of where it runs (Cloudflare Durable Object or the local dev server).
// It stores only what the Python app stores: the parent's choices (consent, pause, off), Meera's checks, and window
// labels with times and scores. No audio ever reaches it; the kitchen page labels sound on the parent's own device.
import { CLASSES, MEAL, actions, newState, tick, tzOffset, validateRules } from "../public/js/core.js";
import { SHOWN_SOUNDS } from "../public/js/sounds.js";

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

/** A new household's stored record, and its two keys (returned once, stored only as hashes). */
export async function create({ parent, caregiver, tz } = {}, now) {
  const kitchenKey = randomId(24), familyKey = randomId(24);
  const state = { ...newState(), names: { parent: cleanName(parent, "Dad"), caregiver: cleanName(caregiver, "Meera") },
    tz: validTz(tz) ? tz : "UTC", created: now, hop: 10,
    keys: { kitchen: await sha256(kitchenKey), family: await sha256(familyKey) } };
  return { state, kitchenKey, familyKey };
}

/** The state as either screen may see it (no key hashes). */
export function publicState(s) {
  const { keys, ...rest } = s;
  return rest;
}

function cleanEvent(e, now) {
  if (!e || typeof e !== "object") return null;
  const start = +e.start, end = +e.end;
  if (!(end > start) || end - start > 600 || end > now + 120 || end < now - 86400) return null;
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
    out.w = { k: Math.round(w.k * 1000) / 1000, family: w.family, v: Math.round(w.v * 1000) / 1000 };
  return out;
}

/**
 * Handle one request for this household.
 * store: { getState(), putState(s), addEvents(evs), eventsSince(t), prune(before), wipe() }
 * Returns { status, body }.
 */
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
    if (!["consent", "off", "start", "pause", "resume", "keep_on", "mic"].includes(type)) return { status: 400, body: { error: "unknown action" } };
    if (type !== "consent" && !s.consent) return { status: 409, body: { error: "Kettle needs a yes first." } };
    if (type === "pause") {
      const minutes = body.minutes == null ? null : Math.max(1, Math.min(24 * 60, +body.minutes || 15));
      actions.pause(s, now, { minutes, reason: "parent", off: tzOffset(s.tz, now) });
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
  if (method === "POST" && route === "names") {
    s.names = { parent: cleanName(body?.parent, s.names.parent), caregiver: cleanName(body?.caregiver, s.names.caregiver) };
    changed = true;
    return done(200);
  }
  if (method === "DELETE" && route === "") {
    await store.wipe();
    return { status: 200, body: { deleted: true } };
  }
  return { status: 404, body: { error: "not found" } };
}
