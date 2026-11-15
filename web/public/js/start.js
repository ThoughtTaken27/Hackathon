// Setting up Kettle: three short steps. Who's here -> names -> connect the other screen (code, link, QR).
import { $, el, api, saveHome, linkFor, qr, copy, reduceMotion } from "./ui.js";
import { RELATION_LABELS, NAME_CHIPS, ROOMS, place, personName, caregiverName } from "./people.js";

const W = $("#wizard");
const st = { as: null, relation: null, parent: "", caregiver: "", room: "", roomName: "" };
const names = () => ({ parent: st.parent, caregiver: st.caregiver, relation: st.relation || "parent" });
const roomObj = () => ({ type: st.room || "kitchen", name: st.roomName });
const here = () => place(names(), roomObj(), "family", { mid: true });
const ICON = {
  phone: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M10.5 18.5h3"/></svg>',
  laptop: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="11" rx="2"/><path d="M2 19h20"/></svg>',
  chev: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>',
};
function show(node) {
  W.textContent = ""; W.append(node);
  if (!reduceMotion()) node.animate([{ opacity: 0, transform: "translateY(8px)", filter: "blur(4px)" }, { opacity: 1, transform: "none", filter: "none" }], { duration: 460, easing: "cubic-bezier(.22,1,.36,1)" });
  const f = node.querySelector("input, button"); if (f && f.tagName === "INPUT") f.focus();
}
const dots = (k) => el("span", { class: "dots", "aria-hidden": "true" }, [1, 2, 3].map((i) => el("i", { class: i <= k ? "on" : "" })));
const head = (k, title, lead) => [el("p", { class: "step-k" }, dots(k), `Step ${k} of 3`),
  el("h1", { class: "h1" }, ...(Array.isArray(title) ? [title[0], title[2] ? el("br") : null, el("em", { text: title[1] })].filter(Boolean) : [title])), lead ? el("p", { class: "lead", text: lead }) : null];

function step1() {
  const choice = (as, icon, t1, t2) => el("button", { class: "choice", type: "button", onclick: () => { st.as = as; step2(); } },
    el("span", { class: "ico", html: ICON[icon] }), el("span", {}, el("span", { class: "t1", text: t1 }), el("span", { class: "t2", style: "display:block", text: t2 })), el("span", { class: "chev", html: ICON.chev }));
  show(el("div", {}, ...head(1, ["Where are you ", "right now?", true], "Kettle needs two screens: a spare phone, tablet or laptop that stays in the room, and your own phone."),
    el("div", { class: "choices" },
      choice("family", "phone", "On my own phone or computer", "You'll get a code to type on the room device."),
      choice("kitchen", "laptop", "At the room device", "The spare phone, tablet or laptop that will stay in the room. You'll scan a code with your phone.")),
    el("p", { class: "meta muted", style: "margin-top:20px" }, "Already have a six-letter code? ", el("a", { href: "/pair", text: "Enter it here" }), ".")));
}

function chipGroup(items, onPick, selected) {
  const box = el("div", { class: "row", style: "margin-top:4px", role: "group" });
  const btns = items.map(([id, label]) => el("button", { class: "btn", type: "button", text: label, "aria-pressed": "false", onclick: () => { onPick(id); sync(); } }));
  const sync = (sel = selected()) => btns.forEach((b, k) => { const on = items[k][0] === sel; b.setAttribute("aria-pressed", String(on)); b.classList.toggle("primary", on); });
  box.append(...btns); sync();
  return { node: box, sync };
}

