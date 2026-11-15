// Meera's view (Kettle web): reads the household's labels and draws the same day the kitchen screen shows.
import { today as computeToday, ruleTitle, week, clock, DISPLAY, KIND_NAMES, KINDS_SHOWN } from "./core.js";
import { TEXT as SAFETY_TEXT } from "./safety.js";
import { $, el, setText, api, now, linkFromHash, homes, saveHome, forgetHome, dayBar, legend, evidenceCard, rulesList, qr, linkFor, copy, toast } from "./ui.js";
import { HOP_S } from "./listen.js";

const link = linkFromHash("family");
let srv = null, events = [], t = null, failures = 0;

if (!link) {
  $("#app").innerHTML = "";
  $("#app").append(el("div", { class: "narrow", style: "padding-top:24px" },
    el("h1", { class: "h1", text: "Open your family view" }),
    el("p", { class: "lead", text: "Use the link Kettle gave you when you set it up, or type a six-letter code from the kitchen device." }),
    el("div", { class: "actions" }, el("a", { class: "btn primary lg", href: "/pair", text: "I have a code" }), el("a", { class: "btn lg", href: "/start", text: "Set up Kettle" }))));
} else boot();

const bar = link ? dayBar($("#bar"), { onSelect: (b) => {
  const box = $("#evidence"); box.textContent = "";
  const c = evidenceCard(b); if (c) box.append(c);
  $("#fold").classList.toggle("open", !!c);
} }) : null;
const drawLegend = link ? legend($("#bar")) : null;

async function boot() {
  await poll();
  setInterval(() => { if (!document.hidden) poll(); }, 5000);
  setInterval(() => { if (srv && !document.hidden) draw(); }, 1000);
  document.addEventListener("visibilitychange", () => !document.hidden && poll());
  addEventListener("resize", () => srv && draw());
}
async function poll() {
  try {
    const since = events.length ? events[events.length - 1].end - 3600 : 0;
    const r = await api(`/api/h/${link.id}/state?since=${since}`, { key: link.key, retries: 1 });
    const m = new Map(events.map((e) => [e.end, e])); for (const e of r.events) m.set(e.end, e);
    events = [...m.values()].sort((a, b) => a.end - b.end).filter((e) => e.end > now() - 36 * 3600);
    srv = r.state; failures = 0;
    saveHome(link.id, { parent: srv.names.parent, caregiver: srv.names.caregiver });
    draw();
  } catch (e) {
    if (e.status === 403 || e.status === 404) return gone(e.message);
    if (++failures >= 3) { $("#hb").dataset.state = "stale"; setText($("#hb .text"), "Can't reach Kettle right now. Retrying…"); }
  }
}
function gone(msg) {
  $("#app").innerHTML = "";
  $("#app").append(el("div", { class: "narrow" }, el("h1", { class: "h1", text: "This home isn't available" }), el("p", { class: "lead", text: msg }),
    el("div", { class: "actions" }, el("a", { class: "btn primary lg", href: "/start", text: "Set up Kettle again" }))));
  forgetHome(link.id);
}

