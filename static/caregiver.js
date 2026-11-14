// Kettle caregiver view ("Dad's kitchen today"). Asks the server for today's state once a second.
"use strict";

const $ = (id) => document.getElementById(id);
let today = null, failures = 0, lastOk = null, selectedBlock = null;

const bar = makeDayBar($("bar"), {
  onSelect: (b) => {
    selectedBlock = b;
    const box = $("evidence");
    box.textContent = "";
    if (b) box.append(evidenceCard(b));
    $("fold").classList.toggle("open", !!b);
  },
});
$("bar").after(legend());

function renderHeartbeat(hb, demo) {
  const node = $("hb");
  node.dataset.state = hb.state;
  setText(node.querySelector(".text"), hb.text, false);
}

function renderRules(rs) {
  const box = $("rules");
  box.textContent = "";
  if (!rs.length) {
    box.append(el("div", { class: "rule" },
      el("p", { class: "state", text: "Add a check, like 'kitchen activity by 10:00 AM'." }),
      el("p", { class: "note", text: "Kettle only checks rules you set." })));
    return;
  }
  for (const r of rs) {
    const card = el("div", { class: "rule", "data-state": r.state },
      el("p", { class: "name", text: r.title }),
      el("p", { class: "state", text: r.detail }));
    if (r.note) card.append(el("p", { class: "note", text: r.note }));
    box.append(card);
  }
}

function renderDemo(d, names) {
  const tag = $("demo-tag");
  if (d) {
    tag.hidden = false;
    tag.textContent = "";
    tag.append(el("span", { class: "tag demo", text: `Sample day · ${d.title}` }),
      el("span", { class: "meta muted", style: "margin-left:8px", text: `Recorded sounds from a public research home, not ${names.parent}.` }));
    tag.style.marginBottom = "10px";
  } else {
    tag.hidden = true;
  }
  $("demo-extra").hidden = !d;
  for (const b of $("demo-buttons").children) b.classList.toggle("primary", !!d && b.dataset.sid === d.id);
}

let seenKeys = null, seenHb = null;
function announce(t) {
  if (seenHb && seenHb !== t.heartbeat.state) $("announce").textContent = t.heartbeat.text;
  seenHb = t.heartbeat.state;
  // Tell screen-reader users about a block that just settled ("Washing up, 8:45 AM, how sure: high").
  const keys = new Set(t.blocks.map(blockKey));
  if (seenKeys) {
    const fresh = t.blocks.filter((b) => !seenKeys.has(blockKey(b)) && b.state !== "not_listening");
    if (fresh.length) $("announce").textContent = fresh.map((b) => `${b.label}, ${b.range}${b.how_sure ? `, how sure: ${b.how_sure}` : ""}`).join(". ");
  }
  seenKeys = keys;
}

function render(t) {
  today = t;
  announce(t);
  $("title").textContent = `${t.names.parent}'s kitchen today`;
  document.title = `${t.names.parent}'s kitchen today · Kettle`;
  $("date").textContent = t.date_text;
  renderDemo(t.demo, t.names);
  renderHeartbeat(t.heartbeat, t.demo);
  setText($("summary"), t.summary);
  bar.render(t);
  renderRules(t.rules);
  $("head-line").textContent = t.head && t.head.trained_on && t.head.trained_on.startsWith("STUB") ? "Model: temporary stub." : "";
}

async function poll() {
  try {
    const t = await api("/api/today");
    failures = 0;
    lastOk = t;
    render(t);
  } catch (e) {
    failures += 1;
    if (failures >= 3 && lastOk) {
      const node = $("hb");
      node.dataset.state = "error";
      node.querySelector(".text").textContent =
        `Kettle stopped working on the kitchen laptop at ${clock(lastOk.now, lastOk.tz_offset)}. The day so far is shown below.`;
    }
  }
}

// ---------------------------------------------------------------- sample days
const SCENARIOS = [["usual", "A usual morning"], ["quiet", "A quiet morning"], ["tv", "A TV-only afternoon"]];
for (const [sid, name] of SCENARIOS) {
  const b = el("button", { class: "btn", type: "button", text: name });
  b.dataset.sid = sid;
  b.addEventListener("click", async () => { render(await api(`/api/demo/${sid}`, {})); });
  $("demo-buttons").append(b);
}
$("demo-stop").addEventListener("click", async () => render(await api("/api/demo/stop", {})));
$("demo-sleep").addEventListener("click", async () => render(await api("/api/demo/sleep", {})));

// ---------------------------------------------------------------- try your own sound
const TRY_MSG = {
  unreadable: "That isn't audio Kettle can read. Try a WAV, MP3, M4A or OGG file.",
  too_big: "That file is too big. Try a clip under 60 seconds.",
};

