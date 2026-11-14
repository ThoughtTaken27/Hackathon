# Kettle results (2026-11-14 10:46 CST, commit 9c95c8d809, head e9c8f1c92870)

Primary metric: macro F1 over the 9 SINS activities, 10-s windows. Dev numbers: **dev folds (also used for selection)**, N = 3684 clips from 257 sessions, prevalence-reweighted, 95% session-bootstrap CI.

## Dev folds: ours vs baselines (macro F1, %)

| System | Macro F1 [95% CI] |
|---|---|
| **Kettle: CED-tiny + logistic head, 4-mic node average** | 85.6 [81.7, 88.1] |
| **Kettle, single mic (channel 0, what one laptop hears)** | 84.9 [81.3, 87.4] |
| majority | 4.6 [3.4, 5.8] |
| loudness rule | 10.0 [8.5, 11.4] |
| logmel lr | 78.3 [73.8, 81.1] |
| ced tiny zeroshot | 37.7 [34.3, 41.4] |
| DCASE 2018 baseline (published, dev CV, full data) | 84.5 |
| Best DCASE 2018 entry (published, dev CV) | 90.0 |

## Per activity (dev, single mic): misses and false alarms

| Activity | Caught (recall) | Precision | Missed | False alarms | N |
|---|---|---|---|---|---|
| Quiet | 90.7 [87.0, 94.2] | 88.3 [81.5, 92.8] | 44 | 107 | 471 |
| Cooking | 89.0 [82.6, 93.7] | 84.8 [61.5, 98.2] | 31 | 30 | 283 |
| Washing up | 87.9 [83.6, 93.1] | 67.6 [42.2, 82.3] | 30 | 42 | 247 |
| Eating | 91.8 [86.5, 96.9] | 95.7 [89.4, 98.9] | 20 | 13 | 245 |
| Moving about | 74.2 [68.1, 79.9] | 33.1 [23.4, 45.5] | 118 | 108 | 457 |
| Conversation | 91.8 [85.9, 96.4] | 93.2 [86.7, 97.3] | 43 | 13 | 527 |
| Vacuuming | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 0 | 0 | 460 |
| TV | 99.0 [97.9, 100.0] | 99.6 [98.6, 100.0] | 5 | 7 | 499 |
| Working (typing) | 72.9 [64.0, 80.2] | 89.5 [83.4, 94.2] | 134 | 105 | 495 |

**Not sure:** θ = 0.67 (chosen on dev: reweighted shown-label precision ≥ 0.90); coverage 80.5% of windows get a label, precision of shown labels 90.4%. Temperature 1.05; ECE 0.020.

## Through the shipped timeline (activity sessions, dev)

With 2-of-3 smoothing: 69.3% of 257 activity sessions caught, 2.15 false-alarm blocks per hour of audio. Without smoothing: 56.4% caught, 11.63 per hour (10.23 h of stitched audio).

## Off-list sounds (not one of the 9 activities)

0.8 [0.2, 2.8]% of 260 off-list clips got a confident label with θ and the novelty gate (52.7 [46.6, 58.7]% with θ alone). Every one of those labels is wrong by construction.

## Ablations (dev, single mic)

- train ch0 only: 83.6
- no class balancing: 85.1

## Published DCASE 2018 Task 5 numbers

Published systems scored all 72,972 eval clips and trained on all 72,984 dev clips with 4-channel posterior averaging; ours is a seeded, reweighted subsample with a head trained on <= 1,000 clips per class.
Source: https://dcase.community/challenge2018/task-monitoring-domestic-activities-results (opened 2026-11-14)

