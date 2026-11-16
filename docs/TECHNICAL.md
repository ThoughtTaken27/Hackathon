# Kettle
**Track:** Health
**Team:** names are on the submission form (Round 1 is reviewed blind)

*This project is a prototype and is not medical advice. Kettle is not an emergency device and can't call for help.*

# The problem
About 28% of US adults 65 and older who live in the community live alone (US Administration for Community Living, [2023 Profile of Older Americans](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans)). When one of them has early memory loss, the family member who would notice a change in their day often lives hours away. Their options are bad: calls feel like checking up, cameras feel like being watched, and sensor kits cost hundreds of dollars plus a monthly fee, and none of the nine we studied publishes how often it misses something or raises a false alarm.

# What we built
**Our user:** Meera, 34, lives 300 miles from her father Ravi, 79, who has early memory loss and lives alone (invented people). At 10 AM she wonders: *has Dad been active in the kitchen this morning?*

- **What goes in:** sound from a spare laptop on Ravi's kitchen counter. Ravi says yes on his own screen first, sees exactly what Meera sees, and can pause it or turn it off.
- **What comes out:** every 10 seconds, a label. It is one of the activities (cooking, washing up, eating, conversation, TV, quiet…), **"Not sure"** (low confidence, or a sound unlike anything it learned), or **"Can't tell"** (not listening). The audio stays in the browser's memory and is overwritten; only labels, scores, times and allowed sound names leave the laptop.
- **How Meera uses it:** her phone shows a calm day bar, a one-line summary, and the checks she set, such as *"Kitchen activity by 10:00 AM: Met at 8:05 (cooking)"*, *Missed* or *Can't tell*.
- **Kettle reports activity, not intent:** cooking sounds mean the kitchen was busy, not that Ravi ate or is well.

# What we added
**Our own idea** (not one of the suggested projects). What we added:
- **Our own user and setting:** a family member far away, with the parent's consent and pause built into the product.
- **Our own question:** can one laptop microphone give reliable activity awareness, and how often does it miss an activity or raise a false one when the home, the sounds and the microphone change?
- **Our own tests:**
  - Misses and false alarms per activity on a held-out test, scored once.
  - A pre-registered test on recordings from other homes.
  - A live test in a teammate's kitchen. It exposed a failure, which we fixed and re-measured.

