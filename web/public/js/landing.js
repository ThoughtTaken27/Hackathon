// Kettle landing: both real screens play a sample day inside device frames; numbers come from results.json.
import { $, el, setText, dayBar, legend, rulesList, homes, reduceMotion } from "./ui.js";
import { play } from "./sample.js";

// ---------- the kitchen screen (Dad) and the family view (Meera), drawn with the app's own components
const K = $("#kitchen-canvas"), F = $("#family-canvas");
K.append(el("div", { class: "kitchen k-mini" },
  el("div", { class: "k-status", "data-state": "listening" }, el("span", { class: "dot" }), el("div", {},
    el("h1", { class: "k-head", id: "k-head", text: "Listening for kitchen sounds" }),
    el("p", { class: "k-body", text: "Meera sees the kinds of sounds, not recordings or words." }))),
  el("div", { class: "chip big" }, el("span", { class: "txt", id: "k-chip", text: "Waiting for the first sound…" })),
  el("div", { class: "k-controls" }, el("span", { class: "btn kbtn primary pause", text: "Pause" }), el("span", { class: "btn kbtn", text: "Turn it off" })),
  el("div", { id: "k-bar" })));
F.append(el("div", { class: "f-mini" },
  el("div", { class: "notch" }), el("div", { class: "sbar" }, el("span", { class: "num", id: "f-clock", text: "9:41" }), el("span", { text: "●●●" })),
  el("p", { class: "eyebrow", text: "What Meera sees" }), el("h1", { text: "Dad's kitchen today" }),
  el("p", { class: "hb", "data-state": "listening" }, el("span", { class: "dot" }), el("span", { class: "text", id: "f-hb", text: "Listening · last heard just now" })),
  el("p", { class: "summary", id: "f-sum" }),
  el("div", { class: "card" }, el("div", { id: "f-bar" })),
  el("div", { class: "rules", id: "f-rules" })));
const kBar = dayBar($("#k-bar"), { big: true }), fBar = dayBar($("#f-bar")), fLegend = legend($("#f-bar"));

let player = null;
function frame(t) {
  setText($("#k-chip"), t.chip || "Waiting for the first sound…");
  setText($("#f-sum"), t.summary || "Nothing heard yet today.");
  $("#f-clock").textContent = t.now_text.replace(/ (AM|PM)$/, "");
  kBar.render(t); fBar.render(t); fLegend(t);
  rulesList($("#f-rules"), t.rules);
}
async function start(sid) {
  if (player) player.stop();
  document.querySelectorAll(".stage-bar [data-sid]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.sid === sid)));
  player = await play(sid, frame, { seconds: reduceMotion() ? 0.5 : 18, loop: true });
}
document.querySelectorAll(".stage-bar [data-sid]").forEach((b) => b.addEventListener("click", () => start(b.dataset.sid)));
$("#watch").addEventListener("click", (e) => { e.preventDefault(); $("#stage").scrollIntoView({ behavior: reduceMotion() ? "auto" : "smooth", block: "center" }); start("nobreakfast"); });

// play only while the stage is on screen
let started = false;
new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting && !started) { started = true; start("nobreakfast"); }
  if (!e.isIntersecting && player && started) { player.stop(); started = false; }
}), { threshold: 0.25 }).observe($("#stage"));

// ---------- scale the 1280x800 and 390x844 screens into their frames
function fit() {
  document.querySelectorAll(".dev").forEach((d) => {
    const g = d.querySelector(".glass"), c = d.querySelector(".canvas");
    const s = g.clientWidth / +d.dataset.w;
    c.style.width = d.dataset.w + "px"; c.style.height = d.dataset.h + "px"; c.style.transform = `scale(${s})`;
  });
}
new ResizeObserver(fit).observe(document.body); fit();

// ---------- the privacy tile's waveform
const wave = $("#fv-wave"), bars = [];
for (let i = 0; i < 36; i++) { const b = el("i"); wave.append(b); bars.push(b); }
let ph = 0, waveOn = false, waveT = null;
const tickWave = () => { ph += 0.5; bars.forEach((b, i) => b.style.setProperty("--h", (0.15 + 0.75 * Math.abs(Math.sin(i * 0.7 + ph) * Math.cos(i * 0.23 - ph * 0.4))).toFixed(2))); };
tickWave();
if (!reduceMotion()) new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting && !waveOn) { waveOn = true; waveT = setInterval(tickWave, 150); } else if (!e.isIntersecting) { waveOn = false; clearInterval(waveT); } })).observe(wave);

// ---------- numbers from results.json (never typed by hand)
fetch("/data/results.json").then((r) => r.json()).then((r) => {
  const set = (k, v) => { const n = document.querySelector(`[data-k="${k}"]`); if (n && v != null) n.textContent = v; };
  const ev = r.dcase_eval, ma = ev && ev.meal_activity;
  if (ev) set("f1", ev.ours_ch0.macro_f1.value.toFixed(1));
  if (ma) { set("caught", Math.round(ma.caught.value) + "%"); set("fa", ma.false_alarm_rate.value.toFixed(1) + "%"); }
  const ol = r.offlist && { value: r.offlist.confident_wrong };
  if (ol && ol.value != null) set("ns", ol.value.toFixed(1) + "%");
}).catch(() => {});

// ---------- returning visitors get a shortcut to their home
const mine = Object.values(homes()).sort((a, b) => b.saved - a.saved)[0];
if (mine) { const a = $("#nav-home"); a.hidden = false; a.href = mine.familyKey ? "/family" : "/kitchen"; a.textContent = mine.familyKey ? `${mine.parent || "My"}'s kitchen` : "Kitchen screen"; }

// ---------- sections unfold once
const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("seen"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -10% 0px" });
document.querySelectorAll(".sec, .numbers").forEach((s) => io.observe(s));
