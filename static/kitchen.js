// Kettle kitchen screen: the parent's consent, the listening state, Pause and Turn it off.
// The microphone runs only while the parent has said yes and Kettle isn't paused or off.
// Audio goes only to the Kettle program on this laptop (ws://localhost), as numbers in memory.
"use strict";

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const PRESENTER = params.has("presenter");
const ui = { step: "intro", mic: "idle", pauseMenu: false, resumedAt: 0, resumedText: "", down: false, showChip: null, failures: 0 };
let today = null, audio = null;

const bar = makeDayBar($("bar"), { big: true });

// ---------------------------------------------------------------- microphone (RAM only)

async function startMic() {
  ui.mic = "asking";
  draw();
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  } catch (e) {
    ui.mic = e && (e.name === "NotFoundError" || e.name === "OverconstrainedError") ? "none" : "denied";
    api("/api/mic", { state: ui.mic === "none" ? "none" : "blocked" }).catch(() => {});
    draw();
    return;
  }
  const ctx = new AudioContext({ sampleRate: 16000 });
  await ctx.audioWorklet.addModule("/static/worklet.js");
  const src = ctx.createMediaStreamSource(stream);
  const node = new AudioWorkletNode(ctx, "kettle-tap");
  const ratio = ctx.sampleRate / 16000;
  let pending = [], carry = 0;
  audio = { stream, ctx, node, ws: null, backoff: 1 };
  node.port.onmessage = (e) => {
    const x = e.data;
    if (ratio === 1) { for (let i = 0; i < x.length; i++) pending.push(x[i]); }
    else { for (let p = carry; p < x.length; p += ratio) pending.push(x[Math.floor(p)]); carry = (carry + Math.ceil((x.length - carry) / ratio) * ratio) - x.length; }
    if (pending.length >= 1600) {
      const out = new Int16Array(pending.length);
      for (let i = 0; i < pending.length; i++) out[i] = Math.max(-1, Math.min(1, pending[i])) * 32767;
      pending = [];
      if (audio && audio.ws && audio.ws.readyState === 1) audio.ws.send(out.buffer);
    }
  };
  src.connect(node);
  connectWs();
  ui.mic = "on";
  api("/api/mic", { state: "ok" }).catch(() => {});
  draw();
}

function connectWs() {
  if (!audio) return;
  const ws = new WebSocket(`ws://${location.host}/ws/audio`);
  ws.binaryType = "arraybuffer";
  ws.onopen = () => { if (audio) audio.backoff = 1; };
  ws.onclose = () => {
    if (!audio) return;
    const wait = Math.min(8, audio.backoff);
    audio.backoff *= 2;
    setTimeout(connectWs, wait * 1000);
  };
  audio.ws = ws;
}

function stopMic() {
  if (!audio) { ui.mic = "idle"; return; }
  const a = audio;
  audio = null;
  a.stream.getTracks().forEach((t) => t.stop());
  try { a.ws && a.ws.close(); } catch (e) { /* already closed */ }
  a.ctx.close();
  ui.mic = "idle";
}

// ---------------------------------------------------------------- actions

async function act(path, body = {}) {
  try { today = await api(path, body); ui.pauseMenu = false; sync(); }
  catch (e) {
    if (e.status === 403) showOnlyHere();
  }
}
function showOnlyHere() {
  $("extra").textContent = "";
  $("extra").append(el("p", { class: "k-body", text: "Open this page on the kitchen laptop itself to change it." }));
}
function speak(lines) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  for (const l of lines) speechSynthesis.speak(new SpeechSynthesisUtterance(l));
}

function button(text, onclick, cls = "") { return el("button", { class: `btn kbtn ${cls}`, type: "button", text, onclick }); }

// ---------------------------------------------------------------- what to show

