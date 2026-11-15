// Kettle landing (dark): a live sample day in the hero panel, interactive steps, both real screens, numbers from results.json.
import { DISPLAY, COLOUR, clock } from "./core.js";
import { $, el, setText, dayBar, legend, rulesList, homes, reduceMotion } from "./ui.js";
import { play } from "./sample.js";

const RM = reduceMotion();

// ---------- nav frosts once you scroll
const nav = $("#nav");
const onScroll = () => nav.classList.toggle("solid", scrollY > 24);
addEventListener("scroll", onScroll, { passive: true }); onScroll();
const mine = Object.values(homes()).sort((a, b) => b.saved - a.saved)[0];
if (mine) { const a = $("#nav-home"); a.href = mine.familyKey ? "/family" : "/kitchen"; a.textContent = mine.familyKey ? `${mine.parent || "My"}'s kitchen` : "Kitchen screen"; }

// ---------- hero panel: what Kettle heard (Dad's laptop) beside what Meera sees
const heardList = $("#lp-heard"), steps = [...document.querySelectorAll(".lp-steps span")];
const heroBar = dayBar($("#lp-bar"));
let heard = [], stepT = [];
function runSteps() {
  stepT.forEach(clearTimeout); stepT = [];
  steps.forEach((s) => s.classList.remove("done", "now"));
  steps.forEach((s, i) => stepT.push(setTimeout(() => { steps.forEach((x, j) => { x.classList.toggle("done", j < i); x.classList.toggle("now", j === i); }); }, i * (RM ? 0 : 160))));
  stepT.push(setTimeout(() => steps.forEach((x) => { x.classList.add("done"); x.classList.remove("now"); }), RM ? 0 : 760));
}
function heroFrame(t) {
  $("#lp-clock").textContent = t.now_text;
  const e = t.last_event;
  if (e) {
    heard.unshift(e); heard = heard.slice(0, 6);
    heardList.textContent = "";
    heard.forEach((x, i) => {
      const ns = x.novel || x.conf < 0.66;
      const li = el("li", { class: (ns ? "ns " : "") + (i === 0 ? "enter" : "") },
        el("span", { class: "t num", text: clock(x.end, t.tz_offset) }),
        el("span", { class: "sw", style: `background:var(${COLOUR[x.label]})${ns ? ";opacity:.35" : ""}` }),
        el("span", { class: "lab" }, ns ? "Not sure" : DISPLAY[x.label], el("small", { text: (x.sounds[0] || {}).name || "" })),
        el("span", { class: "conf num" }, el("i", {}, el("b", { style: `--p:${x.conf}` })), x.conf.toFixed(2)));
      heardList.append(li);
    });
    runSteps();
  }
  setText($("#lp-sum"), t.summary || "Listening. Nothing named yet.");
  $("#lp-count").textContent = `${t.sample.i} of ${t.sample.n} labels`;
  heroBar.render(t);
  rulesList($("#lp-rules"), t.rules);
}
let heroPlayer = null;
const startHero = async () => { heard = []; heroPlayer = await play("usual", heroFrame, { seconds: RM ? 0.5 : 34, loop: true }); };
new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting && !heroPlayer) startHero(); else if (!x.isIntersecting && heroPlayer) { heroPlayer.stop(); heroPlayer = null; } }), { threshold: 0.2 }).observe($(".lx-panel"));