function renderTry(r) {
  const box = $("try-result");
  box.textContent = "";
  if (r.status === "too_short") {
    box.append(el("p", { text: `That clip is ${Math.round(r.seconds)} seconds. Kettle needs at least 10 seconds.` }));
    return;
  }
  if (r.status !== "ok") { box.append(el("p", { text: TRY_MSG[r.status] || TRY_MSG.unreadable })); return; }
  const total = r.windows.length ? r.windows[r.windows.length - 1].end : 10;
  const mini = el("div", { class: "mini-bar", "aria-hidden": "true" });
  for (const b of r.blocks) {
    const n = el("span", { class: blockClass({ ...b, how_sure: b.conf >= 0.8 ? "high" : "medium" }) });
    if (b.activity) n.style.setProperty("--c", `var(${ACT_COLOUR[b.activity]})`);
    n.style.left = `${(100 * b.start) / total}%`;
    n.style.width = `${(100 * (b.end - b.start)) / total}%`;
    mini.append(n);
  }
  const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;
  const heard = r.blocks.map((b) => `${b.label} ${mmss(b.start)}–${mmss(b.end)}`).join(" · ");
  box.append(el("p", { class: "meta muted", text: r.file }), mini);
  if (r.all_not_sure) {
    box.append(el("p", { text: "Kettle wasn't sure about any of this. It knows 9 household activities; this may be something else." }));
  } else {
    box.append(el("p", { text: `Kettle heard: ${heard}` }));
  }
  const top = r.windows[0];
  if (top && top.sounds.length) box.append(el("p", { class: "meta muted", text: soundsSentence(top.sounds) + " (first 10 s)" }));
  if (r.cut) box.append(el("p", { class: "meta muted", text: "Kettle reads the first 60 seconds only." }));
}

async function tryBytes(name, bytes) {
  const box = $("try-result");
  box.textContent = "";
  box.append(el("p", { class: "shimmer", text: `Listening to ${name}…` }));
  try {
    const r = await fetch("/api/try", { method: "POST", headers: { "Content-Type": "application/octet-stream", "X-Filename": name }, body: bytes });
    renderTry(await r.json());
  } catch (e) {
    box.textContent = "";
    box.append(el("p", { text: "Kettle couldn't read that just now. Try again." }));
  }
}

$("file").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  if (f) tryBytes(f.name, await f.arrayBuffer());
  e.target.value = "";
});
const drop = $("drop");
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", async (e) => {
  e.preventDefault(); drop.classList.remove("over");
  const f = e.dataTransfer.files[0];
  if (f) tryBytes(f.name, await f.arrayBuffer());
});

const SAMPLE_NAMES = { "unclear.flac": "An unclear clip", "washing-up.flac": "Washing up", "white-noise.wav": "White noise", "silence.wav": "Silence", "not-audio.txt": "A file that isn't audio" };
api("/api/try-samples").then((list) => {
  const row = $("samples");
  row.append(el("span", { class: "meta muted", style: "align-self:center", text: "Or try:" }));
  for (const s of list) {
    const b = el("button", { class: "btn", type: "button", text: SAMPLE_NAMES[s.name] || s.name });
    b.addEventListener("click", async () => {
      const bytes = await (await fetch(`/api/try-samples/${encodeURIComponent(s.name)}`)).arrayBuffer();
      tryBytes(s.name, bytes);
    });
    row.append(b);
  }
});

// ---------------------------------------------------------------- rule editor sheet
let draft = [];
function fieldRow(r, i) {
  const type = el("select", { "aria-label": "Kind of check" },
    el("option", { value: "kitchen_by", text: "Kitchen activity by" }),
    el("option", { value: "any_by", text: "Some sound of activity by" }),
    el("option", { value: "tv_over", text: "TV on for more than (hours)" }));
  type.value = r.type;
  const val = el("input", r.type === "tv_over"
    ? { type: "number", min: "0.5", max: "16", step: "0.5", value: r.hours, "aria-label": "Hours" }
    : { type: "time", value: r.time, "aria-label": "Time" });
  const rm = el("button", { class: "btn quiet", type: "button", text: "Remove" });
  type.addEventListener("change", () => { draft[i] = type.value === "tv_over" ? { type: "tv_over", hours: 4 } : { type: type.value, time: "10:00" }; drawSheet(); });
  val.addEventListener("input", () => { if (draft[i].type === "tv_over") draft[i].hours = Number(val.value); else draft[i].time = val.value; });
  rm.addEventListener("click", () => { draft.splice(i, 1); drawSheet(); });
  return el("div", { class: "field" }, type, val, rm);
}
function drawSheet() {
  const box = $("sheet-fields");
  box.textContent = "";
  draft.forEach((r, i) => box.append(fieldRow(r, i)));
  $("add-rule").disabled = draft.length >= 3;
}
function openSheet(open) {
  $("sheet").classList.toggle("open", open);
  $("scrim").classList.toggle("open", open);
  if (open) { draft = (today ? today.rule_defs : []).map((r) => ({ ...r })); drawSheet(); $("sheet-msg").textContent = ""; }
}
$("edit-rules").addEventListener("click", () => openSheet(true));
$("cancel-rules").addEventListener("click", () => openSheet(false));
$("scrim").addEventListener("click", () => openSheet(false));
$("add-rule").addEventListener("click", () => { if (draft.length < 3) { draft.push({ type: "kitchen_by", time: "10:00" }); drawSheet(); } });
$("save-rules").addEventListener("click", async () => {
  try { render(await api("/api/rules", { rules: draft })); openSheet(false); }
  catch (e) { $("sheet-msg").textContent = "Each check needs a time, or a number of hours between 0.5 and 16."; }
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") openSheet(false); });

poll();
setInterval(poll, 1000);
