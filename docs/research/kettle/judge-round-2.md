# Judge simulation, round 2 (Sat Nov 14, 16:28–16:30 CT)

Fresh subagent (Sonnet 5.5) playing a skeptical audio-ML researcher; saw only README, docs/WRITEUP.md, results/ and the round-4 screenshot sheets (after the round-1 changes and the item-9 fix).

**Scores:** Round 1 ≈ 74/100 (Technical 24/30 · Originality 11/20 · Impact + track fit 14/20 · Testing + honesty 13/15 · Communication 12/15), up from ≈ 71. Finals ≈ 71/100 (Demo 22/30 · Depth 22/30 · Impact 12/20 · Q&A 15/20), up from ≈ 70.

**Hardest questions it would ask:** (1) why would a laptop mic in a real kitchen behave like SINS's arrays; (2) what caused the dev → held-out recall drops (moving about 76 → 55, washing up 89 → 73); (3) the strict kitchen-session catch is 15 of 33, so why trust "Missed"; (4) how the 1,113 moments were drawn and why "level with the baseline" means anything; (5) isn't Apple's 31.8 a straw man, and where's a non-deep baseline on held-out.

**Its three changes, and what we did**
| # | Change | Done? |
|---|---|---|
| 1 | Held-out worst-slice analysis from the saved predictions: per microphone × activity recall, lead with the worst cell, no invented causes (+3–4) | **Done.** `eval/__main__.py:rescore_eval` → `dcase_eval.node_activity_recall` (Wilson CIs, labelled post-hoc); table + worst cell in `results/metrics.md`. Because every held-out moment is heard by all 7 microphones, a row isolates the microphone: working (typing) 63% on node 3 vs up to 88% elsewhere, while moving about is 50–60% on every microphone (so its drop isn't a microphone effect). One sentence in README/WRITEUP. The moving-about confusion (69 → working, 49 → quiet) is in `metrics.md`'s confusion matrix |
| 2 | Reframe the headline: "close to, not directly comparable" in the lead with the reason; demote Apple to a labelled footnote; strict 15 of 33 as the θ headline; say it's a benchmark replay, not a real kitchen (+3–4) | **Done** in `tools/writeup_numbers.py` (README, WRITEUP, SUBMISSION-DRAFT regenerated): lead says not directly comparable (full set + all dev data vs our pre-registered sample), Apple is "for context only: zero-shot, a different label set", the off-list 0.4% is in the lead, "recordings from one research home replayed through the app, not yet a real kitchen"; θ paragraph leads with 15 of 33 (46%, CI 30–62) |
| 3 | A held-out log-mel baseline, or an honest latency note (+2–3) | **Log-mel on held-out: skipped.** The pre-registration (`eval/PREREGISTER.md`, commit 0119c57) allows one run, and the zero-shot and majority baselines were scored inside that run. Adding a new system now means re-reading the test audio after seeing the results, a comparison chosen post hoc, which is the kind of second look the pre-registration exists to prevent. Log-mel stays a dev-only baseline, labelled so. **Latency: done.** The privacy check was re-run for 180 s on the current code, and `results/runtime.json` reports what was and wasn't measured (see MORNING-BRIEF) |

Points not taken: "cut the own-kitchen promises" (kept: Lane A runs the set Sunday and the slot is labelled "not measured yet"; removing it would hide the protocol). Fine-tuning and a domain-shift test are "with another week".
