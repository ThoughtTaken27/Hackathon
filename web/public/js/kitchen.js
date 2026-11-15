// Dad's kitchen screen (Kettle web). Pairs with a code, asks Dad first, labels sound on this laptop, sends only labels.
import { today as computeToday, canListen } from "./core.js";
import { $, el, setText, api, now, linkFromHash, saveHome, forgetHome, dayBar, toast } from "./ui.js";
import { loadModel, startMic, HOP_S } from "./listen.js";

const link = linkFromHash("kitchen");
const ui = { step: "intro", pauseMenu: false, mic: "idle", model: 0, down: false, failures: 0, showChip: true, resumedAt: 0, resumedText: "" };
let srv = null, events = [], queue = [], mic = null, wake = null, t = null;
const bar = dayBar($("#bar"), { big: true });
const QKEY = link ? `kettle.queue.${link.id}` : null;
try { queue = QKEY ? JSON.parse(localStorage.getItem(QKEY)) || [] : []; } catch { queue = []; }
const saveQueue = () => { try { localStorage.setItem(QKEY, JSON.stringify(queue.slice(-2000))); } catch {} };

function button(text, onclick, cls = "") { return el("button", { class: `btn kbtn ${cls}`, type: "button", text, onclick }); }
function speak(lines) { if (!("speechSynthesis" in window)) return; speechSynthesis.cancel(); for (const l of lines) speechSynthesis.speak(new SpeechSynthesisUtterance(l)); }

// ---------------------------------------------------------------- not paired yet: type the code
if (!link) {
  $("#status").dataset.state = "never";
  $("#head").textContent = "Connect this laptop to your family";
  const inp = el("input", { class: "input code-input", maxlength: 7, autocomplete: "off", autocapitalize: "characters", spellcheck: "false", "aria-label": "Six-letter code", placeholder: "ABC 123" });
  const err = el("p", { class: "err", role: "alert" });
  const go = async () => {
    err.textContent = "";
    try {
      const r = await api("/api/pair", { method: "POST", body: { code: inp.value } });
      saveHome(r.id, { [r.role + "Key"]: r.key });
      location.href = r.role === "kitchen" ? "/kitchen" : "/family";
    } catch (e) { err.textContent = e.message; }
  };
  inp.addEventListener("keydown", (e) => e.key === "Enter" && go());
  $("#body").append(el("p", { class: "k-body", text: "Type the six-letter code from the family member's phone." }), el("div", { style: "max-width:420px;margin-top:20px" }, inp, err));
  $("#controls").append(button("Connect", go, "primary"), el("a", { class: "btn kbtn quiet-k", href: "/start", text: "Set up Kettle from scratch" }));
  inp.focus();
} else boot();

