# Kettle

**Track:** AI + Health · **Team:** (names on the submission form; Round 1 is blind)
*This project is a prototype and is not medical advice. Kettle is not an emergency device.*

<!-- lead:start -->
On the official DCASE 2018 test set (run once with a frozen model; 1,113 moments × 7 microphones = 7,791 clips from 91 sessions), Kettle scores **84.1** macro F1 (95% CI 74.4–86.7) on one microphone and 85.3 on four: level with the official 2018 baseline (85.0 known / 83.1 unseen microphones, full set) and below the best entry (90.4 / 88.4). A Mac already hears a kettle, but Apple's built-in sound classifier scores 31.8 on the same clips. Our contribution isn't the leaderboard: it's publishing every activity's misses and false alarms, and a "Not sure", consent and pause design built around them.
<!-- lead:end -->

## The problem
About 28% of US adults 65+ living in the community live alone (US Administration for Community Living, *2023 Profile of Older Americans*). For an adult child far from a parent with early memory loss, "did Dad have breakfast?" has no good answer: calling feels like checking up, cameras feel like spying, and sensor kits cost hundreds plus a monthly fee. In 418 reviews we coded, the top pains were the parent feeling watched, daily chores for the parent, and alerts that miss problems or cry wolf. None of the nine products we studied publishes how often it's wrong (that we found).

