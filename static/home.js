// Kettle opening page: the hero instrument, live numbers from results/metrics.json, scaled device frames, scroll-in.
const $ = (id) => document.getElementById(id);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// ---------- hero instrument: a staged morning, sound → label → block on the day bar ----------
const SCENES = [
  { t: "7:20 AM", v: "Working (typing)", sure: "how sure: high", seg: 0, now: 10, amp: 0.32, jitter: 0.5 },
  { t: "8:05 AM", v: "Cooking", sure: "how sure: high", seg: 1, now: 43, amp: 0.92, jitter: 0.9 },
  { t: "8:30 AM", v: "Eating", sure: "how sure: medium", seg: 2, now: 50, amp: 0.5, jitter: 0.7 },
  { t: "8:45 AM", v: "Washing up", sure: "how sure: high", seg: 3, now: 56, amp: 0.7, jitter: 0.45 },
  { t: "9:30 AM", v: "TV", sure: "how sure: high", seg: 4, now: 84, amp: 0.55, jitter: 0.25 },
  { t: "10:40 AM", v: "Quiet", sure: "nothing heard", seg: -1, now: 99, amp: 0.05, jitter: 0.6 },
];
const wave = $("wave"), bar = $("ins-bar"), segs = [...bar.querySelectorAll("i")];
const N = 56, bars = [];
for (let i = 0; i < N; i++) { const b = document.createElement("i"); wave.append(b); bars.push(b); }
let scene = SCENES[1], phase = 0, timer = null, waveTimer = null;

function setText(node, text) {
  if (node.textContent === text) return;
  node.textContent = text;
  node.classList.remove("swap"); void node.offsetWidth; node.classList.add("swap");
}
function show(s, animate = true) {
  scene = s;
  setText($("ins-time"), s.t); setText($("ins-v"), s.v); setText($("ins-sure"), s.sure);
  wave.classList.toggle("quiet", s.seg < 0);
  if (s.seg >= 0) segs[s.seg].classList.add("on");
  bar.style.setProperty("--now", s.now + "%");
}
function drawWave() {
  // smooth pseudo-noise around the scene's loudness; a quiet room stays nearly flat
  phase += 0.55;
  for (let i = 0; i < N; i++) {
    const env = 0.55 + 0.45 * Math.sin(i / N * Math.PI);
    const n = 0.5 + 0.5 * Math.sin(i * 0.9 + phase) * Math.cos(i * 0.37 - phase * 0.6);
    const h = Math.max(0.05, Math.min(1, scene.amp * env * (1 - scene.jitter + scene.jitter * (n + Math.random() * 0.35))));
    bars[i].style.setProperty("--h", h.toFixed(3));
  }
}
function runLoop() {
  let k = 0;
  segs.forEach((s) => s.classList.remove("on"));
  const step = () => {
    show(SCENES[k]);
    k++;
    if (k < SCENES.length) timer = setTimeout(step, 2300);
    else timer = setTimeout(runLoop, 3600);   // hold the finished morning, then start again
  };
  step();
}
function startHero() {
  if (reduce) { SCENES.forEach((s) => { if (s.seg >= 0) segs[s.seg].classList.add("on"); }); show(SCENES[1]); drawWave(); return; }
  if (!waveTimer) waveTimer = setInterval(drawWave, 140);
  if (!timer) runLoop();
}
function stopHero() { clearInterval(waveTimer); clearTimeout(timer); waveTimer = null; timer = null; }
const heroIO = new IntersectionObserver((es) => es.forEach((e) => (e.isIntersecting && !document.hidden ? startHero() : stopHero())));
heroIO.observe($("wave"));
document.addEventListener("visibilitychange", () => (document.hidden ? stopHero() : startHero()));

// ---------- numbers: read from results/metrics.json, never typed by hand ----------
(async () => {
  try {
    const r = await (await fetch("/api/results")).json();
    if (r.status !== "ok") return;
    const ev = r.dcase_eval, ma = ev && ev.meal_activity;
    const set = (k, v) => { const n = document.querySelector(`[data-k="${k}"]`); if (n && v != null) n.textContent = v; };
    if (ev) set("f1", ev.ours_ch0.macro_f1.value.toFixed(1));
    if (ma) { set("caught", Math.round(ma.caught.value) + "%"); set("fa", ma.false_alarm_rate.value.toFixed(1) + "%"); }
    const pc = r.privacy_check;
    if (pc && pc.checks) {
      const c = pc.checks;
      const writes = (c.new_or_changed_audio_extension_files || []).length + (c.new_or_changed_files_with_audio_magic_bytes || []).length;
      set("audio", String(writes));
    }
  } catch (e) { /* keep the committed figures */ }
})();

// ---------- sample day on both screens ----------
async function play(btn) {
  btn.disabled = true;
  try {
    const res = await fetch("/api/demo/usual", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!res.ok) throw new Error(String(res.status));
    $("play-note").textContent = "Playing a usual morning on both screens. Watch the day bar fill in.";
    $("screens").scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  } catch (e) {
    $("play-note").textContent = "Only the kitchen laptop can start a sample day. Open this page on the laptop running Kettle.";
  } finally { setTimeout(() => (btn.disabled = false), 1200); }
}
$("play").addEventListener("click", (e) => play(e.currentTarget));
$("play2").addEventListener("click", (e) => play(e.currentTarget));

// ---------- device frames: render the real pages at their native size, scaled to fit ----------
function fit() {
  document.querySelectorAll(".laptop, .phone").forEach((dev) => {
    const w = +dev.dataset.w, h = +dev.dataset.h, glass = dev.querySelector(".glass"), f = glass.querySelector("iframe");
    const s = glass.clientWidth / w;
    f.style.width = w + "px"; f.style.height = h + "px"; f.style.transform = `scale(${s})`;
  });
}
new ResizeObserver(fit).observe(document.body);
fit();

// ---------- sections unfold once as they scroll in ----------
const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("seen"); io.unobserve(e.target); } }),
  { rootMargin: "0px 0px -12% 0px" });
document.querySelectorAll(".sec").forEach((s) => io.observe(s));
