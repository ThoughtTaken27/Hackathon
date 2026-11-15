// "Beyond the research home": every number here is read from data/beyond.json (eval/beyond.py) and
// data/stress_teach.json (eval/stress_teach.py). None is typed by hand. Shown above the benchmark on How sure (plan G1, G4, G8).
import { KIND_NAMES } from "./core.js";
const h = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) (k === "text" ? (n.textContent = v) : n.setAttribute(k, v));
  for (const c of kids.flat()) if (c != null) n.append(c);
  return n;
};
const p = (r) => (r && r.pct != null ? `${r.pct.toFixed(1)}%` : "–");
const ci = (r) => (r && r.ci95 ? ` (${r.ci95[0].toFixed(0)}–${r.ci95[1].toFixed(0)})` : "");
const n = (r) => (r ? `${r.k}/${r.n}` : "");
function table(head, rows, caption) {
  return h("div", { class: "tbl-wrap" }, h("table", { class: "tbl" }, caption ? h("caption", { text: caption }) : null,
    h("thead", {}, h("tr", {}, head.map((x) => h("th", { scope: "col", text: x })))),
    h("tbody", {}, rows.map((r) => h("tr", {}, r.map((x, i) => (i ? h("td", { text: x }) : h("th", { scope: "row", text: x }))))))));
}

async function main() {
  const box = document.getElementById("beyond");
  let B, S;
  try { [B, S] = await Promise.all(["/data/beyond.json", "/data/stress_teach.json"].map((u) => fetch(u).then((r) => r.json()))); } catch { return; }
  const sec = h("section", { class: "beyond", "aria-labelledby": "beyond-h" });
  sec.append(h("h2", { class: "section-title", id: "beyond-h", text: "Beyond the research home" }),
    h("p", { class: "meta", text: "Two on-device additions, measured before the app used them: teaching Kettle a new kitchen at setup, and naming everyday household sounds. Thresholds were picked on dev folds 1–2 and are reported on folds 3–4, or on public ESC-50 clips never used to pick them. The held-out test was not re-run." }));

  // teach this kitchen
  const E = B.enrolment;
  const m = E.by_minutes;
  sec.append(h("h3", { text: "Teaching Kettle a kitchen (3 minutes at setup)" }),
    h("p", { class: "meta", text: `Kettle's setup step records about a minute each of quiet, washing up and cooking. Those windows stay on the laptop and only help windows the model couldn't name (alpha ${E.alpha}, radius ${E.rho}× the setup spread, ${E.knn} nearest). Simulated two ways (the second opinion is not included here).` }),
    table(["Simulation", "Before", "After", "Not sure before → after"], [
      ...Object.entries(m).map(([min, v]) => [`New microphone, ${min} min per activity (macro F1, N=${v.before.n_windows})`, v.before.macro_f1.toFixed(1), v.after.macro_f1.toFixed(1), `${p(v.before.not_sure_share)} → ${p(v.after.not_sure_share)}`]),
      ...S.teach.map((v) => [`${v.condition[0].toUpperCase() + v.condition.slice(1)}, 1 min (kitchen noticed, N=${v.before.kitchen_noticed.n})`, p(v.before.kitchen_noticed), p(v.after.kitchen_noticed), `${p(v.before.not_sure)} → ${p(v.after.not_sure)}`])]),
    h("p", { class: "gap", text: "A small, honest gain: fewer Not sure windows and a little more kitchen activity noticed, no rise in false kitchen activity. It does nothing for the cheap-microphone case. An earlier version that always mixed in the setup windows made results worse, so it was dropped." }));

  // named sounds
  const T = B.sound_types.types;
  sec.append(h("h3", { text: "Everyday sounds Kettle computes (15; only those that pass the bar below are shown to families)" }),
    h("p", { class: "meta", text: "Read straight from the sound model's own outputs (no training). Each threshold is the 99th percentile of that sound's score in recordings where it shouldn't occur." }),
    table(["Sound", "Found in matching public clips", "Named where it shouldn't be (dev)"],
      Object.values(T).map((r) => [r.name, r.esc50_hit ? `${p(r.esc50_hit)} (${n(r.esc50_hit)})` : r.heard_in_related_dev_test ? `${p(r.heard_in_related_dev_test)} of ${r.heard_in_related_dev_test.related.join("/")} windows` : "no public test clips", `${p(r.false_fire_dev_test)} (${n(r.false_fire_dev_test)})`])),
    h("p", { class: "gap", text: `Privacy: when a cough, snore, crying or bathroom sound is louder than every allowed sound, Kettle names nothing. Sensitive public clips given any name: ${p(B.sound_types.veto.sensitive_named_before_veto)} before this rule, ${p(B.sound_types.sensitive_any_name)} after (N=${B.sound_types.sensitive_any_name.n}). Still missed: a toilet flush is called running water or a kettle ${p(B.sound_types.sensitive_by_category.toilet_flush)} of the time.` }));

  sec.append(h("h3", { text: "\"Unlike anything it learned\": the threshold trade-off" }),
    table(["Novelty threshold", "Dev windows accepted", "Off-list clips accepted"], B.novelty.curve.map((c) => [c.threshold.toFixed(1) + (Math.abs(c.threshold - B.novelty.frozen_threshold) < 0.05 ? " (used)" : ""), `${c.dev_accepted_pct}%`, `${c.offlist_accepted_pct}%`])),
    h("p", { class: "gap", text: "The threshold stays frozen. Teaching Kettle a kitchen lifts it only near that kitchen's own setup sounds." }));

  box.append(sec);
  accuracy(box);
}

