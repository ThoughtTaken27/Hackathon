// Kettle landing (dark): a live sample day in the hero panel, interactive steps, both real screens, numbers from results.json.
import { DISPLAY, COLOUR, KIND_NAMES, clock, rawLabel } from "./core.js";
import { $, el, setText, dayBar, legend, readout, rulesList, homes, reduceMotion } from "./ui.js";
import { play } from "./sample.js";
import { place } from "./people.js";
import { words, scrub, ticker, progress, onScrollFrame } from "./fx.js";

const RM = reduceMotion();
const NAMES = { parent: "your parent", caregiver: "You" };      // the landing names nobody: any parent, any family

// ---------- nav frosts once you scroll
const nav = $("#nav");
const onScroll = () => nav.classList.toggle("solid", scrollY > 24);
addEventListener("scroll", onScroll, { passive: true }); onScroll();
const mine = Object.values(homes()).sort((a, b) => b.saved - a.saved)[0];
if (mine) { const a = $("#nav-home"); a.href = mine.familyKey ? "/family" : "/kitchen"; a.textContent = mine.familyKey ? place({ parent: mine.parent, relation: mine.relation }, mine.room, "family") : "Room screen"; }

// ---------- invented-example switcher: only changes the title text
document.querySelectorAll(".lp-sw").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".lp-sw").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  $("#lp-title").textContent = `${place({ parent: b.dataset.n, relation: b.dataset.r }, { type: b.dataset.t })}, today`;
}));

// ---------- hero panel: what Kettle heard (the device in the room) beside what the family sees
const heardList = $("#lp-heard"), steps = [...document.querySelectorAll(".lp-steps span")];
const heroRo = readout($("#lp-ro"));
const heroBar = dayBar($("#lp-bar"), { onSelect: (b) => heroRo(b) });
heroRo.bind(heroBar);
let heard = [], stepT = [];
function runSteps() {
  stepT.forEach(clearTimeout); stepT = [];
  steps.forEach((s) => s.classList.remove("done", "now"));
  steps.forEach((s, i) => stepT.push(setTimeout(() => { steps.forEach((x, j) => { x.classList.toggle("done", j < i); x.classList.toggle("now", j === i); }); }, i * (RM ? 0 : 160))));
  stepT.push(setTimeout(() => steps.forEach((x) => { x.classList.add("done"); x.classList.remove("now"); }), RM ? 0 : 760));
}
// One row of "What Kettle heard": time, colour, label, the named everyday sound (the same allow-list the family sees), confidence.
function heardRow(x, t) {
  const lab = rawLabel(x, 0.66), ns = lab === "not_sure";       // the same rule the day bar uses
  const name = ns ? "Not sure" : lab === "talk_or_tv" ? "Talking / TV" : DISPLAY[lab];
  const sound = (x.kinds || []).map((k) => KIND_NAMES[k]).filter(Boolean)[0] || "";
  return el("li", { class: (ns ? "ns " : "") + "enter", "data-k": String(x.end) },
    el("span", { class: "t num", text: clock(x.end, t.tz_offset) }),
    el("span", { class: "sw", style: `background:var(${COLOUR[lab] || COLOUR[x.label]})${ns ? ";opacity:.35" : ""}` }),
    el("span", { class: "lab" }, name, el("small", { text: sound })),
    el("span", { class: "conf num" }, el("i", {}, el("b", { style: `--p:${x.conf}` })), x.conf.toFixed(2)));
}
function heroFrame(t) {
  $("#lp-clock").textContent = t.now_text;
  const e = t.last_event;
  if (t.sample.i === 1) { heard = []; heardList.textContent = ""; }            // the sample day starts again
  if (e) {
    heard.unshift(e); heard = heard.slice(0, 6);
    // FLIP: rows keep their element, so the list slides down by one row instead of being redrawn
    const before = new Map([...heardList.children].map((n) => [n.dataset.k, n.getBoundingClientRect().top]));
    const keep = new Set(heard.map((x) => String(x.end)));
    for (const n of [...heardList.children]) if (!keep.has(n.dataset.k)) n.remove(); else n.classList.remove("enter");
    heard.forEach((x, i) => {
      const li = heardList.querySelector(`[data-k="${x.end}"]`) || heardRow(x, t);
      if (heardList.children[i] !== li) heardList.insertBefore(li, heardList.children[i] || null);
    });
    if (!RM) for (const n of heardList.children) {
      const b = before.get(n.dataset.k);
      const d = b == null ? 0 : b - n.getBoundingClientRect().top;
      if (d) n.animate([{ transform: `translateY(${d}px)` }, { transform: "none" }], { duration: 480, easing: "cubic-bezier(.22,1,.36,1)" });
    }
    runSteps();
  }
  setText($("#lp-sum"), t.summary || "Listening. Nothing named yet.");
  $("#lp-count").textContent = `${t.sample.i} of ${t.sample.n} labels`;
  heroBar.render(t);
  if (!heroBar.selected()) heroRo(null, t.blocks.length > 0);
  rulesList($("#lp-rules"), t.rules);
}
let heroPlayer = null;
const startHero = async () => { heard = []; heroPlayer = await play("usual", heroFrame, { seconds: RM ? 0.5 : 46, loop: true, names: NAMES }); };
new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting && !heroPlayer) startHero(); else if (!x.isIntersecting && heroPlayer) { heroPlayer.stop(); heroPlayer = null; } }), { threshold: 0.2 }).observe($(".lx-panel"));

