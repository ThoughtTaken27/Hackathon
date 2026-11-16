// The room screen (Kettle web; route /kitchen). Pairs with a code, asks the person first, labels sound on this device, sends only labels.
import { today as computeToday, canListen, rawLabel, clock, tzOffset, DISPLAY, MEAL, KIND_NAMES, KINDS_SHOWN, HIDEABLE } from "./core.js";
import { ROOMS, who } from "./people.js";
import { $, el, setText, api, now, linkFromHash, saveHome, forgetHome, dayBar, toast, codeInput } from "./ui.js";
import { loadModel, startMic, HOP_S, modelHead } from "./listen.js";
import { buildEnrolment } from "./sense.js";
import { newEngine, step as safetyStep, timeouts as safetyTimeouts, answer as safetyAnswer, help as safetyHelp, TEXT as SAFETY_TEXT } from "./safety.js";

// What this device is, in the words the parent and the family will read. Kettle runs in a browser tab, so the "kitchen device"
// can be a spare phone or tablet on a charger as well as a laptop.
const UA = navigator.userAgent || "";
const DEVICE = /iPad|Tablet|Android(?!.*Mobile)/.test(UA) || (navigator.maxTouchPoints > 1 && /Macintosh/.test(UA)) ? "tablet" : /Android|iPhone|iPod|Mobile/.test(UA) ? "phone" : "laptop";
const link = linkFromHash("kitchen");
const ui = { step: "intro", pauseMenu: false, mic: "idle", model: 0, down: false, failures: 0, showChip: true, resumedAt: 0, resumedText: "", setup: null, check: null };
// First-time setup on this device, after the parent says yes: 2) where to put it, 3) a live sound check. Remembered per home.
const SKEY = link ? `kettle.setup.${link.id}` : null;
let setupFinished = false;              // also in memory, so blocked storage can't loop the parent back into setup
const setupDone = () => { if (setupFinished) return true; try { return localStorage.getItem(SKEY) === "1"; } catch { return true; } };
const finishSetup = () => { setupFinished = true; try { localStorage.setItem(SKEY, "1"); } catch {} ui.setup = null; ui.check = null; draw(); };
// After the sound check, setup's last step offers "Teach Kettle this kitchen" before anything else, so it isn't missed.
const toTeachOffer = () => { ui.setup = "teach"; ui.check = null; draw(); };
const SETUP_STEPS = 4;
let srv = null, events = [], queue = [], mic = null, wake = null, t = null, silentRun = 0, flushing = false;
const bar = dayBar($("#bar"), { big: true });
const QKEY = link ? `kettle.queue.${link.id}` : null;
try { queue = QKEY ? JSON.parse(localStorage.getItem(QKEY)) || [] : []; } catch { queue = []; }
const saveQueue = () => { try { localStorage.setItem(QKEY, JSON.stringify(queue.slice(-2000))); } catch {} };

// ---------------------------------------------------------------- teach Kettle this kitchen (plan A3 + E3 microphone check)
// The setup windows' embeddings stay in this browser's storage; nothing about them is sent.
const EKEY = link ? `kettle.enrol.${link.id}` : null;
let enrolment = null;
try { enrolment = EKEY ? JSON.parse(localStorage.getItem(EKEY)) : null; } catch { enrolment = null; }
const TEACH = [
  { c: "absence", head: "Step 1 of 3: keep the kitchen quiet", body: "Stay still for about 40 seconds. Kettle is learning what quiet sounds like here.", s: 40 },
  { c: "dishwashing", head: "Step 2 of 3: wash up or run the tap", body: "Rinse a few dishes for about a minute, the way you usually do.", s: 60 },
  { c: "cooking", head: "Step 3 of 3: cook, or pretend to", body: "Stir a pan, chop something or fry for about a minute. Real kitchen sounds work best.", s: 60 },
];
// Teaching steps for the room the device is in (people.js ROOMS[type].teach), mapped to the head's classes.
// The kitchen keeps its measured three steps above; other rooms are a prototype (not measured), and the screens say so.
const TEACH_CLASS = { quiet: "absence", wash: "dishwashing", cook: "cooking", tv: "watching_tv", move: "other", walk: "other", drawer: "other", door: "other", tap: "dishwashing" };
function roomType() { const r = srv && srv.names && srv.names.room; return r && ROOMS[r.type] ? r.type : "kitchen"; }
const isKitchen = () => roomType() === "kitchen";
function roomWord() { return who(srv ? srv.names : null, "person").room; }
function roomSounds() { return isKitchen() ? "kitchen sounds" : `the sounds of the ${roomWord()}`; }
function teachSteps() {
  if (isKitchen()) return TEACH;
  const steps = ROOMS[roomType()].teach;
  return steps.map((x, i) => ({ c: TEACH_CLASS[x.c] || "other", label: x.head, s: x.c === "quiet" ? 40 : 60,
    head: `Step ${i + 1} of ${steps.length}: ${x.head.charAt(0).toLowerCase()}${x.head.slice(1)}`,
    body: x.c === "quiet" ? "Stay still for about 40 seconds. Kettle is learning what quiet sounds like here." : `${x.body} Keep going for about a minute.` }));
}
const teach = { step: -1, ready: false, t0: 0, samples: [], quietDbs: [], activeDbs: [], stepDbs: [], lastSent: 0, failed: false, level: 0 };
const WARM_S = 10;                                // the 10-s window must be filled with this step's sound first
function startTeach() {
  if (!mic) { toast("Kettle is still starting the microphone. Try again in a few seconds."); return; }
  if (ui.setup === "teach") { setupFinished = true; try { localStorage.setItem(SKEY, "1"); } catch {} ui.setup = null; }
  Object.assign(teach, { step: 0, ready: false, t0: now(), samples: [], quietDbs: [], activeDbs: [], stepDbs: [], failed: false });
  mic.setHop(2); draw();
}
function teachTick() {
  if (teach.step < 0 || !teach.ready) return;          // each step waits until the parent says they're ready
  const st = teachSteps()[teach.step];
  if (now() - teach.t0 < st.s + WARM_S) { draw(); return; }
  if (st.c !== "absence") {                       // microphone check: the activity must be clearly louder than quiet
    const q = median(teach.quietDbs), a = median(teach.stepDbs);
    if (!(a >= q + 6)) { teach.failed = true; draw(); return; }
    teach.activeDbs.push(...teach.stepDbs);
  }
  teach.stepDbs = [];
  if (teach.step + 1 < teachSteps().length) { teach.step++; teach.ready = false; draw(); return; }
  enrolment = buildEnrolment(modelHead(), teach.samples, teach.quietDbs, teach.activeDbs);
  try { localStorage.setItem(EKEY, JSON.stringify(enrolment)); } catch {}
  teach.step = -1; mic && mic.setHop(HOP_S);
  ui.taughtAt = Date.now(); draw();
}
function stopTeach() { teach.step = -1; teach.failed = false; mic && mic.setHop(HOP_S); draw(); }
function forgetTeach() { enrolment = null; try { localStorage.removeItem(EKEY); } catch {} ; toast(`Kettle forgot what it learned in this ${roomWord()}.`); draw(); }
function median(xs) { const v = xs.filter(Number.isFinite).sort((a, b) => a - b); return v.length ? v[Math.floor(v.length / 2)] : -Infinity; }

