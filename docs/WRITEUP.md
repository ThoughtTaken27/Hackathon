# Kettle: activity awareness without recording

**Track:** AI + Health · **Team:** names on the submission form (Round 1 is blind)
*This project is a prototype and is not medical advice. Kettle is not an emergency device.*

**Research question:** can a single household microphone give a family reliable awareness of a parent's daily activity, without recording anything, when the home, the sounds and the microphone change? Kettle is built to **know when it doesn't know** and to measure its own failures.

<!-- lead:start -->
On the official DCASE 2018 test set (run once with a frozen model; 1,113 moments × 7 microphones = 7,791 clips from 91 sessions), Kettle scores **84.1** macro F1 (95% CI 74.4–86.7) on one microphone and 85.3 on four. That is close to the official 2018 baseline's published 85.0 (known microphones) / 83.1 (unseen), but not directly comparable: they scored the full test set and trained on all development data; we scored a pre-registered sample. The best entry scored 90.4 / 88.4. Our contribution isn't the leaderboard: it's publishing every activity's misses and false alarms separately, a "Not sure" that gave a confident label to only 0.4% of 260 off-list sounds, and a consent and pause design built around them. These are recordings from one research home replayed through the app, not yet a real kitchen. (For context only: Apple's built-in sound classifier, zero-shot with a different label set, scores 31.8 on the same clips.)
<!-- lead:end -->

## Problem
About 28% of US adults 65+ living in the community live alone (US Administration for Community Living, *2023 Profile of Older Americans*). When one of them has early memory loss, a family member far away wants a quiet signal that the day is going normally, without calling to check up. Cameras feel like being watched, and sensor kits cost hundreds plus a monthly fee. None of the nine products we studied publishes how often it misses something or raises a false alarm (that we found).

## Who it's for, and the moment they reach for it
**Meera, 34, lives 300 miles from her father Ravi, 79, who has early memory loss and lives alone** (invented people). At 10 AM she wonders: *has Dad been active in the kitchen this morning?* Her phone answers *"Kitchen activity by 10:00 AM: Met at 8:05 (cooking)"*, *"Missed"* or *"Can't tell"*. **Kettle reports activity, not intent:** cooking sounds mean the kitchen was busy, not that Ravi ate or is well. Ravi is a user too. He says yes on his own screen, sees exactly what Meera sees, and can pause it.

## Three contributions
1. **A lightweight pipeline that runs on the device:** a frozen 5.5 M-parameter audio encoder and a logistic head label each 10-second window in the kitchen laptop's browser. The audio is discarded; only labels, scores, times and allowed sound names leave.
2. **A timeline that shows its uncertainty:** every block is an activity, **"Not sure"** (low confidence, or a sound unlike anything it learned) or **"Can't tell"** (not listening). It never guesses to fill a gap.
3. **An evaluation of its own failures:** misses and false alarms per activity on a held-out test scored once; a pre-registered test on other homes; and a live test in a real kitchen that exposed a failure, which we fixed and re-measured.

## How it works
```
mic → 10-s window (memory only) → CED-tiny encoder (frozen) → logistic head (9 activities) → θ = 0.66 + novelty check → label or "Not sure"
                                     └→ 527 AudioSet tags → second opinion for unnamed kitchen windows; named sounds (only those that pass a bar)
labels → timeline rules (2-of-3 smoothing, 30-s gap bridging, kitchen stretch named from evidence) → day bar, checks
```
- **Data:** SINS / DCASE 2018 Task 5, one person living alone for a week, recorded by 4 microphone arrays. We used 8,920 development clips from 257 sessions, in the official session-disjoint folds.
- **Held-out test:** a pre-registered sample of the official test set, scored once with the model frozen.
- **Encoder choice:** CED-tiny is about 40× less compute than AST, at similar dev accuracy.
- **No LLM:** it can't hear without sending audio to a cloud.

<!-- calibration:start -->
**What "Teach Kettle this kitchen" does (3-minute kitchen calibration):** the parent is told to keep quiet (40 s), run the tap (1 min) and cook (1 min); the step they were asked to do is the label (no manual labelling). The device keeps the encoder's 192-number summary of each window from those steps (never the audio) and the kitchen's quiet loudness. Afterwards, only for a window the head can't name, the 5 nearest setup windows vote (weight 0.6) if they're within 1.5× the setup windows' own spread; a confident head is never overruled. The frozen head, θ and the novelty threshold don't change; nothing is sent. Simulated on dev (a head trained without the test microphone, then 3 minutes of that microphone): kitchen activity noticed 85.3% → 87.2% (N = 1,206 windows), "Not sure" 10.5% → 7.4%, false kitchen activity 2.1% → 2.2% (`results/beyond.json`). A small gain, measured on the research home's own microphones, not in a new kitchen. In the web app the kitchen's quiet level also marks any window at or below it as Quiet (added Sun Nov 15 after a live test; checked only on generated room tone, `results/sound_check_web.json`).
<!-- calibration:end -->

## Results
<!-- results:start -->
**Held-out test (official DCASE 2018 eval sample, run once, all 7 microphones; macro F1, 95% session-bootstrap CI):**

| System | Macro F1 | N |
|---|---|---|
| **Kettle, one microphone** | **84.1 [74.4, 86.7]** | 7,791 clips / 1,113 moments / 91 sessions |
| Kettle, 4-microphone average | 85.3 [75.5, 88.1] | same |
| Apple SoundAnalysis, zero-shot | 31.8 [25.7, 37.9] | same clips |
| Same encoder, zero-shot label map | 38.5 [30.9, 47.2] | same clips |
| Always "Quiet" | 5.0 [1.6, 7.8] | same clips |
| DCASE 2018 official baseline (published) | 85.0 known mics · 83.1 unseen mics | full eval set, all dev data |
| DCASE 2018 best entry (published) | 90.4 · 88.4 | full eval set |

**Held-out, per activity (one microphone): misses and false alarms counted separately**

| Activity | Caught (recall) | Missed | False alarms | N clips |
|---|---|---|---|---|
| Quiet | 95.1 [93.1, 95.9] | 97 | 198 | 1,988 |
| Cooking | 86.1 [71.4, 93.0] | 67 | 36 | 483 |
| Washing up | 72.6 [49.5, 84.9] | 96 | 35 | 350 |
| Eating | 84.9 [75.0, 91.8] | 53 | 42 | 350 |
| Some activity | 55.4 [40.6, 73.5] | 156 | 248 | 350 |
| Conversation | 96.9 [92.5, 100.0] | 11 | 81 | 350 |
| Vacuuming | 93.1 [71.4, 100.0] | 24 | 0 | 350 |
| TV | 98.6 [97.6, 100.0] | 29 | 4 | 2,107 |
| Typing | 80.6 [72.7, 87.1] | 284 | 173 | 1,463 |

**Meera's check (any kitchen activity), held-out:** the top label caught **1,039 of 1,183** kitchen-activity windows (**missed 144**): 87.8% raw, **89.3%** [85.3, 94.1] reweighted. **False alarms** on **41 of 6,608** other windows: 0.62% raw, **0.5%** [0.2, 1.1] reweighted. Counts are raw; reweighted percentages re-scale each activity to the full test set's activity mix (the sample topped rare activities up to at least 50 moments each, which over-represents them), as pre-registered. Computed after the run from its saved predictions (not in the pre-registration).

Development folds (optimistic; they chose the model): Kettle 85.1 [81.1, 87.4], log-mel statistics + logistic regression (no deep model) 79.7 [75.5, 82.4], AST (16× bigger) + the same head 83.0 [79.1, 85.7] on a 2,700-clip subset where Kettle scores 85.5; N = 8,920 clips / 257 sessions.
<!-- results:end -->

**Does it work outside the home it learned from? (pre-registered, `python -m eval.other_homes`)**
<!-- crosshome:start -->
| Real-home kitchen clips (DESED; split by uploader, test half scored once) | Shown as kitchen activity | False kitchen activity on other DESED clips |
|---|---|---|
| Head alone | 6.3% [1.4, 11.8] (5 of 79) | 0 of 191 |
| Head + second opinion (tags), as shipped | **43.0% [25.9, 60.5] (34 of 79)** (tune half: 63.0%) | 0 of 191 |

For comparison, in the research home's held-out test the top label caught 87.8% of kitchen-activity windows (raw; 1,183 windows); in other homes, 43.0% of real-home kitchen clips. It fails safe: 615 of 667 other-home clips were flagged "unlike anything it learned" and shown as "Not sure", not as a wrong activity. One 10-s clip each, no smoothing; scored Sat Nov 14 (`results/other_homes.json`), before the stretch-naming rules, which change which activity is named, not whether one is.
<!-- crosshome:end -->

**A live test in a real kitchen, and what we changed.** A teammate ran Kettle at home. A parent cooking with metal pots showed as "eating", and plate clatter showed as "washing up" with no tap running. Each 10-second window had been named from its single loudest kitchen tag. Now a kitchen stretch is named from evidence across all its windows, and every everyday-sound name ("kettle", "running water"…) must pass a bar written before scoring. Most names failed the bar, so families don't see them. (Public test halves were looked at more than once while the naming rule was built: `results/kitchen_naming.json`. The clean measurement, our own labelled kitchen recording, is still to do.)
<!-- accuracy:start -->
**Naming a kitchen stretch from evidence across its windows (rules 2c, 2d), same events before → after:**

| Set (unit) | Measure | Before | After | Denominator |
|---|---|---|---|---|
| Research home, dev (one session heard by one microphone node) | right activity | 130 | 132 | 132 kitchen-activity recordings (33 sessions × 4 microphone nodes; 1,027 recordings in all) |
| Research home, dev | false kitchen activity | 13 | 13 | 895 other recordings |
| Kitchen20, test half (one clip each) | wrong activity | 9 | 7 | 222 kitchen-activity clips (of 465; 243 others) |
| DESED real homes, test half (one 10-s clip each) | dish clatter called washing up or eating | 6 | 1 | 15 dish-clatter clips (of 231) |

**Everyday sound names, held-out halves: hand-written rules → a trained sound head (pre-registered bar: precision ≥ 90% and recall ≥ 40%; `eval/PREREGISTER-SOUNDS-V2.md`):**

| Sound | Precision, rules → head | Recall, rules → head | False names per 1,000 other windows | Positives / other windows | Shown |
|---|---|---|---|---|---|
| Kettle or a hot drink | 44.0% → 100.0% | 50.0% → 40.9% | 3.02 → 0.0 | 22 / 4,631 | yes |
| Frying or sizzling | 73.2% → 87.2% | 93.2% → 93.2% | 3.28 → 1.31 | 44 / 4,579 | hidden |
| Chopping | 56.7% → 100.0% | 77.3% → 54.5% | 2.82 → 0.0 | 22 / 4,613 | yes |
| Blender | 55.2% → – | 76.2% → 0.0% | 1.92 → 0.0 | 21 / 6,768 | hidden (failed on tune, head not used) |
| Microwave | 54.5% → 82.6% | 28.6% → 90.5% | 0.74 → 0.59 | 21 / 6,794 | hidden |
| Dishes and cutlery | 57.0% → 87.9% | 60.7% → 87.9% | 11.06 → 2.93 | 107 / 4,432 | hidden |
| Running water | 67.1% → 95.7% | 77.5% → 62.0% | 5.97 → 0.44 | 71 / 4,525 | yes |
| Cupboards and drawers | 0.0% → 97.9% | 0.0% → 82.1% | 10.03 → 0.22 | 56 / 4,586 | yes |
| A door | 3.7% → 100.0% | 7.7% → 7.7% | 11.45 → 0.0 | 26 / 4,541 | hidden |
| Timer or appliance beep | 34.0% → 93.3% | 85.3% → 92.6% | 33.92 → 1.36 | 136 / 6,634 | yes |
| Talking / TV | 97.8% → 95.0% | 79.2% → 91.6% | 1.51 → 4.04 | 500 / 5,945 | yes |
| Vacuum cleaner | 86.5% → 88.9% | 98.9% → 100.0% | 10.66 → 8.63 | 439 / 6,376 | hidden |
| Typing | 74.1% → 95.1% | 28.4% → 43.9% | 8.46 → 1.92 | 535 / 6,262 | yes |
| Footsteps | 50.0% → 94.1% | 59.1% → 72.7% | 2.07 → 0.16 | 22 / 6,287 | yes |
| Glass breaking | 58.3% → 78.9% | 93.3% → 100.0% | 1.48 → 0.59 | 15 / 6,779 | hidden |

8 of 15 names passed (Kettle or a hot drink, Chopping, Running water, Cupboards and drawers, Timer or appliance beep, Talking / TV, Typing, Footsteps), up from 1 with the rules; the other 7 stay hidden from families (`results/sound_head.json`). The test halves were scored once before, with the rules; every choice in the head came from the tune halves.
<!-- accuracy:end -->

<!-- tradeoff:start -->
"Not sure" below θ = 0.66 (chosen on dev so shown labels are right 90% of the time). On dev, kitchen-activity blocks covered at least half of 33 of 33 kitchen sessions, but the right activity formed one such block in only 15: short "Not sure" stretches split it. A timeline rule added after the frozen test run (bridge a "Not sure" gap of up to 30 s inside one activity; model and θ unchanged) raised that to 26 of 33 and cut false kitchen blocks from 3.87 to 3.23 per 16-hour day. Its cost: 14% of held-out windows were "Not sure".
<!-- tradeoff:end -->

<!-- privacy:start -->
**Privacy, verified for the Python app:** `python -m eval.privacy_check` listened through the browser microphone for 60 s (26 windows labelled) while watching the disk and the network: 0 file writes outside the labels file (Python audit hook), 0 open write handles (lsof), 0 new audio files by extension, 0 by audio file signature, and 0 outbound connections (`results/privacy_check.json`). **The browser version has not had an equivalent network audit:** there, privacy is by design (only labels, scores, times and allowed sound names are posted; the server drops any other field) and checked by code review and tests, not by watching traffic.
<!-- privacy:end -->

## Where it fails
<!-- failures:start -->
1. **Cooking → washing up** (63 dev clips): Rinsing and running water during cooking sounds like washing up.
2. **TV → conversation** (12 dev clips): TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.
3. **Some activity → quiet** (91 dev clips): 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.
<!-- failures:end -->
4. **Other homes:** most windows look unfamiliar, so families see a lot of "Not sure" (above).
5. **TV:** a TV as loud as the cooking hides much of it (`results/stress.json`).
6. **Groups we can't test:** SINS is one person in one home, so we can't check age or sex. The other homes are sound clips, not people.

**Not part of our claims:** the code also has an experimental layer for a few urgent sounds (a smoke alarm, screaming, a crash then a cry) that asks "Are you OK?" on the kitchen screen. It was tested only on public and synthetic clips (`results/safety.json`), never in a home, so we make no detection claim for it. Kettle can't call for help.

## What we'd do next
- Record and label our own kitchens (protocol in `docs/REAL-KITCHEN-PROTOCOL.md`), then run a two-week diary study in five consenting households, scored per home.
- Fine-tuning with microphone and room augmentation, tested on held-out homes.
- A network audit of the browser app.
- Retrain the head on commercially licensed recordings: SINS and ESC-50 are non-commercial.

## Sources and credits
- **Data:** SINS / DCASE 2018 Task 5 (KU Leuven; CC BY-NC 4.0; Zenodo 1247102, 1291760, 1964758) and its published results; DESED (Zenodo 3588172); Kitchen20; ESC-50 (CC BY-NC 3.0); AudioSet ontology; Nonspeech7k; free-spoken-digit-dataset (test clips only).
- **Models:** CED-tiny (Apache-2.0). Comparisons only: CED-small, AST, CLAP, Apple SoundAnalysis.
- **Statistic:** ACL 2023 Profile of Older Americans.
- **Infrastructure:** ONNX Runtime Web, Cloudflare Workers, PyTorch, Transformers, scikit-learn.
- **AI tools:** Claude Code (Anthropic) wrote most of the code and documents under our direction. Aside (an AI browser agent) built the web app and gathered the reviews. REA was our product-teardown tool. Log: `docs/AI-USAGE-LOG.md`; every module explained: `docs/EXPLAIN.md`.
- **Reproduce every number:** `notebooks/kettle_reproduce.ipynb`, `python -m eval.other_homes`, `python -m eval.sounds`, `python tools/export_accuracy.py`.