// ---------------------------------------------------------------- paired
async function boot() {
  await poll();
  setInterval(poll, 5000);
  setInterval(() => { if (srv) draw(); }, 1000);
  setInterval(flush, 4000);
  addEventListener("online", flush);
  document.addEventListener("visibilitychange", () => { if (!document.hidden && mic) lockScreen(); });
  addEventListener("resize", () => draw());
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
async function act(type, extra = {}) {
  ui.pauseMenu = false;
  try { const r = await api(`/api/h/${link.id}/action`, { method: "POST", key: link.key, body: { type, ...extra } }); srv = r.state; sync(); }
  catch (e) { toast(e.message || "Couldn't reach Kettle. Trying again."); }
}
async function flush() {
  if (!queue.length || !srv || !canListen(srv, now())) return;
  const batch = queue.slice(0, 60);
  try {
    await api(`/api/h/${link.id}/events`, { method: "POST", key: link.key, body: { events: batch, tz: Intl.DateTimeFormat().resolvedOptions().timeZone }, retries: 1 });
    queue = queue.slice(batch.length); saveQueue(); ui.down = false;
  } catch (e) { if (e.status === 409) { queue = []; saveQueue(); } }
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
      onLevel: (v) => meter(v),
      onWindow: (w) => {
        const ev = { start: w.start, end: w.end, label: w.label, conf: w.conf, probs: w.probs, novel: w.novel, w: w.w, sounds: w.sounds };
        events.push(ev); queue.push(ev); saveQueue(); flush();
        if (srv) srv.last_window_t = ev.end;
        draw(true);
      },
    });
    ui.mic = "on"; lockScreen();
    act("mic", { state: "ok" });
  } catch (e) {
    ui.mic = e && e.name === "NotFoundError" ? "none" : "denied";
    act("mic", { state: ui.mic === "none" ? "none" : "blocked" });
  }
  draw();
}
function stopListening() { if (mic) { mic.stop(); mic = null; } if (wake) { wake.release().catch(() => {}); wake = null; } if (ui.mic === "on") ui.mic = "idle"; }
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
  if (ui.gone) return { state: "error", head: "This laptop isn't connected any more.", body: [ui.gone, "Ask your family member for a new code."],
    controls: [el("a", { class: "btn kbtn primary", href: "/kitchen", text: "Enter a new code", onclick: () => { forgetHome(link.id); } })] };
  if (ui.down) return { state: "error", head: "Kettle can't reach the internet.", body: ["It keeps listening and will send what it heard when the connection is back."],
    controls: [button("Try again", () => poll(), "primary")], bar: true, chip: true };
  if (!k.consent) {
    if (ui.step === "teachback") return { state: "never", head: `Is it OK for ${n.caregiver} to see this?`, body: [`${n.caregiver} will see the kinds of sound and when they happened. Nothing else.`],
      controls: [button(`Yes, ${n.caregiver} can see this`, () => act("consent"), "primary"), button("No, not now", () => { ui.step = "declined"; draw(); })] };
    if (ui.step === "declined") return { state: "off", head: "Kettle is off.", body: ["This laptop isn't listening. Press Start when you want it on."],
      controls: [button("Start", () => { ui.step = "intro"; draw(); }, "primary")] };
    const lines = ["The program is called Kettle. It uses this laptop's microphone and only notes the kind of sound, like 'dishes' or 'TV'.",
      "It keeps no recordings and no words. The sound never leaves this laptop.", `${n.caregiver} sees a day timeline like this one. You can pause it or turn it off any time.`];
    return { state: "never", head: "This laptop listens for kitchen sounds.", body: lines, example: true,
      controls: [button("Next", () => { ui.step = "teachback"; draw(); }, "primary"), button("Not now", () => { ui.step = "declined"; draw(); }),
        button("Read this to me", () => speak(["This laptop listens for kitchen sounds.", ...lines]), "quiet-k")] };
  }
  if (k.off) return { state: "off", head: "Kettle is off.", body: ["This laptop isn't listening. Press Start when you want it on."], controls: [button("Start", () => act("start"), "primary")] };
  if (k.paused) {
    const weekly = k.pause_reason === "weekly";
    const until = weekly ? "Kettle waits for your answer before listening again." : hb.until_text ? `Starts listening again at ${hb.until_text}${hb.text.includes("tomorrow") ? " tomorrow" : ""}.` : "";
    return { state: "paused", head: weekly ? "Kettle has paused. Keep it on?" : "Paused. Kettle isn't listening.", body: [`${n.caregiver} sees: Paused by you at ${hb.since_text}.`, until], bar: true,
      controls: weekly ? [button("Keep it on", () => act("keep_on"), "primary"), button("Turn it off", () => act("off"))]
        : [button("Resume listening", () => act("resume"), "primary pause"), button("Turn it off", () => act("off"))] };
  }
  if (k.weekly_due) return { state: hb.state, head: "Kettle has been on for a week. Keep it on?", body: [`${n.caregiver} sees the kinds of sounds, not recordings or words.`, "If nobody answers, Kettle pauses tomorrow until you choose."],
    controls: [button("Keep it on", () => act("keep_on"), "primary"), button("Turn it off", () => act("off"))] };
  if (ui.mic === "loading") return { state: "starting", head: "Getting Kettle ready…", body: ["Kettle's sound model is loading onto this laptop. This happens once."], progress: true, controls: [] };
  if (ui.mic === "model_failed") return { state: "error", head: "Kettle couldn't load.", body: ["Check the internet connection, then try again."], controls: [button("Try again", () => { ui.mic = "idle"; sync(); }, "primary")] };
  if (ui.mic === "asking" || ui.mic === "idle") return { state: "starting", head: "A box will pop up about the microphone.", body: ["Press Allow. Only this laptop uses it."],
    controls: [el("button", { class: "btn quiet", type: "button", text: "No box appeared? Try again", style: "font-size:var(--fs-lead)", onclick: () => { stopListening(); ui.mic = "idle"; sync(); } })] };
  if (ui.mic === "denied" || ui.mic === "none") {
    const none = ui.mic === "none";
    return { state: "error-soft", head: none ? "No microphone found." : "Kettle can't hear the kitchen.",
      body: [none ? "Plug one in, or use a laptop with a built-in microphone." : `The microphone is switched off for Kettle. This isn't something you did wrong. ${n.caregiver} or a helper can turn it on.`],
      helper: none ? null : ["Steps for a helper", "Chrome: click the icon left of the address, then Microphone, then Allow, then Try again. Safari: Settings for this website, then Microphone, then Allow."],
      controls: [button("Try again", () => { ui.mic = "idle"; sync(); }, "primary")] };
  }
  const today = new Date(now() * 1000).toLocaleDateString("en-US", { weekday: "long", timeZone: srv.tz });
  const since = k.consent_day === today ? `Listening since ${k.consent_text} today.` : `Listening since ${k.consent_day}.`;
  const base = { bar: true, chip: true, checks: t.rules.map((r) => r.title),
    controls: [button("Pause", () => { ui.pauseMenu = true; draw(); }, "primary pause"), button("Turn it off", () => act("off"))] };
  if (Date.now() - ui.resumedAt < 10000 && ui.resumedText) return { ...base, state: "listening", head: "Kettle is listening again.", body: [ui.resumedText] };
  if (hb.state === "starting") return { ...base, state: "starting", head: "Listening…", body: ["The first sound label appears in about 10 seconds."] };
  return { ...base, state: hb.state === "listening" ? "listening" : "starting", head: "Listening for kitchen sounds",
    body: [`${since} ${n.caregiver} sees the kinds of sounds, not recordings or words.`] };
}