// ---------- how it works: four steps, auto-advancing, each with its own screen
const flowUI = $("#flow-ui"), accs = [...document.querySelectorAll(".acc")], accBox = $(".lx-acc");
const STEP_MS = 6500;
let cur = 0, timer = null, flowBar = null;
const meter = () => el("span", { class: "su-meter", "aria-hidden": "true" }, el("i"), el("i"), el("i"), el("i"), el("i"));
const views = [
  () => [el("p", { class: "su-k", text: "Meera's phone · Step 3 of 3" }), el("p", { class: "su-h", text: "Now connect Dad's laptop" }),
    el("p", { class: "su-p", text: "On his kitchen laptop, open Kettle and type:" }), el("p", { class: "su-code num", html: "K7P<span> </span>4QX" }),
    el("p", { class: "su-p", text: "The code works for 48 hours." })],
  () => [el("p", { class: "su-k", text: "Dad's kitchen laptop" }), el("p", { class: "su-h", text: "This laptop listens for kitchen sounds." }),
    el("p", { class: "su-p", text: "It only notes the kind of sound, like dishes or TV. It keeps no recordings and no words. You can pause it or turn it off any time." }),
    el("div", {}, el("span", { class: "su-btn", text: "Yes, Meera can see this" }), el("span", { class: "su-btn ghost", text: "Not now" }))],
  () => [el("p", { class: "su-k" }, el("i"), "Dad's kitchen laptop, listening"), el("p", { class: "su-h", text: "Listening for kitchen sounds" }),
    el("span", { class: "su-chip" }, "Sounds like cooking", meter()),
    el("div", { class: "su-list" }, el("p", {}, el("span", { text: "Sound, 10 seconds" }), el("b", { text: "dropped" })), el("p", {}, el("span", { text: "Label sent to Meera" }), el("b", { text: "Cooking, 8:05 AM" })))],
  () => { const box = el("div"); const holder = [el("p", { class: "su-k", text: "Meera's phone" }), el("p", { class: "su-h", text: "Dad's kitchen today" }),
    el("p", { class: "su-p", id: "su-sum", text: "So far today: cooking around 8:05 AM, eating around 8:30 AM and TV from about 9:30 AM." }), box, el("div", { class: "lp-rules", id: "su-rules", style: "grid-template-columns:1fr" })];
    flowBar = dayBar(box); return holder; },
];
let flowFrames = null;
function show(i, user = false) {
  cur = i;
  accs.forEach((a, j) => { a.setAttribute("aria-selected", String(j === i)); a.style.setProperty("--dur", `${STEP_MS}ms`); const p = a.querySelector(".acc-p i"); p.style.animation = "none"; void p.offsetWidth; p.style.animation = ""; });
  flowUI.textContent = ""; flowUI.append(...views[i]());
  flowUI.classList.remove("swap"); void flowUI.offsetWidth; flowUI.classList.add("swap");
  if (flowFrames) { flowFrames.stop(); flowFrames = null; }
  if (i === 3) play("usual", (t) => { flowBar && flowBar.render(t); const s = $("#su-sum"); if (s) s.textContent = t.summary; const r = $("#su-rules"); if (r) rulesList(r, t.rules); }, { seconds: 4 }).then((p) => (flowFrames = p));
  clearTimeout(timer);
  if (!RM) timer = setTimeout(() => show((cur + 1) % views.length), STEP_MS);
  if (user) accBox.classList.remove("paused");
}
accs.forEach((a, i) => a.addEventListener("click", () => show(i, true)));
accBox.addEventListener("pointerenter", () => { accBox.classList.add("paused"); clearTimeout(timer); });
accBox.addEventListener("pointerleave", () => { accBox.classList.remove("paused"); clearTimeout(timer); if (!RM) timer = setTimeout(() => show((cur + 1) % views.length), STEP_MS / 2); });
let flowStarted = false;
new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting && !flowStarted) { flowStarted = true; show(0); } })).observe($("#how"));

// ---------- two screens: the real kitchen screen and family view in device frames
const K = $("#kitchen-canvas"), F = $("#family-canvas");
K.classList.add("light-scope"); F.classList.add("light-scope");
K.append(el("div", { class: "kitchen k-mini" },
  el("div", { class: "k-status", "data-state": "listening" }, el("span", { class: "dot" }), el("div", {},
    el("h1", { class: "k-head", text: "Listening for kitchen sounds" }), el("p", { class: "k-body", text: "Meera sees the kinds of sounds, not recordings or words." }))),
  el("div", { class: "chip big" }, el("span", { class: "txt", id: "k-chip", text: "Waiting for the first sound…" })),
  el("div", { class: "k-controls" }, el("span", { class: "btn kbtn primary pause", text: "Pause" }), el("span", { class: "btn kbtn", text: "Turn it off" })),
  el("div", { id: "k-bar" })));
