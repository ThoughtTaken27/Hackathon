# Judge simulation, round 1 (Sat Nov 14, 13:52–13:55 CT)

Fresh subagent (Sonnet 5.5) playing a skeptical audio-ML researcher; saw only README, docs/WRITEUP.md, results/ and round-3 screenshots.

**Scores:** Round 1 ≈ 71/100 (Technical 24/30 · Originality 11/20 · Impact + track fit 13/20 · Testing + honesty 12/15 · Communication 11/15). Finals ≈ 70/100 (Demo 23/30 · Depth 21/30 · Impact 12/20 · Q&A 14/20).

**Hardest questions it would ask:** did you beat the 2018 baseline, and why lead with Apple; what is the effective N and why is the CI asymmetric; what breaks when a weak "moving about" class feeds the day bar; how was θ chosen when no θ changes misses; any evidence in a real kitchen with a laptop mic.

**Its three changes, and what we did**
| # | Change | Done? |
|---|---|---|
| 1 | Run the own-kitchen set with a protocol written first (+3–4 R1, +3–4 finals) | **Skipped by the build (constraint: the agent must never create or label it).** Protocol is written (`eval/OWN_KITCHEN_GUIDE.md`, scorer, Wilson CIs); Lane A runs it Sunday. The write-up now says it is in progress, not done |
| 2 | Fair framing: lead with the published baseline, effective N, separate held-out and dev tables, flag the post-hoc kitchen metric, explain recall drops (+3–4) | **Done** (`tools/writeup_numbers.py` → README, WRITEUP, SUBMISSION-DRAFT; how-sure page lead) |
| 3 | Make θ and timeline claims match evidence; reconcile per-hour vs per-day; measure live latency; re-date the privacy check; effective-N caveat (+2–3) | **Done:** θ paragraph now says no kitchen session went unnoticed at any θ and θ was chosen for shown-label precision; units reconciled; CI note added; 30-min live run on the fixed code re-measures latency and privacy (the code reviewer found the bug that nulled latency) |

Other points taken: the write-up was cut from ~1,240 to ~960 words of prose (Lane B to finish the last trim); the lowered recall classes are named with the honest "one run can't separate causes".
