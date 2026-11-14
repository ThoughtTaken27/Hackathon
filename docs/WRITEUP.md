# Kettle

**Track:** AI + Health · **Team:** (names on the submission form; Round 1 is blind)
*This project is a prototype and is not medical advice. Kettle is not an emergency device.*

<!-- lead:start -->
On the official DCASE 2018 test set (run once with a frozen model; 1,113 moments × 7 microphones = 7,791 clips from 91 sessions), Kettle scores **84.1** macro F1 (95% CI 74.4–86.7) on one microphone and 85.3 on four: level with the official 2018 baseline (85.0 known / 83.1 unseen microphones, full set) and below the best entry (90.4 / 88.4). A Mac already hears a kettle, but Apple's built-in sound classifier scores 31.8 on the same clips. Our contribution isn't the leaderboard: it's publishing every activity's misses and false alarms, and a "Not sure", consent and pause design built around them.
<!-- lead:end -->

## The problem
About 28% of US adults 65+ living in the community live alone (US Administration for Community Living, *2023 Profile of Older Americans*). For an adult child far from a parent with early memory loss, "did Dad have breakfast?" has no good answer: calls feel like checking up, cameras like spying, and sensor kits cost hundreds plus a monthly fee. In 418 reviews we coded, the top pains were the parent feeling watched, daily chores for the parent, and alerts that miss or cry wolf. None of the nine products we studied publishes how often it's wrong (that we found).

## What we built
For Meera, 34, 300 miles from her father Ravi, 79 (both invented). A laptop on his counter labels 10-second windows of sound into a day bar ("cooking around 8:15–8:30 AM, TV from about 9:30") with the sounds behind each block, or "Not sure". Audio never leaves memory; speech becomes the word "Conversation". Meera sees a heartbeat ("Listening · last heard just now" vs "Not listening since 10:42 AM") and checks she sets ("Kitchen activity by 10:00 AM": Met / Missed / Can't tell). Ravi says yes on his own screen, sees what she sees, and can pause it. Sample days run the same model with no microphone.

## What we added
Our own question: can one laptop microphone do a sensor kit's job, and **how often does it miss an activity or raise a false one**? Our own setting: a distant caregiver, with the parent's consent and pause as product states. Our own data (Sunday, reported only once scored): two teammates' kitchens, labelled by a teammate who didn't write the code.

## How it works
SINS / DCASE 2018 Task 5 (one person living alone for a week, 4 microphone arrays); 8,920 development clips. A frozen pretrained encoder (CED-tiny, 5.5 M parameters, ~40× faster than AST on a laptop CPU) and a logistic-regression head trained on the official session-disjoint folds. Rules decide what the screen says: "Not sure" for low confidence or sounds unlike anything learned, 2-of-3 smoothing, "Can't tell" when not listening. No LLM: it can't hear without sending audio to a cloud.

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

CIs resample the 91 test sessions (the lower end is pessimistic: some resamples lack a rare activity). Sample, scoring and microphone rule were pre-registered before any test audio was fetched; the rule couldn't identify the 3 unseen microphones, so we report all 7 together and claim no unseen-microphone number.

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

Recall fell from dev to held-out for moving about 76% → 55%, washing up 89% → 73%, eating 92% → 85%, vacuuming 100% → 93% (a different stretch of the week and other microphones; one run can't separate the causes).

**Meera's check (any kitchen activity), held-out:** caught 89.3 [85.3, 94.1]% of 1,183 windows (**missed 144**); **false alarms** on 0.5 [0.2, 1.1]% of 6,608 other windows (41). Computed after the run from its saved predictions (not in the pre-registration).

Development folds (optimistic; they chose the model): Kettle 85.1 [81.1, 87.4], log-mel statistics + logistic regression (no deep model) 79.7 [75.5, 82.4], AST (16× bigger) + the same head 83.0 [79.1, 85.7] on a 2,700-clip subset where Kettle scores 85.5; N = 8,920 clips / 257 sessions.
<!-- results:end -->

<!-- tradeoff:start -->
"Not sure" below θ = 0.66 (chosen on dev so shown labels are right 90% of the time). On dev, no kitchen session went unnoticed at any θ from 0.30 to 0.90; θ only moved false kitchen blocks (7.75 → 3.87 per 16-hour day). Its cost: 14% of held-out windows were "Not sure".
<!-- tradeoff:end -->

**Where it fails** (real dev-fold mistakes, `results/failures.md`):
<!-- failures:start -->
1. **Cooking → washing up** (63 dev clips): Rinsing and running water during cooking sounds like washing up.
2. **TV → conversation** (12 dev clips): TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.
3. **Moving about → quiet** (91 dev clips): 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.
<!-- failures:end -->

**What we can't test:** SINS is one person in one home, so age and sex can't be checked; our kitchens are the only other homes (exploratory, small N). The held-out run is a seeded sample of the official test set, close to but not a leaderboard number.

## What we'd do next
Five consenting households for two weeks, scored against a written diary; fine-tuning with microphone augmentation for new rooms; an old phone as the kitchen device; private access from outside the home.

## Sources
SINS / DCASE 2018 Task 5 (KU Leuven; CC BY-NC 4.0 / CC BY-NC-ND 4.0; Zenodo 1247102, 1291760, 1964758) and its published results; CED-tiny/small (Xiaomi, Apache-2.0); AST (MIT, BSD-3); Apple SoundAnalysis; ESC-50 (CC BY-NC 3.0); ACL 2023 Profile of Older Americans; nine products studied (README). AI tools: Claude Code, REA, Aside (`docs/AI-USAGE-LOG.md`). Reproduce every number: `notebooks/kettle_reproduce.ipynb`.
