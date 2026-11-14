# Morning brief: Kettle (read this first, Sunday 9 AM CT)

Written by the unattended stage-3 build (Claude Code, /goal run), Sat Nov 14, 10:09 AM → see the timestamp at the bottom.
Everything is on the local branch **`kettle`**. **Nothing was pushed and no PR was opened.** Every number below is copied
from `results/metrics.json` (made by `python -m eval`); none is typed from memory.

## 1. What exists now (two minutes)
- **The idea in one sentence:** a laptop already in a parent's kitchen turns household sounds into a calm day timeline for the adult child far away, keeps no audio and no words, and publishes how often it misses an activity and how often it raises a false alarm.
- **Track:** AI + Health ("manage an ongoing one better"): Meera (34, invented) and her father Ravi (79, invented, early memory loss, lives alone).
- **Run it** (fresh clone, no keys): `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python smoke_test.py && python app.py`, then open http://localhost:8000 and press **Play a sample day: a usual morning**. The kitchen screen is http://localhost:8000/kitchen (Chrome; it asks for the microphone). Screenshots: `docs/screenshots/readme/`, every state in `docs/screenshots/round-4/` (sheets in `round-4/sheets/`; critiques in `docs/screenshots/critique-round-{1,2,3,4}.md`).
- **Status against the plan:**

| Milestone | Status | Proof |
|---|---|---|
| M1 walking skeleton | done | `smoke_test.py` PASS (5–15 s) |
| M2 data + embeddings | done | 8,920 dev clips (76.5 min fetch, 0 failed), 7,791 eval clips; CED-tiny all 4 channels |
| M3 models + baselines | done; head frozen `fa5de76a…` | majority, loudness rule, log-mel + LR, Apple SoundAnalysis, CED-tiny zero-shot, AST zero-shot + probe (seeded 2,700-clip subset), CED-small probe; CLAP **cut** (time) |
| M4 eval harness | done | `python -m eval` → `results/`; `python -m eval.check_metrics` → 0 bare numbers |
| M5 product | done | live mode, sample days, caregiver view + heartbeat + checks, parent's consent/pause/off/weekly, try-your-own-sound, how-sure page, privacy check |
| M6 one frozen eval run | done 13:04–13:15 CT, commit `351e929`, pre-registered at `0119c57` | `results/eval_run.json` (1 attempt) |
| M7 design ×3 (+1) | done | `docs/screenshots/critique-round-{1,2,3,4}.md`, fresh critic (r2), usability walkthrough (r3); round 4 capture fails on any page error or traceback: 136 screens, 0 problems |
| M8 review + fresh clone | done | fresh code review, every real finding fixed (`c09f082`); fresh clone from the README, no keys: see `results/fresh_clone.txt` (re-run 16:40 CT on the final code) |
| M9 judge simulation ×2 | done | `docs/research/kettle/judge-round-{1,2}.md`: ≈ 71 → 74 (Round 1), ≈ 70 → 71 (finals); top changes made or skipped with a reason |
| M10 hand-off | done | this file, `docs/EXPLAIN.md` (every module), `.overnight/kettle/BUILD_DONE` |

- **Numbers (single microphone, macro F1 with 95% session-bootstrap CI):**
  - **Held-out (official DCASE 2018 Task 5 eval sample, run once, all 7 microphones, N = 7,791 clips / 91 sessions): Kettle 84.1 [74.4, 86.7]; 4-mic average 85.3 [75.5, 88.1]; Apple's built-in classifier 31.8 [25.7, 37.9] on the same clips.** Published DCASE 2018 baseline 85.0 (known mics) / 83.1 (unseen mics); best entry 90.4 / 88.4 (full set, all data; not strictly comparable).
  - **Meera's metric (any kitchen activity), held-out:** caught 89.3% [85.3, 94.1] of 1,183 windows (144 missed); false alarms on 0.5% [0.2, 1.1] of 6,608 other windows (41).
  - Dev folds (also used for selection), N = 8,920 / 257 sessions: Kettle 85.1 [81.1, 87.4]; log-mel + LR 79.7 [75.5, 82.4]; AST probe 83.0 [79.1, 85.7] on a 2,700-clip subset; AST zero-shot 38.9; Apple 32.4 [29.9, 35.1].
  - "Not sure": off-list sounds (dogs, sirens, noise, silence) get a confident label 0.4% [0.1, 2.1] of the time with the novelty check, 56.2% [50.1, 62.1] without. Calibration error 1.6 → 1.5 points. Smoothing cuts false-alarm blocks from 11.1 to 3.2 per hour.

