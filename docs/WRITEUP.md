# Kettle

**Track:** AI + Health · **Team:** (names on the submission form; Round 1 is blind)
*This project is a prototype and is not medical advice. Kettle is not an emergency device.*

<!-- lead:start -->
Your Mac already hears a kettle. Asked which of 9 household activities is happening, Apple's built-in sound classifier scores **31.8** macro F1 on the official DCASE 2018 test clips; Kettle, on one microphone, scores **84.1** (95% CI 74.4–86.7, 7,791 clips, run once with a frozen model).
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
Held-out = the official DCASE 2018 Task 5 test set: a pre-registered seeded sample, 7,791 clips × all 7 microphones, 91 sessions, run once with the frozen model. Our pre-registered check couldn't tell which microphones are the 3 unseen ones, so we report all 7 together (published systems: known 85.0, unseen 83.1 for the baseline).

| System (macro F1, 95% CI) | Held-out test, one mic | Dev folds, one mic |
|---|---|---|
| **Kettle** | **84.1 [74.4, 86.7]** | 85.1 [81.1, 87.4] |
| Apple SoundAnalysis, zero-shot | 31.8 [25.7, 37.9] | 32.4 [29.9, 35.1] |
| Same encoder, zero-shot label map | 38.5 [30.9, 47.2] | 37.5 [34.4, 41.1] |
| Always "Quiet" | 5.0 [1.6, 7.8] | 4.6 [3.5, 5.7] |
| Log-mel + logistic regression (no deep model) | – | 79.7 [75.5, 82.4] |
| DCASE 2018 baseline / best entry (published, full data) | 85.0–83.1 / 90.4–88.4 | – |

**Meera's check (any kitchen activity), held-out:** caught 89.3 [85.3, 94.1]% of 1,183 windows (**missed 144**); **false alarms** on 0.5 [0.2, 1.1]% of 6,608 other windows (41).

Weakest on the held-out test: moving about (caught 55%, 156 missed, 248 false alarms of 350); washing up (caught 73%, 96 missed, 35 false alarms of 350); working (typing) (caught 81%, 284 missed, 173 false alarms of 1,463). Every activity's misses and false alarms: README and the app's "How sure is Kettle?" page.
<!-- results:end -->

<!-- tradeoff:start -->
Below θ = 0.66 confidence Kettle says "Not sure" (chosen on dev folds so shown labels are right 90% of the time; 85% of windows get a label). A false "kitchen activity" could hide a skipped breakfast; a missed one costs Meera an unnecessary call. We lean toward fewer false ones: through the day bar on dev folds, θ = 0.66 gives 3.87 false kitchen-activity blocks per 16-hour day and doesn't notice 0 of 33 kitchen sessions, versus 7.75 and 0 at θ = 0.30.
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
