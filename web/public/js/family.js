// The family view (Kettle web): reads the household's labels and draws the same day the room screen shows.
import { today as computeToday, ruleTitle, week, clock, DISPLAY, KIND_NAMES, KINDS_SHOWN } from "./core.js";
import { TEXT as SAFETY_TEXT } from "./safety.js";
import { $, el, setText, api, now, linkFromHash, homes, saveHome, forgetHome, dayBar, legend, evidenceCard, readout, rulesList, qr, linkFor, copy, toast } from "./ui.js";
import { HOP_S } from "./listen.js";
import { pushSupport, subscribe, currentSubscription, unsubscribe, registerSW } from "./pushclient.js";

// a notification opens /family?h=<home>[&ack=<alert>]: pick that home (the key stays in this browser), then clean the address
const qs = new URLSearchParams(location.search);
const link = (() => {
  const l = linkFromHash("family"), h = qs.get("h"), saved = h && homes()[h];
  return saved && saved.familyKey && (!l || l.id !== h) ? { id: h, key: saved.familyKey, role: "family" } : l;
})();
const ackId = qs.get("ack");
if (qs.has("h") || qs.has("ack")) history.replaceState(null, "", location.pathname + location.hash);
let srv = null, events = [], t = null, failures = 0, lastSig = "", lastDraw = 0, pushDrawn = false;

if (!link) {
  $("#app").innerHTML = "";
  $("#app").append(el("div", { class: "narrow", style: "padding-top:24px" },
    el("h1", { class: "h1", text: "Open your family view" }),
    el("p", { class: "lead", text: "Use the link Kettle gave you when you set it up, or type a six-letter code from the listening device." }),
    el("div", { class: "actions" }, el("a", { class: "btn primary lg", href: "/pair", text: "I have a code" }), el("a", { class: "btn lg", href: "/start", text: "Set up Kettle" }))));
} else boot();

// The readout above the bar (ui.js) names the stretch you're on. The evidence card below only rebuilds when the chosen
// stretch or its text changes, so an open "Details" stays open while the page refreshes.
let evKey = "";
const ro = link ? readout($("#readout")) : null;
const bar = link ? dayBar($("#bar"), { onSelect: (b) => {
  ro(b);
  const k = b ? `${b.start}|${b.end}|${b.card}|${(b.heard || []).join()}` : "";
  if (k === evKey) return; evKey = k;
  const box = $("#evidence"), c = evidenceCard(b);
  box.textContent = ""; if (c) box.append(c);
  $("#fold").classList.toggle("open", !!c);
} }) : null;
if (ro) ro.bind(bar);
const drawLegend = link ? legend($("#bar")) : null;