F.append(el("div", { class: "f-mini" },
  el("div", { class: "notch" }), el("div", { class: "sbar" }, el("span", { class: "num", id: "f-clock", text: "9:41" }), el("span", { text: "●●●" })),
  el("p", { class: "eyebrow", text: "What Meera sees" }), el("h1", { text: "Dad's kitchen today" }),
  el("p", { class: "hb", "data-state": "listening" }, el("span", { class: "dot" }), el("span", { class: "text", text: "Listening · last heard just now" })),
  el("p", { class: "summary", id: "f-sum" }), el("div", { class: "card" }, el("div", { id: "f-bar" })), el("div", { class: "rules", id: "f-rules" })));
const kBar = dayBar($("#k-bar"), { big: true }), fBar = dayBar($("#f-bar")), fLegend = legend($("#f-bar"));
let stage = null, stageOn = false;
function stageFrame(t) {
  setText($("#k-chip"), t.chip || "Waiting for the first sound…");
  setText($("#f-sum"), t.summary || "Nothing heard yet today.");
  $("#f-clock").textContent = t.now_text.replace(/ (AM|PM)$/, "");
  kBar.render(t); fBar.render(t); fLegend(t); rulesList($("#f-rules"), t.rules);
}
async function startStage(sid) {
  if (stage) stage.stop();
  document.querySelectorAll(".lx-seg [data-sid]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.sid === sid)));
  stage = await play(sid, stageFrame, { seconds: RM ? 0.5 : 18, loop: true });
}
document.querySelectorAll(".lx-seg [data-sid]").forEach((b) => b.addEventListener("click", () => startStage(b.dataset.sid)));
new IntersectionObserver((es) => es.forEach((x) => {
  if (x.isIntersecting && !stageOn) { stageOn = true; startStage("usual"); }
  if (!x.isIntersecting && stageOn) { stageOn = false; stage && stage.stop(); }
}), { threshold: 0.2 }).observe($("#stage"));
function fit() {
  document.querySelectorAll(".dev").forEach((d) => {
    const g = d.querySelector(".glass"), c = d.querySelector(".canvas"), s = g.clientWidth / +d.dataset.w;
    c.style.width = d.dataset.w + "px"; c.style.height = d.dataset.h + "px"; c.style.transform = `scale(${s})`;
  });
}
new ResizeObserver(fit).observe(document.body); fit();

// ---------- numbers from results.json (never typed by hand)
fetch("/data/results.json").then((r) => r.json()).then((r) => {
  const set = (k, v) => document.querySelectorAll(`[data-k="${k}"]`).forEach((n) => { if (v != null) n.textContent = v; });
  const ev = r.dcase_eval, ma = ev && ev.meal_activity;
  if (ev) set("f1", ev.ours_ch0.macro_f1.value.toFixed(1));
  if (ma) { set("caught", String(Math.round(ma.caught.value))); set("fa", ma.false_alarm_rate.value.toFixed(1)); }
  if (r.offlist && r.offlist.confident_wrong != null) set("ns", Number(r.offlist.confident_wrong).toFixed(1));
  const c = r.privacy_check && r.privacy_check.checks;
  if (c) set("audio", String((c.new_or_changed_audio_extension_files || []).length + (c.new_or_changed_files_with_audio_magic_bytes || []).length));
}).catch(() => {});

// ---------- sections unfold once
const io = new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting) { x.target.classList.add("seen"); io.unobserve(x.target); } }), { rootMargin: "0px 0px -8% 0px" });
document.querySelectorAll(".lx-sec, .lx-why").forEach((s) => io.observe(s));
