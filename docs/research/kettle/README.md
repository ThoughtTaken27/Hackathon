# Kettle research: incumbent teardowns (stage 1, Sat Nov 14, 2026, 08:53–09:35 CT)

## 10-line summary a judge could read
1. We studied 8 products that tell a family whether an older parent's day went normally: Howz, Canary Care, havn, Assistiv, Apple Sound Recognition, Alexa Together/Emergency Assist, StackCare and Care Daily (plus Snug and Caregiver Aware, lighter).
2. We coded **418 real reviews and posts** (153 stating a pain) into themes, by keyword rules and a full manual read by one coder.
3. The pains that hurt most are human: the parent feels **watched** (17), the product makes the **parent do something** daily (25), and alerts **miss real problems** (15) or **cry wolf** (16).
4. Sound-based detectors are a main source of both: Alexa's smoke alerts arrived 2 of 15 times, TV set off glass-break alerts, and Apple's Sound Recognition drew 30 knock alerts an hour and used up to 36% of a battery per day.
5. **No incumbent publishes any detection, miss or false-alarm rate.** havn and Assistiv sell sound sensing with none; havn's own pages contradict each other on whether it records audio.
6. Two pains we expected turned out small: users barely mention the 1–2 week cold start or installation.
7. Kettle's answer: a laptop or old phone already in the kitchen, nothing for the parent to do, listening only after the parent says yes, a pause button on their screen, and no audio ever written or sent.
8. It shows a calm day bar of activities with the sounds behind each one and a "not sure" state, plus a heartbeat so silence is never ambiguous.
9. And it **publishes its accuracy** per activity, with N, on a public week-long recording of one person living alone (SINS / DCASE 2018 Task 5), against the published challenge systems and against Apple's own built-in sound classifier.
10. We will not build fall detection, emergency calls, smoke detection or speech features: they are safety-critical or break the privacy promise.

## Index
| File | What it is |
|---|---|
| [`pain-points.md`](pain-points.md) | **Core deliverable.** Method, ranked themes with counts, shares, severity, examples and links |
| [`better-than.md`](better-than.md) | **Payoff.** Top 10 pains → incumbents' handling → Kettle's answer → how we prove it → effort; 3 things no incumbent does; what we won't build |
| [`feature-matrix.md`](feature-matrix.md) | Products × features (hardware, price, setup, cold start, activities, parent view, privacy, alerts, accuracy, offline, sharing) with Kettle's planned column |
| [`ui-patterns.md`](ui-patterns.md) | What each incumbent puts first on screen (measured), patterns to take, anti-patterns, Kettle's screens in words |
| [`rea-evidence.md`](rea-evidence.md) | REA evidence ledger: every call, Evidence ID, observation vs inference vs unknown |
| `teardown-*.md` | One per product, product-teardown template: howz, canarycare, havn, assistiv, apple-sound-recognition, alexa-together, stackcare, caredaily, snug (short) |
| [`coded-items.csv`](coded-items.csv) | All 418 items: id, product, source, stars, date, kind, themes, one-line text, URL |
| [`apple-soundanalysis-classes.txt`](apple-soundanalysis-classes.txt) | Apple's built-in SoundAnalysis classifier: 303 classes (macOS 27.2.1). Baseline input for stage 3 |
| `raw/` | Source material: App Store JSON, Canary CMS JSON, scout report on DCASE prior art, chatbot test, coding scripts (`build_items.py`, `code_items.py`, `export_coded.py`) |
| `rea/` | REA bundle part 1 and the public JS bundles exported from Canary Care and havn (third-party code kept for analysis only; **never used in the product**) |
| `shots/` | Public store screenshots and site images (research only; **never shipped in the app**) |

Regenerate the coded data: `cd docs/research/kettle/raw && python3 build_items.py && python3 code_items.py && python3 export_coded.py`.

## Open questions (best guesses made, unattended)
1. **Coding reliability.** One coder (the agent), no agreement score. Guess: counts ±20%. A teammate could re-code 50 random rows of `coded-items.csv` blind to check.
2. **Selection bias in sensor-kit reviews.** Canary and Howz reviews are almost all 5★ (Canary has no 1–2★ in 114). Guess: unhappy buyers return the kit; dissatisfaction shows up on Reddit instead. Shares are of pains in this market, not product quality scores.
3. **havn's microphone.** The shipped How-It-Works copy (REA) says motion and environment only; the FAQ describes a microphone and 4-second clips. We report both; which is true of the device is unknown.
4. **Apple Sound Recognition on Mac.** Apple lists iPhone, iPad, Vision Pro, CarPlay. The Mac has the sound-category strings (REA) but we did not find the feature in Mac settings. Treated as not on Mac.
5. **Apple zero-shot mapping.** There is no television class among the 303. Stage 3 must fix the 303→9 mapping before seeing test results and report the TV/conversation confusion.
6. **Post-2019 pretrained-embedding results on SINS.** None found (Scholar unreachable). "Frozen AST + linear head on SINS is unpublished" is a cautious claim; re-check before the write-up says it.
7. **Prices** for havn, Assistiv, Care Daily and current Howz consumer kits are unpublished.
8. **REA bundle part 2** is 40 MB, so it lives in `.overnight/kettle/` (git-ignored), not in the repo. The raw Aside transcripts also stay local in `.overnight/kettle/aside/` because they contain reviewers' names and usernames; the committed files carry paraphrases and links only, so regenerating `coded-items.csv` needs that local folder.
9. **Care Daily's RCT** (Levenson et al., 2025) was not opened at the primary source.
10. **"Eating" vs "cooking".** The chatbot test and SINS per-class results both say eating is hard to hear. Copy must say "kitchen activity", never "Dad ate".
