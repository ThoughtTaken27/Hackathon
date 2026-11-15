// Handover v3.5, 3.3: tell the family's phones. After the household stores or updates an urgent alert (household.js returns
// `notify`), the host (Cloudflare Durable Object or dev server) calls notify() in the background, so the kitchen's request returns
// at once. Each subscribed phone gets one encrypted Web Push (push.js). The payload holds the kind of sound, the time and the home
// id: never the family key, never audio, never scores. Subscriptions the push service calls gone (404/410) are deleted.
import { sendPush } from "./push.js";
import { clock, tzOffset } from "../public/js/core.js";
import { TEXT } from "../public/js/safety.js";

function where(names) {
  const r = (names && names.room) || {};
  if (r.type === "other" && r.name) return `the ${r.name} screen`;
  if (!r.type || r.type === "home") return "the Kettle screen";
  return `the ${{ living: "living room" }[r.type] || r.type} screen`;
}

/** The notification for one alert (or a test). tier "urgent" = high urgency and stays on screen; "update" and "test" don't. */
export function payloadFor(home, n) {
  const off = tzOffset(n.tz || "UTC", n.at || (n.alert && n.alert.at) || 0);
  const url = `/family?h=${home}`;
  if (n.test) return { title: "Kettle: test alert", body: "Alerts work on this phone. A real one looks like this and stays until you open it.",
    tier: "test", tag: `kettle-test-${home}`, url, alertId: "", home };
  const a = n.alert, when = clock(a.at, off), what = TEXT[a.kind] || "something urgent", who = (n.names && n.names.parent) || "They";
  const base = { tag: `kettle-${a.id}`, url, alertId: a.id, home };
  if (a.checkin === "ok") return { ...base, tier: "update", title: "Kettle: they said they're OK",
    body: `Heard ${what} at ${when}. ${who} pressed "I'm OK"${a.answered ? ` at ${clock(a.answered, off)}` : ""}.` };
  const line = a.kind === "help" ? `${who} pressed "I need help" at ${when}.`
    : a.checkin === "asking" ? `Heard ${what} at ${when}. Asking "Are you OK?" on ${where(n.names)} now.`
    : a.checkin === "no_answer" ? `Heard ${what} at ${when}. Nobody answered "Are you OK?".`
    : a.checkin === "help" ? `Heard ${what} at ${when}. ${who} pressed "I need help".`
    : `Heard ${what} at ${when}. Open to see.`;
  return { ...base, tier: "urgent", title: "Kettle: urgent", body: line };
}

/** Send one notice to every subscribed phone; drop dead subscriptions. Returns sendPush results (for tests). Never throws. */
export async function notify(store, home, n, keys, fetchImpl = fetch) {
  try {
    const s = await store.getState();
    const subs = (s && s.push) || [];
    if (!subs.length || !keys) return [];
    const p = payloadFor(home, n);
    const urgent = p.tier === "urgent";
    const res = await Promise.all(subs.map((sub) => sendPush(sub, p, keys, { urgency: urgent ? "high" : "normal", ttl: urgent ? 6 * 3600 : 3600, fetchImpl })));
    const gone = new Set(subs.filter((_, i) => res[i].gone).map((x) => x.endpoint));
    if (gone.size) {
      const s2 = await store.getState();
      if (s2) { s2.push = (s2.push || []).filter((x) => !gone.has(x.endpoint)); await store.putState(s2); }
    }
    return res;
  } catch {
    return [];
  }
}
