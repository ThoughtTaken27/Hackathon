# Kettle

**Track:** AI + Health · **Team:** (names on the submission form; Round 1 is blind)
*This project is a prototype and is not medical advice. Kettle is not an emergency device.*

<!-- lead:start -->
Your Mac already hears a kettle. Asked which of 9 household activities is happening, Apple's built-in sound classifier scores **31.8** macro F1 on the official DCASE 2018 test clips; Kettle, on one microphone, scores **84.1** (95% CI 74.4–86.7, 7,791 clips, run once with a frozen model).
<!-- lead:end -->

## The problem
About 28% of US adults 65 and over who live in the community live alone (US Administration for Community Living, *2023 Profile of Older Americans*). For an adult child far from a parent with early memory loss, "did Dad get up and have breakfast?" has no good answer: calling feels like checking up, cameras feel like spying, and sensor kits cost £419 plus £29 a month or $95–119 a month. In 418 reviews and posts we coded, the top pains were the parent feeling watched, being made to do something every day, and alerts that miss real problems or cry wolf. None of the nine products we studied publishes how often it's wrong (that we could find).

## What we built
Meera, 34 (invented persona), lives 300 miles from her father Ravi, 79. A laptop on his kitchen counter listens in 10-second windows and turns them into a day bar ("cooking around 8:15–8:30 AM, washing up, TV from about 9:30") with the sounds behind each block and a "Not sure" state. Audio stays in memory and is never saved or sent; speech becomes the word "Conversation", never words. Meera sees a heartbeat ("Listening · last heard 40 s ago", or "Not listening since 10:42 AM"), so silence never looks like a normal day, and up to three checks she sets ("Kitchen activity by 10:00 AM": Met / Not yet / Missed / Can't tell). Ravi says yes on his own screen, sees exactly what Meera sees, and can pause it; she sees "Paused by Dad". A sample-day mode and "Try your own sound" run the same model with no microphone.

## What we added
Our own question: can one ordinary laptop microphone do a sensor kit's job, and **how often does it miss an activity or raise a false one**, per activity and per activity session? Our own setting: a distant caregiver of a parent with memory loss, with the parent's consent and pause as product states. Our own data: two teammates' kitchens, recorded with consent and labelled by a teammate who didn't write the code (Sunday; the honest worst case).

## How it works
Data: SINS / DCASE 2018 Task 5, one person living alone for a week, 4 microphone arrays; we trained on 8,920 development clips (≤ 1,000 per activity, all sessions, folds and microphones; 9 sessions held out for the sample days). Model: a frozen pretrained audio encoder (CED-tiny, 5.5 M parameters: within a point of CED-small and ahead of AST on our folds, and ~40× faster than AST on a laptop CPU) plus a logistic-regression head we trained. Transparent rules then decide what the screen says: "Not sure" below a confidence threshold θ or when a sound is unlike every activity it learned, 2-of-3 smoothing, "Can't tell" when it wasn't listening. No LLM: it can't hear the kitchen without sending audio to a cloud.

## Results
<!-- results:start -->
Held-out numbers: the official DCASE 2018 Task 5 evaluation set, a pre-registered seeded sample (7,791 clips, 1,113 moments × 7 microphones), run once on 2026-11-14 13:04:02 CST with the frozen model (commit 351e929, model fa5de76a), reweighted to the true class counts. Not confirmed by the mic-fingerprint rule; per-node numbers only.

| System | Macro F1 [95% CI] | Data |
|---|---|---|
| **Kettle, one mic** (all 7 eval microphones) | **84.1 [74.4, 86.7]** | held-out test, N = 7,791 clips / 91 sessions |
| Kettle, 4-mic average (all 7 eval microphones) | 85.3 [75.5, 88.1] | held-out test |
| Apple SoundAnalysis, zero-shot | 31.8 [25.7, 37.9] | held-out test, same clips |
| CED-tiny, zero-shot | 38.5 [30.9, 47.2] | held-out test, same clips |
| Always 'Quiet' | 5.0 [1.6, 7.8] | held-out test, same clips |
| Kettle, one mic | 85.1 [81.1, 87.4] | dev folds, N = 8,920 clips / 257 sessions |
| Log-mel statistics + logistic regression (no deep model) | 79.7 [75.5, 82.4] | dev folds |
| AST + same head | 83.0 [79.1, 85.7] | dev folds; seeded subset: 2700 clips (ast_subset.json), Kettle 85.5 on the same clips |
| Apple SoundAnalysis, zero-shot | 32.4 [29.9, 35.1] | dev folds |
| AST, zero-shot | 38.9 [35.6, 42.7] | dev folds; seeded subset: 2700 clips (ast_subset.json), Kettle 85.5 on the same clips |
| Always 'Quiet' | 4.6 [3.5, 5.7] | dev folds |
| DCASE 2018 baseline (published) | 85.0 known mics · 83.1 unseen mics | full eval set, all dev data |
| Best DCASE 2018 entry (published) | 90.4 · 88.4 | full eval set |

**For Meera's check (any kitchen activity: cooking, washing up or eating), dev folds:** caught 95.3 [93.8, 96.5]% of 3,000 windows (missed 164); wrongly called kitchen activity on 1.8 [0.7, 3.7]% of 5,920 other windows (106).

| Activity | Caught | Missed | False alarms | N |
|---|---|---|---|---|
| Quiet | 95.1 [93.1, 95.9] | 97 | 198 | 1988 |
| Cooking | 86.1 [71.4, 93.0] | 67 | 36 | 483 |
| Washing up | 72.6 [49.5, 84.9] | 96 | 35 | 350 |
| Eating | 84.9 [75.0, 91.8] | 53 | 42 | 350 |
| Moving about | 55.4 [40.6, 73.5] | 156 | 248 | 350 |
| Conversation | 96.9 [92.5, 100.0] | 11 | 81 | 350 |
| Vacuuming | 93.1 [71.4, 100.0] | 24 | 0 | 350 |
| TV | 98.6 [97.6, 100.0] | 29 | 4 | 2107 |
| Working (typing) | 80.6 [72.7, 87.1] | 284 | 173 | 1463 |

On 260 sounds that aren't household activities (dogs, sirens, alarms, noise, silence), Kettle gave a confident label to 0.4 [0.1, 2.1]% (vs 56.2 [50.1, 62.1]% without its 'unlike anything it learned' check).
Through the day bar (2-of-3 smoothing), 66% of 257 activity sessions were caught with 3.23 false-alarm blocks per hour (11.1 without smoothing).
<!-- results:end -->

<!-- tradeoff:start -->
Below θ = 0.66 confidence Kettle says "Not sure" (chosen on dev folds so shown labels are right 90% of the time; 85% of windows get a label). A false "kitchen activity" could hide a skipped breakfast; a missed one costs Meera an unnecessary call. We lean toward fewer false ones: through the day bar, θ = 0.65 gives 12.91 false kitchen-activity blocks per 16-hour day and misses 17 of 33 meal sessions, versus 23.89 and 12 at θ = 0.30 (dev folds).
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
