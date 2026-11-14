# Morning brief: Kettle (read this first, Sunday 9 AM CT)

Written by the unattended stage-3 build (Claude Code, /goal run), Sat Nov 14, 10:09 AM → see the timestamp at the bottom.
Everything is on the local branch **`kettle`**. **Nothing was pushed and no PR was opened.** Every number below is copied
from `results/metrics.json` (made by `python -m eval`); none is typed from memory.

## 1. What exists now (two minutes)
- **The idea in one sentence:** a laptop already in a parent's kitchen turns household sounds into a calm day timeline for the adult child far away, keeps no audio and no words, and publishes how often it misses an activity and how often it raises a false alarm.
- **Track:** AI + Health ("manage an ongoing one better"): Meera (34, invented) and her father Ravi (79, invented, early memory loss, lives alone).
- **Run it** (fresh clone, no keys): `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python smoke_test.py && python app.py`, then open http://localhost:8000 and press **Play a sample day: a usual morning**. The kitchen screen is http://localhost:8000/kitchen (Chrome; it asks for the microphone). Screenshots: `docs/screenshots/readme/`, every state in `docs/screenshots/round-3/` (sheets in `round-3/sheets/`).
- **Status against the plan:**

| Milestone | Status | Proof |
|---|---|---|
| M1 walking skeleton | done | `smoke_test.py` PASS (5–15 s) |
| M2 data + embeddings | done | 8,920 dev clips (76.5 min fetch, 0 failed), 7,791 eval clips; CED-tiny all 4 channels |
| M3 models + baselines | done; head frozen `fa5de76a…` | majority, loudness rule, log-mel + LR, Apple SoundAnalysis, CED-tiny zero-shot, AST zero-shot + probe (seeded 2,700-clip subset), CED-small probe; CLAP **cut** (time) |
| M4 eval harness | done | `python -m eval` → `results/`; `python -m eval.check_metrics` → 0 bare numbers |
| M5 product | done | live mode, sample days, caregiver view + heartbeat + checks, parent's consent/pause/off/weekly, try-your-own-sound, how-sure page, privacy check |
| M6 one frozen eval run | done 13:04–13:15 CT, commit `351e929`, pre-registered at `0119c57` | `results/eval_run.json` (1 attempt) |
| M7 design ×3 | done | `docs/screenshots/critique-round-{1,2,3}.md`, fresh critic (r2), usability walkthrough (r3) |
| M8 review + fresh clone | see §2 | |
| M9 judge simulation ×2 | see §2 | |
| M10 hand-off | this file | |

- **Numbers (single microphone, macro F1 with 95% session-bootstrap CI):**
  - **Held-out (official DCASE 2018 Task 5 eval sample, run once, all 7 microphones, N = 7,791 clips / 91 sessions): Kettle 84.1 [74.4, 86.7]; 4-mic average 85.3 [75.5, 88.1]; Apple's built-in classifier 31.8 [25.7, 37.9] on the same clips.** Published DCASE 2018 baseline 85.0 (known mics) / 83.1 (unseen mics); best entry 90.4 / 88.4 (full set, all data; not strictly comparable).
  - **Meera's metric (any kitchen activity), held-out:** caught 89.3% [85.3, 94.1] of 1,183 windows (144 missed); false alarms on 0.5% [0.2, 1.1] of 6,608 other windows (41).
  - Dev folds (also used for selection), N = 8,920 / 257 sessions: Kettle 85.1 [81.1, 87.4]; log-mel + LR 79.7 [75.5, 82.4]; AST probe 83.0 [79.1, 85.7] on a 2,700-clip subset; AST zero-shot 38.9; Apple 32.4 [29.9, 35.1].
  - "Not sure": off-list sounds (dogs, sirens, noise, silence) get a confident label 0.4% [0.1, 2.1] of the time with the novelty check, 56.2% [50.1, 62.1] without. Calibration error 1.6 → 1.5 points. Smoothing cuts false-alarm blocks from 11.1 to 3.2 per hour.

## 2. What is not done or not right (ranked by points at risk)
(Updated at the end of the run; see the "Final status" section at the bottom.)

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
| 0:00–0:15 | Kitchen laptop on a counter; caregiver phone; one line: Apple's classifier 31.8 vs Kettle 84.1 on the official test clips | `/how-sure` top on screen |
| 0:15–0:35 | Kitchen consent: "This laptop listens for kitchen sounds." → "Is it OK for Meera to see this?" → Listening | fresh `/kitchen` (delete `data/timeline/` first) |
| 0:35–1:05 | Live: plates under a running tap → chip "Sounds like washing up" → a block settles; speak → "Conversation", no words anywhere; Pause → phone shows "Paused by Dad at …" | real kitchen, Chrome, presenter mode `/kitchen?presenter=1` |
| 1:05–1:20 | Phone: heartbeat, summary, "Kitchen activity by 10:00 AM: Met"; then "Close the laptop lid" → "Not listening since …"; quiet morning → "No clear kitchen activity by 10:00 AM" | sample days on `/` |
| 1:20–1:45 | How sure: kitchen sentence, held-out 84.1 [74.4, 86.7] vs Apple 31.8, per-activity misses and false alarms | `/how-sure` |
| 1:45–1:55 | Where it fails: moving about vs quiet, TV vs conversation, own-kitchen drop (Sunday number) | `/how-sure#failures` |
| 1:55–2:00 | End card: "Kettle. Know Dad's day went normally, without watching him. Prototype, not medical advice." | |

## 8. Credits and logs
`docs/AI-USAGE-LOG.md` (stage-3 row), `docs/DATA-SOURCES.md` (stage-3 section), README "Credits".
