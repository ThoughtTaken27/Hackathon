// Kettle: shared helpers for the caregiver and kitchen pages. Plain browser JavaScript, no build step.
"use strict";

const ACT_COLOUR = {
  absence: "--act-empty", cooking: "--act-cooking", dishwashing: "--act-washing", eating: "--act-eating",
  other: "--act-moving", social_activity: "--act-talk", vacuum_cleaner: "--act-vacuum", watching_tv: "--act-tv",
  working: "--act-working",
};
const ACT_NAME = {
  absence: "Quiet", cooking: "Cooking", dishwashing: "Washing up", eating: "Eating", other: "Moving about",
  social_activity: "Conversation", vacuum_cleaner: "Vacuuming", watching_tv: "TV", working: "Working (typing)",
};

async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const r = await fetch(path, opts);
  if (!r.ok) {
    const err = new Error(`HTTP ${r.status}`);
    err.status = r.status;
    throw err;
  }
  return r.json();
}

function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v);
  }
  for (const kid of kids) if (kid !== null && kid !== undefined) e.append(kid);
  return e;
}

// Unix seconds -> "8:15 AM" in the kitchen's time zone (offset from UTC in seconds, sent by the server).
function clock(t, tz) {
  const s = (((Math.floor(t + tz) % 86400) + 86400) % 86400);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return `${(h % 12) || 12}:${String(m).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`;
}
function hourLabel(h) { return h === 0 || h === 24 ? "12 AM" : h === 12 ? "12 PM" : h < 12 ? `${h} AM` : `${h - 12} PM`; }

function setText(node, text, animate = true) {
  // Crossfade a sentence only when it changes (component-craft: never re-animate unchanged content).
  if (node.textContent === text) return;
  if (!animate || matchMedia("(prefers-reduced-motion: reduce)").matches || !node.textContent) {
    node.textContent = text;
    return;
  }
  node.animate([{ opacity: 1, transform: "none", filter: "none" }, { opacity: 0, transform: "translateY(-3px)", filter: "blur(3px)" }],
    { duration: 200, easing: "cubic-bezier(0.22,1,0.36,1)" }).onfinish = () => {
    node.textContent = text;
    node.animate([{ opacity: 0, filter: "blur(3px)" }, { opacity: 1, filter: "none" }], { duration: 260, easing: "cubic-bezier(0.25,1,0.5,1)" });
  };
}

// ---------------------------------------------------------------- the day bar

function blockKey(b) { return `${b.state}|${b.activity || ""}|${Math.round(b.start)}`; }

function blockClass(b) {
  const c = ["blk", b.state];
  if (b.state === "activity" && b.how_sure === "medium") c.push("medium");
  return c.join(" ");
}

function makeDayBar(root, { big = false, onSelect = null } = {}) {
  root.classList.add("daybar");
  const labels = el("div", { class: "labels", "aria-hidden": "true" });
  const hit = el("div", { class: "bar-hit" });
  const bar = el("div", { class: "bar" });
  const nowTick = el("div", { class: "now-tick", "aria-hidden": "true" });
  const ticks = el("div", { class: "ticks", "aria-hidden": "true" });
  const list = el("ol", { class: "sr" });
  hit.append(bar, nowTick);
  root.append(labels, hit, ticks, list);
  const nodes = new Map();
  let first = true, selected = null, lastBlocks = [];

  // The bar runs from 6 AM (or the first block, if earlier) to a little after now, at least 6 hours,
  // so a 20-minute block is wide enough to see and tap; late in the evening it shows the whole day.
  function range(today) {
    const start6 = today.day0 + 6 * 3600;
    const earliest = Math.min(start6, ...today.blocks.map((b) => b.start));
    const startH = Math.floor((earliest - today.day0) / 3600);
    const nowH = (today.now - today.day0) / 3600;
    const endH = Math.min(24, Math.max(startH + 6, Math.ceil(nowH + 1)));
    return [today.day0 + startH * 3600, today.day0 + endH * 3600];
  }

  function render(today) {
    lastBlocks = today.blocks;
    const [a, z] = range(today);
    const span = z - a;
    const pct = (t) => `${(100 * (Math.max(a, Math.min(z, t)) - a) / span).toFixed(3)}%`;
    const w = (b) => `${Math.max(0.25, (100 * (Math.min(z, b.end) - Math.max(a, b.start)) / span)).toFixed(3)}%`;
    const seen = new Set();
    for (const b of today.blocks) {
      const k = blockKey(b);
      seen.add(k);
      let n = nodes.get(k);
      if (!n) {
        n = el("button", { type: "button", "aria-label": `${b.label}, ${b.range}` });
        n.addEventListener("click", () => select(k));
        if (!first) n.classList.add("settle");
        bar.append(n);
        nodes.set(k, n);
      }
      n.className = blockClass(b) + (n.classList.contains("settle") ? " settle" : "") + (selected === k ? " selected" : "");
      if (b.activity) n.style.setProperty("--c", `var(${ACT_COLOUR[b.activity]})`);
      n.style.left = pct(b.start);
      n.style.width = w(b);
      n.dataset.key = k;
      n.setAttribute("aria-label", `${b.label}, ${b.range}`);
    }
    for (const [k, n] of nodes) if (!seen.has(k)) { n.remove(); nodes.delete(k); }
    // now tick
    const now = today.now;
    nowTick.style.left = pct(now);
    nowTick.hidden = now < a || now > z;
    // labels above the bar: only where they fit without overlapping
    const width = bar.clientWidth || 600;
    const minGap = 8;
    const labelBlocks = today.blocks.filter((b) => b.state !== "empty");
    const prevLabels = new Set([...labels.children].map((s) => s.dataset.key));
    labels.textContent = "";
    let right = -Infinity;
    for (const b of labelBlocks) {
      const x = (width * (Math.max(a, b.start) - a)) / span;
      const bw = (width * (Math.min(z, b.end) - Math.max(a, b.start))) / span;
      const text = b.state === "paused" ? b.label : b.label;
      const tw = text.length * (big ? 8.6 : 7.4) + 4;
      if (x < right + minGap || bw < Math.min(tw, 44) || x + tw > width + 2) continue;
      const s = el("span", { text, style: `left:${(100 * x / width).toFixed(3)}%` });
      s.dataset.key = blockKey(b);
      if (!first && !prevLabels.has(s.dataset.key)) s.classList.add("fade");
      labels.append(s);
      right = x + tw;
    }
    // hour ticks: every 3 h (every 6 h when narrow)
    ticks.textContent = "";
    const spanH = span / 3600;
    const every = spanH <= 8 ? (width < 420 ? 2 : 1) : spanH <= 14 ? (width < 420 ? 4 : 2) : (width < 420 ? 6 : 3);
    const h0 = Math.round((a - today.day0) / 3600);
    const hEnd = Math.round((z - today.day0) / 3600);
    for (let h = h0; h <= hEnd; h += 1) {
      if ((h - h0) % every !== 0) continue;
      ticks.append(el("span", { text: hourLabel(h), style: `left:${pct(today.day0 + h * 3600)}` }));
    }
    // text alternative for screen readers
    list.textContent = "";
    for (const b of today.blocks) list.append(el("li", { text: `${b.label}, ${b.range}` }));
    first = false;
    if (selected && !nodes.has(selected)) select(null);
    else if (selected && onSelect) onSelect(lastBlocks.find((b) => blockKey(b) === selected) || null);
  }

  function select(k) {
    selected = selected === k ? null : k;
    for (const [kk, n] of nodes) n.classList.toggle("selected", kk === selected);
    if (onSelect) onSelect(lastBlocks.find((b) => blockKey(b) === selected) || null);
  }

  return { render, select };
}