function draw() {
  t = computeToday(srv, events, now(), { theta: 0.66, tz: srv.tz, hop: HOP_S, names: srv.names });
  const n = t.names;
  document.title = `${n.parent}'s kitchen today · Kettle`;
  $("#eyebrow").textContent = `What ${n.caregiver} sees`;
  const ttl = $("#title"), ttlText = `${n.parent}'s kitchen, `;
  if (ttl.dataset.t !== ttlText) { ttl.dataset.t = ttlText; ttl.textContent = ttlText; ttl.append(el("em", { text: "today" })); }
  const hm = /^(\d+):\d+ (AM|PM)$/.exec(t.now_text || "");
  if (hm && window.kettleSky) window.kettleSky((+hm[1] % 12) + (hm[2] === "PM" ? 12 : 0));
  $("#date").textContent = `${t.date_text} · ${n.parent}'s time`;
  $("#hb").dataset.state = t.heartbeat.state;
  setText($("#hb .text"), t.heartbeat.battery ? `${t.heartbeat.text} · ${t.heartbeat.battery}` : t.heartbeat.text);
  setText($("#summary"), t.summary || (t.heartbeat.state === "never" ? "" : "Nothing heard yet today."));
  setText($("#coverage"), t.coverage ? t.coverage.text : "");
  const hid = [...(t.kitchen.hide || []).map((c) => DISPLAY[c]), ...(t.kitchen.kinds_off || []).map((k) => KIND_NAMES[k])];
  $("#hidden-note").hidden = !hid.length;
  setText($("#hidden-note"), hid.length ? `${n.parent} chose not to share: ${hid.join(", ")}.` : "");
  const heard = $("#heard"); heard.textContent = "";
  for (const h of t.heard) heard.append(el("li", { text: `${h.name}: ${h.text}${h.n > 1 ? ` (${h.n}×)` : ""}` }));
  $("#heard-sec").hidden = !t.heard.length;
  drawUrgent(n);
  drawWeek();
  $("#foot-who").textContent = `${n.parent} sees the same day on the kitchen screen and can pause Kettle any time.`;
  bar.render(t); drawLegend(t);
  rulesList($("#rules"), t.rules);
  drawInvite();
}

/** Handover 3.6: a red banner for each Urgent alert from the kitchen device that nobody here has marked as seen (last 12 hours). */
function drawUrgent(n) {
  const box = $("#urgent");
  const list = (srv.alerts || []).filter((a) => !a.seen && a.at > now() - 12 * 3600);
  const key = list.map((a) => a.id).join(",");
  if (box.dataset.k === key) return;
  box.dataset.k = key; box.textContent = "";
  for (const a of list) {
    const why = a.checkin === "no_answer" ? ` Nobody answered "Are you OK?" on the kitchen screen.` : a.checkin === "help" ? ` ${n.parent} pressed "I need help".` : "";
    box.append(el("div", { class: "urgent", role: "alert" },
      el("p", { class: "u-h", text: `Urgent: Kettle heard ${SAFETY_TEXT[a.kind] || "something urgent"} at ${clock(a.at, t.tz_offset)}.` }),
      el("p", { class: "u-b", text: `${why} Call ${n.parent} now. Kettle can't call for help itself.`.trim() }),
      el("button", { class: "btn", type: "button", text: "I've seen this", onclick: async () => {
        try { const r = await api(`/api/h/${link.id}/seen`, { method: "POST", key: link.key, body: { id: a.id } }); srv = r.state; draw(); }
        catch (e) { toast(e.message || "Couldn't reach Kettle."); }
      } })));
  }
}
function drawWeek() {
  const w = week(srv, now(), { tz: srv.tz, hop: HOP_S });
  const known = w.rows.some((r) => r.state !== "unknown");
  $("#week-sec").hidden = !known;
  if (!known) return;
  setText($("#week-text"), w.text);
  const box = $("#week"); box.textContent = "";
  for (const r of w.rows) box.append(el("div", { class: "wday", "data-state": r.state, title: r.key },
    el("span", { class: "d", text: r.day }),
    el("span", { class: "v", text: r.state === "yes" ? `✓ ${r.at}` : r.state === "no" ? "Not heard" : "Can't tell" }),
    el("span", { class: "k", text: r.kettle ? `Kettle ${r.kettle}` : "" })));
}