function step2() {
  const err = el("p", { class: "err", role: "alert" });
  const nameField = el("div", { class: "field2" }), careField = el("div", { class: "field2" });
  const pIn = el("input", { class: "input", value: st.parent, maxlength: 24, autocomplete: "off", id: "p", placeholder: "For example Mom, Dad, Nani, Abuela, or their first name" });
  pIn.addEventListener("input", () => { st.parent = pIn.value; });
  const nameChips = el("div", { class: "row", style: "margin-top:4px" }, NAME_CHIPS.map((v) => el("button", { class: "btn", type: "button", text: v, onclick: () => { pIn.value = v; st.parent = v; } })));
  nameField.append(el("label", { for: "p", text: "What do you call them?" }), pIn, nameChips, el("p", { class: "hint", text: "Use their first name if you like. Leave it empty and Kettle says \"your parent\" or similar." }));
  const cIn = el("input", { class: "input", value: st.caregiver, maxlength: 24, autocomplete: "given-name", id: "c", placeholder: "Your first name" });
  const careLabel = el("label", { for: "c" }), careHint = el("p", { class: "hint" });
  careField.append(careLabel, cIn, careHint);
  const rel = chipGroup(Object.entries(RELATION_LABELS), (id) => { st.relation = id; layout(); }, () => st.relation);
  const roomNote = el("p", { class: "hint", style: "display:none", text: "Safety only: no sounds are shown, only alerts. Many families prefer the hallway outside." });
  const rIn = el("input", { class: "input", maxlength: 24, id: "rn", placeholder: "Room name, for example Workshop or Sunroom", style: "display:none;margin-top:8px", value: st.roomName });
  rIn.addEventListener("input", () => { st.roomName = rIn.value; });
  const room = chipGroup(Object.values(ROOMS).map((r) => [r.id, r.label]), (id) => { st.room = id; layout(); }, () => st.room);
  function layout() {
    const self = st.relation === "self";
    nameField.style.display = self ? "none" : "";
    careLabel.textContent = self ? "Who should Kettle tell if something seems wrong?" : "Your first name";
    cIn.placeholder = self ? "A friend, relative or neighbour's first name" : "Your first name";
    careHint.textContent = self ? "Kettle shows this name on your screen, so you know who can see the timeline." : "They see your name on their screen, so they know exactly who can see the timeline.";
    roomNote.style.display = st.room === "bathroom" ? "" : "none";
    rIn.style.display = st.room === "other" ? "" : "none";
    rel.sync(); room.sync();
  }
  layout();
  const go = el("button", { class: "btn primary lg", type: "button", text: "Create our Kettle", onclick: async () => {
    const self = st.relation === "self";
    st.caregiver = cIn.value.trim(); st.parent = self ? "" : pIn.value.trim(); st.roomName = rIn.value.trim();
    if (!st.relation) { err.textContent = "Choose who this is for."; return; }
    if (!st.room) { err.textContent = "Choose where the device will listen."; return; }
    if (st.room === "other" && !st.roomName) { err.textContent = "Add a room name, for example Workshop or Sunroom."; rIn.focus(); return; }
    if (!st.caregiver) { err.textContent = self ? "Add the first name of someone Kettle can tell." : "Add your first name. They see it on their screen."; cIn.focus(); return; }
    go.disabled = true; go.textContent = "Creating…";
    try {
      const room = { type: st.room, name: st.room === "other" ? st.roomName : "" };
      const r = await api("/api/households", { method: "POST", body: { parent: st.parent, relation: st.relation, room, caregiver: st.caregiver, tz: Intl.DateTimeFormat().resolvedOptions().timeZone, as: st.as } });
      saveHome(r.id, { kitchenKey: r.kitchenKey, familyKey: r.familyKey, parent: st.parent, relation: st.relation, room, caregiver: st.caregiver, [r.codeFor + "Code"]: r.code, [r.codeFor + "CodeExp"]: r.codeExpires });
      step3(r);
    } catch (e) { err.textContent = e.message || "Couldn't reach Kettle. Check the connection and try again."; go.disabled = false; go.textContent = "Create our Kettle"; }
  } });
  show(el("div", {}, ...head(2, ["A little about ", "them"], "These names appear on both screens, so the words feel like yours."),
    el("div", { class: "field2" }, el("label", { text: "Who is this for?", id: "rl" }), rel.node), nameField,
    el("div", { class: "field2" }, el("label", { text: "Where will the device listen?" }), room.node, rIn, roomNote), careField,
    err, el("div", { class: "actions" }, go, el("button", { class: "btn quiet", type: "button", text: "Back", onclick: step1 }))));
  cIn.addEventListener("keydown", (e) => e.key === "Enter" && go.click());
}

async function step3(r) {
  const C = caregiverName(names(), "family"), self = st.relation === "self";
  const spot = here(), who = personName(names()), whoMid = personName(names(), { mid: true });
  const otherUrl = r.codeFor === "kitchen" ? linkFor("kitchen", r.id, r.kitchenKey) : linkFor("family", r.id, r.familyKey);
  const mine = r.as === "kitchen" ? linkFor("kitchen", r.id, r.kitchenKey) : linkFor("family", r.id, r.familyKey);
  const code = el("p", { class: "code-big num", html: `${r.code.slice(0, 3)}<span> </span>${r.code.slice(3)}` });
  const card = el("div", { class: "pair-card" });
  if (r.codeFor === "kitchen") {
    card.append(el("p", { class: "step-k", text: `On the device that stays in ${spot}` }),
      el("ol", { class: "steps-mini" }, el("li", { text: `Open ${location.host}/kitchen in Chrome or Safari on a spare phone, tablet or laptop.` }), el("li", { text: "Type this code:" })), code,
      el("p", { class: "meta muted", text: "The code works for 48 hours. Or send this link to that device:" }),
      el("div", { class: "linkbox" }, el("code", { text: otherUrl }), el("button", { class: "btn", type: "button", text: "Copy", onclick: () => copy(otherUrl) })),
      el("ol", { class: "steps-mini", style: "counter-reset: s 2" }, el("li", { text: self ? "Read one screen and press Yes. Nothing starts without that." : `${who} reads one screen and presses Yes. Nothing starts without that.` }), el("li", { text: `Kettle then shows ${self ? "you" : whoMid} where to put it and checks that it can hear the room. About two minutes.` })));
  } else {
    const q = await qr(otherUrl, 196);
    card.append(el("p", { class: "step-k", text: self ? "On your phone" : `On ${C === "you" ? "your" : C + "'s"} phone` }),
      el("div", { class: "pair" }, el("div", {}, el("p", { class: "panel-h", text: "Scan with your phone's camera" }), el("p", { class: "meta muted", text: `Or open ${location.host}/pair on it and type:` }), code), q),
      el("div", { class: "linkbox" }, el("code", { text: otherUrl }), el("button", { class: "btn", type: "button", text: "Copy", onclick: () => copy(otherUrl) })));
  }
  show(el("div", {}, ...head(3, r.codeFor === "kitchen" ? ["Now connect the device in ", spot] : ["Now connect ", "your phone"],
    r.codeFor === "kitchen" ? "You can do this now, or the next time you're there. Your view shows the code until it's connected." : `This device is now the screen in ${spot}. Connect your phone, then hand over to ${self ? "yourself" : whoMid}.`),
    card,
    el("div", { class: "actions" },
      el("a", { class: "btn primary lg", href: mine, text: r.as === "kitchen" ? `Continue to the screen in ${spot}` : "Open my family view" }),
      el("button", { class: "btn lg", type: "button", text: "Copy my own link", onclick: () => copy(mine) })),
    el("p", { class: "meta muted", style: "margin-top:14px", text: "Save your link somewhere safe. Anyone with it can see this home's timeline. You can delete the home any time in Settings." })));
}

step1();
