# Kettle

**Track:** AI + Health · **Team:** names on the submission form (Round 1 is blind)
*This project is a prototype and is not medical advice. Kettle is not an emergency device: it can't call for help.*

**In one line:** a spare laptop in an older parent's kitchen turns everyday sound into a calm timeline of the day for a family member far away (no recordings, no words), and publishes how often it misses an activity and how often it cries wolf.

<!-- lead:start -->
On the official DCASE 2018 test set (run once with a frozen model; 1,113 moments × 7 microphones = 7,791 clips from 91 sessions), Kettle scores **84.1** macro F1 (95% CI 74.4–86.7) on one microphone and 85.3 on four. That is close to the official 2018 baseline's published 85.0 (known microphones) / 83.1 (unseen), but not directly comparable: they scored the full test set and trained on all development data; we scored a pre-registered sample. The best entry scored 90.4 / 88.4. Our contribution isn't the leaderboard: it's publishing every activity's misses and false alarms separately, a "Not sure" that gave a confident label to only 0.4% of 260 off-list sounds, and a consent and pause design built around them. These are recordings from one research home replayed through the app, not yet a real kitchen. (For context only: Apple's built-in sound classifier, zero-shot with a different label set, scores 31.8 on the same clips.)
<!-- lead:end -->

## Problem
About 28% of US adults 65+ living in the community live alone (US Administration for Community Living, *2023 Profile of Older Americans*). When one of them has early memory loss, a skipped breakfast or a change in kitchen routine is often the first sign that something is off, and the family member who'd notice lives hours away. Their options are bad: calls feel like checking up, cameras feel like being watched, and sensor kits cost hundreds plus a monthly fee. None of the nine products we studied publishes how often it's wrong (that we found).

## Who it's for, and the moment they reach for it
**Meera, 34, 300 miles from her father Ravi, 79, who has early memory loss and lives alone** (invented people). At 10 AM she wonders "did Dad have breakfast?". She opens her phone and sees *"Kitchen activity by 10:00 AM: Met at 8:05 (cooking)"*, or *"Missed. You might call to say hello."* Ravi is a user too: he says yes on his own kitchen screen, sees exactly what Meera sees, and can pause it.

## What we built
1. Ravi's kitchen laptop shows three plain sentences and asks him first ("Is it OK for Meera to see this?"; it can read them aloud). Then it checks the microphone and spends **3 minutes learning this kitchen** (quiet, washing up, cooking).
2. Every 10 seconds the laptop labels the sound: *Cooking, Washing up, Eating, Conversation, TV, Quiet*, or **Not sure**. The audio stays in the browser's memory and is overwritten. Only the label, a few scores and the time are sent.
3. Meera's phone shows a heartbeat ("Listening · last heard just now"), a one-line summary, a day bar with the evidence behind each block, and the checks she set: **Met / Not yet / Missed / Can't tell**.
4. A few urgent sounds raise a red note on Meera's view. A smoke alarm goes straight to her. Screaming, or a crash then a cry, makes the kitchen ask **"Are you OK?"** first, and Meera is told only if nobody answers or Ravi presses "I need help".
5. "How sure is Kettle?" shows every measured miss and false alarm.

It runs in two modes. The Python app runs offline on one laptop and produces every benchmark number. The web app (link on the submission form) runs the same frozen model in the browser through ONNX; a tiny sync service carries only labels between the two devices.

## What we added (beyond a tutorial)
- **Our own question:** can one laptop microphone do a sensor kit's job, and **how often does it miss an activity, and how often does it raise a false one?** We report these separately for every activity, as the brief asks.
- **Our own setting:** consent, pause, "Not sure" and "Can't tell" are product states, not footnotes.
- **Our own test, and a fix measured in public:**
  - A teammate ran Kettle in their own kitchen. A parent cooking with metal pots showed as "eating", and plate clatter showed as "washing up" with no tap running.
  - We traced the cause: each 10-second window was named from its single loudest kitchen tag.
  - The fix names a kitchen stretch from evidence across all its windows. We measured it before and after.
  - We held every everyday-sound name ("kettle", "running water"…) to a bar written before scoring. Most names failed it, so they are hidden rather than shown wrong.

## How it works
```
microphone ─► 10-s window (memory only) ─► CED-tiny encoder (frozen, 5.5 M params) ─► logistic head (9 activities)
                                             └─► 527 AudioSet tags ─► "second opinion" + named sounds + safety detectors
label + scores + time ─► timeline rules (θ, "unlike anything it learned", 2-of-3 smoothing, stretch naming) ─► day bar, checks
```
- **Training data:** SINS / DCASE 2018 Task 5, one person living alone for a week, 4 microphone arrays, 8,920 development clips, official session-disjoint folds.
- **Why this model:** CED-tiny is about 40× faster than AST on a laptop CPU. A bigger encoder didn't help (results below).
- **Rules, not an LLM, decide what the screen says:** an LLM can't hear without sending audio to a cloud.

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

**Meera's check (any kitchen activity), held-out:** caught 89.3 [85.3, 94.1]% of 1,183 windows (**missed 144**); **false alarms** on 0.5 [0.2, 1.1]% of 6,608 other windows (41). Computed after the run from its saved predictions (not in the pre-registration).

Development folds (optimistic; they chose the model): Kettle 85.1 [81.1, 87.4], log-mel statistics + logistic regression (no deep model) 79.7 [75.5, 82.4], AST (16× bigger) + the same head 83.0 [79.1, 85.7] on a 2,700-clip subset where Kettle scores 85.5; N = 8,920 clips / 257 sessions.
<!-- results:end -->

**After a live test in a real kitchen (all from `results/*.json`, filled by `tools/export_accuracy.py`):**
<!-- accuracy:start -->
| Change (Sun Nov 15, after a live test in a teammate's kitchen) | Before → after | N |
|---|---|---|
| Kitchen stretch named from evidence across its windows (rules 2c, 2d): research home, right activity | 130 → 132 of 132 sessions | 1,027 sessions |
| Same, Kitchen20 test half: wrong activity | 9 → 7 of 222 clips | 465 clips |
| Same, DESED homes test half: dish clatter called washing up or eating | 6 → 1 of 15 | 231 clips |
| Named sound "kettle": precision (false names per 1,000 windows) | 16.0% (17.06) → 44.0% (3.02) | 22 kettle clips |
| Named sound "running water": precision (false names per 1,000 windows) | 47.8% (15.69) → 67.1% (5.97) | 71 tap clips |
| Sound names that passed the pre-registered bar (precision ≥ 90%, recall ≥ 40%) | 1 of 15: TV or radio (97.8% precision, 79.2% recall); the rest are hidden | test halves |
| Not shipped: a trained judge on the 527 tags (strictest cutoff) | wrong activity 4 → 0, but right 218 → 212: failed the gate written before the run | development, out-of-fold |
<!-- accuracy:end -->

<!-- tradeoff:start -->
"Not sure" below θ = 0.66 (chosen on dev so shown labels are right 90% of the time). On dev, kitchen-activity blocks covered at least half of 33 of 33 kitchen sessions, but the right activity formed one such block in only 15: short "Not sure" stretches split it. A timeline rule added after the frozen test run (bridge a "Not sure" gap of up to 30 s inside one activity; model and θ unchanged) raised that to 26 of 33 and cut false kitchen blocks from 3.87 to 3.23 per 16-hour day. Its cost: 14% of held-out windows were "Not sure".
<!-- tradeoff:end -->

## Where it fails
<!-- failures:start -->
1. **Cooking → washing up** (63 dev clips): Rinsing and running water during cooking sounds like washing up.
2. **TV → conversation** (12 dev clips): TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.
3. **Some activity → quiet** (91 dev clips): 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.
<!-- failures:end -->
4. **Real kitchens:** outside the research home, most windows are "unlike anything it learned", so a family sees a lot of **Not sure** (`results/confetti.json`). The 3-minute teaching step helps only a little. A recording of our own kitchen, labelled by a teammate who didn't write the code, is the measurement we still owe.
5. **Groups we can't test:** SINS is one person in one home, so we can't check age or sex. The other homes (Kitchen20, DESED) are sound clips, not people.

## What we'd do next
- Five consenting households for two weeks, scored against a written diary.
- Learn each kitchen from the family's own labelled minutes. A trained "judge" across homes was close but failed our pre-written gate.
- An old phone as the kitchen device.
- Push notifications for the urgent notes.

## Sources and credits
- **Data:** SINS / DCASE 2018 Task 5 (KU Leuven; CC BY-NC 4.0, Zenodo 1247102) and its published results; Kitchen20; DESED; ESC-50 (CC BY-NC 3.0); Nonspeech7k; free-spoken-digit-dataset (test clips only).
- **Models:** CED-tiny and CED-small (Xiaomi, Apache-2.0); AST (MIT); Apple SoundAnalysis (baseline only).
- **Statistic:** ACL 2023 Profile of Older Americans.
- **Libraries and hosting:** ONNX Runtime Web; Cloudflare Workers.
- **AI tools:** Claude Code, REA, Aside. What each wrote is in `docs/AI-USAGE-LOG.md`, and every module is explained in `docs/EXPLAIN.md`.
- **Full list with links:** the app's Credits page and `docs/DATA-SOURCES.md`.
- **Reproduce every number:** `notebooks/kettle_reproduce.ipynb`, `python -m eval.sounds`, `python -m eval.judge`.