// ---------------------------------------------------------------- larger text and dim screen (plan F5, E9)
try { if (localStorage.getItem("kettle.bigText") === "1") document.documentElement.classList.add("big-text"); } catch {}
function toggleText() {
  const on = document.documentElement.classList.toggle("big-text");
  try { localStorage.setItem("kettle.bigText", on ? "1" : "0"); } catch {}
  draw();
}
function dimScreen() {
  const cover = el("button", { class: "dim-cover", type: "button", text: "Kettle is still listening. Touch the screen to wake it.", onclick: () => cover.remove() });
  document.body.append(cover);
}


function button(text, onclick, cls = "") { return el("button", { class: `btn kbtn ${cls}`, type: "button", text, onclick }); }
function speak(lines) { if (!("speechSynthesis" in window)) return; speechSynthesis.cancel(); for (const l of lines) speechSynthesis.speak(new SpeechSynthesisUtterance(l)); }

// ---------------------------------------------------------------- not paired yet: type the code
if (!link) {
  $("#status").dataset.state = "never";
  $("#head").textContent = `Connect this ${DEVICE} to your family`;
  const err = el("p", { class: "err", role: "alert" });
  const go = async (code) => {
    err.textContent = "";
    try {
      const r = await api("/api/pair", { method: "POST", body: { code } });
      saveHome(r.id, { [r.role + "Key"]: r.key });
      location.href = r.role === "kitchen" ? "/kitchen" : "/family";
    } catch (e) { err.textContent = e.message; ci.error(); ci.focus(); }
  };
  const ci = codeInput({ onComplete: go });
  ci.input.addEventListener("input", () => { err.textContent = ""; });
  $("#body").append(el("p", { class: "k-body", text: "Type the six-letter code from your family member's phone." }), el("div", { style: "margin-top:24px" }, ci.node, err));
  $("#controls").append(button("Connect", () => (ci.value().length === 6 ? ci.submit() : ((err.textContent = "Type all six letters and numbers."), ci.error())), "primary"),
    el("a", { class: "btn kbtn quiet-k", href: "/start", text: "Set up Kettle from scratch" }));
  ci.focus();
} else boot();

// ---------------------------------------------------------------- paired
async function boot() {
  await poll();
  watchBattery();
  let sec = 0;
  everySecond(() => {
    sec++;
    if (sec % 5 === 0) poll();
    if (sec % 4 === 0) flush();
    teachTick();
    if (mic) handleSafety(safetyTimeouts(safety, now()));
    if (alertQ.length && sec % 2 === 0) flushAlerts();
    watchdog();
    if (srv && !document.hidden) draw();
  });
  addEventListener("online", flush);
  // Coming back to this tab: say that Kettle kept listening while it was out of sight.
  let hiddenAt = 0, heardAt = 0;
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) { hiddenAt = Date.now(); heardAt = events.length; return; }
    if (mic) lockScreen();
    if (srv) draw();
    const n = events.length - heardAt;
    if (mic && hiddenAt && Date.now() - hiddenAt > 20000) toast(`Kettle kept listening while this was out of sight: ${n} moment${n === 1 ? "" : "s"} noted.`);
    hiddenAt = 0;
  });
  addEventListener("resize", () => draw());
  // Closing this page stops Kettle. Ask first, so it isn't closed by accident while it listens.
  addEventListener("beforeunload", (e) => { if (mic && !ui.elsewhere) { e.preventDefault(); e.returnValue = ""; } });
}

// ---------------------------------------------------------------- keep listening while the parent uses the laptop for other things
/** Run fn once a second from a worker clock (not slowed down in a background tab); a plain timer if workers are unavailable. */
function everySecond(fn) {
  try { const w = new Worker("/js/tick.js?v=w5"); w.onmessage = fn; w.onerror = () => { w.terminate(); setInterval(fn, 1000); }; }
  catch { setInterval(fn, 1000); }
}
/** If the microphone stopped delivering sound (the browser suspended it, a device was unplugged), start it again. */
let lastWindowAt = 0;
function watchdog() {
  if (!mic || ui.mic !== "on" || !lastWindowAt) return;
  if (Date.now() - lastWindowAt > (HOP_S * 3 + 15) * 1000) { lastWindowAt = 0; stopListening(); ui.mic = "idle"; sync(); }
}
// Only one kitchen screen listens at a time: a second tab or the small window takes over, the other one stands by.
const channel = link && "BroadcastChannel" in window ? new BroadcastChannel(`kettle.kitchen.${link.id}`) : null;
const TAB = Math.random().toString(36).slice(2);
if (channel) channel.onmessage = ({ data }) => {
  if (data && data.type === "listening" && data.tab !== TAB && mic) { stopListening(); ui.elsewhere = true; draw(); }
};
function claim() { ui.elsewhere = false; channel && channel.postMessage({ type: "listening", tab: TAB }); }
/** A small window of its own: it can sit in a corner or be minimised while the parent uses the laptop for other things. */
function popOut() {
  const w = window.open("/kitchen", "kettle-kitchen", "popup,width=480,height=760");
  if (!w) { toast("The browser blocked the new window. Allow pop-ups for this site, or keep this tab open."); return; }
  stopListening(); ui.elsewhere = true; draw();
}
function popOutButton() { return window.opener || ui.elsewhere ? null : button("Keep it in a small window", popOut, "quiet-k"); }
/** The browser tab says what Kettle is doing, so it's visible from any other tab. */
function tabTitle(s) {
  const t = ui.elsewhere ? "Kettle (in another window)" : s.state === "paused" ? "Paused · Kettle"
    : mic && ui.mic === "on" && !s.state.startsWith("error") ? "● Listening · Kettle"
    : s.state === "off" ? "Off · Kettle" : s.state.startsWith("error") ? "Needs attention · Kettle" : `Kettle · ${roomWord()}`;
  if (document.title !== t) document.title = t;
}

