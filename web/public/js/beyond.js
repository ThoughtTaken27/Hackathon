// "Beyond the research home": every number here is read from data/beyond.json (eval/beyond.py) and
// data/stress.json (eval/stress.py). None is typed by hand. Shown above the benchmark on How sure (plan G1, G4, G8).
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
  try { [B, S] = await Promise.all(["/data/beyond.json", "/data/stress.json"].map((u) => fetch(u).then((r) => r.json()))); } catch { return; }
  const sec = h("section", { class: "beyond", "aria-labelledby": "beyond-h" });
  sec.append(h("h2", { class: "section-title", id: "beyond-h", text: "Beyond the research home" }),
    h("p", { class: "meta", text: "Everything further down this page comes from one research home (SINS). This section tests what that benchmark can't: quieter cooks, a TV left on, echoey rooms, cheap microphones, other everyday sounds, and teaching Kettle a new kitchen. Thresholds were picked on dev folds 1–2 and are reported on folds 3–4, or on public ESC-50 clips never used to pick them. The held-out test was not re-run." }),
    h("p", { class: "callout", text: "Real kitchens: not measured yet. A live test with 10 recordings from other kitchens found the right activity on top but marked most windows \"unlike anything it learned\". The protocol for measuring real kitchens is written down before recording (docs/REAL-KITCHEN-PROTOCOL.md)." }));

  // where it breaks
  const row = (label, r) => [label, `${p(r.right)}${ci(r.right)}`, p(r.not_sure), `${p(r.kitchen_noticed)} (${n(r.kitchen_noticed)})`];
  sec.append(h("h3", { text: "Where Kettle breaks" }),
    h("p", { class: "meta", text: `The ${S.clips} sample clips (9 sessions kept out of training), changed the way real kitchens change them. Small N: read the slope, not the decimals.` }),
    table(["Condition", "Right activity (95% CI)", "Not sure", "Kitchen activity noticed"], [
      ...S.loudness.map((r) => row(r.gain_db ? `${-r.gain_db} dB quieter` : "As recorded", r)),
      ...S.tv.filter((r) => r.snr_db != null).map((r) => row(`TV underneath, ${r.snr_db} dB below the sound`, r)),
      ...S.room.filter((r) => r.condition !== "clean").map((r) => row(r.condition[0].toUpperCase() + r.condition.slice(1), r))]),
    h("p", { class: "gap", text: "Worst case: a TV left on. With the TV only 5 dB below the cooking, kitchen activity is almost never noticed. Kettle then shows TV or Not sure, never a made-up meal, but a family with the TV on all morning should not rely on the breakfast check." }));

  // teach this kitchen
  const E = B.enrolment;
  const m = E.by_minutes;
  sec.append(h("h3", { text: "Teaching Kettle a kitchen (3 minutes at setup)" }),
    h("p", { class: "meta", text: `Kettle's setup step records about a minute each of quiet, washing up and cooking. Those windows stay on the laptop and only help windows the model couldn't name (alpha ${E.alpha}, radius ${E.rho}× the setup spread, ${E.knn} nearest). Simulated two ways.` }),
    table(["Simulation", "Before", "After", "Not sure before → after"], [
      ...Object.entries(m).map(([min, v]) => [`New microphone, ${min} min per activity (macro F1, N=${v.before.n_windows})`, v.before.macro_f1.toFixed(1), v.after.macro_f1.toFixed(1), `${p(v.before.not_sure_share)} → ${p(v.after.not_sure_share)}`]),
      ...S.teach.map((v) => [`${v.condition[0].toUpperCase() + v.condition.slice(1)}, 1 min (kitchen noticed, N=${v.before.kitchen_noticed.n})`, p(v.before.kitchen_noticed), p(v.after.kitchen_noticed), `${p(v.before.not_sure)} → ${p(v.after.not_sure)}`])]),
    h("p", { class: "gap", text: "A small, honest gain: fewer Not sure windows and a little more kitchen activity noticed, no rise in false kitchen activity. It does nothing for the cheap-microphone case. An earlier version that always mixed in the setup windows made results worse, so it was dropped." }));

  // named sounds
  const T = B.sound_types.types;
  sec.append(h("h3", { text: "Everyday sounds Kettle can name (18)" }),
    h("p", { class: "meta", text: "Read straight from the sound model's own outputs (no training). Each threshold is the 99th percentile of that sound's score in recordings where it shouldn't occur." }),
    table(["Sound", "Found in matching public clips", "Named where it shouldn't be (dev)"],
      Object.values(T).map((r) => [r.name, r.esc50_hit ? `${p(r.esc50_hit)} (${n(r.esc50_hit)})` : r.heard_in_related_dev_test ? `${p(r.heard_in_related_dev_test)} of ${r.heard_in_related_dev_test.related.join("/")} windows` : "no public test clips", `${p(r.false_fire_dev_test)} (${n(r.false_fire_dev_test)})`])),
    h("p", { class: "gap", text: `Privacy: when a cough, snore, crying or bathroom sound is louder than every allowed sound, Kettle names nothing. Sensitive public clips given any name: ${p(B.sound_types.veto.sensitive_named_before_veto)} before this rule, ${p(B.sound_types.sensitive_any_name)} after (N=${B.sound_types.sensitive_any_name.n}). Still missed: a toilet flush is called running water or a kettle ${p(B.sound_types.sensitive_by_category.toilet_flush)} of the time.` }));

  // appliance + novelty
  const A = B.appliance_gate;
  sec.append(h("h3", { text: "Appliance hum and \"unlike anything it learned\"" }),
    h("p", { class: "meta", text: `Cooking is held back as Not sure when fan, microwave or vacuum hum is louder than every kitchen sound. On dev folds 3–4 it keeps ${p(A.dev_test_correct_cooking_kept)} of correct Cooking and removes ${A.dev_test_false_cooking_before - A.dev_test_false_cooking_after} of ${A.dev_test_false_cooking_before} false Cooking windows. A small effect; it targets the vacuum the live test caught.` }),
    table(["Novelty threshold", "Dev windows accepted", "Off-list clips accepted"], B.novelty.curve.map((c) => [c.threshold.toFixed(1) + (Math.abs(c.threshold - B.novelty.frozen_threshold) < 0.05 ? " (used)" : ""), `${c.dev_accepted_pct}%`, `${c.offlist_accepted_pct}%`])),
    h("p", { class: "gap", text: "The threshold stays frozen: without real-kitchen recordings there is no fair way to loosen it. Teaching Kettle a kitchen lifts it only near that kitchen's own setup sounds." }));

  sec.append(h("h3", { text: "What can't be tested here" }),
    h("p", { class: "meta", text: "Age and sex fairness can't be measured on one person's home. Tested instead: loudness, TV, room echo, microphone quality and sounds outside the 9 activities. Not tested: other cooking styles, other languages on TV, several people at once." }));
  box.append(sec);
}
main();