// Detection accuracy round, Sun Nov 15 (handover v3.2): read from data/accuracy.json (tools/export_accuracy.py <- results/*.json).
async function accuracy(box) {
  let A;
  try { A = await fetch("/data/accuracy.json").then((r) => r.json()); } catch { return; }
  const sec = h("section", { class: "beyond", "aria-labelledby": "acc-h" });
  const set = { sins_dev_sessions: "Research home, dev sessions", kitchen20_tune: "Kitchen20 clips, tune half", kitchen20_test: "Kitchen20 clips, test half",
    desed_tune: "DESED homes, tune half", desed_test: "DESED homes, test half" };
  const K = A.kitchen_naming;
  sec.append(h("h2", { class: "section-title", id: "acc-h", text: "Kitchen naming after a live test in a real kitchen" }),
    h("p", { class: "meta", text: "In a teammate's kitchen, pots while cooking showed as \"washing up\" and a ladle as \"eating\": each 10-second window was named from its single loudest kitchen tag. Since Sun Nov 15 a kitchen stretch is named from evidence across all its windows (rules 2c, 2d). Same events through the app's own timeline code, old rule vs new." }),
    table(["Set", "Meal stretches named right", "Wrong activity", "False kitchen on non-meal sounds"],
      Object.entries(K).map(([k, v]) => [`${set[k] || k} (N=${v.n})`, `${v.before.right} → ${v.after.right} of ${v.before.meal}`, `${v.before.wrong_activity} → ${v.after.wrong_activity}`, `${v.before.false_kitchen} → ${v.after.false_kitchen} of ${v.before.not_meal}`])),
    h("p", { class: "gap", text: "Honesty note: the public test halves were scored more than once while this rule was built (details in results/kitchen_naming.json). The clean measurement is a recording of a real kitchen, which we have not made yet." }));
  const S = A.sound_head;
  const shownN = Object.values(S.head).filter((v) => v.shown).length;
  sec.append(h("h3", { text: "Named sounds: a trained sound head, held to a pre-registered bar" }),
    h("p", { class: "meta", text: `Each everyday sound has its own small classifier on the model's embedding, trained only on the tune halves of five public sets. A name is shown to families only if, on the held-out halves, precision ≥ ${S.bar.precision}% and recall ≥ ${S.bar.recall}% (eval/PREREGISTER-SOUNDS-V2.md). Before it, hand-written rules on single tags passed for 1 sound; the head passes for ${shownN}.` }),
    table(["Sound", "Precision: rules → head", "Recall: rules → head", "False names per 1,000 other windows", "Shown"],
      Object.keys(S.head).map((k) => [KIND_NAMES[k] || k, `${p(S.rules[k].precision)} → ${p(S.head[k].precision)}`, `${p(S.rules[k].recall)} → ${p(S.head[k].recall)} (N=${S.head[k].recall.n})`,
        `${S.rules[k].false_per_1000} → ${S.head[k].false_per_1000}`, S.head[k].shown ? "yes" : S.hidden_on_tune.includes(k) ? "hidden (failed on tune, never tested)" : "hidden"])),
    h("p", { class: "gap", text: `Hidden sounds are still computed on the device (for the privacy veto and safety notes) but never sent. Frying, dishes and the microwave came close and stay hidden: we don't move the bar after seeing the result. Honesty note: these held-out halves were scored once before, with the rules (results/sounds.json); every choice in the head came from the tune halves. Ten-second public clips are not a real kitchen.` }));
  const J = A.judge.dev, best = J["0.9"];
  sec.append(h("h3", { text: "Tried and not shipped" }),
    h("p", { class: "gap", text: `A trained judge on the 527 sound tags, across many homes: at its strictest it removed every wrong-activity call (${best.wrong_activity[0]} → ${best.wrong_activity[1]}) but named fewer real meals (${best.right[0]} → ${best.right[1]}), so it failed the gate we wrote before running it. Bridging "unlike anything it learned" gaps and naming TV from its tag didn't move the development numbers. All in results/judge.json and results/confetti.json.` }));
  box.append(sec);
}
main();