// ---------- how it works: four steps, auto-advancing, each with its own screen
const flowUI = $("#flow-ui"), accs = [...document.querySelectorAll(".acc")], accBox = $(".lx-acc");
const STEP_MS = 6500;
let cur = 0, timer = null, flowBar = null;
const meter = () => el("span", { class: "su-meter", "aria-hidden": "true" }, el("i"), el("i"), el("i"), el("i"), el("i"));
const views = [
  () => [el("p", { class: "su-k", text: "Your phone · Step 3 of 3" }), el("p", { class: "su-h", text: "Now connect the room device" }),
    el("p", { class: "su-p", text: "On the room device, open Kettle and type:" }), el("p", { class: "su-code num", html: "K7P<span> </span>4QX" }),
    el("p", { class: "su-p", text: "The code works for 48 hours." })],
  () => [el("p", { class: "su-k", text: "The room device" }), el("p", { class: "su-h", text: "This device listens for the sounds of the room." }),
    el("p", { class: "su-p", text: "It only notes the kind of sound, like dishes or TV. It keeps no recordings and no words. You can pause it or turn it off any time." }),
    el("div", {}, el("span", { class: "su-btn", text: "Yes, my family can see this" }), el("span", { class: "su-btn ghost", text: "Not now" }))],
  () => [el("p", { class: "su-k" }, el("i"), "The room device, listening"), el("p", { class: "su-h", text: "Listening for the sounds of the room" }),
    el("span", { class: "su-chip" }, "Sounds like cooking", meter()),
    el("div", { class: "su-list" }, el("p", {}, el("span", { text: "Sound, 10 seconds" }), el("b", { text: "dropped" })), el("p", {}, el("span", { text: "Label sent to the family" }), el("b", { text: "Cooking, 8:05 AM" })))],
  () => { const box = el("div"); const holder = [el("p", { class: "su-k", text: "Your phone" }), el("p", { class: "su-h", text: "The kitchen today" }),
    el("p", { class: "su-p", id: "su-sum", text: "So far today: cooking around 8:05 AM, eating around 8:30 AM and talking / TV from about 9:30 AM." }), box, el("div", { class: "lp-rules", id: "su-rules", style: "grid-template-columns:1fr" })];
    flowBar = dayBar(box); return holder; },
];
let flowFrames = null;
function show(i, user = false) {
  cur = i;
  accs.forEach((a, j) => { a.setAttribute("aria-selected", String(j === i)); a.style.setProperty("--dur", `${STEP_MS}ms`); const p = a.querySelector(".acc-p i"); p.style.animation = "none"; void p.offsetWidth; p.style.animation = ""; });
  flowUI.textContent = ""; flowUI.append(...views[i]());
  flowUI.classList.remove("swap"); void flowUI.offsetWidth; flowUI.classList.add("swap");
  if (flowFrames) { flowFrames.stop(); flowFrames = null; }
  if (i === 3) play("usual", (t) => { flowBar && flowBar.render(t); const s = $("#su-sum"); if (s) s.textContent = t.summary; const r = $("#su-rules"); if (r) rulesList(r, t.rules); }, { seconds: 4, names: NAMES }).then((p) => (flowFrames = p));
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
K.append(el("div", { class: "kitchen k-mini" },
  el("div", { class: "k-status", "data-state": "listening" }, el("span", { class: "dot" }), el("div", {},
    el("h1", { class: "k-head", text: "Listening for the sounds of the room" }), el("p", { class: "k-body", text: "The family sees the kinds of sounds, not recordings or words." }))),
  el("div", { class: "chip big" }, el("span", { class: "txt", id: "k-chip", text: "Waiting for the first sound…" })),
  el("div", { class: "k-controls" }, el("span", { class: "btn kbtn primary pause", text: "Pause" }), el("span", { class: "btn kbtn", text: "Turn it off" })),
  el("div", { id: "k-bar" })));
// The phone: the real family view's parts (same classes, same readout, same grouped checks), at phone size.
F.append(el("div", { class: "f-mini fam" },
  el("div", { class: "notch" }), el("div", { class: "sbar" }, el("span", { class: "num", id: "f-clock", text: "9:41" }), el("span", { text: "●●●" })),
  el("header", { class: "fam-head" },
    el("p", { class: "fam-date num", id: "f-date", text: "Today" }),
    el("h1", { class: "fam-title" }, "Your parent's kitchen ", el("span", { class: "dim", text: "today" })),
    el("p", { class: "hb", "data-state": "listening" }, el("span", { class: "dot" }), el("span", { class: "text", text: "Listening · last heard just now" }))),
  el("p", { class: "fam-summary summary", id: "f-sum" }),
  el("section", { class: "day-card" }, el("div", { id: "f-ro" }), el("div", { id: "f-bar" })),
  el("div", { class: "rules", id: "f-rules" })));
const fRo = readout($("#f-ro"));
const kBar = dayBar($("#k-bar"), { big: true }), fBar = dayBar($("#f-bar"), { onSelect: (b) => fRo(b) }), fLegend = legend($("#f-bar"));
fRo.bind(fBar);
let stage = null, stageOn = false;
function stageFrame(t) {
  setText($("#k-chip"), t.chip || "Waiting for the first sound…");
  setText($("#f-sum"), t.summary || "Nothing heard yet today.");
  $("#f-clock").textContent = t.now_text.replace(/ (AM|PM)$/, "");
  setText($("#f-date"), `${t.date_text} · ${t.now_text}`);
  kBar.render(t); fBar.render(t); fLegend(t); rulesList($("#f-rules"), t.rules);
  if (!fBar.selected()) fRo(null, t.blocks.length > 0);
}
async function startStage(sid) {
  if (stage) stage.stop();
  document.querySelectorAll(".lx-seg [data-sid]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.sid === sid)));
  moveInd();
  stage = await play(sid, stageFrame, { seconds: RM ? 0.5 : 18, loop: true, names: NAMES });
}
document.querySelectorAll(".lx-seg [data-sid]").forEach((b) => b.addEventListener("click", () => { startStage(b.dataset.sid); requestAnimationFrame(centerSeg); }));
new IntersectionObserver((es) => es.forEach((x) => {
  if (x.isIntersecting && !stageOn) { stageOn = true; startStage("nobreakfast"); }
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
const tickSeen = new WeakSet();
const runTick = (n) => { if (n.dataset.to && tickSeen.has(n) && !n.dataset.ran) { n.dataset.ran = "1"; ticker(n, n.dataset.to); } };
const tickIO = new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting) { tickSeen.add(x.target); runTick(x.target); tickIO.unobserve(x.target); } }), { rootMargin: "0px 0px -12% 0px" });
document.querySelectorAll("[data-k]").forEach((n) => tickIO.observe(n));
fetch("/data/results.json").then((r) => r.json()).then((r) => {
  const set = (k, v) => document.querySelectorAll(`[data-k="${k}"]`).forEach((n) => { if (v != null) { n.textContent = v; n.dataset.to = v; runTick(n); } });
  const ev = r.dcase_eval, ma = ev && ev.meal_activity;
  if (ev) set("f1", ev.ours_ch0.macro_f1.value.toFixed(1));
  if (ma) { set("caught", String(Math.round(ma.caught.value))); set("fa", ma.false_alarm_rate.value.toFixed(1)); }
  if (r.offlist && r.offlist.confident_wrong != null) set("ns", Number(r.offlist.confident_wrong.value ?? r.offlist.confident_wrong).toFixed(1));
  const c = r.privacy_check && r.privacy_check.checks;
  if (c) set("audio", String((c.new_or_changed_audio_extension_files || []).length + (c.new_or_changed_files_with_audio_magic_bytes || []).length));
}).catch(() => {});

// ---------- sections unfold once
const io = new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting) { x.target.classList.add("seen"); io.unobserve(x.target); } }), { rootMargin: "0px 0px -8% 0px" });
document.querySelectorAll(".lx-sec, .lx-why").forEach((s) => io.observe(s));


