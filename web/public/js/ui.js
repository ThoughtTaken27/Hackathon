// Shared UI for Kettle web: DOM helpers, the API client (retries, offline queue), saved homes, the day bar,
// its legend and the evidence card. Plain ES modules, no build step.
import { COLOUR, DISPLAY } from "./core.js";

// One 3D emoji per thing Kettle can name (Microsoft Fluent Emoji, MIT; static WebP in /img/emoji). Colour stays the
// day bar's key; the emoji sits on a tint of that colour so the two always agree.
export const EMOJI = { cooking: "pot", dishwashing: "sponge", eating: "bowl", watching_tv: "tv", talk_or_tv: "tv",
  social_activity: "speaking", vacuum_cleaner: "broom", working: "keyboard", other: "footprints", kitchen: "teapot",
  absence: "leaf", empty: "leaf", not_sure: "thinking" };   // picked at real size (20 px): each must read at a glance on white
export function emoji(key, cls = "ej-i") {
  const n = EMOJI[key]; if (!n) return null;
  const i = document.createElement("img"); i.className = cls; i.src = `/img/emoji/${n}.webp`; i.alt = ""; i.width = i.height = 48;
  i.decoding = "async"; i.setAttribute("aria-hidden", "true"); return i;
}
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
// Typographic glue for display text: "8:35–8:50 AM" and "10 AM" never split across lines (no-break space before AM/PM,
// word joiners around a range dash). Display only; the strings in data and tests are unchanged.
export const glue = (t) => typeof t !== "string" ? t : t.replace(/(\d) (AM|PM|h|min|s)\b/g, "$1\u00A0$2").replace(/(\d)–(\d)/g, "$1\u2060–\u2060$2");
export function setText(node, text) {
  text = glue(text);
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
/** Seconds since midnight -> "9:42 AM". */
function hourMin(sec) {
  const m = Math.max(0, Math.min(1439, Math.floor(sec / 60))), h = Math.floor(m / 60), mm = String(m % 60).padStart(2, "0");
  return `${h % 12 || 12}:${mm} ${h < 12 ? "AM" : "PM"}`;
}
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
  // Drag to read the day: on a phone the stretches are too thin to tap, so a finger slides along the bar and the stretch
  // under it is selected, with a line and a small label showing what and when. Tapping still works; arrow keys too.
  const scrub = el("div", { class: "scrub", hidden: true, "aria-hidden": "true" }, el("span", { class: "scrub-tip" }));
  hit.append(bar, nowTick, scrub, empty);
  hit.tabIndex = 0;
  hit.setAttribute("role", "slider");
  hit.setAttribute("aria-label", "Drag along the day to see what was happening");
  hit.setAttribute("aria-valuemin", "0"); hit.setAttribute("aria-valuemax", "100");
  root.append(labels, hit, ticks, list);
  if (onSelect) root.append(el("p", { class: "drag-hint" },
    el("span", { class: "touch", text: "Slide a finger along the day to see what was happening and when." }),
    el("span", { class: "mouse", text: "Click or drag along the day to see what was happening and when." })));
  const nodes = new Map();
  let first = true, selected = null, last = [], lastT = null, span0 = null, drag = null, swallowClick = false;
  // Real text widths (the old guess of 7.4 px a letter overlapped labels on phones, where the kitchen text is larger).
  const cv = document.createElement("canvas").getContext("2d");
  const fonts = new Map();              // one style read per node per render, not one per label (each read can force a style recalc)
  const textW = (node, text) => { let f = fonts.get(node); if (!f) { const cs = getComputedStyle(node); f = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`; fonts.set(node, f); } cv.font = f; return cv.measureText(text).width; };
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
    last = t.blocks; lastT = t; fonts.clear();
    empty.hidden = t.blocks.length > 0;
    empty.textContent = t.heartbeat.state === "never" ? `The day appears here once ${t.names.parentMid || t.names.parent} turns Kettle on.` : "Nothing heard yet today.";
    const [a, z] = range(t), span = z - a;
    span0 = [a, z];
    const pct = (x) => `${((100 * (Math.max(a, Math.min(z, x)) - a)) / span).toFixed(3)}%`;
    const w = (b) => `${Math.max(0.25, (100 * (Math.min(z, b.end) - Math.max(a, b.start))) / span).toFixed(3)}%`;
    const seen = new Set();
    for (const b of t.blocks) {
      const k = blockKey(b); seen.add(k);
      let n = nodes.get(k);
      if (!n) {
        n = el("button", { type: "button" });
        n.addEventListener("click", (e) => { if (swallowClick) { swallowClick = false; e.preventDefault(); return; } select(k); });
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
    const showLabels = labels.offsetParent !== null || getComputedStyle(labels).display !== "none";
    for (const b of showLabels ? t.blocks.filter((x) => x.state !== "empty") : []) {
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
      // the last label is right-aligned, so the one before it needs a full label's width plus a gap clear of the end
      if (h !== hEnd && (hEnd - h) * 3600 / span * width < room * 1.5) continue;
      ticks.append(el("span", { text: hourLabel(h), style: `left:${pct(t.day0 + h * 3600)}` }));
    }
    list.textContent = "";
    for (const b of t.blocks) list.append(el("li", { text: `${b.label}, ${b.range}` }));
    first = false;
    if (selected && !nodes.has(selected)) select(null);
    else if (selected && onSelect) onSelect(last.find((b) => blockKey(b) === selected) || null);
  }
  function select(k) { setSelected(selected === k ? null : k); if (!selected) scrub.hidden = true; }
  function setSelected(k) {
    if (k === selected) return;
    selected = k;
    for (const [kk, n] of nodes) n.classList.toggle("selected", kk === selected);
    if (onSelect) onSelect(last.find((b) => blockKey(b) === selected) || null);
  }
  // The stretch at time x (seconds): the one containing it, else the nearest within 3% of the bar (a thin stretch is easy to hit).
  function blockAt(x) {
    const [a, z] = span0, tol = 0.03 * (z - a);
    let best = null, bd = Infinity;
    for (const b of last) {
      if (b.state === "empty" && b.end - b.start < 60) continue;
      const d = x < b.start ? b.start - x : x > b.end ? x - b.end : 0;
      if (d < bd || (d === bd && d === 0 && b.state !== "empty")) { best = b; bd = d; }
    }
    return best && bd <= tol ? best : null;
  }
  function scrubTo(clientX) {
    if (!span0 || !last.length) return;
    const r = bar.getBoundingClientRect();
    const f = Math.max(0, Math.min(1, (clientX - r.left) / Math.max(1, r.width)));
    const [a, z] = span0, x = a + f * (z - a);
    const b = blockAt(x);
    scrub.hidden = false;
    scrub.style.left = `${(100 * f).toFixed(3)}%`;
    const tip = scrub.firstChild;
    tip.textContent = b ? `${hourMin(x - lastT.day0)} · ${b.label}` : hourMin(x - lastT.day0);
    // keep the label inside the bar
    const tw = tip.offsetWidth, px = f * r.width;
    tip.style.transform = `translateX(${Math.round(Math.max(-px, Math.min(r.width - px - tw, -tw / 2)))}px)`;
    hit.setAttribute("aria-valuetext", tip.textContent);
    const nk = b ? blockKey(b) : null;
    if (drag && drag.moved && nk && nk !== selected && navigator.vibrate) { try { navigator.vibrate(6); } catch {} }   // a light tick per stretch (Android)
    setSelected(nk);
  }
  hit.addEventListener("pointerdown", (e) => {
    if (e.button > 0 || !last.length) return;
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: false, horiz: e.pointerType !== "touch", before: selected };
    if (drag.horiz) { hit.setPointerCapture(e.pointerId); scrubTo(e.clientX); }
  });
  hit.addEventListener("pointermove", (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (!drag.horiz) {                                         // a finger: decide once whether this is a drag along the bar or a page scroll
      if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
      if (Math.abs(dy) > Math.abs(dx)) { drag = null; return; }
      drag.horiz = true;
      try { hit.setPointerCapture(e.pointerId); } catch { /* the pointer may already be gone */ }
    }
    drag.moved = true;
    hit.classList.add("scrubbing");
    scrubTo(e.clientX);
  });
  const end = (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    if (!drag.moved && e.type === "pointerup") {
      if (e.pointerType === "touch") scrubTo(e.clientX);                 // a plain tap anywhere near a stretch
      if (selected && selected === drag.before) { setSelected(null); scrub.hidden = true; }   // tapping the open stretch again closes it
    }
    swallowClick = true;                                                 // the stretch's own click would toggle it a second time
    setTimeout(() => { swallowClick = false; }, 400);
    hit.classList.remove("scrubbing");
    drag = null;
  };
  hit.addEventListener("pointerup", end);
  hit.addEventListener("pointercancel", end);
  // One stretch earlier or later (arrow keys, and the readout's arrow buttons on a phone).
  function step(dir, edge = false) {
    if (!last.length || !span0) return;
    const seq = last.filter((b) => !(b.state === "empty" && b.end - b.start < 60));
    let i = seq.findIndex((b) => blockKey(b) === selected);
    i = edge ? (dir < 0 ? 0 : seq.length - 1) : i < 0 ? (dir < 0 ? seq.length - 1 : 0) : i + dir;
    const b = seq[Math.max(0, Math.min(seq.length - 1, i))];
    const r = bar.getBoundingClientRect(), [a, z] = span0;
    scrubTo(r.left + (r.width * ((Math.max(a, b.start) + Math.min(z, b.end)) / 2 - a)) / (z - a));
  }
  hit.addEventListener("keydown", (e) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key) || !last.length) return;
    e.preventDefault();
    step(e.key === "ArrowLeft" || e.key === "Home" ? -1 : 1, e.key === "Home" || e.key === "End");
  });
  return { render, select, step, selected: () => selected };
}

/** The line above a day bar: the stretch you're on (tap, drag, or the arrows), or a one-line hint when nothing is chosen.
 *  Same component on the family view, the landing demo and the phone mock-up, so they can't drift apart.
 *  Usage: const ro = readout(node); const bar = dayBar(box, { onSelect: (b) => ro(b) }); ro.bind(bar); ro(null, hasBlocks) */
export function readout(root, { hint = ["Slide along the day to read it", "Drag along the day to read it"], empty = "The day fills in as Kettle hears it" } = {}) {
  root.classList.add("readout");
  root.setAttribute("aria-live", "polite");
  const arrow = (d, label) => el("button", { class: "ro-step", type: "button", "aria-label": label, html: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="${d}"/></svg>` });
  const prev = arrow("M10 3.5 5.5 8l4.5 4.5", "Earlier stretch"), next = arrow("M6 3.5 10.5 8 6 12.5", "Later stretch");
  const body = el("div", { class: "ro-body" });
  root.textContent = ""; root.append(prev, body, next);
  let bar = null, has = false;
  prev.addEventListener("click", () => bar && bar.step(-1));
  next.addEventListener("click", () => bar && bar.step(1));
  function show(b, hasBlocks) {
    if (hasBlocks != null) has = hasBlocks;
    prev.disabled = next.disabled = !has;
    const key = b ? `${b.start}|${b.label}|${b.range}` : `none|${has}`;
    if (body.dataset.k === key) return; body.dataset.k = key;
    body.textContent = "";
    if (b) {
      const key = b.activity || b.state, pic = emoji(key);
      let sw;
      if (pic) {                                            // the emoji on a tint of its day-bar colour
        sw = el("i", { class: "ro-sw ro-ej" }); sw.append(pic);
        sw.style.setProperty("--c", `var(${COLOUR[b.activity] || (key === "talk_or_tv" ? "--act-tv" : "--act-moving")})`);
      } else sw = el("i", { class: "ro-sw" + (b.activity ? "" : ` blk ${b.state}`) });
      if (b.activity && !pic) sw.style.background = `var(${COLOUR[b.activity]})`;
      body.append(el("span", { class: "ro-line" }, sw, el("b", { text: b.label })), el("span", { class: "ro-time num", text: glue(b.range) }));
    } else body.append(el("span", { class: "ro-hint" }, ...(has ? [el("span", { class: "touch", text: hint[0] }), el("span", { class: "mouse", text: hint[1] })] : [el("span", { text: empty })])));
    body.classList.remove("swap"); void body.offsetWidth; body.classList.add("swap");
  }
  show.bind = (b) => { bar = b; };
  return show;
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
    for (const [st, name] of [["talk_or_tv", "Talking / TV"], ["not_sure", "Not sure"], ["not_listening", "Not listening"], ["paused", "Paused"], ["private", "Private"]])
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
  if (b.heard && b.heard.length) card.append(el("p", { text: `Sounds Kettle named here: ${b.heard.join(", ").toLowerCase()}.` }));
  if (b.taught) card.append(el("p", { class: "why", text: `${b.taught} of these windows were named with help from what Kettle learned in this kitchen.` }));
  if (b.sounds && b.sounds.length && !(b.heard && b.heard.length) && ["activity", "empty", "not_sure", "talk_or_tv"].includes(b.state)) {
    card.append(el("p", { text: soundsSentence(b.sounds) }));
    const grid = el("div", { class: "scores" });
    for (const s of b.sounds) grid.append(el("span", { text: s.name }), el("span", { class: "num", text: s.score.toFixed(2) }));
    card.append(el("details", {}, el("summary", { text: "Details" }), grid,
      el("p", { class: "why", text: "Scores from the sound model's own list of everyday sounds. Only household sounds on Kettle's allow-list leave the laptop, never words, voices or bathroom sounds." })));
  }
  card.append(el("p", { class: "why", text: "Kettle labels 10-second stretches of sound. It keeps no recording." }));
  return card;
}

export function rulesList(root, rules) {
  const key = JSON.stringify(rules.map((r) => [r.state, r.title, r.detail, r.note]));
  if (root._k === key) return; root._k = key;          // unchanged checks: leave the DOM alone
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