## 2. What is not done or not right (ranked by points at risk)
Ranked by points at risk.
1. **No real-kitchen number yet (Testing 15, finals Q&A).** Every result is SINS: one research home, fixed microphone arrays. The own-kitchen set is Lane A's job today (the build was not allowed to create or label it). Until it's scored, the write-up says "not yet a real kitchen". This is the judges' first question in both simulations.
2. **The live microphone path has only been driven by Chromium's fake mic** (the privacy check, 180 s, 8 activity changes, median 7.1 s to the timeline). Parth's live rehearsal in a real kitchen (Lane C) is the first real-mic test. Have the sample day ready as the fallback.
3. **A day-bar rule changed after the frozen test run (addendum item 10).** The "17 of 33 kitchen sessions missed" was fragmentation: short "Not sure" stretches split each session into 3–12 pieces even though the right activity covered 64–94% of it. Timeline rule 2b now bridges a "Not sure" gap of ≤ 30 s inside one activity (dev-only choice; model and θ unchanged; the held-out numbers are window-level and don't use the timeline). Dev, shipped θ: strict 15 → 26 of 33 kitchen sessions; false kitchen blocks 3.87 → 3.23 per day; all activities 66.5% → 80.2%. The 13:27 switch to an "any overlap" rule was a post-hoc metric change, and DECISIONS (16:55) now says so. Expect a judge to ask "isn't that tuning after the test?"; the answer is in EXPLAIN (`kettle/timeline.py`).
4. **Held-out recall dropped for moving about (76 → 55) and washing up (89 → 73).** The new per-microphone table shows moving about is low on every microphone (50–60%), so it isn't a microphone effect; one run can't separate the rest.
5. **No unseen-microphone number** (the pre-registered fingerprint rule didn't confirm the nodes), **no log-mel baseline on held-out** (skipped: a post-hoc second look at the test set), **CLAP cut**, **AST only on a 2,700-clip dev subset**.
6. **Write-up is ~1,390 words including tables and sources** (prose ~950). Lane B trims prose only; the number blocks regenerate.
7. Cosmetic: the phone rules sheet truncates "TV on for more than (hours)"; the Python 3.11 requirement is strict (3.12 untested).

**Addendum status (`.claude/overnight/kettle/k3-addendum.md`):**
| # | Item | Status |
|---|---|---|
| 1 | Submission draft by Sat 9 PM | done: `docs/SUBMISSION-DRAFT.md`, numbers from `results/`; Parth presses submit |
| 2a | Reliability plot + ECE with CI | done: ECE 1.6 → 1.5 [0.8, 2.6] points, `results/reliability_dev.png` |
| 2b | θ cost story | done: trade-off table with three session rules + plot; the write-up explains fragmentation and the bridging rule |
| 3 | Honest slices (no age/sex) | done: per microphone (dev and held-out × activity), per activity; per-home rows empty until Sunday |
| 4 | Kitchen-activity metric in the headline | done: held-out caught 89.3 [85.3, 94.1]% of 1,183 windows, 144 missed; false alarms 0.5% of 6,608 |
| 5 | Lead with a measured gap | done, then reframed by judge round 2: lead with the held-out score and the "not directly comparable" caveat; Apple's 31.8 is context, labelled zero-shot with a different label set |
| 6 | Reproduce notebook < 5 min with outputs | done: 67 s re-run at 16:37 CT, ALL MATCH |
| 7 | Per-judge Q&A | done: PRD §23 and `docs/EXPLAIN.md` |
| 8 | Pitch quotes | **cut**: neither quote found as worded (DECISIONS 11:20); Parth may open them Sunday |
| 9 | 17 of 33 kitchen sessions | done with item 10: cause was fragmentation (diagnosed on dev) |
| 10 | Metric softened, not fixed | done: one rule stated everywhere (merged kitchen blocks cover ≥ 50%: 33 of 33), strict and any-overlap columns beside it; bridging rule 2b (strict 15 → 26 of 33); DECISIONS 16:55 rows name the 13:27 change as post hoc; tests in `tests/test_timeline.py` and `tests/test_theta_tradeoff.py` |

## 3. Decisions made overnight that a human should confirm
All in `docs/DECISIONS.md` (stage-3 rows from 10:12 onward). The ones to look at first:
1. **Novelty gate** in "Not sure" (Mahalanobis distance, 99th percentile of dev). Reverse: drop `novelty` from `models/head.json` (both rates are reported).
2. **CLAP cut**; **AST on a seeded subset**; **demo hold-out = 1 session per activity**.
3. **Mic-fingerprint rule didn't confirm the unseen mics** → we report all 7 nodes, not an "unknown-mic" number. If you find a source naming the nodes, the per-node table is in `results/metrics.md`.
4. **Eval embeddings not committed** (ND licence); predictions are.
5. **"Paused by Dad at …"** kept (PRD §20.9a).
6. **Both unverified pitch quotes dropped** (not found as worded).
7. **Day bar spans 6 AM → a little after now**, not 6 AM → midnight.

## 4. First hour for Parth
1. Read `docs/PRD.md` §0, §22 (what changed), §23 (per-judge Q&A) and `docs/EXPLAIN.md`.
2. Run `python smoke_test.py`, `python -m eval` (≈6 min) and open the notebook `notebooks/kettle_reproduce.ipynb` (runs in < 1 min).
3. Review: `git log --oneline c212a74..kettle` and `git diff c212a74..kettle --stat`.
4. If it's good: push `kettle` and open a PR to `main` (the overnight run never pushes). **Before pushing:** `results/baselines/apple_dev.jsonl` (60 MB) was committed in a few early commits and later untracked; the history is ~112 MB. If GitHub complains, squash the branch before pushing.
5. Unblock Lane A (own kitchens) by 9:30 AM.

## 5. Team lanes (copy-paste prompts; start each in a fresh Claude Code session with `/model sonnet`)

### Lane A: own-kitchen test set (a teammate who did NOT write the code; 9 AM–1 PM)
Files you may touch: `eval/own_kitchen/labels.csv`, `eval/own_kitchen/CONSENT.md`, `eval/own_kitchen/NOTES.md`. Audio stays in `data/private/own_kitchen/` (git-ignored).
- Task 1 (consent): > *"Read AGENTS.md §0 and eval/OWN_KITCHEN_GUIDE.md. Walk me through the consent form and the recording checklist one step at a time. Don't write any code. Ask me to confirm each step before the next."* Done when every audible person has initialled `eval/own_kitchen/CONSENT.md`.
- Task 2 (record + label): > *"I'm recording kitchen sounds for Kettle's own-kitchen test set following eval/OWN_KITCHEN_GUIDE.md. Help me fill eval/own_kitchen/labels.csv as I go (copy labels_template.csv first): columns file,start_s,end_s,activity,session,notes, activity from the 9 names in the guide. After each session, check my rows for overlaps or gaps and tell me, but never change an activity label yourself."* Done when ≥ 40 minutes of rows exist, on ≥ 2 days or kitchens.
- Task 3 (check): > *"Run `python -m eval.own_kitchen_check` and explain any errors in plain words. Don't edit labels.csv to make it pass; tell me what's wrong and I'll fix it."* Done when it prints "ready to score".
- Task 4: Parth runs `python -m eval --split own-kitchen` **once**, then `python -m eval --render` and `python tools/writeup_numbers.py`. Lane A writes three sentences in `eval/own_kitchen/NOTES.md`: what got worse vs SINS and the likely cause.

### Lane B: video and write-up (Saturday evening draft, final Sunday 1–6 PM)
Files you may touch: `docs/WRITEUP.md` (outside the `<!-- … -->` number blocks), `docs/video/SHOTLIST.md`, `docs/DATA-SOURCES.md` (new rows).
- Task 1: > *"Read docs/PRD.md §18 and §23 and docs/WRITEUP.md. Turn the video script into a shot list in docs/video/SHOTLIST.md: for each line, what's on screen, which app state to set up first (use the sample days and the kitchen page), and who records it. Every number must come from results/metrics.json; write {from results} where a number goes."* Done when every 15-second beat has a shot.
- Task 2: > *"Read docs/WRITEUP.md. Without touching anything between <!-- and --> markers (those are filled from results by tools/writeup_numbers.py), tighten the prose to fit one page (about 550 words of prose plus the table). Keep 'This project is a prototype and is not medical advice.' Show me a diff."*
- Task 3 (after Lane A): > *"Run python tools/writeup_numbers.py, then check that every number in docs/WRITEUP.md and README.md matches results/metrics.json. List any mismatch; don't edit numbers by hand."*

### Lane C: Parth
Review, push, the live-mic rehearsal (Chrome, a real kitchen, plates under a tap), recording the video, submission (`docs/SUBMISSION-DRAFT.md` has every form field).

## 6. Explain it to a judge (everyone, 20 minutes)
Each person runs `/explain quiz <module>` until 4/5: `kettle/timeline.py` (Not sure, smoothing, gaps), `kettle/rules.py` (Can't tell is never Missed), `kettle/live.py` (consent gate, RAM-only buffer), `eval/dev.py` (folds, nested C, baselines), `eval/metrics.py` (why reweighting, why session bootstrap), `eval/dcase.py` (the one run). Per-judge answers: PRD §23.

## 7. Video shot list (2:00, from PRD §18; numbers from results)
| Time | Shot | Set up |
|---|---|---|
| 0:00–0:15 | Kitchen laptop on a counter; caregiver phone; one line: "On the official test clips it had never heard, Kettle caught 86% of cooking and 85% of eating, and says 'Not sure' instead of guessing" (judge round 2: don't lead with Apple) | `/how-sure` top on screen |
| 0:15–0:35 | Kitchen consent: "This laptop listens for kitchen sounds." → "Is it OK for Meera to see this?" → Listening | fresh `/kitchen` (delete `data/timeline/` first) |
| 0:35–1:05 | Live: plates under a running tap → chip "Sounds like washing up" → a block settles; speak → "Conversation", no words anywhere; Pause → phone shows "Paused by Dad at …" | real kitchen, Chrome, presenter mode `/kitchen?presenter=1` |
| 1:05–1:20 | Phone: heartbeat, summary, "Kitchen activity by 10:00 AM: Met"; then "Close the laptop lid" → "Not listening since …"; quiet morning → "No clear kitchen activity by 10:00 AM" | sample days on `/` |
| 1:20–1:45 | How sure: kitchen sentence, held-out 84.1 [74.4, 86.7] (close to the 2018 baseline, not directly comparable), per-activity misses and false alarms; Apple 31.8 only as context | `/how-sure` |
| 1:45–1:55 | Where it fails: moving about vs quiet, TV vs conversation, own-kitchen drop (Sunday number) | `/how-sure#failures` |
| 1:55–2:00 | End card: "Kettle. Know Dad's day went normally, without watching him. Prototype, not medical advice." | |

## 7b. Today's clock (Sunday, CT)
9:00 read this · 9:30 Lane A starts recording · 1:00 PM FREEZE (bug fixes and docs only) · 1–5 PM video and write-up · 5 PM fresh clone + `/ship-check` · **9:00 PM submit** (hard close 10:59 PM).

## 8. Credits and logs
`docs/AI-USAGE-LOG.md` (stage-3 row), `docs/DATA-SOURCES.md` (stage-3 section), README "Credits".

---
Final update: Sat Nov 14 2026, 4:38 PM (Central). Build finished early; nothing pushed. Addendum item 10 (added 4:20 PM) done at 5:00 PM.