async function poll() {
  try {
    const since = events.length ? events[events.length - 1].end - 3600 : 0;
    const r = await api(`/api/h/${link.id}/state?since=${since}`, { key: link.key, retries: 1 });
    merge(r.events);
    srv = r.state; ui.failures = 0; ui.down = false;
    saveHome(link.id, { parent: srv.names.parent, caregiver: srv.names.caregiver });
    sync();
  } catch (e) {
    if (e.status === 403 || e.status === 404) { ui.gone = e.message; draw(); return; }
    ui.failures++; if (ui.failures >= 3 && srv) { ui.down = true; draw(); }
  }
}
function merge(list) {
  const m = new Map(events.map((e) => [e.end, e]));
  for (const e of list || []) m.set(e.end, e);
  events = [...m.values()].sort((a, b) => a.end - b.end).filter((e) => e.end > now() - 36 * 3600);
}
// ---------------------------------------------------------------- safety (handover v3.5, 3.2): red at once, then ask
// The engine (safety.js) runs on this device; only an Urgent alert's kind, time and check-in state go to the family. A crash then a
// cry, screaming, shouting or repeated crying tells the family AT ONCE ("asking") and asks "Are you OK?" here; the answer (or no
// answer) updates that same alert (same time = same alert on the server). Smoke, CO and gunshots skip the question.
// Concern-tier notes (C6 stove, C7 beeping, C9 water) stay off on purpose ({ concern: false } below): they have never been checked
// end to end, so they would be unmeasured alerts (How sure says so).
const safety = newEngine();
if (window.kettleDebug) window.kettleSafety = safety;     // browser tests set kettleDebug to read the engine's recent windows
const WIRED = ["smoke", "co", "gunshot", "fall", "fall_still", "scream", "shout", "distress", "help"];
const ALERT_Q = "kettle.alertQueue";
let alertQ = (() => { try { return JSON.parse(localStorage.getItem(ALERT_Q) || "[]"); } catch { return []; } })(), alertBusy = false;
const saveAlertQ = () => { try { localStorage.setItem(ALERT_Q, JSON.stringify(alertQ)); } catch {} };
/** Alerts are queued and retried until the server has them: a dropped connection must never lose one. */
function sendAlert(kind, at, checkin) { alertQ.push({ kind, at, checkin }); saveAlertQ(); flushAlerts(); }
async function flushAlerts() {
  if (alertBusy || !alertQ.length || !link) return;
  alertBusy = true;
  try {
    while (alertQ.length) {
      const a = alertQ[0];
      if (a.at < now() - 3000) { alertQ.shift(); saveAlertQ(); continue; }          // too old to be news (the server keeps an hour)
      try { const r = await api(`/api/h/${link.id}/action`, { method: "POST", key: link.key, body: { type: "alert", ...a }, retries: 2 }); srv = r.state; ui.alertFailed = false; }
      catch (e) { if (!e.status || e.status >= 500 || e.status === 429) { ui.alertFailed = true; break; } }   // offline: keep it, try again next second
      alertQ.shift(); saveAlertQ();
    }
  } finally { alertBusy = false; }
}
const fam = () => who(srv ? srv.names : null, "person");
const clockNow = (t) => clock(t, tzOffset((srv && srv.tz) || "UTC", t));
function handleSafety(acts) {
  for (const a of acts || []) {
    if (a.do === "checkin") {
      ui.checkin = { type: a.type, at: a.at, deadline: a.deadline, text: SAFETY_TEXT[a.type] };
      if (WIRED.includes(a.type)) sendAlert(a.type, a.at, "asking");          // the family is told now, not after the countdown
      speak(["Are you OK?", "Kettle heard " + SAFETY_TEXT[a.type] + ".", `${fam().Caregiver} has been told.`, "Press I'm OK, or I need help."]);
      draw();
    } else if (a.do === "alert" && (a.tier === "urgent" || a.checkin === "ok") && WIRED.includes(a.after || a.type)) {
      // an answer or a timeout updates the alert sent when the check-in began; smoke, CO, gunshot and the help button are new alerts
      const kind = a.after || a.type, at = a.checkin && a.checkin !== "help" ? (a.since ?? a.at) : a.after ? a.since : a.at;
      sendAlert(kind, at, a.checkin || "none");
      ui.checkin = null;
      if (a.checkin !== "ok") { ui.alerted = { at: Date.now(), kind, text: SAFETY_TEXT[kind], checkin: a.checkin || "none" }; speak([`Kettle heard ${SAFETY_TEXT[kind]}.`, `Kettle told ${fam().caregiver}.`]); }
      draw();
    } else if (a.do === "alert" && ui.checkin) { ui.checkin = null; draw(); }
  }
}
function reply(r) {
  const acts = safetyAnswer(safety, now(), r); ui.checkin = null; handleSafety(acts);
  if (r === "ok") toast(`Thank you. ${fam().Caregiver} can see you're OK.`);
  draw();
}

async function act(type, extra = {}) {
  ui.pauseMenu = false;
  try { const r = await api(`/api/h/${link.id}/action`, { method: "POST", key: link.key, body: { type, ...extra } }); srv = r.state; sync(); }
  catch (e) { toast(e.message || "Couldn't reach Kettle. Trying again."); }
}
async function flush() {
  if (flushing || !queue.length || !srv || !canListen(srv, now())) return;      // one upload at a time: a window is sent once
  flushing = true;
  const batch = queue.slice(0, 60);
  try {
    await api(`/api/h/${link.id}/events`, { method: "POST", key: link.key, body: { events: batch, tz: Intl.DateTimeFormat().resolvedOptions().timeZone }, retries: 1 });
    queue = queue.slice(batch.length); saveQueue(); ui.down = false;
  } catch (e) { if (e.status === 409) { queue = []; saveQueue(); } }
  finally { flushing = false; }
}