## What we built
For Meera, 34 (invented), 300 miles from her father Ravi, 79. A laptop on his kitchen counter labels 10-second windows of sound into a day bar ("cooking around 8:15–8:30 AM, TV from about 9:30") with the sounds behind each block, or "Not sure". Audio never leaves memory; speech becomes the word "Conversation". Meera sees a heartbeat ("Listening · last heard 40 s ago" vs "Not listening since 10:42 AM"), so silence never looks like a normal day, and checks she sets ("Kitchen activity by 10:00 AM": Met / Not yet / Missed / Can't tell). Ravi says yes on his own screen, sees what she sees, and can pause it. A sample-day mode runs the same model with no microphone.

## What we added
Our own question: can one ordinary laptop microphone do a sensor kit's job, and **how often does it miss an activity or raise a false one**, per activity and per activity session? Our own setting: a distant caregiver of a parent with memory loss, with the parent's consent and pause as product states. Our own data: two teammates' kitchens, recorded with consent and labelled by a teammate who didn't write the code (Sunday; the honest worst case).

## How it works
Data: SINS / DCASE 2018 Task 5 (one person living alone for a week, 4 microphone arrays); 8,920 development clips, ≤ 1,000 per activity across all sessions, folds and microphones. Model: a frozen pretrained encoder (CED-tiny, 5.5 M parameters; within a point of CED-small, ahead of AST, ~40× faster than AST on a laptop CPU) plus a logistic-regression head we trained on the official session-disjoint folds. Rules then decide what the screen says: "Not sure" below a confidence threshold θ or for sounds unlike anything it learned, 2-of-3 smoothing, "Can't tell" when it wasn't listening. No LLM: it can't hear without sending audio to a cloud.

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

Pre-registered before any test audio was fetched (sample, scoring, microphone rule). Not confirmed by the mic-fingerprint rule; per-node numbers only, so we report all 7 microphones together; an unseen-microphone number is not claimed. The trained baselines below (log-mel, AST) were only run on the development folds.

**Held-out, per activity (one microphone): misses and false alarms counted separately**

| Activity | Caught (recall) | Missed | False alarms | N clips |
|---|---|---|---|---|
| Quiet | 95.1 [93.1, 95.9] | 97 | 198 | 1,988 |
| Cooking | 86.1 [71.4, 93.0] | 67 | 36 | 483 |
| Washing up | 72.6 [49.5, 84.9] | 96 | 35 | 350 |
| Eating | 84.9 [75.0, 91.8] | 53 | 42 | 350 |
| Moving about | 55.4 [40.6, 73.5] | 156 | 248 | 350 |
| Conversation | 96.9 [92.5, 100.0] | 11 | 81 | 350 |
| Vacuuming | 93.1 [71.4, 100.0] | 24 | 0 | 350 |
| TV | 98.6 [97.6, 100.0] | 29 | 4 | 2,107 |
| Working (typing) | 80.6 [72.7, 87.1] | 284 | 173 | 1,463 |

Recall fell from development to held-out for moving about 76% → 55%, washing up 89% → 73%, eating 92% → 85%, vacuuming 100% → 93%. The test set is a different stretch of the same week with a different mix of sessions and microphones; with only one held-out run we can't separate those causes.

**Meera's check (any kitchen activity), held-out:** caught 89.3 [85.3, 94.1]% of 1,183 windows (**missed 144**); **false alarms** on 0.5 [0.2, 1.1]% of 6,608 other windows (41). Computed after the run from its saved predictions (not in the pre-registration).

**Development folds (session-disjoint, 4-fold; optimistic: the same folds chose the model):**

| System | Macro F1 | Notes |
|---|---|---|
| **Kettle, one microphone** | **85.1 [81.1, 87.4]** | N = 8,920 clips / 257 sessions |
| Log-mel statistics + logistic regression (no deep model) | 79.7 [75.5, 82.4] |  |
| CED-small (4× bigger) + same head | 85.9 [81.9, 88.1] |  |
| AST (16× bigger) + same head | 83.0 [79.1, 85.7] | seeded subset: 2700 clips (ast_subset.json); Kettle 85.5 on the same clips |
| Apple SoundAnalysis, zero-shot | 32.4 [29.9, 35.1] |  |
| AST, zero-shot label map | 38.9 [35.6, 42.7] | seeded subset: 2700 clips (ast_subset.json); Kettle 85.5 on the same clips |
| Always "Quiet" | 4.6 [3.5, 5.7] |  |

Dev, Meera's check: caught 95.3 [93.8, 96.5]% of 3,000 kitchen windows (missed 164); false alarms on 1.8 [0.7, 3.7]% of 5,920 others (106).
<!-- results:end -->

<!-- tradeoff:start -->
**The "Not sure" bar θ.** Below θ = 0.66 confidence Kettle says "Not sure". We chose θ on dev folds so that shown labels are right 90% of the time (85% of windows get a label). For Meera's check it barely matters on dev: across 33 kitchen sessions (1.55 days of stitched audio) no kitchen session went unnoticed at any θ from 0.30 to 0.90, and θ only moved the count of false kitchen-activity blocks between 6 and 12 (3.87 per 16-hour day at the chosen θ, 7.75 at θ = 0.30). Those are kitchen-level false alarms; the "per hour" figure above counts every activity confusion, including cooking vs washing up. The cost of a high θ shows up elsewhere: 14% of held-out windows were "Not sure".
<!-- tradeoff:end -->

**Where it fails** (real dev-fold mistakes, `results/failures.md`):
<!-- failures:start -->
1. **Cooking heard as washing up** (63 dev clips; e.g. `DevNode2_ex46_83`: Washing up 0.98, Cooking 0.01; it heard door, dishes, drawer open or close). Rinsing and running water during cooking sounds like washing up.
2. **TV heard as conversation** (12 dev clips; e.g. `DevNode4_ex229_102`: Conversation 0.88, TV 0.11; it heard speech, silence, television). TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.
3. **Moving about heard as quiet** (91 dev clips; e.g. `DevNode1_ex87_13`: Quiet 0.93, Moving about 0.05; it heard silence, rustle, tick-tock). 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.
<!-- failures:end -->

**What we can't test:** the public recordings are one person in one home, so age and sex can't be checked; our kitchens are the only other homes (exploratory, small N). Every development number was also used to choose the model, so it's optimistic; the held-out run is the unbiased one, and it's a seeded sample of the official test set, not the full leaderboard set.

## What we'd do next
Five consenting households for two weeks, scored against a written diary; fine-tuning with microphone augmentation for new rooms; an old phone as the kitchen device; private access from outside the home.

## Sources
SINS / DCASE 2018 Task 5 dev (CC BY-NC 4.0, doi:10.5281/zenodo.1247102) and eval (CC BY-NC-ND 4.0, Zenodo 1291760 / 1964758), KU Leuven; DCASE 2018 Task 5 results (dcase.community); CED-tiny and CED-small (Xiaomi, Apache-2.0); AST (MIT, BSD-3); Apple SoundAnalysis; ESC-50 (CC BY-NC 3.0); ACL 2023 Profile of Older Americans; products studied: Howz, Canary Care, havn, Assistiv, Apple Sound Recognition, Alexa Together, StackCare, Care Daily, Snug. Libraries: PyTorch, transformers, scikit-learn, FastAPI, Playwright. AI tools: Claude Code (code and research), REA (product teardowns), Aside (research); see `docs/AI-USAGE-LOG.md`. Reproduce every number: `notebooks/kettle_reproduce.ipynb`.