// before Dad's laptop has said yes: show how to connect it (only on the device that holds the kitchen key)
let inviteShown = "";
async function drawInvite() {
  const box = $("#invite");
  const home = homes()[link.id] || {};
  const need = t.heartbeat.state === "never";
  const key = need ? (home.kitchenKey ? "k" : "nok") : "";
  if (key === inviteShown) return; inviteShown = key; box.textContent = "";
  if (!need) return;
  const P = t.names.parent;
  if (!home.kitchenKey) { box.append(el("div", { class: "banner" }, el("p", {}, el("strong", { text: `Waiting for ${P}'s kitchen device.` }), ` Kettle starts when ${P} says yes on the kitchen screen.`))); return; }
  let code = home.kitchenCode;
  if (!code || (home.kitchenCodeExp || 0) < now() + 600) {
    try { const r = await api(`/api/h/${link.id}/code`, { method: "POST", key: link.key, body: { for: "kitchen", key: home.kitchenKey } });
      code = r.code; saveHome(link.id, { kitchenCode: code, kitchenCodeExp: r.codeExpires }); } catch { code = null; }
  }
  const url = linkFor("kitchen", link.id, home.kitchenKey);
  box.append(el("div", { class: "pair-card", style: "margin-top:20px" },
    el("p", { class: "step-k", text: "Next: connect the kitchen device" }),
    el("h2", { class: "section-title", text: `On ${P}'s kitchen device, go to ${location.host}/kitchen and type` }),
    code ? el("p", { class: "code-big num", html: `${code.slice(0, 3)}<span> </span>${code.slice(3)}` }) : null,
    el("p", { class: "meta muted", text: `Or send ${P} this link. Open it on the phone, tablet or laptop that stays in the kitchen.` }),
    el("div", { class: "linkbox" }, el("code", { text: url }), el("button", { class: "btn", type: "button", text: "Copy link", onclick: () => copy(url) }))));
}

// ---------------------------------------------------------------- checks editor
const sheet = $("#sheet"), scrim = $("#scrim");
let draft = [];
function openSheet(which) { which.classList.add("open"); scrim.classList.add("open"); }
function closeSheets() { for (const s of document.querySelectorAll(".sheet")) s.classList.remove("open"); scrim.classList.remove("open"); }
scrim.addEventListener("click", closeSheets);
addEventListener("keydown", (e) => e.key === "Escape" && closeSheets());
$("#print")?.addEventListener("click", () => window.print());
$("#edit-rules")?.addEventListener("click", () => { draft = srv.rules.map((r) => ({ ...r })); fields(); openSheet(sheet); });
$("#cancel-rules")?.addEventListener("click", closeSheets);
$("#add-rule")?.addEventListener("click", () => { if (draft.length < 3) { draft.push({ type: "kitchen_by", time: "10:00" }); fields(); } });
$("#save-rules")?.addEventListener("click", async () => {
  try { const r = await api(`/api/h/${link.id}/rules`, { method: "POST", key: link.key, body: { rules: draft } }); srv = r.state; closeSheets(); draw(); toast("Checks saved"); }
  catch (e) { $("#sheet-msg").textContent = e.message; }
});
function fields() {
  const box = $("#sheet-fields"); box.textContent = "";
  draft.forEach((r, i) => {
    const type = el("select", { "aria-label": "Kind of check" },
      ["kitchen_by", "any_by", "kind_by", "tv_over"].map((v) => el("option", { value: v, selected: r.type === v, text: { kitchen_by: "Kitchen activity by", any_by: "Some sound of activity by", kind_by: "A sound heard by", tv_over: "TV on for more than (hours)" }[v] })));
    const kind = r.type === "kind_by" ? el("select", { "aria-label": "Which sound", onchange: (e) => { r.kind = e.target.value; } },
      Object.entries(KIND_NAMES).filter(([id]) => KINDS_SHOWN.has(id)).map(([id, name]) => el("option", { value: id, selected: r.kind === id, text: name }))) : null;
    const val = r.type === "tv_over" ? el("input", { type: "number", min: 0.5, max: 16, step: 0.5, value: r.hours ?? 4, "aria-label": "Hours" })
      : el("input", { type: "time", value: r.time || "10:00", "aria-label": "Time" });
    type.addEventListener("change", () => { draft[i] = type.value === "tv_over" ? { type: "tv_over", hours: 4 } : type.value === "kind_by" ? { type: "kind_by", kind: [...KINDS_SHOWN][0], time: "09:00" } : { type: type.value, time: "10:00" }; fields(); });
    val.addEventListener("change", () => { if (r.type === "tv_over") r.hours = +val.value; else r.time = val.value; });
    box.append(el("div", { class: "field" }, type, kind, val, el("button", { class: "btn quiet", type: "button", text: "Remove", onclick: () => { draft.splice(i, 1); fields(); } })));
  });
  $("#add-rule").disabled = draft.length >= 3;
  const presets = [["Breakfast by 10", { type: "kitchen_by", time: "10:00" }], ["Lunch by 2", { type: "kitchen_by", time: "14:00" }],
    ["Evening meal by 8", { type: "kitchen_by", time: "20:00" }], ...(KINDS_SHOWN.has("kettle") ? [["Morning drink by 9", { type: "kind_by", kind: "kettle", time: "09:00" }]] : [])];
  box.append(el("div", { class: "row presets", style: "margin-top:10px;flex-wrap:wrap;gap:8px" }, el("span", { class: "meta muted", text: "Quick add:" }),
    ...presets.map(([label, r]) => el("button", { class: "btn quiet", type: "button", text: label, disabled: draft.length >= 3 || null, onclick: () => { if (draft.length < 3) { draft.push({ ...r }); fields(); } } }))));
}