// ---------------------------------------------------------------- microphone + model
async function startListening() {
  if (mic || ui.mic === "asking" || ui.mic === "loading") return;
  ui.mic = "loading"; draw();
  try {
    await loadModel((p) => { ui.model = p; draw(); });
  } catch (e) { ui.mic = "model_failed"; draw(); return; }
  ui.mic = "asking"; draw();
  try {
    mic = await startMic({
      clockNow: now,
      onLevel: (v) => { meter(v); teach.level = v; },
      context: () => ({ enrolment, kindsOff: (srv && srv.kinds_off) || [], teaching: teach.step >= 0 }),
      onWindow: (w) => {
        lastWindowAt = Date.now();
        if (dev.ms == null) { dev.ms = w.ms; reportDevice(); }
        // A muted or switched-off microphone delivers exact silence. That is "not listening", never "Quiet": tell the family.
        // Exact silence is never sent as a sound label (it isn't "Not sure", it's a microphone giving nothing).
        silentRun = w.peak < 1e-4 ? silentRun + 1 : 0;
        if (silentRun === 3) act("mic", { state: "blocked" });
        if (silentRun > 0) return;
        if (silentRun === 0 && srv && srv.mic === "blocked") act("mic", { state: "ok" });
        if (teach.step >= 0) {                           // teaching: keep this kitchen's windows on the device
          const st = teachSteps()[teach.step];
          if (teach.ready && w.end - teach.t0 >= WARM_S && w.end - teach.t0 <= st.s + WARM_S) {
            if (w.emb) teach.samples.push({ c: st.c, emb: Float32Array.from(w.emb) });
            (st.c === "absence" ? teach.quietDbs : teach.stepDbs).push(w.db);
          }
          if (w.end - teach.lastSent < HOP_S - 0.5) return;    // still one window per 10 s to the family while teaching
          teach.lastSent = w.end;
        }
        if (w.safety && teach.step < 0) handleSafety(safetyStep(safety, { t: w.end, ...w.safety, db: w.db, floor: enrolment ? enrolment.floor : null,
          kinds: w.kinds, kindsDevice: w.kindsDevice, label: w.label }, { urgent: true, concern: false }));
        const ev = shareable(w);
        events.push(ev); queue.push(ev); saveQueue(); flush();
        if (ui.setup === "check" && !ui.check) ui.check = { label: rawLabel(ev, 0.66) };
        if (srv) srv.last_window_t = ev.end;
        draw(true);
      },
    });
    ui.mic = "on"; lockScreen(); claim(); lastWindowAt = Date.now();
    act("mic", { state: "ok" });
  } catch (e) {
    ui.mic = e && e.name === "NotFoundError" ? "none" : "denied";
    act("mic", { state: ui.mic === "none" ? "none" : "blocked" });
  }
  draw();
}
/** What may leave this device for one window: labels the parent chose to keep private become just "Private" (plan D2). */
function shareable(w) {
  const hide = (srv && srv.hide) || [];
  const top = Object.keys(w.probs).sort((a, b) => w.probs[b] - w.probs[a]);
  const voices = top.slice(0, 2).every((c) => HIDEABLE.includes(c)) && top.slice(0, 2).some((c) => hide.includes(c));
  if (hide.includes(w.label) || voices) return { start: w.start, end: w.end, label: "private", conf: 0, probs: Object.fromEntries(Object.keys(w.probs).map((c) => [c, 0])), novel: false, private: true, sounds: [], kinds: [] };
  return { start: w.start, end: w.end, label: w.label, conf: w.conf, probs: w.probs, novel: w.novel, w: w.w, sounds: w.sounds, kinds: w.kinds, taught: w.taught };
}
function stopListening() { if (mic) { mic.stop(); mic = null; } if (wake) { wake.release().catch(() => {}); wake = null; } if (ui.mic === "on") ui.mic = "idle"; }
// ---------------------------------------------------------------- device report: kind, plugged in or not, and how fast it labels
const dev = { kind: DEVICE, charging: null, level: null, ms: null, sent: "" };
function reportDevice() {
  const key = `${dev.charging}|${dev.level == null ? "" : Math.round(dev.level * 20)}|${dev.ms == null ? "" : 1}`;
  if (key === dev.sent || !link) return;
  dev.sent = key;
  api(`/api/h/${link.id}/action`, { method: "POST", key: link.key, body: { type: "device", kind: dev.kind, charging: dev.charging, level: dev.level, ms: dev.ms } })
    .then((r) => { srv = r.state; draw(); }).catch(() => { dev.sent = ""; });
}
async function watchBattery() {
  try {
    if (!navigator.getBattery) return reportDevice();          // Safari and Firefox don't share battery state; Kettle then says nothing about it
    const b = await navigator.getBattery();
    const read = () => { dev.charging = b.charging; dev.level = b.level; reportDevice(); draw(); };
    b.addEventListener("chargingchange", read); b.addEventListener("levelchange", read); read();
  } catch { reportDevice(); }
}
/** Plain lines about this device, shown under the listening headline: speed, power, and the screen staying on. */
function deviceLines() {
  const out = [];
  if (dev.ms != null) out.push(dev.ms > 8000 ? `This ${DEVICE} is slow for Kettle: it needs ${(dev.ms / 1000).toFixed(1)} s to label 10 seconds of sound, so some moments are skipped.`
    : `This ${DEVICE} labels 10 seconds of sound in ${(dev.ms / 1000).toFixed(1)} s.`);
  if (dev.charging === false) out.push(`Plug this ${DEVICE} in. Kettle listens all day and needs the power${dev.level != null ? ` (battery ${Math.round(dev.level * 100)}%)` : ""}.`);
  if (DEVICE === "laptop") out.push("You can use other tabs and apps. Kettle keeps listening while this window stays open.");
  if (DEVICE !== "laptop") out.push(`Leave this page open with the screen on. Kettle keeps it awake while it listens${"wakeLock" in navigator ? "" : " if this " + DEVICE + "'s auto-lock is set to Never"}.`);
  return out;
}
async function lockScreen() { try { if ("wakeLock" in navigator && !wake) { wake = await navigator.wakeLock.request("screen"); wake.addEventListener("release", () => (wake = null)); } } catch {} }
let meterEl = null, lastMeter = 0;
function meter(v) {
  if (!meterEl || performance.now() - lastMeter < 90) return; lastMeter = performance.now();
  const bars = meterEl.children, lvl = Math.min(1, Math.sqrt(v) * 1.6);
  for (let i = 0; i < bars.length; i++) bars[i].style.setProperty("--v", Math.max(0.15, lvl * (0.55 + 0.45 * Math.sin(i * 1.7 + lastMeter / 160))).toFixed(2));
}

