# Kettle results (2026-11-14 16:18 CST, commit 298da1c195, head fa5de76a7970)

Primary metric: macro F1 over the 9 SINS activities, 10-s windows. Dev numbers: **dev folds (also used for selection)**, N = 8920 clips from 257 sessions, prevalence-reweighted, 95% session-bootstrap CI.

## Held-out test: official DCASE 2018 Task 5 eval sample, run once

Run 2026-11-14 13:04:02 CST · commit 351e929292 · head fa5de76a7970 · N = 7791 clips, 1113 moments

| Slice | Ours, 4-mic node average | Ours, single mic (ch 0) | DCASE baseline | Best entry |
|---|---|---|---|---|
| All 7 nodes | 85.3 [75.5, 88.1] | 84.1 [74.4, 86.7] | – | – |

Published DCASE 2018 Task 5 (full eval set, all dev data): baseline 85.0 known mics / 83.1 unseen mics; best entry 90.4 / 88.4. Our 'all 7 nodes' mixes known and unseen microphones, so it sits between those columns by construction; not strictly comparable.

**Kitchen activity (caregiver metric), held-out:** caught 89.3 [85.3, 94.1]% of 1183 windows (missed 144); false alarms on 0.5 [0.2, 1.1]% of 6608 other windows (41). Computed after the run from the same frozen predictions; not in the pre-registration.

Mic mapping: NOT confirmed by the mic-fingerprint rule; per-node numbers only.

| Eval node | 4-mic average | Single mic | N clips |
|---|---|---|---|
| EvalNode1 | 86.3 [76.5, 89.3] | 85.2 [75.2, 87.5] | 1113 |
| EvalNode2 | 86.7 [76.6, 89.4] | 84.4 [74.4, 87.0] | 1113 |
| EvalNode3 | 80.5 [70.7, 84.0] | 79.9 [70.5, 83.6] | 1113 |
| EvalNode4 | 87.3 [77.2, 90.6] | 85.6 [75.6, 89.0] | 1113 |
| EvalNode5 | 86.5 [76.4, 89.3] | 85.6 [75.5, 88.7] | 1113 |
| EvalNode6 | 85.0 [74.9, 88.8] | 85.0 [74.9, 88.1] | 1113 |
| EvalNode7 | 84.8 [75.5, 87.5] | 83.4 [74.5, 86.6] | 1113 |

Baselines on the same held-out clips (single mic): majority 5.0 [1.6, 7.8]; ced tiny zeroshot 38.5 [30.9, 47.2]; ast zeroshot: not run (no AST embeddings of the eval clips; AST is reported on dev); apple zeroshot 31.8 [25.7, 37.9]. Share of windows below θ ('Not sure'): 14.2 [13.5, 15.0]%.

## The caregiver's metric: kitchen activity (cooking, washing up or eating), dev folds, single mic

Caught 95.3 [93.8, 96.5]% of 3000 kitchen-activity windows (missed 164); right 87.8 [75.2, 95.7]% of the time it said kitchen activity; false alarms on 1.8 [0.7, 3.7]% of 5920 other windows (106 windows). Reweighted to true prevalence; session-bootstrap 95% CI.

## Dev folds: ours vs baselines (macro F1, %)

| System | Macro F1 [95% CI] |
|---|---|
| **Kettle: CED-tiny + logistic head, 4-mic node average** | 86.2 [82.1, 88.6] |
| **Kettle, single mic (channel 0, what one laptop hears)** | 85.1 [81.1, 87.4] |
| majority | 4.6 [3.5, 5.7] |
| loudness rule | 10.2 [8.9, 11.6] |
| logmel lr | 79.7 [75.5, 82.4] |
| ced tiny zeroshot | 37.5 [34.4, 41.1] |
| ast probe (seeded subset: 2700 clips (ast_subset.json); Kettle on the same clips: 85.5 [81.4, 88.0]) | 83.0 [79.1, 85.7] |
| ast zeroshot (seeded subset: 2700 clips (ast_subset.json); Kettle on the same clips: 85.5 [81.4, 88.0]) | 38.9 [35.6, 42.7] |
| ced small probe | 85.9 [81.9, 88.1] |
| apple zeroshot | 32.4 [29.9, 35.1] |
| DCASE 2018 baseline (published, dev CV, full data) | 84.5 |
| Best DCASE 2018 entry (published, dev CV) | 90.0 |

## Per activity (dev, single mic): misses and false alarms