let exampleNode = null;
function exampleBar() {
  if (exampleNode) return exampleNode;
  const fake = { day0: 0, now: 11 * 3600, names: t.names, heartbeat: { state: "listening" }, blocks: [
    { start: 6 * 3600, end: 7.6 * 3600, state: "empty", activity: "absence", label: "Quiet", range: "" },
    { start: 8 * 3600, end: 8.4 * 3600, state: "activity", activity: "cooking", label: "Cooking", range: "", how_sure: "high" },
    { start: 8.45 * 3600, end: 8.75 * 3600, state: "activity", activity: "dishwashing", label: "Washing up", range: "", how_sure: "high" },
    { start: 9.2 * 3600, end: 10.6 * 3600, state: "activity", activity: "watching_tv", label: "TV", range: "", how_sure: "high" }] };
  const box = el("div", { class: "example", "aria-label": "Example of the day timeline (not real)" }, el("span", { class: "tag", text: "Example, not real" }), el("div"));
  setTimeout(() => dayBar(box.lastChild).render(fake), 0);
  return (exampleNode = box);
}

let prevChip = null;
function sync() {
  if (!srv) return;
  const was = sync.paused; sync.paused = !!(srv.paused_until && now() < srv.paused_until);
  t = computeToday(srv, events, now(), { theta: 0.66, tz: srv.tz, hop: HOP_S, names: srv.names });
  if (was && !sync.paused) {
    ui.resumedAt = Date.now();
    const last = t.blocks.filter((b) => b.state === "paused").pop();
    ui.resumedText = last ? (last.end - last.start < 60 ? "Paused for under a minute." : `Paused from ${last.range}.`) : "";
  }
  const should = canListen(srv, now());
  if (should && ui.mic === "idle") startListening();
  if (!should && mic) stopListening();
  draw();
}

function draw(fresh = false) {
  if (!srv) return;
  t = computeToday(srv, events, now(), { theta: 0.66, tz: srv.tz, hop: HOP_S, names: srv.names });
  const s = screen(t);
  $("#who-tag").textContent = `${t.names.parent}'s kitchen`;
  $("#status").dataset.state = s.state;
  setText($("#head"), ui.pauseMenu ? "How long should Kettle stop listening?" : s.head);
  const body = $("#body"); body.textContent = "";
  for (const line of s.body.filter(Boolean)) body.append(el("p", { class: "k-body", text: line }));
  if (s.progress) body.append(el("div", { class: "progress", role: "progressbar", "aria-valuenow": Math.round(ui.model * 100) }, el("i", { style: `width:${Math.round(ui.model * 100)}%` })));
  const extra = $("#extra"); extra.textContent = "";
  if (s.checks && s.checks.length && !ui.pauseMenu) {
    extra.append(el("div", { class: "k-checks" }, el("p", { text: `Checks ${t.names.caregiver} set. They only read the timeline; Kettle tells ${t.names.caregiver} nothing else.` }),
      el("ul", {}, s.checks.map((c) => el("li", { text: c })))));
  }
  if (s.example) body.append(exampleBar());
  if (s.helper) body.append(el("details", { class: "helper" }, el("summary", { text: s.helper[0] }), el("p", { text: s.helper[1] })));
  const ctr = $("#controls"); ctr.textContent = "";
  if (ui.pauseMenu) {
    $("#status").dataset.state = "never";
    ctr.append(el("div", { class: "pause-menu" }, button("Pause for 15 minutes", () => act("pause", { minutes: 15 })), button("Pause for 1 hour", () => act("pause", { minutes: 60 })),
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