// =================================================================== level 2: scroll-driven motion (js/fx.js)
// hero headline: words blur in one after another, the page's one orchestrated moment
const h1 = $("#hero-h"); h1.classList.remove("rise"); h1.classList.add("words-in"); words(h1);
const fin = $("#fin-h"); words(fin);
new IntersectionObserver((es, o) => es.forEach((x) => { if (x.isIntersecting) { fin.classList.add("words-in"); o.disconnect(); } }), { threshold: 0.6 }).observe(fin);

// hero: the sky drifts slower than the page, the copy lifts away, the live panel tilts up to meet you
const heroBg = $(".lx-hero-bg"), heroIn = $(".lx-hero-in"), panelWrap = $(".lx-panel-wrap");
const stageIn = $(".stage-in"), finalSec = $(".lx-final");
const why = scrub($(".lx-why-text .lx-scrub"));
onScrollFrame(() => {
  if (RM) return;
  const y = scrollY;
  if (y < 1400) {
    heroBg.style.transform = `translate3d(0, ${(y * 0.38).toFixed(1)}px, 0)`;
    heroBg.style.opacity = (1 - Math.min(1, Math.max(0, (y - 380) / 520))).toFixed(3);   // the sky is gone before it can drift under the next section
    const f = Math.min(1, y / 520);
    heroIn.style.opacity = (1 - f).toFixed(3);
    heroIn.style.transform = `translate3d(0, ${(-y * 0.12).toFixed(1)}px, 0)`;
    const p = progress(panelWrap, 1.0, 0.25);
    panelWrap.style.transform = `perspective(1800px) rotateX(${((1 - p) * 14).toFixed(2)}deg) scale(${(0.94 + p * 0.06).toFixed(4)})`;
  }
  why();
  const ps = progress(stageIn, 1.05, 0.35);
  stageIn.style.transform = `perspective(2000px) rotateX(${((1 - ps) * 9).toFixed(2)}deg) translate3d(0, ${((1 - ps) * 40).toFixed(1)}px, 0)`;
  const pf = progress(finalSec, 1.2, -0.2);
  finalSec.style.setProperty("--fy", `${((pf - 0.5) * -60).toFixed(1)}px`);
});

