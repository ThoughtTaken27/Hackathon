// Shared UI for Kettle web: DOM helpers, the API client (retries, offline queue), saved homes, the day bar,
// its legend and the evidence card. Plain ES modules, no build step.
import { COLOUR, DISPLAY } from "./core.js";

export const $ = (s, r = document) => r.querySelector(s);
export const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
export function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) e.append(kid);
  return e;
}
/** Crossfade text only when it changes. */
export function setText(node, text) {
  if (node.textContent === text) return;
  if (reduceMotion() || !node.textContent) { node.textContent = text; return; }
  node.animate([{ opacity: 1, filter: "none" }, { opacity: 0, transform: "translateY(-3px)", filter: "blur(3px)" }], { duration: 180, easing: "cubic-bezier(.22,1,.36,1)" })
    .onfinish = () => { node.textContent = text; node.animate([{ opacity: 0, transform: "translateY(3px)", filter: "blur(3px)" }, { opacity: 1, transform: "none", filter: "none" }], { duration: 280, easing: "cubic-bezier(.22,1,.36,1)" }); };
}

// ---------------------------------------------------------------- saved homes (this device only)
const HOMES = "kettle.homes.v1";
export function homes() { try { return JSON.parse(localStorage.getItem(HOMES)) || {}; } catch { return {}; } }
export function saveHome(id, patch) { const h = homes(); h[id] = { ...(h[id] || {}), ...patch, id, saved: Date.now() }; try { localStorage.setItem(HOMES, JSON.stringify(h)); } catch {} return h[id]; }
export function forgetHome(id) { const h = homes(); delete h[id]; try { localStorage.setItem(HOMES, JSON.stringify(h)); } catch {} }
/** "#k=<id>.<key>" or "#f=<id>.<key>" -> {id, key, role}; saved so the bare page works next time. */
export function linkFromHash(role) {
  const m = location.hash.match(/[#&]([kf])=([a-z0-9]{6,24})\.([a-z0-9]{16,64})/);
  if (m) {
    const r = m[1] === "k" ? "kitchen" : "family";
    saveHome(m[2], { [r + "Key"]: m[3] });
    history.replaceState(null, "", location.pathname);          // keep the key out of the address bar and history
    if (r === role) return { id: m[2], key: m[3], role: r };
  }
  const list = Object.values(homes()).filter((h) => h[role + "Key"]).sort((a, b) => b.saved - a.saved);
  return list.length ? { id: list[0].id, key: list[0][role + "Key"], role } : null;
}
export const linkFor = (role, id, key) => `${location.origin}/${role === "kitchen" ? "kitchen" : "family"}#${role === "kitchen" ? "k" : "f"}=${id}.${key}`;

// ---------------------------------------------------------------- API client: retries with backoff, shared clock
let skew = 0;                                                       // server clock - this device's clock (s)
export const now = () => Date.now() / 1000 + skew;
export async function api(path, { method = "GET", body, key, retries = 3 } = {}) {
  let wait = 600;
  for (let i = 0; ; i++) {
    try {
      const r = await fetch(path, { method, headers: { "content-type": "application/json", ...(key ? { authorization: `Bearer ${key}` } : {}) },
        body: body === undefined ? undefined : JSON.stringify(body), cache: "no-store" });
      const j = await r.json().catch(() => ({}));
      if (j.now) skew = j.now - Date.now() / 1000;
      if (!r.ok) { const e = new Error(j.error || `HTTP ${r.status}`); e.status = r.status; e.body = j; throw e; }
      return j;
    } catch (e) {
      if ((e.status && e.status < 500 && e.status !== 429) || i >= retries) throw e;
      await new Promise((ok) => setTimeout(ok, wait + Math.random() * 300)); wait *= 2;
    }
  }
}
export const online = () => navigator.onLine !== false;

// ---------------------------------------------------------------- day bar
function hourLabel(h) { return h === 0 || h === 24 ? "12 AM" : h === 12 ? "12 PM" : h < 12 ? `${h} AM` : `${h - 12} PM`; }
const blockKey = (b) => String(Math.round(b.start));
const blockClass = (b) => ["blk", b.state, b.state === "activity" && b.how_sure === "medium" ? "medium" : ""].join(" ").trim();

export function dayBar(root, { big = false, onSelect = null, from = 6 } = {}) {
  root.classList.add("daybar");
  const labels = el("div", { class: "labels", "aria-hidden": "true" });
  const hit = el("div", { class: "bar-hit" });
  const bar = el("div", { class: "bar" });
  const nowTick = el("div", { class: "now-tick", "aria-hidden": "true" });
  const ticks = el("div", { class: "ticks", "aria-hidden": "true" });
  const list = el("ol", { class: "sr" });
  const empty = el("div", { class: "empty-day", hidden: true });
  hit.append(bar, nowTick, empty);
  root.append(labels, hit, ticks, list);
  const nodes = new Map();
  let first = true, selected = null, last = [], lastT = null;
  // Real text widths (the old guess of 7.4 px a letter overlapped labels on phones, where the kitchen text is larger).
  const cv = document.createElement("canvas").getContext("2d");
  const textW = (node, text) => { const cs = getComputedStyle(node); cv.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`; return cv.measureText(text).width; };
  // Redraw when the bar's width changes (rotation, sheet opening, first layout): labels and ticks depend on it.
  let lastW = 0;
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(() => { const w = bar.clientWidth; if (lastT && w && Math.abs(w - lastW) > 1) render(lastT); }).observe(bar);
  // From the first hour Kettle heard anything today (6 AM before that), to a little after now; at least 3 hours.
  function range(t) {
    const first = t.blocks.length ? Math.min(...t.blocks.map((b) => b.start)) : t.day0 + from * 3600;
    let startH = Math.max(0, Math.floor((first - t.day0) / 3600));
    const nowH = (t.now - t.day0) / 3600;
    const endH = Math.min(24, Math.max(startH + 3, Math.ceil(nowH + 1)));
    if (endH - startH < 3) startH = Math.max(0, endH - 3);
    return [t.day0 + startH * 3600, t.day0 + endH * 3600];
  }
  function render(t) {
    last = t.blocks; lastT = t;
    empty.hidden = t.blocks.length > 0;
    empty.textContent = t.heartbeat.state === "never" ? `The day appears here once ${t.names.parent} turns Kettle on.` : "Nothing heard yet today.";
    const [a, z] = range(t), span = z - a;
    const pct = (x) => `${((100 * (Math.max(a, Math.min(z, x)) - a)) / span).toFixed(3)}%`;
    const w = (b) => `${Math.max(0.25, (100 * (Math.min(z, b.end) - Math.max(a, b.start))) / span).toFixed(3)}%`;
    const seen = new Set();
    for (const b of t.blocks) {
      const k = blockKey(b); seen.add(k);
      let n = nodes.get(k);
      if (!n) {
        n = el("button", { type: "button" });
        n.addEventListener("click", () => select(k));
        if (!first) n.classList.add("settle");
        bar.append(n); nodes.set(k, n);
      }
      n.className = blockClass(b) + (n.classList.contains("settle") ? " settle" : "") + (selected === k ? " selected" : "");
      if (b.activity) n.style.setProperty("--c", `var(${COLOUR[b.activity]})`);
      n.style.left = pct(b.start); n.style.width = w(b);
      n.setAttribute("aria-label", `${b.label}, ${b.range}`);
    }
    for (const [k, n] of nodes) if (!seen.has(k)) { n.remove(); nodes.delete(k); }
    nowTick.style.left = pct(t.now);
    nowTick.hidden = t.now < a || t.now > z || !t.blocks.length;
    const width = bar.clientWidth;
    lastW = width;
    if (!width) { labels.textContent = ""; ticks.textContent = ""; return; }           // not laid out yet: the observer redraws
    const prev = new Set([...labels.children].map((s) => s.dataset.key));
    labels.textContent = "";
    let right = -Infinity;
    for (const b of t.blocks.filter((x) => x.state !== "empty")) {
      const x = (width * (Math.max(a, b.start) - a)) / span, bw = (width * (Math.min(z, b.end) - Math.max(a, b.start))) / span;
      const tw = textW(labels, b.label) + 2;
      if (x < right + 10 || bw < Math.min(tw, 44) || x + tw > width + 2) continue;
      const s = el("span", { text: b.label, style: `left:${((100 * x) / width).toFixed(3)}%` });
      s.dataset.key = blockKey(b);
      if (!first && !prev.has(s.dataset.key)) s.classList.add("fade");
      labels.append(s); right = x + tw;
    }
    ticks.textContent = "";
    // as many hour labels as fit with a clear gap: the widest label ("10 AM") plus 14 px between neighbours
    const spanH = span / 3600, room = textW(ticks, "10 AM") + 14, fit = Math.max(2, Math.floor(width / room));
    const every = [1, 2, 3, 4, 6, 12].find((e) => spanH / e <= fit) || 12;
    const h0 = Math.round((a - t.day0) / 3600), hEnd = Math.round((z - t.day0) / 3600);
    for (let h = h0; h <= hEnd; h++) {
      if ((h - h0) % every !== 0) continue;
      if (h !== hEnd && hEnd - h < every && (hEnd - h0) % every === 0) continue;     // never crowd the last label
      ticks.append(el("span", { text: hourLabel(h), style: `left:${pct(t.day0 + h * 3600)}` }));
    }
    list.textContent = "";
    for (const b of t.blocks) list.append(el("li", { text: `${b.label}, ${b.range}` }));
    first = false;
    if (selected && !nodes.has(selected)) select(null);
    else if (selected && onSelect) onSelect(last.find((b) => blockKey(b) === selected) || null);
  }
  function select(k) {
    selected = selected === k ? null : k;
    for (const [kk, n] of nodes) n.classList.toggle("selected", kk === selected);
    if (onSelect) onSelect(last.find((b) => blockKey(b) === selected) || null);
  }
  return { render, select };
}

export function legend(root) {
  const lg = el("div", { class: "legend", "aria-hidden": "true" });
  root.append(lg);
  let key = "";
  return (t) => {
    const acts = [...new Set(t.blocks.filter((b) => b.state === "activity").map((b) => b.activity))];
    const states = new Set(t.blocks.map((b) => b.state));
    const k = acts.join() + [...states].join();
    if (k === key) return; key = k;
    lg.textContent = "";
    for (const a of acts) lg.append(el("span", {}, el("i", { style: `background:var(${COLOUR[a]})` }), DISPLAY[a]));
    for (const [st, name] of [["talk_or_tv", "Talking or TV"], ["not_sure", "Not sure"], ["not_listening", "Not listening"], ["paused", "Paused"]])
      if (states.has(st)) lg.append(el("span", {}, el("i", { class: `blk ${st}`, style: "position:static;display:inline-block" }), name));
    if (states.has("empty")) lg.append(el("span", {}, el("i", { style: "height:2px;background:var(--act-empty);vertical-align:3px" }), "Quiet"));
    lg.hidden = !lg.children.length;
  };
}

function soundsSentence(sounds) {
  if (!sounds || !sounds.length) return "";
  const n = sounds.map((s) => s.name.toLowerCase().split(",")[0]);
  return n.length === 1 ? `Sounds Kettle heard: mostly ${n[0]}.` : `Sounds Kettle heard: mostly ${n[0]}, some ${n.slice(1).join(" and ")}.`;
}
export function evidenceCard(b) {
  if (!b) return null;
  const sw = el("span", { class: "sw" });
  if (b.activity) sw.style.background = `var(${COLOUR[b.activity]})`; else sw.className = `sw blk ${b.state}`;
  const parts = b.card.split(" · ");
  const card = el("div", { class: "evidence", role: "region", "aria-label": `${b.label} details` },
    el("p", { class: "head" }, sw, el("span", { text: parts[0] }), el("span", { class: "muted t", text: parts[1] || "" })));
  const rest = parts.slice(2).join(" · ");
  if (rest) card.append(el("p", { text: rest }));
  if (b.sounds && b.sounds.length && ["activity", "empty", "not_sure", "talk_or_tv"].includes(b.state)) {
    card.append(el("p", { text: soundsSentence(b.sounds) }));
    const grid = el("div", { class: "scores" });
    for (const s of b.sounds) grid.append(el("span", { text: s.name }), el("span", { class: "num", text: s.score.toFixed(2) }));
    card.append(el("details", {}, el("summary", { text: "Details" }), grid,
      el("p", { class: "why", text: "Scores from the sound model's own list of everyday sounds. Kettle shows only kitchen and living-room sounds, never words or who is speaking." })));
  }
  card.append(el("p", { class: "why", text: "Kettle labels 10-second stretches of sound. It keeps no recording." }));
  return card;
}

export function rulesList(root, rules) {
  root.textContent = "";
  for (const r of rules) {
    root.append(el("div", { class: "rule", "data-state": r.state },
      el("p", { class: "name", text: r.title }), el("p", { class: "state", text: r.detail }), r.note ? el("p", { class: "note", text: r.note }) : null));
  }
}

/** A QR code as an SVG element (qrcode-generator, MIT). */
export async function qr(text, size = 176) {
  if (!window.qrcode) await new Promise((ok, bad) => { const s = el("script", { src: "/vendor/qrcode.js" }); s.onload = ok; s.onerror = bad; document.head.append(s); });
  const q = window.qrcode(0, "M"); q.addData(text); q.make();
  const n = q.getModuleCount(), cell = size / (n + 8);
  let path = "";
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) path += `M${(c + 4) * cell} ${(r + 4) * cell}h${cell}v${cell}h-${cell}z`;
  const wrap = el("div", { class: "qr", "aria-label": "QR code" });
  wrap.innerHTML = `<svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" role="img"><rect width="${size}" height="${size}" rx="14" fill="#fff"/><path d="${path}" fill="#171717"/></svg>`;
  return wrap;
}

export function toast(text) {
  let t = $(".toast");
  if (!t) { t = el("div", { class: "toast", role: "status", "aria-live": "polite" }); document.body.append(t); }
  t.textContent = text; t.classList.remove("show"); void t.offsetWidth; t.classList.add("show");
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2600);
}
export async function copy(text) { try { await navigator.clipboard.writeText(text); toast("Copied"); } catch { toast("Couldn't copy. Select the text instead."); } }

// ---------------------------------------------------------------- six-box pairing code
// One real <input> (so paste, autofill and screen readers work) drawn as six boxes. A wrong code shakes the row:
// timings from transitions.dev "Error State Shake" (MIT): 6 px, 4 px overshoot, 80/60/80/60 ms, cubic-bezier(0.22, 1, 0.36, 1).
export function codeInput({ onComplete, label = "Six-letter code" } = {}) {
  const boxes = Array.from({ length: 6 }, (_, i) => el("span", { class: "cbox" + (i === 2 ? " split" : "") }));
  const inp = el("input", { class: "code-real", inputmode: "text", maxlength: 7, autocomplete: "one-time-code", autocapitalize: "characters",
    spellcheck: "false", "aria-label": label, enterkeyhint: "go" });
  const row = el("div", { class: "code6" }, ...boxes, inp);
  const clean = () => inp.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6);
  let busy = false, replace = false;                       // one submit at a time: auto-submit on the 6th letter, then Enter/Go, must not POST twice
  const submit = () => { if (busy || clean().length !== 6 || !onComplete) return; busy = true; onComplete(clean()); };
  const paint = () => {
    const v = clean(), focused = document.activeElement === inp;
    boxes.forEach((b, i) => { if (v[i] && b.textContent !== v[i] && i === v.length - 1) { b.classList.remove("pop"); void b.offsetWidth; b.classList.add("pop"); }
      b.textContent = v[i] || ""; b.classList.toggle("cur", focused && i === Math.min(v.length, 5)); b.classList.toggle("on", !!v[i]); });
    row.classList.remove("bad");
  };
  inp.addEventListener("input", () => { inp.value = clean(); paint(); if (inp.value.length === 6) submit(); });
  inp.addEventListener("beforeinput", (e) => { if (replace && e.inputType.startsWith("insert")) { inp.value = ""; replace = false; } });
  inp.addEventListener("focus", paint); inp.addEventListener("blur", paint);
  inp.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  row.addEventListener("click", () => inp.focus());
  return {
    node: row, input: inp, value: clean, focus: () => inp.focus(), submit,
    error() {
      busy = false;
      row.classList.add("bad");
      replace = true;                   // the next letter typed starts a fresh code (no selection handles on phones)
      if (reduceMotion()) return;
      row.animate([{ transform: "translateX(0)" }, { transform: "translateX(-6px)" }, { transform: "translateX(6px)" }, { transform: "translateX(-4px)" }, { transform: "translateX(4px)" }, { transform: "translateX(0)" }],
        { duration: 360, easing: "cubic-bezier(0.22, 1, 0.36, 1)" });
    },
    clear() { inp.value = ""; paint(); },
  };
}
