// "What do you want to call this device?" — asked before a code is entered, on /pair and on the room screen. One pairing code
// works for any number of devices (48 hours); the name tells the family which device is which ("Kitchen laptop", "Mum's phone").
import { el } from "./ui.js";

const KEY = "kettle.deviceName";
export const savedDeviceName = () => { try { return localStorage.getItem(KEY) || ""; } catch { return ""; } };
export const saveDeviceName = (n) => { try { localStorage.setItem(KEY, n); } catch {} };

/** A labelled name box with tap-to-fill suggestions. Returns { node, input, value(), focus() }. */
export function deviceNameField(suggestions, { big = false } = {}) {
  const input = el("input", { class: "input" + (big ? " lg" : ""), id: "devname", maxlength: 24, autocomplete: "off", value: savedDeviceName(),
    placeholder: suggestions[0] ? `For example: ${suggestions[0]}` : "A short name", enterkeyhint: "next" });
  const chips = el("div", { class: "row", style: "flex-wrap:wrap;gap:8px;margin-top:10px" },
    ...suggestions.map((s) => el("button", { class: "btn sm", type: "button", text: s, onclick: () => { input.value = s; input.focus(); } })));
  const node = el("div", { class: "field2" },
    el("label", { for: "devname", text: big ? "Device name" : "What do you want to call this device?" }), input, chips,
    el("p", { class: "hint", text: "Everyone in the family sees this name, so they know which device is which." }));
  return { node, input, value: () => input.value.trim().slice(0, 24), focus: () => input.focus() };
}