function screen(t) {
  const n = t.names, k = t.kitchen, hb = t.heartbeat;
  if (ui.down) {
    return { state: "error", head: "Kettle has stopped.", body: ["Press Try again, or ask " + n.caregiver + " for help."],
      controls: [button("Try again", () => location.reload(), "primary")],
      helper: ["For a helper", "The Kettle program on this laptop isn't answering. Start it again with: python app.py. Today's timeline is kept."] };
  }
  if (!k.consent) {
    if (ui.step === "teachback") {
      return { state: "never", head: `Is it OK for ${n.caregiver} to see this?`, body: ["She will see the kinds of sound and when they happened. Nothing else."],
        controls: [button(`Yes, ${n.caregiver} can see this`, () => act("/api/consent"), "primary"), button("No, not now", () => { ui.step = "declined"; draw(); })] };
    }
    if (ui.step === "declined") {
      return { state: "off", head: "Kettle is off.", body: ["This laptop isn't listening. Press Start when you want it on."],
        controls: [button("Start", () => { ui.step = "intro"; draw(); }, "primary")] };
    }
    const lines = ["The program is called Kettle. It uses this laptop's microphone and only notes the kind of sound, like 'dishes' or 'TV'.", "It keeps no recordings and no words.",
      `${n.caregiver} sees a day timeline like this one. You can pause it or turn it off any time.`];
    return { state: "never", head: "This laptop listens for kitchen sounds.", body: lines, example: true,
      controls: [button("Next", () => { ui.step = "teachback"; draw(); }, "primary"), button("Not now", () => { ui.step = "declined"; draw(); }),
        button("Read this to me", () => speak(["This laptop listens for kitchen sounds.", ...lines]))] };
  }
  if (k.off) {
    return { state: "off", head: "Kettle is off.", body: ["This laptop isn't listening. Press Start when you want it on."],
      controls: [button("Start", () => act("/api/start"), "primary")] };
  }
  if (k.paused) {
    const weekly = k.pause_reason === "weekly";
    const until = weekly ? `Kettle waits for your answer before listening again.`
      : hb.until_text ? `Starts listening again at ${hb.until_text}${hb.text.includes("tomorrow") ? " tomorrow" : ""}.` : "";
    return { state: "paused", head: weekly ? "Kettle has paused. Keep it on?" : "Paused. Kettle isn't listening.",
      body: [`${n.caregiver} sees: Paused by you at ${hb.since_text}.`, until], bar: true,
      controls: weekly ? [button("Keep it on", () => act("/api/keep-on"), "primary"), button("Turn it off", () => act("/api/off"))]
        : [button("Resume listening", () => act("/api/resume"), "primary pause"), button("Turn it off", () => act("/api/off"))] };
  }
  if (k.weekly_due) {
    return { state: hb.state, head: "Kettle has been on for a week. Keep it on?", body: [`${n.caregiver} sees the kinds of sounds, not recordings or words.`, "If nobody answers, Kettle pauses tomorrow until you choose."],
      controls: [button("Keep it on", () => act("/api/keep-on")), button("Turn it off", () => act("/api/off"))] };
  }
  if (t.demo) {
    return { state: hb.state, head: `Sample day: ${t.demo.title}`, body: [`Recorded sounds from a public research home, played fast. Not ${n.parent}.`],
      chip: true, bar: true,
      controls: [hb.state === "paused" ? button("Resume listening", () => act("/api/resume"), "primary pause") : button("Pause", () => { ui.pauseMenu = true; draw(); }, "primary pause"),
        button("Stop sample", () => act("/api/demo/stop"))] };
  }
  if (ui.mic === "asking" || ui.mic === "idle") {
    return { state: "starting", head: "A box will pop up about the microphone.", body: ["Press Allow. Only this laptop uses it."],
      controls: [el("button", { class: "btn quiet", type: "button", text: "No box appeared? Try again", style: "font-size:var(--fs-lead)", onclick: () => { stopMic(); ui.mic = "idle"; sync(); } })] };
  }
  if (ui.mic === "denied" || ui.mic === "none") {
    const none = ui.mic === "none";
    return { state: "error-soft", head: none ? "No microphone found." : "Kettle can't hear the kitchen.",
      body: [none ? "Plug one in, or use a laptop with a built-in microphone." : `The laptop's microphone is switched off for Kettle. This isn't something you did wrong. ${n.caregiver} or a helper can turn it on.`],
      helper: none ? null : ["Steps for a helper", "Chrome: click the icon left of the address, then Microphone, then Allow, then Try again. Safari: Settings for this website, then Microphone, then Allow."],
      controls: [button("Try again", () => { ui.mic = "idle"; sync(); }, "primary"), button("Play a sample day instead", () => act("/api/demo/usual"))] };
  }
  const since = k.consent_day === new Date(t.now * 1000).toLocaleDateString("en-US", { weekday: "long" })
    ? `Listening since ${k.consent_text} today.` : `Listening since ${k.consent_day}.`;
  const checks = t.rules.map((r) => r.title);
  const base = { bar: true, chip: true, checks,
    controls: [button("Pause", () => { ui.pauseMenu = true; draw(); }, "primary pause"), button("Turn it off", () => act("/api/off"))] };
  if (Date.now() - ui.resumedAt < 10000 && ui.resumedText) {
    return { ...base, state: "listening", head: "Kettle is listening again.", body: [ui.resumedText] };
  }
  if (hb.state === "starting") {
    return { ...base, state: "starting", head: "Listening…", body: ["The first sound label appears in about 10 seconds."] };
  }
  return { ...base, state: hb.state === "listening" ? "listening" : "starting", head: "Listening for kitchen sounds",
    body: [`${since} ${n.caregiver} sees the kinds of sounds, not recordings or words.`] };
}