# How it works
**Data:**
- **[SINS / DCASE 2018 Task 5](https://doi.org/10.5281/zenodo.1247102):** one person living alone for a week, recorded by 4 microphone arrays, labelled by the dataset's authors. We used 8,920 development clips from 257 sessions in the official session-disjoint folds.
- **Held-out test:** a pre-registered, seeded sample of the official test set (7,791 clips, 1,113 moments, 91 sessions), fetched only after the sample, the scoring and the microphone rule were written down.
- **Cleaning:** one channel per microphone array (what one laptop microphone gets); 10-second clips at 16 kHz mono; rare activities topped up to at least 50 moments in the test sample, with percentages reweighted back to the true activity mix.
- **Other homes, never used for training:** [DESED](https://doi.org/10.5281/zenodo.3588172) real-home clips, [Kitchen20](https://github.com/marc-moreaux/kitchen20) and [ESC-50](https://github.com/karolpiczak/ESC-50), each split by uploader (ESC-50: by source recording) into a tune half and a test half. Kitchen20's cutlery and plates clips were left out as ambiguous.

**Model:**
- **[CED-tiny](https://huggingface.co/mispeech/ced-tiny)**, a frozen 5.5 M-parameter audio encoder pretrained on AudioSet, plus a logistic-regression head over 9 activities trained on the development folds.
- **Why:** it is small enough to run in a browser (exported to ONNX; same label as Python on 90 of 90 sample clips). On the development folds, a 4× bigger version of the same encoder was within the error bars, and AST (16× bigger) scored lower on the same clips.
- **Rules decide what the screen says:**
  - Show a label only at confidence ≥ θ = 0.66 (chosen on dev so shown labels are right 90% of the time).
  - Say "Not sure" for sounds unlike anything it learned (a distance check on the encoder's output).
  - A "second opinion" from the encoder's own 527 sound tags for kitchen windows the head can't name.
  - 2-of-3 smoothing, and kitchen stretches named from evidence across all their windows.
- **No LLM:** it couldn't hear without sending audio to a cloud.

<!-- calibration:start -->
**What "Teach Kettle this kitchen" does (3-minute kitchen calibration):** the parent is told to keep quiet (40 s), run the tap (1 min) and cook (1 min); the step they were asked to do is the label (no manual labelling). The device keeps the encoder's 192-number summary of each window from those steps (never the audio) and the kitchen's quiet loudness. Afterwards, only for a window the head can't name, the 5 nearest setup windows vote (weight 0.6) if they're within 1.5× the setup windows' own spread; a confident head is never overruled. The frozen head, θ and the novelty threshold don't change; nothing is sent. Simulated on dev (a head trained without the test microphone, then 3 minutes of that microphone): kitchen activity noticed 85.3% → 87.2% (N = 1,206 windows), "Not sure" 10.5% → 7.4%, false kitchen activity 2.1% → 2.2% (`results/beyond.json`). A small gain, measured on the research home's own microphones, not in a new kitchen. In the web app the kitchen's quiet level also marks any window at or below it as Quiet (added Sun Nov 15 after a live test; checked only on generated room tone, `results/sound_check_web.json`).
<!-- calibration:end -->

<!-- privacy:start -->
**Privacy, verified for the Python app:** `python -m eval.privacy_check` listened through the browser microphone for 60 s (26 windows labelled) while watching the disk and the network: 0 file writes outside the labels file (Python audit hook), 0 open write handles (lsof), 0 new audio files by extension, 0 by audio file signature, and 0 outbound connections (`results/privacy_check.json`). **The browser version has not had an equivalent network audit:** there, privacy is by design (only labels, scores, times and allowed sound names are posted; the server drops any other field) and checked by code review and tests, not by watching traffic.
<!-- privacy:end -->

# Results
<!-- headline:start -->
**Our simplest baseline (always say "Quiet") scored 5.0 [1.6, 7.8] macro F1, and Apple's built-in sound classifier scored 31.8 [25.7, 37.9]. Our model scored 84.1 [74.4, 86.7] on held-out test data:** a pre-registered sample of the official DCASE 2018 test set (7,791 ten-second clips from 91 sessions), scored once with the model frozen. Macro F1 averages the 9 activities equally; brackets are 95% intervals from resampling sessions.
<!-- headline:end -->

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
| Talking / TV | 98.6 [97.6, 100.0] | 29 | 4 | 2,107 |
| Typing | 80.6 [72.7, 87.1] | 284 | 173 | 1,463 |

**Meera's check (any kitchen activity), held-out:** the top label caught **1,039 of 1,183** kitchen-activity windows (**missed 144**): 87.8% raw, **89.3%** [85.3, 94.1] reweighted. **False alarms** on **41 of 6,608** other windows: 0.62% raw, **0.5%** [0.2, 1.1] reweighted. Counts are raw; reweighted percentages re-scale each activity to the full test set's activity mix (the sample topped rare activities up to at least 50 moments each, which over-represents them), as pre-registered. Computed after the run from its saved predictions (not in the pre-registration).

Development folds (optimistic; they chose the model): Kettle 85.1 [81.1, 87.4], log-mel statistics + logistic regression (no deep model) 79.7 [75.5, 82.4], AST (16× bigger) + the same head 83.0 [79.1, 85.7] on a 2,700-clip subset where Kettle scores 85.5; N = 8,920 clips / 257 sessions.
<!-- results:end -->

**Outside the home it learned from (pre-registered):**
<!-- crosshome:start -->
| Real-home kitchen clips (DESED; split by uploader, test half scored once) | Shown as kitchen activity | False kitchen activity on other DESED clips |
|---|---|---|
| Head alone | 6.3% [1.4, 11.8] (5 of 79) | 0 of 191 |
| Head + second opinion (tags), as shipped | **43.0% [25.9, 60.5] (34 of 79)** (tune half: 63.0%) | 0 of 191 |

For comparison, in the research home's held-out test the top label caught 87.8% of kitchen-activity windows (raw; 1,183 windows); in other homes, 43.0% of real-home kitchen clips. It fails safe: 615 of 667 other-home clips were flagged "unlike anything it learned" and shown as "Not sure", not as a wrong activity. One 10-s clip each, no smoothing; scored Sat Nov 14 (`results/other_homes.json`), before the stretch-naming rules, which change which activity is named, not whether one is.
<!-- crosshome:end -->

**A live test in a real kitchen, and the fix.** In a teammate's kitchen, a parent cooking with metal pots showed as "eating", and plate clatter showed as "washing up" with no tap running. Each 10-second window had been named from its single loudest kitchen tag. Now a kitchen stretch is named from evidence across all its windows, and every everyday-sound name must pass a bar written before scoring. The public test halves were looked at more than once while the naming rule was built (`results/kitchen_naming.json`). The clean measurement, our own labelled kitchen recording, is still to do.
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

<!-- realhomes:start -->
**Real homes, scored once (TUT Sound Events 2016 "home": 10 recordings, 36.3 minutes, 216 ten-second windows, every event labelled by the dataset's authors; nothing tuned on it):**

- Windows with washing up or a running tap (N=55): the timeline named some kitchen activity in 52.7% [39.8, 65.3], "Washing up" itself in 21.8% [12.9, 34.4], and said "Not sure" in 41.8% [29.7, 55.0].
- Windows with no kitchen sound (N=113): a kitchen activity was named anyway in 8.8% [4.9, 15.5].
- Named sounds: tap named in 0 of 46 windows that had it, 0 wrong names; dishes named in 0 of 72 windows that had it, 0 wrong names; cupboard named in 2 of 29 windows that had it, 0 wrong names; footsteps named in 0 of 24 windows that had it, 0 wrong names.

So in homes it never heard, Kettle rarely names a sound wrongly but also rarely names one at all; the precision-first thresholds don't carry over. `results/real_homes.json` (`python -m eval.real_homes`).

**Trying to fix that (sound head v3, pre-registered in `eval/PREREGISTER-SOUNDS-V3.md`):** we added real-home audio (those 10 TUT homes and half of DESED) to the sound head's training and tested once on 448 windows from real homes it never heard (TUT-SED 2016 evaluation homes + the other half of DESED). It named more sounds correctly there (80 → 96 true names; false names per 1,000 windows 33.48 → 35.71), but fewer names passed the bar (7 → 5), so by the rule we wrote first it is **not shipped**; v2 stays. Per sound in those new homes (v2): frying 34 of 42; blender 0 of 37; dishes 1 of 92; tap 1 of 79; cupboard 0 of 22; alarm 6 of 39; vacuum 38 of 42; footsteps 0 of 26. `results/sound_head_v3.json`.
<!-- realhomes:end -->

<!-- tradeoff:start -->
"Not sure" below θ = 0.66 (chosen on dev so shown labels are right 90% of the time). On dev, kitchen-activity blocks covered at least half of 33 of 33 kitchen sessions, but the right activity formed one such block in only 15: short "Not sure" stretches split it. A timeline rule added after the frozen test run (bridge a "Not sure" gap of up to 30 s inside one activity; model and θ unchanged) raised that to 26 of 33 and cut false kitchen blocks from 3.87 to 3.23 per 16-hour day. Its cost: 14% of held-out windows were "Not sure".
<!-- tradeoff:end -->

**Where it fails, and why we think so:**
<!-- failures:start -->
1. **Cooking → washing up** (63 dev clips): Rinsing and running water during cooking sounds like washing up.
2. **Talking / TV → conversation** (12 dev clips): TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.
3. **Some activity → quiet** (91 dev clips): 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.
<!-- failures:end -->
4. **Other homes** (above): most windows look unlike anything it learned. One home, one person and one set of microphones is too narrow, so families see a lot of "Not sure".
5. **A TV left on:** TV audio is mostly speech and music, and it masks the quieter kitchen sounds (`results/stress.json`).
6. **Groups we can't test:** SINS is one person in one home, so we can't check age or sex.

*Not part of our claims:* an experimental layer for a few urgent sounds (a smoke alarm, screaming, a crash then a cry) is in the code. It was tested only on public and synthetic clips (`results/safety.json`), never in a home.

# What we'd do next
1. **Measure real homes:** record and label our own kitchens (protocol in `docs/REAL-KITCHEN-PROTOCOL.md`), then run a two-week diary study in five consenting households, scored per home.
2. **Close the gap between homes:** fine-tune with microphone and room augmentation and a few labelled minutes from each new kitchen, tested on held-out homes.

# Sources
- **Datasets:**
  - [SINS / DCASE 2018 Task 5](https://doi.org/10.5281/zenodo.1247102): [eval audio](https://zenodo.org/records/1291760), [labels](https://zenodo.org/records/1964758), [published results](https://dcase.community/challenge2018/task-monitoring-domestic-activities-results); CC BY-NC.
  - [DESED](https://doi.org/10.5281/zenodo.3588172).
  - [Kitchen20](https://github.com/marc-moreaux/kitchen20).
  - [ESC-50](https://github.com/karolpiczak/ESC-50) (CC BY-NC 3.0).
  - [AudioSet](https://research.google.com/audioset/) ontology.
  - Nonspeech7k.
  - [free-spoken-digit-dataset](https://github.com/Jakobovski/free-spoken-digit-dataset) (test clips only).
- **Pretrained models:**
  - [CED-tiny](https://huggingface.co/mispeech/ced-tiny) ([paper](https://arxiv.org/abs/2308.11957), Apache-2.0).
  - Comparisons only: CED-small, [AST](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593), [CLAP](https://arxiv.org/abs/2211.06687), Apple SoundAnalysis.
- **Libraries and hosting:** [ONNX Runtime Web](https://github.com/microsoft/onnxruntime), Cloudflare Workers, PyTorch, Transformers, scikit-learn.
- **Statistic:** [ACL 2023 Profile of Older Americans](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans).
- **Tutorials:** none followed.
- **AI tools:**
  - [Claude Code](https://claude.com/claude-code) (Anthropic) wrote most of the code and documents under our direction.
  - Aside, an AI browser agent, built the web app and gathered the product reviews.
  - REA was our product-teardown tool.
  - What each wrote is in `docs/AI-USAGE-LOG.md`; every module is explained in `docs/EXPLAIN.md`.
- **Reproduce every number:** `notebooks/kettle_reproduce.ipynb`, `python -m eval.other_homes`, `python -m eval.sounds`, `python tools/export_accuracy.py`.
