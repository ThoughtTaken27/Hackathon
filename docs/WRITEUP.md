# Kettle
**Track:** Health

*This project is a prototype and is not medical advice.*

# The problem
Millions of older Americans with early memory loss are living completely alone - hours away from the children who love them. They are too busy working or too far away, forcing adults into the painful trap of a weekly call where the parent hides their decline. On the other hand, cameras feel like they're being watched and expensive sensor kits make things worse with false alarm and it reaches a peak where families tune them out. Families that are left blind until a missed warning sign can turn a preventable emergency into a crisis.  

# What we built
**Our user:** Meera, 34, lives 300 miles from her father Ravi, 79, who has early memory loss and lives alone. At 10 AM she wonders: *What has Dad been up to in the kitchen this morning?*

- **What goes in:** sound from the kitchen goes into a laptop on Ravi's kitchen counter. Ravi says yes on his own screen first and sees exactly what Meera sees.
- **What comes out:** every 10 seconds, a label with timestamps pops up. It is one of the activities such as cooking, washing up, eating, conversation, etc or if the house is quiet or has the TV running in the background. The audio stays in the browser's memory and is overwritten; only labels, scores, times and allowed sound names leave the laptop.
- **How Meera uses it:** her phone shows a calm day bar with labels, a one-line summary, and the checks she set, such as *"Kitchen activity by 10:00 AM: Met at 8:05 (cooking)"*, *Missed* or *Can't tell*.

# What we added
**Our own idea**

