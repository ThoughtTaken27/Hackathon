// "How sure is Kettle?": the measured misses and false alarms, read from results/metrics.json.
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
})();

function renderResults(box, r) {
  box.append(el("pre", { text: JSON.stringify(r, null, 1).slice(0, 2000) }));
}