async function boot() {
  registerSW();
  if (ackId) { try { await api(`/api/h/${link.id}/seen`, { method: "POST", key: link.key, body: { id: ackId } }); } catch {} }
  await poll();
  setInterval(() => { if (!document.hidden) poll(); }, 5000);
  setInterval(() => { if (srv && !document.hidden) draw(); }, 15000);   // the clock moves by minutes; new labels redraw from poll()
  document.addEventListener("visibilitychange", () => !document.hidden && poll());
  addEventListener("resize", () => srv && draw());
}
async function poll() {
  try {
    const since = events.length ? events[events.length - 1].end - 3600 : 0;
    const r = await api(`/api/h/${link.id}/state?since=${since}`, { key: link.key, retries: 1 });
    const m = new Map(events.map((e) => [e.end, e])); for (const e of r.events) m.set(e.end, e);
    events = [...m.values()].sort((a, b) => a.end - b.end).filter((e) => e.end > now() - 36 * 3600);
    const sig = JSON.stringify(r.state) + "|" + events.length + "|" + (events.length ? events[events.length - 1].end : 0);
    srv = r.state; failures = 0;
    saveHome(link.id, { parent: srv.names.parent, caregiver: srv.names.caregiver });
    if (sig !== lastSig || Date.now() - lastDraw > 14000) { lastSig = sig; draw(); }
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
  lastDraw = Date.now();
  const n = t.names;
  // titles name the room, never a relationship ("The kitchen today", not "Dad's kitchen"); the name they gave appears only in sentences
  const ttlText = n.self ? `Your ${n.room}` : n.roomType === "home" ? "At home" : `The ${n.room}`;
  document.title = `${ttlText} today · Kettle`;
  const ttl = $("#title");
  if (ttl.dataset.t !== ttlText) { ttl.dataset.t = ttlText; ttl.textContent = `${ttlText} `; ttl.append(el("span", { class: "dim", text: "today" })); }
  const hm = /^(\d+):\d+ (AM|PM)$/.exec(t.now_text || "");
  if (hm && window.kettleSky) window.kettleSky((+hm[1] % 12) + (hm[2] === "PM" ? 12 : 0));
  setText($("#date"), n.self ? `${t.date_text} · ${t.now_text}` : `${t.date_text} · ${t.now_text} there`);
  $("#hb").dataset.state = t.heartbeat.state;
  const hbText = t.heartbeat.text.replace(/ Nothing is known after that\.$/, "");        // the summary already says what isn't known
  setText($("#hb .text"), t.heartbeat.battery ? `${hbText} · ${t.heartbeat.battery}` : hbText);
  setText($("#summary"), t.summary || (t.heartbeat.state === "never" ? "" : "Nothing heard yet today."));
  setText($("#coverage"), t.coverage ? t.coverage.text : "");
  const hid = [...(t.kitchen.hide || []).map((c) => DISPLAY[c]), ...(t.kitchen.kinds_off || []).map((k) => KIND_NAMES[k])];
  $("#hidden-note").hidden = !hid.length;
  setText($("#hidden-note"), hid.length ? `${n.parent} chose not to share: ${hid.join(", ")}.` : "");
  const heard = $("#heard"); heard.textContent = "";
  for (const h of t.heard) heard.append(el("li", { text: `${h.name}: ${h.text}${h.n > 1 ? ` (${h.n}×)` : ""}` }));
  $("#heard-sec").hidden = !t.heard.length;
  drawUrgent(n);
  if (!pushDrawn) { pushDrawn = true; drawPush(); }
  drawWeek();
  $("#foot-who").textContent = n.self ? "You see the same day on the room screen and can pause Kettle any time." : `${n.parent} sees the same day on the ${n.room} screen and can pause Kettle any time.`;
  bar.render(t); drawLegend(t);
  if (!bar.selected()) ro(null, t.blocks.length > 0);
  rulesList($("#rules"), t.rules);
  drawInvite();
}

/**
 * Handover v3.5, 3.2/3.6: a banner for each Urgent alert from the room device that nobody here has marked as seen (last 12 hours).
 * Red while it may need someone (asking, no answer, I need help, smoke/CO/gunshot); amber once they pressed "I'm OK".
 */
let alertsKnown = null;
function drawUrgent(n) {
  const box = $("#urgent");
  const list = (srv.alerts || []).filter((a) => !a.seen && a.at > now() - 12 * 3600);
  const key = list.map((a) => `${a.id}:${a.checkin}`).join(",");
  // a new or worse alert while this page is open: buzz, retitle the tab, and show a system notification if allowed
  const red = list.filter((a) => a.checkin !== "ok").map((a) => `${a.id}:${a.checkin}`);
  if (alertsKnown && red.some((k) => !alertsKnown.has(k))) {
    try { navigator.vibrate && navigator.vibrate([300, 100, 300]); } catch {}
    const a = list.find((x) => x.checkin !== "ok" && !alertsKnown.has(`${x.id}:${x.checkin}`));
    try { if ("Notification" in window && Notification.permission === "granted" && document.hidden) new Notification("Kettle: urgent", { body: `Heard ${SAFETY_TEXT[a.kind] || "something urgent"} at ${clock(a.at, t.tz_offset)}.`, tag: `kettle-${a.id}`, icon: "/img/icon-192.png" }); } catch {}
  }
  alertsKnown = new Set(list.map((a) => `${a.id}:${a.checkin}`));
  if (red.length) document.title = "● Urgent · Kettle";
  drawAlertLog(n);
  if (box.dataset.k === key) return;
  box.dataset.k = key; box.textContent = "";
  for (const a of list) {
    const ok = a.checkin === "ok", at = clock(a.at, t.tz_offset), what = SAFETY_TEXT[a.kind] || "something urgent";
    const head = a.kind === "help" ? `${n.parent} pressed "I need help" at ${at}.` : `Kettle heard ${what} at ${at}.`;
    const state = ok ? `${n.parent} pressed "I'm OK"${a.answered ? ` at ${clock(a.answered, t.tz_offset)}` : ""}. Worth a call when you can.`
      : a.checkin === "asking" ? `Asking "Are you OK?" on the ${n.room} screen now. Call ${n.parentMid} if you can.`
      : a.checkin === "no_answer" ? `Nobody answered "Are you OK?" on the ${n.room} screen. Call ${n.parentMid} now.`
      : a.checkin === "help" ? `${n.parent} pressed "I need help". Call ${n.parentMid} now.`
      : `Call ${n.parentMid} now. Kettle can't call for help itself.`;
    box.append(el("div", { class: `urgent ${ok ? "u-ok" : "u-red"}`, role: "alert", "data-checkin": a.checkin },
      el("p", { class: "u-k", text: ok ? `Update · ${at}` : `Urgent · ${at}` }),
      el("p", { class: "u-h", text: head }),
      el("p", { class: "u-b", text: state }),
      el("div", { class: "u-act" }, el("button", { class: "btn u-seen", type: "button", text: "I've seen this", onclick: async () => {
        try { const r = await api(`/api/h/${link.id}/seen`, { method: "POST", key: link.key, body: { id: a.id } }); srv = r.state; draw(); }
        catch (e) { toast(e.message || "Couldn't reach Kettle."); }
      } })),
      el("p", { class: "u-note", text: "Kettle is a prototype. It doesn't replace a smoke or CO detector, or 911." })));
  }
}
/** Today's urgent alerts stay listed after they're seen, so the day can be read back later. */
function drawAlertLog(n) {
  const box = $("#alert-log"); if (!box) return;
  const day = (srv.alerts || []).filter((a) => a.at > now() - 24 * 3600);
  const k = day.map((a) => `${a.id}:${a.checkin}:${a.seen ? 1 : 0}`).join(",");
  if (box.dataset.k === k) return; box.dataset.k = k; box.textContent = "";
  box.hidden = !day.length;
  if (!day.length) return;
  box.append(el("p", { class: "al-h", text: "Urgent alerts in the last 24 hours" }),
    el("ul", {}, ...day.slice().reverse().map((a) => el("li", { "data-ok": a.checkin === "ok" ? "1" : "" },
      el("span", { class: "al-t num", text: clock(a.at, t.tz_offset) }),
      el("span", { text: `${a.kind === "help" ? `"I need help" pressed` : SAFETY_TEXT[a.kind] || "urgent"}${a.checkin === "ok" ? `, then "I'm OK"` : a.checkin === "no_answer" ? ", no answer" : a.checkin === "help" && a.kind !== "help" ? `, then "I need help"` : ""}${a.seen ? " · seen" : ""}` })))));
}

// ---------------------------------------------------------------- alerts on this phone (Web Push, handover v3.5 3.3)
let pushKey = null, pushOn = null;
async function drawPush() {
  const box = $("#push"); if (!box) return;
  const sup = pushSupport();
  if (pushOn === null) {
    const sub = await currentSubscription();
    pushOn = !!sub;
    // re-send this phone's subscription on every visit (the server dedupes it), so alerts survive a server-side reset
    if (sub) api(`/api/h/${link.id}/push`, { method: "POST", key: link.key, body: { subscription: sub } }).catch(() => {});
  }
  box.textContent = "";
  const why = { "ios-needs-home-screen": "On iPhone: tap Share, then Add to Home Screen, open Kettle from there, then turn alerts on.",
    denied: "Notifications are blocked for this site. Allow them in your browser's site settings, then reload.",
    "no-push": "This browser can't get alerts. Try Chrome, Edge or Firefox, or Safari from the Home Screen.", "no-sw": "This browser can't get alerts. Try Chrome, Edge or Firefox." }[sup.why];
  const status = el("p", { class: "push-s", "data-on": pushOn ? "1" : "", text: pushOn ? "Alerts are on for this phone. Urgent sounds notify you even when Kettle is closed."
    : why || "Get a notification the moment Kettle hears a smoke alarm, a crash then a cry, screaming or a gunshot." });
  const msg = el("p", { class: "push-m", "aria-live": "polite" });
  const on = el("button", { class: "btn primary", type: "button", text: "Turn on alerts", disabled: !sup.ok || null, onclick: async () => {
    msg.textContent = "Turning on…";
    try {
      if (!pushKey) pushKey = (await api("/api/push/key")).publicKey;
      const sub = await subscribe(pushKey);
      await api(`/api/h/${link.id}/push`, { method: "POST", key: link.key, body: { subscription: sub } });
      pushOn = true; drawPush(); toast("Alerts are on");
    } catch (e) { msg.textContent = e.message || "Couldn't turn alerts on."; }
  } });
  const test = el("button", { class: "btn", type: "button", text: "Send a test alert", onclick: async () => {
    msg.textContent = "Sending…";
    try { const r = await api(`/api/h/${link.id}/pushtest`, { method: "POST", key: link.key, body: {} }); msg.textContent = `Sent to ${r.subscribed} phone${r.subscribed === 1 ? "" : "s"}. It should arrive in a few seconds.`; }
    catch (e) { msg.textContent = e.message || "Couldn't send a test."; }
  } });
  const off = el("button", { class: "btn quiet", type: "button", text: "Turn off", onclick: async () => {
    const sub = await currentSubscription();
    try { if (sub) await api(`/api/h/${link.id}/push`, { method: "DELETE", key: link.key, body: { endpoint: sub.endpoint } }); } catch {}
    await unsubscribe(); pushOn = false; drawPush();
  } });
  box.append(el("div", { class: "sec-head" }, el("h2", { class: "sec-title", text: "Urgent alerts" })), status,
    el("div", { class: "actions push-a" }, ...(pushOn ? [test, off] : [on])), msg,
    el("p", { class: "sec-foot", text: "Kettle is a prototype, not an emergency service. It doesn't replace a smoke or CO detector, or 911." }));
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

// before the parent's device has said yes: show how to connect it (only on the device that holds the kitchen key)
let inviteShown = "";
async function drawInvite() {
  const box = $("#invite");
  const home = homes()[link.id] || {};
  const need = t.heartbeat.state === "never";
  const key = need ? (home.kitchenKey ? "k" : "nok") : "";
  if (key === inviteShown) return; inviteShown = key; box.textContent = "";
  if (!need) return;
  const n = t.names, P = n.parentMid, R = n.room;
  if (!home.kitchenKey) { box.append(el("div", { class: "banner" }, el("p", {}, el("strong", { text: `Waiting for ${n.possMid} ${R} device.` }), ` Kettle starts when ${P} says yes on the ${R} screen.`))); return; }
  let code = home.kitchenCode;
  if (!code || (home.kitchenCodeExp || 0) < now() + 600) {
    try { const r = await api(`/api/h/${link.id}/code`, { method: "POST", key: link.key, body: { for: "kitchen", key: home.kitchenKey } });
      code = r.code; saveHome(link.id, { kitchenCode: code, kitchenCodeExp: r.codeExpires }); } catch { code = null; }
  }
  const url = linkFor("kitchen", link.id, home.kitchenKey);
  box.append(el("div", { class: "pair-card", style: "margin-top:20px" },
    el("p", { class: "step-k", text: `Next: connect the ${R} device` }),
    el("h2", { class: "section-title", text: `On ${n.possMid} ${R} device, go to ${location.host}/listen and type` }),
    code ? el("p", { class: "code-big num", html: `${code.slice(0, 3)}<span> </span>${code.slice(3)}` }) : null,
    el("p", { class: "meta muted", text: `Or send ${P} this link. Open it on the phone, tablet or laptop that stays in the ${R}.` }),
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
$("#add-rule")?.addEventListener("click", () => { if (draft.length < 3) { draft.push(t && !["kitchen", "home", "other"].includes(t.names.roomType) ? { type: "any_by", time: "10:00" } : { type: "kitchen_by", time: "10:00" }); fields(); } });
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
  const kitchenish = !t || ["kitchen", "home", "other"].includes(t.names.roomType);
  const presets = kitchenish ? [["Breakfast by 10", { type: "kitchen_by", time: "10:00" }], ["Lunch by 2", { type: "kitchen_by", time: "14:00" }],
    ["Evening meal by 8", { type: "kitchen_by", time: "20:00" }], ...(KINDS_SHOWN.has("kettle") ? [["Morning drink by 9", { type: "kind_by", kind: "kettle", time: "09:00" }]] : [])]
    : [["Up and about by 10", { type: "any_by", time: "10:00" }], ["Some activity by 2", { type: "any_by", time: "14:00" }], ["Some activity by 8 PM", { type: "any_by", time: "20:00" }],
      ...(KINDS_SHOWN.has("footsteps") ? [["Footsteps by 11", { type: "kind_by", kind: "footsteps", time: "11:00" }]] : [])];
  box.append(el("div", { class: "row presets", style: "margin-top:10px;flex-wrap:wrap;gap:8px" }, el("span", { class: "meta muted", text: "Quick add:" }),
    ...presets.map(([label, r]) => el("button", { class: "btn quiet", type: "button", text: label, disabled: draft.length >= 3 || null, onclick: () => { if (draft.length < 3) { draft.push({ ...r }); fields(); } } }))));
}

// ---------------------------------------------------------------- settings: invite, rename, delete
$("#menu-btn")?.addEventListener("click", async () => {
  if (!srv) return;
  const body = $("#settings-body"); body.textContent = "";
  const n = srv.names;
  const pIn = el("input", { class: "input", value: n.parent || "", maxlength: 24, placeholder: "Their first name, or what you call them", "aria-label": "What you call them" });
  const cIn = el("input", { class: "input", value: n.caregiver || "", maxlength: 24, "aria-label": "Your name" });
  body.append(
    el("div", { class: "field2" }, el("label", { text: "What you call them" }), pIn),
    el("div", { class: "field2" }, el("label", { text: "Your name, as the room screen shows it" }), cIn),
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
    el("p", { class: "meta muted", text: "Removes every label and setting from Kettle's server for good. The listening device stops sending." }),
    el("div", { class: "actions", style: "margin-top:12px" },
      el("button", { class: "btn danger-link", type: "button", text: "Delete everything", onclick: async (e) => {
        if (e.currentTarget.dataset.sure !== "1") { e.currentTarget.dataset.sure = "1"; e.currentTarget.textContent = "Press again to delete for good"; return; }
        try { await api(`/api/h/${link.id}`, { method: "DELETE", key: link.key }); forgetHome(link.id); location.href = "/"; } catch (err) { toast(err.message); }
      } }),
      el("span", { style: "flex:1" }), el("button", { class: "btn quiet", type: "button", text: "Close", onclick: closeSheets })));
  body.append(del);
  openSheet($("#settings"));
});