# How it works
**Data:**
- **[SINS / DCASE 2018 Task 5](https://doi.org/10.5281/zenodo.1247102):** includes one person living alone for a week, recorded by 4 microphone arrays, labelled by the dataset's authors. We used 8,920 development clips from 257 sessions in the official session-disjoint folds.
- **Held-out test:** a pre-registered, seeded sample of the official test set (7,791 clips, 1,113 moments, 91 sessions), fetched only after the sample, the scoring and the microphone rule were written down.
- **Cleaning:** one channel per microphone array (what one laptop microphone gets); 10-second clips at 16 kHz mono; rare activities topped up to at least 50 moments in the test sample, with percentages reweighted back to the activity mix.
- **Other homes, never used for training:** [DESED](https://doi.org/10.5281/zenodo.3588172) real-home clips, [Kitchen20](https://github.com/marc-moreaux/kitchen20) and [ESC-50](https://github.com/karolpiczak/ESC-50), each split by uploader (ESC-50: by source recording) into a tune half and a test half. 

**Model:**
- **[CED-tiny](https://huggingface.co/mispeech/ced-tiny)**, a frozen 5.5 M-parameter audio encoder pretrained on AudioSet, plus a logistic-regression head over 9 activities trained on the development folds.
- **Why:** it is small enough to run in a browser (exported to ONNX; same label as Python on 90 of 90 sample clips). On the development folds, a 4× bigger version of the same encoder was within the error bars, and AST (16× bigger) scored lower on the same clips.
- **Rules decide what the screen says:**
  - Show a label only at confidence ≥ θ = 0.66 (chosen on dev so shown labels are right 90% of the time).
  - Say "Not sure" for sounds unlike anything it learned (a distance check on the encoder's output).
  - A "second opinion" from the encoder's own 527 sound tags for kitchen windows the head can't name.
  - 2-of-3 smoothing, and kitchen stretches named from evidence across all their windows.
- **No LLM:** it couldn't hear without sending audio to a cloud.

# Results
<!-- headline:start -->
**Our model scored 84.1 [74.4, 86.7] on held-out test data while Apple's built-in sound classifier scored 31.8 [25.7, 37.9], more than 2.5 times higher. It's also far above our baseline of always guessing "Quiet" (5.0 [1.6, 7.8])** We froze the model before testing and scored it only once on a pre-registered sample of the official DCASE 2018 test set (7,791 ten-second clips from 91 sessions). Because macro F1 averages all the 9 activities equally, the model cannot increase its score by only getting common sounds correct. The brackets represent 95% confidence intervals calculated by resampling the sessions.
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

**Kitchen activity check, held-out:** the top label caught **1,039 of 1,183** kitchen-activity windows (**missed 144**): 87.8% raw, **89.3%** [85.3, 94.1] reweighted. **False alarms** on **41 of 6,608** other windows: 0.62% raw, **0.5%** [0.2, 1.1] reweighted. Counts are raw; reweighted percentages re-scale each activity to the full test set's activity mix (the sample topped rare activities up to at least 50 moments each, which over-represents them), as pre-registered. Computed after the run from its saved predictions (not in the pre-registration).

For context, our development folds which we used to select the model and are therefore slightly optimistic showed Kettle scoring 85.1 [81.1, 87.4] across 8,920 clips (257 sessions). On a 2,700-clip subset of that development data, Kettle (85.5) also outperformed both a simple logistic regression model using log-mel statistics (79.7) and a 16 times larger AST model using the same classification head (83.0).
<!-- results:end -->

**Outside the home it learned from (pre-registered):**
<!-- crosshome:start -->
| Real-home kitchen clips (DESED; split by uploader, test half scored once) | Shown as kitchen activity | False kitchen activity on other DESED clips |
|---|---|---|
| Head alone | 6.3% [1.4, 11.8] (5 of 79) | 0 of 191 |
| Head + second opinion (tags), as shipped | **43.0% [25.9, 60.5] (34 of 79)** (tune half: 63.0%) | 0 of 191 |

For comparison, in the research home's held-out test the top label caught 87.8% of kitchen-activity windows (raw; 1,183 windows); in other homes, 43.0% of real-home kitchen clips. The system fails safely rather than crying wolf. When tested on 667 10 second clips, it recognized 615 of them as "unlike anything it learned" and shown as "Not sure", not as a wrong activity. (We ran this test before adding our stretch-naming rules, which only affect which specific activity gets chosen, not whether an activity is detected.)
<!-- crosshome:end -->

**A live test in a real kitchen, and the fix.** In a teammate's kitchen, cooking with metal pots showed up as "eating", and plate clatter showed as "washing up" with no tap running. Each 10-second window had been named from its single loudest kitchen tag. Now a kitchen stretch is named from evidence across all its windows, and every everyday-sound name must pass a bar written before choosing a label. 
<!-- accuracy:start -->
**Naming a kitchen stretch from evidence across its windows (rules 2c, 2d), same events before → after:**

| Set (unit) | Measure | Before | After | Denominator |
|---|---|---|---|---|
| Research home, dev (one session heard by one microphone node) | right activity | 130 | 132 | 132 kitchen-activity recordings (33 sessions × 4 microphone nodes; 1,027 recordings in all) |
| Research home, dev | false kitchen activity | 13 | 13 | 895 other recordings |
| Kitchen20, test half (one clip each) | wrong activity | 9 | 7 | 222 kitchen-activity clips (of 465; 243 others) |
| DESED real homes, test half (one 10-s clip each) | dish clatter called washing up or eating | 6 | 1 | 15 dish-clatter clips (of 231) |

**Everyday sound names, held-out halves (pre-registered bar: precision ≥ 90% and recall ≥ 40%):**

| Sound | Precision before → after | False names per 1,000 other windows, before → after | Recall after | Positives / other windows | Shown |
|---|---|---|---|---|---|
| Kettle or a hot drink | 44.0% → 100.0% | 3.02 → 0.0 | 40.9% | 22 / 4,631 | yes |
| Running water | 67.1% → 95.7% | 5.97 → 0.44 | 62.0% | 71 / 4,525 | yes |
| Microwave | 54.5% → 82.6% | 0.74 → 0.59 | 90.5% | 21 / 6,794 | hidden |
| Talking / TV | 97.8% → 95.0% | 1.51 → 4.04 | 91.6% | 500 / 5,945 | yes |


**Where it fails, and why we think so:**
<!-- failures:start -->
1. **Cooking → washing up** (63 dev clips): Rinsing and running water during cooking sounds like washing up.
2. **TV → conversation** (12 dev clips): TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.
3. **Some activity → quiet** (91 dev clips): 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.
4. **Other homes** (above): most homes sound unlike anything it learned. One home, one person and one set of microphones is too narrow. 
5. **A TV left on:** TV audio is mostly speech and music, and it masks the quieter kitchen sounds (`results/stress.json`).
<!-- failures:end -->

**Urgent sounds:** a smoke or CO alarm, a crash then a cry or 2 minutes of stillness, screaming, shouting, a gunshot, or the "I need help" button turns the family's view red and notifies their phone at once. On held-out simulated timelines (60 each, nobody answering) it caught a smoke alarm during cooking 88.3%, a crash then a cry 73.3%, a crash then stillness 71.7% and screaming 83.3%, with **0 false urgent alerts in 12.3 hours** of ordinary home sound (`results/safety.json`). In a live browser test, a smoke alarm turned the family page red 2.8 s after the kitchen screen (`results/e2e_urgent.json`). Limits: the alarms are synthetic tones, the crashes are breaking glass, and we had no gunshot or shouting recordings, so those two have no measured catch rate.

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
- **Images (demo video only):** [old man holding a cup](https://www.dreamstime.com/photos-images/old-man-holding-cup.html) (Dreamstime); [empty kitchen](https://www.dreamstime.com/water-tap-professional-kitchen-restaurant-modern-equipment-devices-empty-morning-interior-made-stainless-steel-image143073683) (Dreamstime); [person looking at a phone](https://www.istockphoto.com/photos/black-woman-looking-at-phone-from-behind) (iStock); [smoke detector](https://sen.news/smoke-sensors-on-steep-ceilings/) (sen.news).
- **Statistic:** [ACL 2023 Profile of Older Americans](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans).
- **Tutorials:** none followed.
- **AI tools:**
  - [Claude Code](https://claude.com/claude-code) (Anthropic) wrote most of the code and documents under our direction.
  - Aside, an AI browser agent, built the web app and gathered the product reviews.
  - REA was our product-teardown tool.
  - What each wrote is in `docs/AI-USAGE-LOG.md`; every module is explained in `docs/EXPLAIN.md`.
- **Reproduce every number:** `notebooks/kettle_reproduce.ipynb`, `python -m eval.other_homes`, `python -m eval.sound_head`, `python tools/export_accuracy.py`.