// ---------------------------------------------------------------- what to show (same states and words as the Python kitchen screen)
function screen(t) {
  const n = t.names, k = t.kitchen, hb = t.heartbeat;
  const sendLine = ui.alertFailed ? "Kettle can't reach the internet. It keeps trying to tell them." : "";
  if (ui.checkin) {
    const left = Math.max(0, Math.ceil(ui.checkin.deadline - now()));
    return { state: "urgent", head: "Are you OK?", body: [`Kettle heard ${ui.checkin.text} at ${clockNow(ui.checkin.at)}.`,
      `${n.Caregiver} has been told. Press I'm OK to let them know you're fine.`,
      `If nobody answers in ${left} seconds, Kettle tells ${n.caregiver} that nobody answered.`, sendLine].filter(Boolean),
      controls: [button("I'm OK", () => reply("ok"), "primary"), button("I need help", () => reply("help"), "danger")] };
  }
  if (ui.alerted && Date.now() - ui.alerted.at < 120000) return { state: "urgent", head: ui.alerted.kind === "help" ? `${n.Caregiver} has been told you need help.` : `Urgent: Kettle heard ${ui.alerted.text}.`,
    body: [`Heard at ${clockNow(ui.alerted.at / 1000)}. ${n.Caregiver} has been told on their phone.`, "If you need help now, call 911 or a neighbour. Kettle can't call for help itself.", sendLine].filter(Boolean),
    controls: [button("OK", () => { ui.alerted = null; draw(); }, "primary")] };
  if (ui.gone) return { state: "error", head: `This ${DEVICE} isn't connected any more.`, body: [ui.gone, "Ask your family member for a new code."],
    controls: [el("a", { class: "btn kbtn primary", href: "/kitchen", text: "Enter a new code", onclick: () => { forgetHome(link.id); } })] };
  if (ui.down) return { state: "error", head: "Kettle can't reach the internet.", body: ["It keeps listening and will send what it heard when the connection is back."],
    controls: [button("Try again", () => poll(), "primary")], bar: true, chip: true };
  if (!k.consent) {
    if (ui.step === "teachback") return { state: "never", stepK: 1, head: `Is it OK for ${n.caregiver} to see this?`, body: [`${n.Caregiver} will see the kinds of sound and when they happened. Nothing else.`],
      controls: [button(`Yes, ${n.caregiver} can see this`, () => act("consent"), "primary"), button("No, not now", () => { ui.step = "declined"; draw(); }),
        button("Read this to me", () => speak([`Is it OK for ${n.caregiver} to see this?`, `${n.Caregiver} will see the kinds of sound and when they happened. Nothing else.`]), "quiet-k")] };
    if (ui.step === "declined") return { state: "off", head: "Kettle is off.", body: [`This ${DEVICE} isn't listening. Press Start when you want it on.`],
      controls: [button("Start", () => { ui.step = "intro"; draw(); }, "primary")] };
    const examples = isKitchen() ? "'dishes', 'TV' or 'people talking'" : roomType() === "living" ? "'TV', 'people talking' or footsteps" : "footsteps, a door, 'TV' or 'people talking'";
    const lines = [`The program is called Kettle. It uses this ${DEVICE}'s microphone and only notes the kind of sound, like ${examples}.`,
      ...(isKitchen() ? [] : [`Kettle was measured on kitchen sounds. In a ${roomWord()} it is a prototype and may say "Not sure" more often.`]),
      `It keeps no recordings and no words. The sound never leaves this ${DEVICE}.`, `${n.Caregiver} sees a day timeline like this one. You can pause it or turn it off any time.`,
      `${n.Caregiver} will also see when people were talking (that shows a visit, never what was said) and when the TV or radio was on. You can hide any of these.`,
      "Kettle never names voices, coughs, crying or bathroom sounds. If a guest or carer comes, you can pause it for them.",
      `If it hears a smoke alarm, screaming, or a crash and then a cry, it asks "Are you OK?" here and tells ${n.caregiver} if nobody answers. It can't call for help itself.`];
    return { state: "never", stepK: setupDone() ? 0 : 1, head: `This ${DEVICE} listens for ${roomSounds()}.`, body: lines, example: true,
      controls: [button("Next", () => { ui.step = "teachback"; draw(); }, "primary"), button("Not now", () => { ui.step = "declined"; draw(); }),
        button("Read this to me", () => speak([`This ${DEVICE} listens for ${roomSounds()}.`, ...lines]), "quiet-k")] };
  }
  if (ui.elsewhere && !k.paused && !k.off) return { state: "starting", head: "Kettle is listening in another window.",
    body: ["You can close this tab. Keep the other Kettle window open; it can be small or minimised."],
    controls: [button("Listen in this tab instead", () => { ui.elsewhere = false; ui.mic = "idle"; sync(); }, "primary")] };
  if (ui.setup === "place" && !k.paused) return placeScreen(n);
  if (k.off) return { state: "off", head: "Kettle is off.", body: [`This ${DEVICE} isn't listening. Press Start when you want it on.`], controls: [button("Start", () => act("start"), "primary")] };
  if (k.paused) {
    const weekly = k.pause_reason === "weekly";
    const until = weekly ? "Kettle waits for your answer before listening again." : hb.until_text ? `Starts listening again at ${hb.until_text}${hb.text.includes("tomorrow") ? " tomorrow" : ""}.` : "";
    return { state: "paused", head: weekly ? "Kettle has paused. Keep it on?" : "Paused. Kettle isn't listening.", body: [`${n.Caregiver} sees: Paused by you at ${hb.since_text}.`, until], bar: true,
      controls: weekly ? [button("Keep it on", () => act("keep_on"), "primary"), button("Turn it off", () => act("off"))]
        : [button("Resume listening", () => act("resume"), "primary pause"), button("Turn it off", () => act("off"))] };
  }
  if (k.weekly_due) return { state: hb.state, head: "Kettle has been on for a week. Keep it on?", body: [`${n.Caregiver} sees the kinds of sounds, not recordings or words.`, "If nobody answers, Kettle pauses tomorrow until you choose."],
    controls: [button("Keep it on", () => act("keep_on"), "primary"), button("Turn it off", () => act("off"))] };
  if (ui.mic === "loading") return { state: "starting", head: "Getting Kettle ready…", body: [`Kettle's sound model is loading onto this ${DEVICE}. This happens once.`], progress: true, controls: [] };
  if (ui.mic === "model_failed") return { state: "error", head: "Kettle couldn't load.", body: ["Check the internet connection, then try again."], controls: [button("Try again", () => { ui.mic = "idle"; sync(); }, "primary")] };
  if (ui.mic === "asking" || ui.mic === "idle") return { state: "starting", head: "A box will pop up about the microphone.", body: [`Press Allow. Only this ${DEVICE} uses it.`],
    controls: [el("button", { class: "btn quiet", type: "button", text: "No box appeared? Try again", style: "font-size:var(--fs-lead)", onclick: () => { stopListening(); ui.mic = "idle"; sync(); } })] };
  if (ui.mic === "denied" || ui.mic === "none") {
    const none = ui.mic === "none";
    return { state: "error-soft", head: none ? "No microphone found." : `Kettle can't hear the ${roomWord()}.`,
      body: [none ? "Plug one in, or use a phone, tablet or laptop with a built-in microphone." : `The microphone is switched off for Kettle. This isn't something you did wrong. ${n.Caregiver} or a helper can turn it on.`],
      helper: none ? null : ["Steps for a helper", "Chrome: click the icon left of the address, then Microphone, then Allow, then Try again. Safari: Settings for this website, then Microphone, then Allow."],
      controls: [button("Try again", () => { ui.mic = "idle"; sync(); }, "primary")] };
  }
  if (ui.setup === "check" && ui.mic === "on") return checkScreen(n);
  if (ui.setup === "teach" && ui.mic === "on" && teach.step < 0) return teachOfferScreen(n);
  if (teach.step >= 0) {
    const st = teachSteps()[teach.step];
    if (teach.failed) return { state: "error-soft", head: "Kettle could hardly hear that.", body: [isKitchen() ? "Move the laptop closer to the sink and the stove, with nothing covering it, then try this step again." : `Move the ${DEVICE} closer to where things happen in the ${roomWord()}, with nothing covering it, then try this step again.`],
      controls: [button("Try this step again", () => { teach.failed = false; teach.stepDbs = []; teach.t0 = now(); draw(); }, "primary"), button("Stop teaching", stopTeach, "quiet-k")] };
    if (!teach.ready) {
      const prev = teach.step > 0 ? `Step ${teach.step} done. ` : "";
      return { state: "listening", head: `${prev}Ready for step ${teach.step + 1} of ${teachSteps().length}?`, body: [st.head.replace(/^Step \d of \d: /, "Next: "), st.body],
        controls: [button(`I'm ready. Start step ${teach.step + 1}`, () => { teach.ready = true; teach.t0 = now(); teach.stepDbs = []; draw(); }, "primary"),
          button("Stop teaching", stopTeach, "quiet-k")] };
    }
    const left = Math.max(0, Math.ceil(st.s + WARM_S - (now() - teach.t0)));
    return { state: "listening", head: st.head, body: [st.body, `${left} seconds left.`], teachMeter: true,
      controls: [button("Stop teaching", stopTeach, "quiet-k")] };
  }
  const today = new Date(now() * 1000).toLocaleDateString("en-US", { weekday: "long", timeZone: srv.tz });
  const since = k.consent_day === today ? `Listening since ${k.consent_text} today.` : `Listening since ${k.consent_day}.`;
  const base = { bar: true, chip: true, checks: t.rules.map((r) => r.title), tools: true, share: true,
    controls: [button("Pause", () => { ui.pauseMenu = true; draw(); }, "primary pause"), button("Turn it off", () => act("off")), popOutButton(),
      button("I need help", () => handleSafety([safetyHelp(safety, now())]), "danger help-now")].filter(Boolean) };
  if (silentRun >= 3) return { ...base, chip: false, state: "error-soft", head: "Kettle hears nothing at all.",
    body: [`The microphone is sending silence, so ${n.caregiver} sees "Not listening". Check it isn't muted (a mute key, or a switch on a headset).`] };
  if (Date.now() - (ui.taughtAt || 0) < 15000) return { ...base, state: "listening", head: `Thank you. Kettle learned this ${roomWord()}.`,
    body: [`What it learned stays on this ${DEVICE}. It helps Kettle with sounds it wasn't sure about; it never overrules a sound it already knows.`] };
  if (Date.now() - ui.resumedAt < 10000 && ui.resumedText) return { ...base, state: "listening", head: "Kettle is listening again.", body: [ui.resumedText] };
  if (hb.state === "starting") return { ...base, state: "starting", head: "Listening…", body: ["The first sound label appears in about 10 seconds."] };
  return { ...base, state: hb.state === "listening" ? "listening" : "starting", head: `Listening for ${roomSounds()}`,
    teachCta: !enrolment, body: [`${since} ${n.Caregiver} sees the kinds of sounds, not recordings or words.`, ...deviceLines()] };
}