function draw() {
  if (!today) return;
  const s = screen(today);
  $("status").dataset.state = s.state;
  setText($("head"), s.head, false);
  const body = $("body");
  body.textContent = "";
  for (const line of s.body.filter(Boolean)) body.append(el("p", { class: "k-body", text: line }));
  if (s.checks && s.checks.length) {
    const ul = el("ul");
    for (const c of s.checks) ul.append(el("li", { text: c }));
    body.append(el("div", { class: "k-rules", style: "margin-top:12px" }, el("p", { text: `Checks ${today.names.caregiver} set (they only read the timeline; Kettle tells her nothing else):` }), ul));
  }
  if (s.example) body.append(exampleBar());
  if (s.helper) body.append(el("details", { class: "helper" }, el("summary", { text: s.helper[0] }), el("p", { text: s.helper[1] })));
  // demo tag: under the message, never on the error screen
  const tag = $("demo-tag");
  tag.hidden = !today.demo || s.state === "error";
  tag.textContent = "";
  if (today.demo) tag.append(el("span", { class: "tag demo", style: "font-size:var(--fs-meta)", text: "Sample day" }));
  // controls / pause menu
  const ctr = $("controls");
  ctr.textContent = "";
  if (ui.pauseMenu) {
    setText($("head"), "How long should Kettle stop listening?", false);
    $("status").dataset.state = "never";
    ctr.append(el("div", { class: "pause-menu" },
      button("Pause for 15 minutes", () => act("/api/pause", { minutes: 15 })),
      button("Pause for 1 hour", () => act("/api/pause", { minutes: 60 })),
      button("Pause until tomorrow morning", () => act("/api/pause", { minutes: null })),
      button("Cancel", () => { ui.pauseMenu = false; draw(); }, "quiet-k")));
  } else {
    for (const c of s.controls) ctr.append(c);
  }
  // chip
  const wrap = $("chip-wrap");
  wrap.textContent = "";
  const big = PRESENTER || !!today.demo;
  if (s.chip) {
    if (ui.showChip === null) ui.showChip = big || today.kitchen.consent_day === new Date(today.now * 1000).toLocaleDateString("en-US", { weekday: "long" });
    wrap.hidden = false;
    if (ui.showChip || big) {
      const txt = today.chip || "Waiting for the first sound…";
      wrap.append(el("div", { class: `chip ${big ? "big" : ""}`, "aria-live": "polite" }, el("span", { class: "txt", text: txt })));
    }
    if (!big) wrap.append(el("button", { class: "btn quiet", type: "button", style: "font-size:var(--fs-lead);margin-left:8px", text: ui.showChip ? "Hide what it hears" : "What does it hear?", onclick: () => { ui.showChip = !ui.showChip; draw(); } }));
  } else {
    wrap.hidden = true;
  }
  $("bar-section").hidden = !s.bar;
  if (s.bar) bar.render(today);
}

// A drawn example of what Meera sees (not real data), so "a day timeline like this one" has something to point at.
let exampleNode = null;
function exampleBar() {
  if (exampleNode) return exampleNode;
  const fake = { day0: 0, now: 11 * 3600, names: today.names, heartbeat: { state: "listening" }, blocks: [
    { start: 6 * 3600, end: 7.6 * 3600, state: "empty", activity: "absence", label: "Quiet", range: "" },
    { start: 8 * 3600, end: 8.4 * 3600, state: "activity", activity: "cooking", label: "Cooking", range: "", how_sure: "high" },
    { start: 8.45 * 3600, end: 8.75 * 3600, state: "activity", activity: "dishwashing", label: "Washing up", range: "", how_sure: "high" },
    { start: 9.2 * 3600, end: 10.6 * 3600, state: "activity", activity: "watching_tv", label: "TV", range: "", how_sure: "high" }] };
  const box = el("div", { class: "example", "aria-label": "Example of the day timeline (not real)" },
    el("span", { class: "tag", text: "Example, not real" }), el("div"));
  setTimeout(() => makeDayBar(box.lastChild).render(fake), 0);
  exampleNode = box;
  return box;
}

let prevChip = null;
function sync() {
  if (!today) return;
  const k = today.kitchen;
  const wasPaused = sync.paused;
  sync.paused = k.paused;
  if (wasPaused && !k.paused && !today.demo) {
    ui.resumedAt = Date.now();
    const last = (today.blocks || []).filter((b) => b.state === "paused").pop();
    ui.resumedText = last ? (last.end - last.start < 60 ? "Paused for under a minute." : `Paused from ${last.range}.`) : "";
  }
  const shouldListen = !today.demo && k.consent && !k.off && !k.paused;
  if (shouldListen && ui.mic === "idle" && !ui.down) startMic();
  if (!shouldListen && audio) stopMic();
  draw();
  const chipNode = document.querySelector(".chip .txt");
  if (chipNode && today.chip !== prevChip && prevChip !== null) { chipNode.classList.remove("swap"); void chipNode.offsetWidth; chipNode.classList.add("swap"); }
  prevChip = today.chip;
}

async function poll() {
  try {
    today = await api("/api/today");
    ui.failures = 0;
    if (ui.down) { ui.down = false; }
    sync();
  } catch (e) {
    ui.failures += 1;
    if (ui.failures >= 3 && today) { ui.down = true; stopMic(); draw(); }
  }
}
addEventListener("resize", () => draw());
poll();
setInterval(poll, 1000);
