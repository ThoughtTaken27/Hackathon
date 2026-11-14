# Write-up and video script (living draft)

Owner: Storyteller (Lane B). Every number is copied from `results/metrics.json` with its N; `{}` marks a number the build hasn't produced yet. Never type a number by hand. Keep names and school out (Round 1 is blind). Final version: one page (~550 words). Template follows the brief: Problem / What we built / What we added / How it works / Results / What we'd do next / Sources.

---

# Kettle: know Dad's day went normally, from kitchen sounds, without watching him

**Track:** AI + Health. *This project is a prototype and is not medical advice.*

## The problem
About 28% of US adults 65 and over who live in the community live alone (US Administration for Community Living, 2023 Profile of Older Americans). For an adult child far away from a parent with early memory loss, "did Dad get up and have breakfast?" has no good answer: calling feels like checking up, cameras feel like spying, and the sensor kits sold for this cost £419 plus £29 a month or $95–119 a month. We coded 418 real reviews and posts about these products: the most painful complaints were the parent feeling watched (17), being made to do something every day (25), and alerts that miss real problems (15) or cry wolf (16). None of the nine products we studied publishes how often it is wrong (that we could find).

## Who it's for
Meera, 34 (invented persona), lives 300 miles from her father Ravi, 79, who has mild cognitive impairment and lives alone. At 11 AM she opens Kettle on her phone and sees "Listening · last heard 40 s ago. So far today: cooking around 8:15–8:45, washing up around 8:45, TV from about 9:15," and her own check, "kitchen activity by 10:00 AM: met." Ravi agreed to it on the kitchen laptop and can pause it any time; Meera sees when he does.

## What we built
A laptop in the kitchen listens in 10-second windows. A pretrained audio encoder (CED-tiny) and a classifier we trained turn each window into one of 9 household activities, with the sounds behind it and a "not sure" state. Audio stays in memory and is never saved or sent; speech becomes the word "Conversation", never a transcript. The caregiver page shows a heartbeat (so silence never looks like a normal day), a day bar, one summary sentence and up to three rules she sets herself. A demo mode plays recorded sample days through the same pipeline with no mic or network.

## What we added
Our own question and setting: can one ordinary laptop mic do the job of a sensor kit, and **how often does it miss an activity or raise a false one?** Our own data: recordings from our own kitchens, labelled by a teammate who didn't write the code, as the honest worst case.

## How it works
Mic → 16 kHz audio in memory → 10-s window → CED-tiny embedding (192 numbers) → logistic-regression head → activity + confidence → "not sure" below a threshold chosen on development data → 2-of-3 smoothing → day bar → caregiver rules (transparent, not learned). We chose CED-tiny because it matched larger encoders on a quick session-disjoint check while running ~40× faster than AST on a laptop CPU. We rejected an LLM (it can't hear the kitchen without sending audio to a cloud) and a learned "unusual day" model (the public data has no clock times to test it).

## Results
Public data: SINS / DCASE 2018 Task 5, a week-long recording of one person living alone. Model choices used the official session-disjoint development folds only; the official evaluation set was run **once** with the frozen model (commit {hash}).

| System | Macro F1 (N=) | Missed / false alarms | Notes |
| --- | --- | --- | --- |
| Always "Quiet" (most common class) | {} | | trivial baseline |
| Apple SoundAnalysis, zero-shot | {} | | what a Mac already ships |
| CLAP, zero-shot | {} | | |
| DCASE 2018 baseline (published) | 83.1 | — | unseen mics, full eval set |
| DCASE 2018 best (published) | 88.4 | — | unseen mics, full eval set |
| **Kettle** | {} | {} | unseen mics, seeded eval sample, 95% CI by session |

**Where it does worst** (worst first): {our own kitchens}, {"Moving about"}, {cooking vs eating}.

**Real failures:** 1. {} 2. {} 3. {}

## Limits
One home and one person in the public data, so we can't show fairness across ages or households; our kitchens are the only other homes. Eating is hard to hear. Our evaluation uses a seeded subsample of the official test set, so it is close to, not exactly, a leaderboard number. Kettle is not an emergency device: it doesn't detect falls and doesn't call anyone.

## What we'd do next
Five consenting households for two weeks, scored against a written diary; fine-tuning with microphone augmentation for new rooms; an old phone as the kitchen device; secure access from outside the house.

## Sources
SINS / DCASE 2018 Task 5 (KU Leuven, CC BY-NC 4.0 / CC BY-NC-ND 4.0); CED-tiny (Apache-2.0); AST (BSD-3); LAION CLAP (Apache-2.0); Apple SoundAnalysis; ACL 2023 Profile of Older Americans; products studied: Howz, Canary Care, havn, Assistiv, Apple Sound Recognition, Alexa Together, StackCare, Care Daily, Snug. AI tools: Claude Code, REA, Aside (see `docs/AI-USAGE-LOG.md`).

---

## 2-minute video script
See `docs/PRD.md` §18 (the source of truth); Lane B turns it into `docs/video/SHOTLIST.md`.

## The sentence a judge repeats
"Of the nine 'is Mum OK' products they checked, it's the only one that says how often it's wrong: missed activities and false alarms, per 10-second window and per activity session, on a public week-long recording of someone living alone, against Apple's own sound classifier."