| Activity | Caught (recall) | Precision | Missed | False alarms | N |
|---|---|---|---|---|---|
| Quiet | 91.5 [89.1, 93.9] | 88.3 [81.8, 92.6] | 85 | 222 | 1000 |
| Cooking | 89.7 [85.9, 92.7] | 86.6 [64.7, 97.9] | 103 | 72 | 1000 |
| Washing up | 89.3 [85.5, 93.2] | 65.5 [39.3, 81.7] | 107 | 115 | 1000 |
| Eating | 92.1 [87.8, 96.1] | 89.4 [77.4, 95.6] | 79 | 44 | 1000 |
| Moving about | 76.5 [71.1, 81.6] | 35.8 [26.8, 46.5] | 235 | 244 | 1000 |
| Conversation | 93.4 [87.9, 97.3] | 91.8 [82.3, 96.9] | 66 | 34 | 1000 |
| Vacuuming | 99.9 [99.6, 100.0] | 100.0 [100.0, 100.0] | 1 | 0 | 920 |
| TV | 98.1 [95.9, 99.8] | 99.5 [98.4, 99.9] | 19 | 15 | 1000 |
| Working (typing) | 73.8 [65.1, 80.5] | 91.5 [87.1, 94.6] | 262 | 211 | 1000 |

**Not sure:** θ = 0.66 (chosen on dev: reweighted shown-label precision ≥ 0.90); coverage 85.0 [81.8, 88.1]% of windows get a label, precision of shown labels 90.1 [86.8, 92.4]%. Temperature 1.00; expected calibration error 1.5 [0.8, 2.6] points.

**Calibration:** expected calibration error 1.6 [0.9, 2.6] points before temperature scaling, 1.5 [0.8, 2.6] after (temperature cross-fitted across folds). Plot: `results/reliability_dev.png`.

## The cost of θ for Meera's check (dev, through the shipped timeline; kitchen activity = cooking, washing up or eating)

| θ | Kitchen sessions not noticed | False kitchen-activity blocks per 16-h day |
|---|---|---|
| 0.30 | 0 of 33 | 7.75 |
| 0.40 | 0 of 33 | 6.46 |
| 0.50 | 0 of 33 | 5.17 |
| 0.60 | 0 of 33 | 3.87 |
| 0.66 (shipped) | 0 of 33 | 3.87 |
| 0.70 | 0 of 33 | 4.52 |
| 0.80 | 0 of 33 | 5.17 |
| 0.90 | 0 of 33 | 4.52 |

Plot: `results/theta_tradeoff_dev.png`. A false 'kitchen activity' can hide a skipped breakfast (Meera isn't told); a missed one can make a normal morning look like 'Not heard by 10:00 AM' (Meera calls). See the write-up for which way we lean.

'Noticed' here means any kitchen-activity block overlaps the session. Under the strict rule (kitchen session caught only if one block of its own activity (cooking, washing up or eating) covers at least half of it), 15 of 33 kitchen sessions are caught (45.5 [29.8, 62.0]%): the day bar notices every kitchen session, but in the rest the right activity never formed one block covering half of it (another kitchen activity, 'Not sure' or shorter blocks filled the gap; we haven't measured which most often). Window-level kitchen recall and these session counts measure different things.

## Slices we can check (and the ones we can't)

SINS is one person in one home, so **age and sex can't be tested**. What we can show:

| Slice | Macro F1 [95% CI], single mic |
|---|---|
| Microphone position DevNode1 (dev) | 83.9 [80.4, 86.3] |
| Microphone position DevNode2 (dev) | 86.2 [81.8, 89.1] |
| Microphone position DevNode3 (dev) | 86.7 [83.1, 89.3] |
| Microphone position DevNode4 (dev) | 84.0 [79.1, 87.1] |
| Home 1: teammate kitchen (Sunday, own-kitchen set) | not measured yet |
| Home 2: teammate kitchen (Sunday, own-kitchen set) | not measured yet |

## Through the shipped timeline (activity sessions, dev)

With 2-of-3 smoothing: 66.5 [60.6, 72.0]% of 257 activity sessions caught, 3.23 false-alarm blocks per hour of audio. Without smoothing: 47.1 [41.1, 53.2]% caught, 11.1 per hour (24.78 h of stitched audio).

## Off-list sounds (not one of the 9 activities)

0.4 [0.1, 2.1]% of 260 off-list clips got a confident label with θ and the novelty gate (56.2 [50.1, 62.1]% with θ alone). Every one of those labels is wrong by construction.

## Ablations (dev, single mic)

- train ch0 only: 85.3 [81.2, 87.5]
- no class balancing: 85.1 [81.0, 87.4]
- mlp head: 84.7 [80.8, 87.0]
- leave one mic node out: held-out node mean 82.7 vs same nodes 85.2 (DevNode1 81.5 [78.0, 83.9], DevNode2 82.7 [78.3, 85.8], DevNode3 85.7 [81.9, 88.3], DevNode4 81.0 [76.9, 84.1])
- chip 5s window: 80.8 [77.0, 83.0]

## Published DCASE 2018 Task 5 numbers

Published systems scored all 72,972 eval clips and trained on all 72,984 dev clips with 4-channel posterior averaging; ours is a seeded, reweighted subsample with a head trained on <= 1,000 clips per class.
Source: https://dcase.community/challenge2018/task-monitoring-domestic-activities-results (opened 2026-11-14)

