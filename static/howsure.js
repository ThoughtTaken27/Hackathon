// "How sure is Kettle?": every number comes from results/metrics.json via /api/results. Nothing is typed by hand.
"use strict";

(async function () {
  const box = document.getElementById("content");
  let r;
  try { r = await api("/api/results"); } catch (e) { r = { status: "error" }; }
  if (r.status !== "ok") {
    document.getElementById("split-line").textContent = "";
    box.append(el("section", { class: "card" },
      el("p", { class: "verdict", text: "No test results yet." }),
      el("p", { text: "Run python -m eval to make them. This page only ever shows numbers from that file." })));
    return;
  }
  renderResults(box, r);
  if (location.hash) { const t = document.querySelector(location.hash); if (t) t.scrollIntoView(); }
})();

const pct = (x) => (x == null ? "–" : `${x.value.toFixed(1)}%`);
const ci = (x) => (x && x.ci95 ? `${x.ci95[0].toFixed(0)}–${x.ci95[1].toFixed(0)}` : "");
const nm = (c) => ACT_NAME[c] || c;

function verdict(per, conf) {
  // Built from the numbers: what it almost always catches, what it mixes up most, what is weakest.
  const strong = per.filter((c) => c.recall.value >= 95 && c.precision.value >= 90).map((c) => nm(c.class).toLowerCase().replace("tv", "TV"));
  let worstPair = null, worstN = 0;
  for (let i = 0; i < 9; i++) for (let j = 0; j < 9; j++) {
    if (i !== j && conf[i][j] + conf[j][i] > worstN && i < j) { worstN = conf[i][j] + conf[j][i]; worstPair = [i, j]; }
  }
  const weakest = per.slice().sort((a, b) => a.f1.value - b.f1.value)[0];
  const parts = [];
  if (strong.length) parts.push(`Kettle catches ${listWords(strong)} almost always.`);
  if (worstPair) parts.push(`It most often mixes up ${nm(per[worstPair[0]].class).toLowerCase()} and ${nm(per[worstPair[1]].class).toLowerCase()}.`);
  parts.push(`${nm(weakest.class)} is its weakest activity.`);
  return parts.join(" ");
}
// Headline numbers count up once on load (600 ms, ease-out); reduced motion shows the final value at once.
function countUp(node, x) {
  if (!x || x.value == null || matchMedia("(prefers-reduced-motion: reduce)").matches) return node;
  const end = x.value, t0 = performance.now();
  const step = (t) => {
    const k = Math.min(1, (t - t0) / 600), e = 1 - Math.pow(1 - k, 3);
    node.textContent = `${(end * e).toFixed(1)}%`;
    if (k < 1) requestAnimationFrame(step);
  };
  node.textContent = "0.0%";
  requestAnimationFrame(step);
  return node;
}
function listWords(xs) { return xs.length <= 1 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`; }

function section(title, id, ...kids) {
  return el("section", { class: "card", id, style: "margin-top:20px" }, el("h2", { class: "section-title", text: title }), ...kids);
}

function renderResults(box, r) {
  const d = r.dev, ev = r.dcase_eval && r.dcase_eval.ours_ch0 ? r.dcase_eval : null;
  const main = ev || d;
  const per = main.ours_ch0.per_class;
  const splitText = ev
    ? `Held-out test, run once on ${ev.run.started}: the official DCASE 2018 eval sample (${ev.n_clips} clips). Earlier rows: development folds.`
    : `Development folds (also used to choose the model), N = ${d.n_clips} clips from ${d.n_sessions} sessions. The held-out test hasn't been run yet.`;
  document.getElementById("split-line").textContent = splitText;

  const kc = Object.fromEntries(per.map((c) => [c.class, c]));
  if (kc.cooking && kc.dishwashing && kc.eating) {
    box.append(el("p", { class: "verdict", text: `For the kitchen, on ${ev ? "test clips it had never heard" : "development clips"}: Kettle caught ${kc.cooking.recall.value.toFixed(0)}% of cooking, ${kc.dishwashing.recall.value.toFixed(0)}% of washing up and ${kc.eating.recall.value.toFixed(0)}% of eating. When it isn't sure, it says "Not sure" instead of guessing.` }));
  }
  box.append(el("p", { class: "gap", text: verdict(per, main.ours_ch0.confusion) }));
  // lead with the measured gap (addendum item 5): what a Mac already ships vs Kettle, same clips, same metric
  const apple = ev ? ev.baselines && ev.baselines.apple_zeroshot : d.baselines.apple_zeroshot && d.baselines.apple_zeroshot.macro_f1;
  const oursHead = ev ? (ev.slices.unknown || ev.slices.all).ch0 : d.ours_ch0.macro_f1;
  if (apple && apple.value != null) {
    box.append(el("p", { class: "gap" },
      el("span", { text: "On the same clips, Kettle on one microphone scores " }), el("strong", { class: "num", text: pct(oursHead) }),
      el("span", { text: ` macro F1: close to the official 2018 DCASE baseline's published ${r.published.dcase2018_baseline.eval_known_mic} (known microphones) / ${r.published.dcase2018_baseline.eval_unknown_mic} (unseen), but not directly comparable, because they scored the full test set and trained on all development data (best entry ${r.published.best_entry.eval_known_mic} / ${r.published.best_entry.eval_unknown_mic}). These are recordings from one research home, not yet a real kitchen. For context only, Apple's built-in sound classifier (zero-shot, a different label set) scores ` }),
      el("strong", { class: "num", text: pct(apple) }),
      el("span", { class: "muted", text: ` (${ev ? "held-out test" : "development folds"}).` })));
  }


  // headline numbers
  const head = el("div", { class: "stat-row" });
  const stat = (label, x, sub) => el("div", { class: "stat" }, countUp(el("p", { class: "stat-n num", text: pct(x) }), x),
    el("p", { class: "meta", text: label }), el("p", { class: "meta muted", text: sub }));
  if (ev) {
    const u = ev.slices.unknown || ev.slices.all;
    head.append(stat(ev.slices.unknown ? "Microphones it never heard (4-mic average)" : "All eval microphones (4-mic average)", u.node_avg, `95% CI ${ci(u.node_avg)} · N = ${u.node_avg.n_clips}`),
      stat("One microphone, like a laptop's", u.ch0, `95% CI ${ci(u.ch0)} · N = ${u.ch0.n_clips}`));
    const a = ev.baselines && ev.baselines.apple_zeroshot;
    if (a && a.value != null) head.append(stat("Apple's built-in sound classifier (zero-shot)", a, `same clips · CI ${ci(a)}`));
  } else {
    head.append(stat("One microphone, like a laptop's", d.ours_ch0.macro_f1, `95% CI ${ci(d.ours_ch0.macro_f1)} · N = ${d.n_clips}`),
      stat("Four-mic average (how DCASE scored it)", d.ours_node_avg.macro_f1, `95% CI ${ci(d.ours_node_avg.macro_f1)}`));
    const a = d.baselines.apple_zeroshot;
    if (a && a.macro_f1) head.append(stat("Apple's built-in sound classifier (zero-shot)", a.macro_f1, `same clips · CI ${ci(a.macro_f1)}`));
  }
  box.append(el("section", { class: "card" }, el("h2", { class: "section-title", text: "Overall score (higher is better): macro F1, the average over the 9 activities of how well each is caught without false alarms" }), head));

  // the caregiver's metric
  const ma = (ev && ev.meal_activity) || d.meal_activity;
  if (ma) {
    box.append(section("What Meera's check uses: any kitchen activity (cooking, washing up or eating)", "meal",
      el("div", { class: "stat-row" },
        el("div", { class: "stat" }, el("p", { class: "stat-n num", text: pct(ma.caught) }), el("p", { class: "meta", text: "of kitchen-activity windows caught" }),
          el("p", { class: "meta muted", text: `missed ${ma.missed} of ${ma.n_meal} · CI ${ci(ma.caught)}` })),
        el("div", { class: "stat" }, el("p", { class: "stat-n num", text: pct(ma.false_alarm_rate) }), el("p", { class: "meta", text: "of other windows wrongly called kitchen activity" }),
          el("p", { class: "meta muted", text: `${ma.false_alarms} of ${ma.n_other} · CI ${ci(ma.false_alarm_rate)}` })),
        el("div", { class: "stat" }, el("p", { class: "stat-n num", text: pct(ma.right_when_it_says_so) }), el("p", { class: "meta", text: "right when it says kitchen activity" }),
          el("p", { class: "meta muted", text: `CI ${ci(ma.right_when_it_says_so)}` }))),
      el("p", { class: "meta muted", style: "margin-top:8px", text: `${ev && ev.meal_activity ? "Held-out test (the same frozen predictions; this metric was computed after the run)" : "Development folds"}, one microphone, 10-second windows, reweighted to how common each activity really is.` })));
  }

  // per activity: misses and false alarms
  const tb = el("tbody");
  for (const c of per) {
    tb.append(el("tr", {},
      el("td", {}, el("span", { class: "sw-inline", style: `background:var(${ACT_COLOUR[c.class]})` }), nm(c.class)),
      el("td", { class: "num" }, pct(c.recall), el("span", { class: "ci", text: ci(c.recall) })),
      el("td", { class: "num strong", text: String(c.missed) }),
      el("td", { class: "num strong", text: String(c.false_alarms) }),
      el("td", { class: "num" }, pct(c.precision), el("span", { class: "ci", text: ci(c.precision) })),
      el("td", { class: "num muted", text: String(c.support) })));
  }
  const table = el("table", {}, el("thead", {}, el("tr", {}, ...["Activity", "Caught", "Missed", "False alarms", "Right when it says so", "N clips"].map((h, i) =>
    el("th", { class: i ? "num" : "", text: h })))), tb);
  box.append(section("Per activity, one microphone: misses and false alarms, counted separately", "per-activity", el("div", { class: "scroll-x" }, table),
    el("p", { class: "meta muted", style: "margin-top:8px", text: `${ev ? (ev.per_class_slice === "unknown" ? "Eval microphones it never heard." : "All eval microphones.") : "Development folds."} "Caught" = recall, "Right when it says so" = precision, both reweighted to how common each activity really is; small grey numbers are 95% session-bootstrap intervals. Missed and false-alarm counts are raw clip counts.` })));

  // baselines chart
  box.append(section("Against simple and built-in alternatives (development folds, macro F1)", "baselines", baselineChart(d, r.published)));

  // where it does worst
  const worst = [];
  if (r.own_kitchen) worst.push([`Our own kitchens (laptop mic, new homes): ${pct(r.own_kitchen.macro_f1_present_classes)}`, `exploratory, N = ${r.own_kitchen.macro_f1_present_classes.n_clips} windows`]);
  else worst.push(["Our own kitchens: not measured yet", "a teammate who didn't write the code records and labels them (eval/OWN_KITCHEN_GUIDE.md)"]);
  if (ev && ev.slices.unknown) worst.push([`Microphones it never heard: ${pct(ev.slices.unknown.ch0)} on one mic vs ${pct(ev.slices.known.ch0)} on known mics`, "held-out test"]);
  const lono = d.ablations.leave_one_node_out;
  if (lono) worst.push([`A dev microphone left out of training: ${lono.mean_held_out}% vs ${lono.mean_same}% with it`, "leave-one-node-out, development folds"]);
  const weakest = per.slice().sort((a, b) => a.f1.value - b.f1.value).slice(0, 2);
  worst.push([`Weakest activities: ${weakest.map((c) => `${nm(c.class)} (F1 ${c.f1.value.toFixed(0)}%)`).join(", ")}`, "the DCASE baseline's weakest was also 'other'"]);
  box.append(section("Where it does worst", "worst", el("ul", { class: "plain" }, ...worst.map(([a, b]) => el("li", {}, el("span", { text: a }), el("span", { class: "meta muted", text: ` · ${b}` }))))));

  // not sure + off-list
  const ns = d.not_sure, off = r.offlist;
  const nsBox = el("div", { class: "stack" },
    el("p", { text: `Below ${Math.round(ns.theta * 100)}% confidence Kettle says "Not sure" instead of guessing. On development clips that leaves ${ns.coverage_metric.value.toFixed(0)}% of windows labelled, and those labels are right ${ns.shown_precision_metric.value.toFixed(0)}% of the time.` }));
  if (d.novelty) nsBox.append(el("p", { text: `It also says "Not sure" when a sound is unlike all 9 activities it learned (${d.novelty.flagged_in_distribution.value.toFixed(0)}% of development windows get flagged this way).` }));
  if (off && off.confident_wrong) nsBox.append(el("p", { text: `On ${off.n} sounds that aren't household activities at all (dogs, sirens, rain, alarm clocks, noise, silence), Kettle gave a confident label to ${pct(off.confident_wrong)} (95% CI ${ci(off.confident_wrong)}). Without the "unlike anything it learned" check it would have been ${pct(off.confident_wrong_without_novelty_gate)}. Every one of those labels would have been wrong.` }));
  const sl = d.session_level;
  if (sl) nsBox.append(el("p", { text: `On the day bar, a block needs 2 of 3 windows to agree. That caught ${sl.smoothing_on.session_recall.value.toFixed(0)}% of ${sl.smoothing_on.sessions.reduce((a, b) => a + b, 0)} activity sessions with ${sl.smoothing_on.false_alarms_per_hour} false-alarm blocks per hour of sound, versus ${sl.smoothing_off.false_alarms_per_hour} per hour without it.` }));
  box.append(section("When Kettle isn't sure", "not-sure", nsBox));

  // calibration and the cost of θ
  const cal = d.calibration, tt = d.theta_tradeoff;
  if (cal && tt) {
    const shipped = tt.reduce((b, r) => (Math.abs(r.theta - d.not_sure.theta) < Math.abs(b.theta - d.not_sure.theta) ? r : b), tt[0]);
    const low = tt[0], high = tt[tt.length - 1];
    const tb = el("tbody");
    for (const r of tt) tb.append(el("tr", { class: r === shipped ? "row-shipped" : "" }, el("td", { class: "num", text: `${Math.round(r.theta * 100)}%${r === shipped ? " (now)" : ""}` }),
      el("td", { class: "num", text: `${r.meal_sessions_missed} of ${r.meal_sessions}` }), el("td", { class: "num", text: String(r.meal_false_alarms_per_day) })));
    box.append(section("How much to trust \"how sure\"", "calibration",
      el("div", { class: "two-col" },
        el("figure", {}, el("img", { src: "/api/results/reliability_dev.png", alt: `Reliability plot: confidence against observed accuracy. Expected calibration error ${cal.ece_after_temperature.value} points.`, loading: "lazy" }),
          el("figcaption", { class: "meta muted", text: `When Kettle says it is X% sure, it is right about X% of the time: the average gap (ECE) is ${cal.ece_after_temperature.value} percentage points (95% CI ${ci(cal.ece_after_temperature)}).` })),
        el("div", {},
          el("p", { text: `A higher "Not sure" bar could trade one mistake for another: a false "kitchen activity" could hide a skipped breakfast; a missed one could prompt a needless call. On development clips it barely mattered for Meera's check: across ${low.meal_sessions} kitchen sessions, ${high.meal_sessions_missed === 0 && low.meal_sessions_missed === 0 ? "none went unnoticed at any bar from" : "missed sessions changed between"} ${Math.round(low.theta * 100)}% and ${Math.round(high.theta * 100)}%, and false kitchen blocks moved between ${Math.min(...tt.map((x) => x.meal_false_alarm_blocks))} and ${Math.max(...tt.map((x) => x.meal_false_alarm_blocks))} over ${low.days} days of sound. We set the bar so the labels Kettle does show are right about ${d.not_sure.shown_precision_metric.value.toFixed(0)}% of the time.` }),
          d.meal_sessions_strict ? el("p", { class: "meta muted", text: `"Noticed" means some kitchen block overlapped the session. Counting only the right kitchen activity covering at least half of it, ${d.meal_sessions_strict.n_caught} of ${d.meal_sessions_strict.n_sessions} kitchen sessions were caught; in the others the right activity never formed one block that long.` }) : null,
          el("div", { class: "scroll-x" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", { class: "num", text: "Not-sure bar" }), el("th", { class: "num", text: "Kitchen sessions not noticed" }), el("th", { class: "num", text: "False kitchen blocks / day" }))), tb))))));
  }

  // slices
  const sl2 = el("tbody");
  for (const [nd, v] of Object.entries(d.per_node || {})) sl2.append(el("tr", {}, el("td", { text: `Microphone position ${nd.replace("DevNode", "")}` }), el("td", { class: "num" }, pct(v), el("span", { class: "ci", text: ci(v) }))));
  const home = r.own_kitchen;
  sl2.append(el("tr", {}, el("td", { text: "Teammates' kitchens (laptop mic)" }), el("td", { class: "num", text: home ? pct(home.macro_f1_present_classes) : "Sunday" })));
  box.append(section("Who and where it was tested", "slices",
    el("p", { text: "The public recordings are one person in one home, so we can't test whether Kettle works equally well across ages or sexes. We say so rather than guess. What we can check is different microphones, different activities and, from Sunday, different kitchens." }),
    el("div", { class: "scroll-x", style: "margin-top:12px" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", { text: "Slice" }), el("th", { class: "num", text: "Macro F1, one mic" }))), sl2))));

  // failures
  if (r.failures && r.failures.length) {
    const fl = el("div", { class: "fails" });
    for (const f of r.failures.slice(0, 6)) {
      fl.append(el("div", { class: "fail" },
        el("p", { style: "color:var(--ink);font-weight:500", text: `${nm(f.true)} heard as ${nm(f.predicted)}` }),
        el("p", { class: "meta", text: `Kettle said: ${Object.entries(f.probs).map(([k, v]) => `${nm(k)} ${v.toFixed(2)}`).join(" · ")}` }),
        el("p", { class: "meta", text: `It heard: ${f.sounds.map((s) => `${s.name} ${s.score.toFixed(2)}`).join(" · ")}` }),
        el("p", { class: "meta muted", text: `Likely cause: ${f.likely_cause} (${f.how_many_like_this} development clips made this mistake; clip ${f.clip}.)` })));
    }
    box.append(section("Real mistakes, and why", "failures", fl));
  }

  // privacy
  const pc = r.privacy_check;
  if (pc) {
    const c = pc.checks;
    box.append(section("Nothing saved: how we check", "privacy",
      el("p", { text: `${pc.pass ? "Passed" : "FAILED"} on ${pc.ran_at}: the real app listened for ${pc.seconds_listened} s and labelled ${pc.windows_labelled} windows. It opened ${c.python_write_opens_outside_labels_file.length} files for writing other than the labels file, held ${c.lsof_write_handles_outside_labels_file.length} other files open for writing, created ${c.new_or_changed_audio_extension_files.length} audio files and ${c.new_or_changed_files_with_audio_magic_bytes.length} files that look like audio, and made ${c.outbound_connections.length} outside connections. A 5 MB upload was read in memory.` }),
      el("p", { class: "meta muted", text: `What the labels file holds: ${pc.labels_file_fields.join(", ")}. ${pc.threat_model}` })));
  }

  box.append(el("p", { class: "meta muted", style: "margin-top:20px", text: `Generated ${r.generated} · commit ${r.commit.slice(0, 10)} · model ${r.head_sha256.slice(0, 12)} · published DCASE numbers: ${r.published.source}. ${r.published.caveat}` }));
}

function baselineChart(d, pub) {
  const rows = [
    ["Kettle, one microphone", d.ours_ch0.macro_f1, "ours"],
    ["Kettle, 4-mic average", d.ours_node_avg.macro_f1, "ours"],
  ];
  const B = d.baselines;
  const add = (k, label, kind = "base") => {
    if (!B[k] || !B[k].macro_f1) return;
    rows.push([B[k].subset ? `${label} *` : label, B[k].macro_f1, kind]);
    if (B[k].subset) subsets.push(`* ${label}: ${B[k].subset}; Kettle scores ${B[k].ours_same_clips.value.toFixed(1)} on the same clips.`);
  };
  const subsets = [];
  add("logmel_lr", "Log-mel statistics + logistic regression (no deep model)");
  add("ast_probe", "AST (86 M params) + the same head");
  add("ced_small_probe", "CED-small + the same head");
  add("clap_probe", "CLAP + the same head");
  add("clap_zeroshot", "CLAP zero-shot (text prompts)");
  add("ast_zeroshot", "AST zero-shot (AudioSet labels mapped)");
  add("ced_tiny_zeroshot", "CED-tiny zero-shot (AudioSet labels mapped)");
  add("apple_zeroshot", "Apple SoundAnalysis zero-shot (what a Mac ships)");
  add("loudness_rule", "Loudness rule (loud = moving about)");
  add("majority", "Always 'Quiet' (majority)");
  rows.push(["DCASE 2018 baseline (published, full data)", { value: pub.dcase2018_baseline.dev_cv }, "pub"]);
  rows.push(["Best DCASE 2018 entry (published)", { value: pub.best_entry.dev_cv }, "pub"]);
  const wrap = el("div", { class: "dotchart", role: "img", "aria-label": "Macro F1 of Kettle and each baseline, with 95% intervals" });
  const tip = el("div", { class: "tip", hidden: true });
  for (const [label, x, kind] of rows) {
    const line = el("div", { class: `dc-row ${kind}` }, el("span", { class: "dc-label", text: label }));
    const track = el("div", { class: "dc-track" });
    if (x.ci95) track.append(el("span", { class: "dc-ci", style: `left:${x.ci95[0]}%;width:${Math.max(0.5, x.ci95[1] - x.ci95[0])}%` }));
    const dot = el("span", { class: "dc-dot", style: `left:${x.value}%`, tabindex: "0" });
    const msg = `${label}: ${x.value.toFixed(1)}%${x.ci95 ? ` (95% CI ${x.ci95[0]}–${x.ci95[1]}, N = ${x.n_clips})` : " (published)"}`;
    const show = (e) => { tip.hidden = false; tip.textContent = msg; const r = wrap.getBoundingClientRect(), rr = dot.getBoundingClientRect(); tip.style.left = `${Math.min(r.width - 220, Math.max(0, rr.left - r.left - 100))}px`; tip.style.top = `${rr.top - r.top - 40}px`; };
    dot.addEventListener("mouseenter", show); dot.addEventListener("focus", show);
    dot.addEventListener("mouseleave", () => (tip.hidden = true)); dot.addEventListener("blur", () => (tip.hidden = true));
    track.append(dot);
    line.append(track, el("span", { class: "dc-val num", text: `${x.value.toFixed(1)}` }));
    wrap.append(line);
  }
  const axis = el("div", { class: "dc-row axis" }, el("span", { class: "dc-label" }), el("div", { class: "dc-track" },
    ...[0, 25, 50, 75, 100].map((v) => el("span", { class: "dc-tick", style: `left:${v}%`, text: String(v) }))), el("span", { class: "dc-val" }));
  wrap.append(axis, tip);
  return el("div", {}, wrap, ...[...new Set(subsets)].map((s) => el("p", { class: "meta muted", style: "margin-top:4px", text: s })), el("p", { class: "meta muted", style: "margin-top:8px", text: "Dots are macro F1 on the same development clips; bars are 95% session-bootstrap intervals. Zero-shot rows use label maps written before any score was computed. Published DCASE rows used all the data and are not strictly comparable." }));
}