// ---------------------------------------------------------------- settings: invite, rename, delete
$("#menu-btn")?.addEventListener("click", async () => {
  if (!srv) return;
  const body = $("#settings-body"); body.textContent = "";
  const n = srv.names;
  const pIn = el("input", { class: "input", value: n.parent, maxlength: 24, "aria-label": "What you call your parent" });
  const cIn = el("input", { class: "input", value: n.caregiver, maxlength: 24, "aria-label": "Your name" });
  body.append(
    el("div", { class: "field2" }, el("label", { text: "What you call your parent" }), pIn),
    el("div", { class: "field2" }, el("label", { text: "Your name, as the kitchen screen shows it" }), cIn),
    el("div", { class: "actions", style: "margin-top:16px" }, el("button", { class: "btn primary", type: "button", text: "Save names", onclick: async () => {
      try { const r = await api(`/api/h/${link.id}/names`, { method: "POST", key: link.key, body: { parent: pIn.value, caregiver: cIn.value } }); srv = r.state; draw(); toast("Saved"); } catch (e) { toast(e.message); }
    } })),
    el("hr", { style: "border:0;border-top:1px solid var(--line);margin:24px 0 8px" }),
    el("p", { class: "panel-h", text: "Add another family member" }),
    el("p", { class: "meta muted", text: "They get the same view. Send them this link, or let them scan the code." }));
  const famUrl = linkFor("family", link.id, link.key);
  body.append(el("div", { class: "linkbox" }, el("code", { text: famUrl }), el("button", { class: "btn", type: "button", text: "Copy", onclick: () => copy(famUrl) })));
  qr(famUrl, 152).then((q) => { q.style.marginTop = "14px"; q.style.justifySelf = "start"; body.insertBefore(q, del); });
  const del = el("div", {}, el("hr", { style: "border:0;border-top:1px solid var(--line);margin:24px 0 8px" }),
    el("p", { class: "panel-h", text: "Delete this home" }),
    el("p", { class: "meta muted", text: "Removes every label and setting from Kettle's server for good. The kitchen device stops sending." }),
    el("div", { class: "actions", style: "margin-top:12px" },
      el("button", { class: "btn danger-link", type: "button", text: "Delete everything", onclick: async (e) => {
        if (e.currentTarget.dataset.sure !== "1") { e.currentTarget.dataset.sure = "1"; e.currentTarget.textContent = "Press again to delete for good"; return; }
        try { await api(`/api/h/${link.id}`, { method: "DELETE", key: link.key }); forgetHome(link.id); location.href = "/"; } catch (err) { toast(err.message); }
      } }),
      el("span", { style: "flex:1" }), el("button", { class: "btn quiet", type: "button", text: "Close", onclick: closeSheets })));
  body.append(del);
  openSheet($("#settings"));
});