// ---------------------------------------------------------------- evidence card

function soundsSentence(sounds) {
  if (!sounds || !sounds.length) return "";
  const names = sounds.map((s) => s.name.toLowerCase().split(",")[0]);
  if (names.length === 1) return `Sounds Kettle heard: mostly ${names[0]}.`;
  return `Sounds Kettle heard: mostly ${names[0]}, some ${names.slice(1).join(" and ")}.`;
}

function evidenceCard(b) {
  if (!b) return null;
  const sw = el("span", { class: "sw" });
  if (b.activity) sw.style.background = `var(${ACT_COLOUR[b.activity]})`;
  else sw.className = `sw blk ${b.state}`;
  const parts = b.card.split(" · ");
  const head = el("p", { class: "head" }, sw, el("span", { text: parts[0] }), el("span", { class: "muted t", text: parts.slice(1, 2).join("") }));
  const rest = parts.slice(2).join(" · ");
  const card = el("div", { class: "evidence", role: "region", "aria-label": `${b.label} details` }, head);
  if (rest) card.append(el("p", { text: rest }));
  if (b.sounds && b.sounds.length && (b.state === "activity" || b.state === "empty" || b.state === "not_sure" || b.state === "talk_or_tv")) {
    card.append(el("p", { text: soundsSentence(b.sounds) }));
    const grid = el("div", { class: "scores" });
    for (const s of b.sounds) grid.append(el("span", { text: s.name }), el("span", { class: "num", text: s.score.toFixed(2) }));
    card.append(el("details", {}, el("summary", { text: "Details" }), grid,
      el("p", { class: "why", text: "These scores come from the sound model's own list of 527 everyday sounds. Kettle shows only kitchen and living-room sounds, never words or who is speaking." })));
  }
  card.append(el("p", { class: "why", text: "Kettle labels 10-second stretches of sound. It keeps no recording." }));
  return card;
}

function legend() {
  const items = [
    ["Cooking", "var(--act-cooking)"], ["Washing up", "var(--act-washing)"], ["Eating", "var(--act-eating)"],
    ["TV", "var(--act-tv)"], ["Conversation", "var(--act-talk)"],
  ];
  const lg = el("div", { class: "legend", "aria-hidden": "true" });
  for (const [n, c] of items) lg.append(el("span", {}, el("i", { style: `background:${c}` }), n));
  lg.append(el("span", {}, el("i", { class: "blk not_sure", style: "position:static" }), "Not sure"));
  lg.append(el("span", {}, el("i", { class: "blk not_listening", style: "position:static" }), "Not listening"));
  lg.append(el("span", {}, el("i", { style: "height:2px;background:var(--act-empty);vertical-align:3px" }), "Quiet"));
  return lg;
}