// ---------------------------------------------------------------- first-time setup: placement, then a live sound check
const STRESS = { tvOff: 84, tvSame: 40 };   // results/stress.json, other homes: kitchen clips caught with no TV vs a TV as loud as the cooking
function guideRow(n, title, sub, status = null) {
  return el("li", { "data-ok": status ? status[0] : "" },
    el("span", { class: "g-n", "aria-hidden": "true", text: status ? "" : String(n) }),
    el("div", {}, el("p", { class: "g-t", text: title }), el("p", { class: "g-s", text: sub }),
      status ? el("p", { class: "g-live", text: status[1] }) : null));
}
function placeScreen(n) {
  const power = dev.charging === true ? ["yes", "Plugged in now."] : dev.charging === false ? ["no", `On battery now (${Math.round((dev.level || 0) * 100)}%). Plug it in.`]
    : ["", "This browser doesn't say. Check the cable."];
  const awake = "wakeLock" in navigator ? ["yes", "Kettle keeps the screen on while this page is open."]
    : ["no", `Set Auto-Lock or Screen timeout to Never in this ${DEVICE}'s settings.`];
  const guide = el("ol", { class: "k-guide" },
    isKitchen() ? guideRow(1, "Near the stove and sink", "Within a couple of steps. Kettle hears less from across the room.")
      : guideRow(1, `Where things happen in the ${roomWord()}`, ROOMS[roomType()].placement[0]),
    guideRow(2, "Away from the TV", `In our tests, a TV as loud as the cooking cut what Kettle caught from ${STRESS.tvOff}% to ${STRESS.tvSame}%.`),
    guideRow(3, "Plugged in", "Kettle listens all day.", power),
    guideRow(4, "Screen on, this page open", "Phones and tablets stop the microphone when the screen locks.", awake));
  return { state: "never", stepK: 2, head: `Where should this ${DEVICE} live?`, body: [], guide,
    controls: [button("It's in place. Start listening", () => { ui.setup = "check"; ui.check = null; sync(); }, "primary"),
      button("Skip setup", () => { finishSetup(); sync(); }, "quiet-k")] };
}
function checkScreen(n) {
  const c = ui.check;
  meterEl = el("span", { class: "meter lg", "aria-hidden": "true" }, ...Array.from({ length: 9 }, () => el("i")));
  if (!c && silentRun >= 2) return { state: "error-soft", stepK: 3, head: "Kettle hears nothing at all.",
    body: [`The microphone is sending silence. Check it isn't muted (a mute key, or a switch on a headset), or try another microphone.`],
    controls: [button("Skip the sound check", toTeachOffer, "quiet-k")] };
  if (!c) return { state: "listening", stepK: 3, head: "Quick sound check", body: [isKitchen() ? "Run the tap, or clink two plates together, for about 10 seconds."
      : "Walk about, open a drawer, or talk for about 10 seconds.", "Kettle will say what it heard."],
    guide: el("div", { class: "k-check" }, meterEl, el("p", { class: "g-s", text: "Listening. The answer appears within 10 seconds." })),
    controls: [button("Skip the sound check", toTeachOffer, "quiet-k")] };
  const name = c.label === "not_sure" ? "something it couldn't name" : c.label === "talk_or_tv" ? "talking / TV" : (DISPLAY[c.label] || c.label).toLowerCase();
  const fits = isKitchen() ? MEAL.has(c.label) : !["absence", "not_sure", "private"].includes(c.label);
  if (fits) return { state: "listening", stepK: 3, done: true, head: `Kettle heard ${name}.`,
    body: [`This spot works. ${n.Caregiver} will see moments like this on the timeline, never the sound itself.`],
    controls: [button("Next", toTeachOffer, "primary")] };
  return { state: "starting", stepK: 3, retry: true, head: `Kettle heard ${name}.`,
    body: [isKitchen() ? "That isn't a kitchen sound yet. Move a little closer to the sink, or make the sound a bit louder, then try again."
      : "Kettle couldn't name that yet. Move a little closer, or make the sound a bit louder, then try again."],
    controls: [button("Try again", () => { ui.check = null; draw(); }, "primary"), button("Next anyway", toTeachOffer, "quiet-k")] };
}

