// How sure: the "Urgent alerts" card (handover v3.5, 3.6). Every number is read from /data/safety.json, which eval/safety.py
// writes next to results/safety.json. Nothing is typed by hand; detectors with no recordings say "not measured".
const E = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) k === "text" ? (n.textContent = v) : n.setAttribute(k, v);
  for (const c of kids.flat()) if (c != null) n.append(c);
  return n;
};
const rate = (r) => (r ? `${r.pct.toFixed(1)}% (${r.k}/${r.n})` : "not measured");

(async function () {
  const box = document.getElementById("urgent-howsure");
  if (!box) return;
  let d;
  try { d = await fetch("/data/safety.json").then((x) => x.json()); } catch { return; }
  const sc = d.scenarios, det = d.detectors, home = sc.ordinary_home_audio;
  const rows = [
    ["Smoke or fire alarm, during cooking", rate(sc.pos_smoke_alarm_during_cooking.rate), "synthetic alarm tones in real kitchen sound", "none"],
    ["A crash, then a groan or cry", rate(sc.pos_crash_then_groan.rate), "public recordings, joined in software", "asks \"Are you OK?\"; family told at once"],
    ["A crash, then 2 minutes of stillness", rate(sc.pos_crash_then_stillness.rate), "public recordings, joined in software", "asks first, family told at once"],
    ["Screaming", rate(sc.pos_screaming.rate), "public recordings (Nonspeech7k)", "asks first, family told at once"],
    ["Repeated crying or groaning", rate(sc.pos_repeated_crying.rate), "public recordings (Nonspeech7k)", "asks first, family told at once"],
    ["Gunshot", det.gunshot && det.gunshot.caught_heldout ? rate(det.gunshot.caught_heldout) : "not measured", "no gunshot recordings available to us", "none"],
    ["Shouting, 3 times in a minute", "not measured", "no shouting recordings available to us", "asks first, family told at once"],
  ];
  const negs = Object.entries(sc).filter(([k]) => k.startsWith("neg_"));
  const negN = negs.reduce((a, [, v]) => a + v.n, 0), negHit = negs.reduce((a, [, v]) => a + v.urgent, 0);
  const g = det.gunshot;
  const table = E("table", {},
    E("thead", {}, E("tr", {}, E("th", { text: "Urgent sound" }), E("th", { class: "num", text: "Caught (held-out timelines)" }), E("th", { text: "Where the sounds came from" }), E("th", { text: "Question first?" }))),
    E("tbody", {}, rows.map(([a, b, c, q]) => E("tr", {}, E("td", { text: a }), E("td", { class: "num", text: b }), E("td", { text: c }), E("td", { text: q })))));
  box.append(E("section", { class: "card", id: "urgent", style: "margin-top:20px" },
    E("h2", { class: "section-title", text: "Urgent alerts: what turns red, and how often it's right" }),
    E("p", { class: "verdict", text: `${home.urgent} false urgent alerts in ${home.hours} hours of ordinary home sound (${home.windows} held-out windows). ${negHit} in ${negN} hard look-alike timelines (TV dramas, dropped pans, timers, cans, knocks, fireworks).` }),
    E("div", { class: "scroll-x" }, table),
    E("p", { class: "meta muted", style: "margin-top:8px", text: `Each row is 60 held-out timelines in which nobody answers "Are you OK?" (the worst case). Thresholds were set on development clips only and the held-out half was scored after a written plan (eval/PREREGISTER-SAFETY-V35.md; reruns are disclosed in results/safety.json). The gunshot threshold (${g ? g.tau : "–"}) sits above every development clip because a can being opened scores like a gunshot; it fired on ${g ? `${g.false_fire_heldout_all.k} of ${g.false_fire_heldout_all.n}` : "–"} held-out everyday clips. A thud alone never turns red: it fires about ${det.impact.false_per_hour_home_audio} times an hour in ordinary homes.` }),
    E("ul", { class: "plain", style: "margin-top:8px" }, (d.limits || []).map((x) => E("li", { class: "meta muted", text: x }))),
    E("p", { class: "meta", style: "margin-top:8px", text: "Kettle is a prototype. It doesn't replace a smoke or CO detector, or 911." })));
  if (location.hash === "#urgent") document.getElementById("urgent").scrollIntoView();
})();
