// "Beyond the research home": every number here is read from data/beyond.json (eval/beyond.py) and
// data/stress_teach.json (eval/stress_teach.py). None is typed by hand. Shown above the benchmark on How sure (plan G1, G4, G8).
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
  sec.append(h("h3", { text: "Everyday sounds Kettle can name (15)" }),
    h("p", { class: "meta", text: "Read straight from the sound model's own outputs (no training). Each threshold is the 99th percentile of that sound's score in recordings where it shouldn't occur." }),
    table(["Sound", "Found in matching public clips", "Named where it shouldn't be (dev)"],
      Object.values(T).map((r) => [r.name, r.esc50_hit ? `${p(r.esc50_hit)} (${n(r.esc50_hit)})` : r.heard_in_related_dev_test ? `${p(r.heard_in_related_dev_test)} of ${r.heard_in_related_dev_test.related.join("/")} windows` : "no public test clips", `${p(r.false_fire_dev_test)} (${n(r.false_fire_dev_test)})`])),
    h("p", { class: "gap", text: `Privacy: when a cough, snore, crying or bathroom sound is louder than every allowed sound, Kettle names nothing. Sensitive public clips given any name: ${p(B.sound_types.veto.sensitive_named_before_veto)} before this rule, ${p(B.sound_types.sensitive_any_name)} after (N=${B.sound_types.sensitive_any_name.n}). Still missed: a toilet flush is called running water or a kettle ${p(B.sound_types.sensitive_by_category.toilet_flush)} of the time.` }));

  sec.append(h("h3", { text: "\"Unlike anything it learned\": the threshold trade-off" }),
    table(["Novelty threshold", "Dev windows accepted", "Off-list clips accepted"], B.novelty.curve.map((c) => [c.threshold.toFixed(1) + (Math.abs(c.threshold - B.novelty.frozen_threshold) < 0.05 ? " (used)" : ""), `${c.dev_accepted_pct}%`, `${c.offlist_accepted_pct}%`])),
    h("p", { class: "gap", text: "The threshold stays frozen. Teaching Kettle a kitchen lifts it only near that kitchen's own setup sounds." }));

  box.append(sec);
}
main();