function teachOfferScreen(n) {
  const steps = teachSteps(), R = roomWord();
  if (!isKitchen()) return { state: "listening", stepK: 4, head: `Teach Kettle this ${R}`, body: [
    `Every ${R} sounds different. In about ${steps.length + 1} minutes Kettle learns how this one sounds.`,
    `What it learns stays on this ${DEVICE}. ${n.Caregiver} gets a more accurate timeline. Kettle was measured on kitchen sounds; in a ${R} it's a prototype.`],
    guide: el("ol", { class: "k-guide" }, ...steps.map((x, i) => guideRow(i + 1, x.label, x.c === "absence" ? "About 40 seconds of stillness." : "About a minute."))),
    controls: [button(`Start teaching (${steps.length + 1} minutes)`, startTeach, "primary"), button("Do it later", finishSetup, "quiet-k")] };
  return { state: "listening", stepK: 4, head: "Teach Kettle this kitchen", body: [
    `Every kitchen sounds different. In 3 minutes Kettle learns how this one sounds: quiet, washing up, then cooking.`,
    `What it learns stays on this ${DEVICE}. ${n.Caregiver} gets a more accurate timeline.`],
    guide: el("ol", { class: "k-guide" }, guideRow(1, "Quiet", "About 40 seconds of stillness."), guideRow(2, "Washing up", "About a minute of rinsing dishes or running the tap."),
      guideRow(3, "Cooking", "About a minute of stirring, chopping or frying.")),
    controls: [button("Start teaching (3 minutes)", startTeach, "primary"), button("Do it later", finishSetup, "quiet-k")] };
}

let exampleNode = null;
function exampleBar() {
  if (exampleNode) return exampleNode;
  const fake = { day0: 0, now: 11 * 3600, names: t.names, heartbeat: { state: "listening" }, blocks: [
    { start: 6 * 3600, end: 7.6 * 3600, state: "empty", activity: "absence", label: "Quiet", range: "" },
    ...(isKitchen() ? [{ start: 8 * 3600, end: 8.4 * 3600, state: "activity", activity: "cooking", label: "Cooking", range: "", how_sure: "high" },
      { start: 8.45 * 3600, end: 8.75 * 3600, state: "activity", activity: "dishwashing", label: "Washing up", range: "", how_sure: "high" }]
      : [{ start: 8 * 3600, end: 8.6 * 3600, state: "activity", activity: "other", label: "Some activity", range: "", how_sure: "high" }]),
    { start: 9.2 * 3600, end: 10.6 * 3600, state: "activity", activity: "watching_tv", label: "Talking / TV", range: "", how_sure: "high" }] };
  const box = el("div", { class: "example", "aria-label": "Example of the day timeline (not real)" }, el("span", { class: "tag", text: "Example, not real" }), el("div"));
  setTimeout(() => dayBar(box.lastChild).render(fake), 0);
  return (exampleNode = box);
}

function tools() {
  const big = document.documentElement.classList.contains("big-text");
  return el("div", { class: "k-tools" },
    enrolment ? button(`Teach Kettle this ${roomWord()} again`, startTeach, "quiet-k") : null,
    enrolment ? button("Forget what it learned", forgetTeach, "quiet-k") : null,
    button(big ? "Smaller text" : "Larger text", toggleText, "quiet-k"),
    button("Dim the screen", dimScreen, "quiet-k"));
}
/** Plan D2: the parent decides which labels and named sounds the family sees. */
function sharePanel(t) {
  const hide = new Set((srv && srv.hide) || []), off = new Set((srv && srv.kinds_off) || []);
  const save = () => act("privacy", { hide: [...hide], kindsOff: [...off] });
  const box = (label, on, flip) => el("label", {}, el("input", { type: "checkbox", checked: on || null, onchange: (e) => { flip(e.target.checked); save(); } }), el("span", { text: label }));
  const acts = HIDEABLE.map((c) => box(c === "social_activity" ? "Conversation (shows a visit, never words)" : DISPLAY[c], !hide.has(c), (v) => (v ? hide.delete(c) : hide.add(c))));
  const kinds = Object.entries(KIND_NAMES).filter(([id]) => KINDS_SHOWN.has(id)).map(([id, name]) => box(name, !off.has(id), (v) => (v ? off.delete(id) : off.add(id))));
  const open = ui.shareOpen ? { open: "" } : {};
  const d = el("details", { class: "k-share", ...open, ontoggle: (e) => { ui.shareOpen = e.target.open; } }, el("summary", { text: `What ${t.names.caregiver} can see` }),
    el("fieldset", {}, el("legend", { text: "Activities (ticked = shared)" }), ...acts),
    el("fieldset", {}, el("legend", { text: "Everyday sounds Kettle can name (ticked = shared)" }), ...kinds));
  return d;
}