// nav: the section you're reading lights up
const spyLinks = [...document.querySelectorAll('.lx-links a[href^="#"]')];
const spy = new IntersectionObserver((es) => es.forEach((x) => { if (x.isIntersecting) spyLinks.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + x.target.id)); }), { rootMargin: "-45% 0px -50% 0px" });
spyLinks.forEach((a) => { const t = document.querySelector(a.getAttribute("href")); if (t) spy.observe(t); });

// built-on row: an endless, slow marquee (Magic UI "marquee": 40 s per loop, pauses on hover, masked edges)
const mq = $(".lx-built ul");
if (mq && !RM) { const track = el("div", { class: "mq-track" }); const a = mq.cloneNode(true), b = mq.cloneNode(true); b.setAttribute("aria-hidden", "true"); track.append(a, b); mq.replaceWith(track); }

// privacy cards: a soft light follows the pointer along the hairline (fine pointers only)
if (matchMedia("(hover: hover) and (pointer: fine)").matches) document.querySelectorAll(".lx-card").forEach((c) => c.addEventListener("pointermove", (e) => {
  const r = c.getBoundingClientRect(); c.style.setProperty("--mx", `${e.clientX - r.left}px`); c.style.setProperty("--my", `${e.clientY - r.top}px`);
}));

// FAQ: answers unfold (height via grid rows) instead of snapping open
document.querySelectorAll(".lx-faq details").forEach((d) => {
  const sum = d.querySelector("summary"), body = d.querySelector("p");
  const wrap = el("div", { class: "faq-b" }); body.replaceWith(wrap); const inner = el("div"); inner.append(body); wrap.append(inner);
  sum.addEventListener("click", (e) => {
    e.preventDefault();
    if (d.open) { d.classList.remove("shown"); setTimeout(() => { if (!d.classList.contains("shown")) d.open = false; }, RM ? 0 : 260); }
    else { d.open = true; requestAnimationFrame(() => requestAnimationFrame(() => d.classList.add("shown"))); }
  });
});

// sample-day switch: the sliding pill
const seg = $(".lx-seg"), ind = el("i", { class: "ind", "aria-hidden": "true" }); seg.prepend(ind); seg.classList.add("has-ind");
function moveInd() {   // size and place the pill from the chosen button itself, so it stays centred at any height and on any row
  const b = seg.querySelector('[aria-pressed="true"]'); if (!b) return;
  ind.style.width = b.offsetWidth + "px"; ind.style.height = b.offsetHeight + "px";
  ind.style.transform = `translate(${b.offsetLeft}px, ${b.offsetTop}px)`;
}
function centerSeg() {                                   // swipe strip on phones: bring the chosen day to the middle
  const b = seg.querySelector('[aria-pressed="true"]');
  if (b && seg.scrollWidth > seg.clientWidth + 2) seg.scrollTo({ left: b.offsetLeft - (seg.clientWidth - b.offsetWidth) / 2, behavior: RM ? "auto" : "smooth" });
}
const segRo = new ResizeObserver(moveInd); segRo.observe(seg); seg.querySelectorAll("button").forEach((b) => segRo.observe(b));
addEventListener("resize", () => requestAnimationFrame(moveInd)); moveInd();