let prevChip = null;
function sync() {
  if (!srv) return;
  const was = sync.paused; sync.paused = !!(srv.paused_until && now() < srv.paused_until);
  t = computeToday(srv, events, now(), { theta: 0.66, tz: srv.tz, hop: HOP_S, names: srv.names, viewer: "person" });
  if (was && !sync.paused) {
    ui.resumedAt = Date.now();
    const last = t.blocks.filter((b) => b.state === "paused").pop();
    ui.resumedText = last ? (last.end - last.start < 60 ? "Paused for under a minute." : `Paused from ${last.range}.`) : "";
  }
  const should = canListen(srv, now());
  if (should && !setupDone() && !ui.setup) ui.setup = "place";
  if (should && ui.mic === "idle" && ui.setup !== "place" && !ui.elsewhere) startListening();
  if (!should && mic) stopListening();
  draw();
}

function draw(fresh = false) {
  if (!srv) return;
  t = computeToday(srv, events, now(), { theta: 0.66, tz: srv.tz, hop: HOP_S, names: srv.names, viewer: "person" });
  const s = screen(t);
  tabTitle(s);
  $("#who-tag").textContent = t.names.place;
  $("#status").dataset.state = s.state;
  $("#status").classList.toggle("done", !!s.done);
  $("#status").classList.toggle("retry", !!s.retry);
  const ks = $("#kstep");
  ks.hidden = !s.stepK || ui.pauseMenu;
  if (s.stepK) { ks.textContent = ""; ks.append(el("span", { class: "dots", "aria-hidden": "true" }, Array.from({ length: SETUP_STEPS }, (_, i) => el("i", { class: i < s.stepK ? "on" : "" }))),
    `Setup, step ${s.stepK} of ${SETUP_STEPS}`); }
  setText($("#head"), ui.pauseMenu ? "How long should Kettle stop listening?" : s.head);
  const body = $("#body"); body.textContent = "";
  for (const line of s.body.filter(Boolean)) body.append(el("p", { class: "k-body", text: line }));
  if (s.progress) body.append(el("div", { class: "progress", role: "progressbar", "aria-valuenow": Math.round(ui.model * 100) }, el("i", { style: `width:${Math.round(ui.model * 100)}%` })));
  const extra = $("#extra");
  // rebuilt only when something in it changes, so a tap on a checkbox is never lost to the 1-s redraw
  const extraKey = JSON.stringify([s.checks, !!s.tools, !!s.share, ui.pauseMenu, srv.hide, srv.kinds_off, !!enrolment,
    document.documentElement.classList.contains("big-text"), t.names.caregiver]);
  const rebuild = extraKey !== ui.extraKey;
  ui.extraKey = extraKey;
  if (rebuild) extra.textContent = "";
  if (rebuild && s.checks && s.checks.length && !ui.pauseMenu) {
    extra.append(el("div", { class: "k-checks" }, el("p", { text: `Checks ${t.names.caregiver} set. They only read the timeline; Kettle tells ${t.names.caregiver} nothing else.` }),
      el("ul", {}, s.checks.map((c) => el("li", { text: c })))));
  }
  if (s.example) body.append(exampleBar());
  if (s.teachCta && !ui.pauseMenu) $("#body").prepend(el("div", { class: "k-teach-cta" },
    el("div", {}, el("p", { class: "t", text: `First, teach Kettle this ${roomWord()}` }),
      el("p", { class: "s", text: "3 minutes: quiet, washing up, cooking. Kettle gets more accurate here, and what it learns stays on this " + DEVICE + "." })),
    button("Start (3 minutes)", startTeach, "primary")));
  if (s.teachMeter) {
    const lvl = el("span", { class: "lvl", "aria-hidden": "true" }, el("i", { style: `width:${Math.round(Math.min(1, Math.sqrt(teach.level) * 1.6) * 100)}%` }));
    body.append(el("div", { class: "teach-meter" }, el("span", { text: "Sound level" }), lvl));
  }
  if (rebuild && s.tools && !ui.pauseMenu) extra.append(tools());
  if (rebuild && s.share && !ui.pauseMenu) extra.append(sharePanel(t));
  if (s.guide) body.append(s.guide);
  if (s.helper) body.append(el("details", { class: "helper" }, el("summary", { text: s.helper[0] }), el("p", { text: s.helper[1] })));
  const ctr = $("#controls"); ctr.textContent = "";
  if (ui.pauseMenu) {
    $("#status").dataset.state = "never";
    ctr.append(el("div", { class: "pause-menu" }, button("A guest or carer is here (2 hours)", () => act("pause", { minutes: 120, reason: "guest" })),
      button("Pause for 15 minutes", () => act("pause", { minutes: 15 })), button("Pause for 1 hour", () => act("pause", { minutes: 60 })),
      button("Pause until tomorrow morning", () => act("pause", { minutes: null })), button("Cancel", () => { ui.pauseMenu = false; draw(); }, "quiet-k")));
  } else for (const c of s.controls) ctr.append(c);
  const wrap = $("#chip-wrap"); wrap.textContent = "";
  wrap.hidden = !s.chip || ui.pauseMenu;
  if (s.chip && !ui.pauseMenu) {
    const txt = t.chip || "Waiting for the first sound…";
    meterEl = el("span", { class: "meter", "aria-hidden": "true" }, el("i"), el("i"), el("i"), el("i"), el("i"));
    const chip = el("div", { class: "chip big", "aria-live": "polite" }, el("span", { class: "txt", text: txt }), mic ? meterEl : null);
    wrap.append(chip);
    if (t.chip !== prevChip && prevChip !== null && fresh) { const n = chip.querySelector(".txt"); n.classList.add("swap"); }
    prevChip = t.chip;
  }
  $("#bar-section").hidden = !s.bar || ui.pauseMenu;
  if (s.bar && !ui.pauseMenu) bar.render(t);
}
