# Kettle results (2026-11-14 13:02 CST, commit 4076fdec29, head fa5de76a7970)

Primary metric: macro F1 over the 9 SINS activities, 10-s windows. Dev numbers: **dev folds (also used for selection)**, N = 8920 clips from 257 sessions, prevalence-reweighted, 95% session-bootstrap CI.

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

**Not sure:** θ = 0.66 (chosen on dev: reweighted shown-label precision ≥ 0.90); coverage 85.0% of windows get a label, precision of shown labels 90.1%. Temperature 1.00; expected calibration error 1.5 [0.8, 2.6] points.

**Calibration:** expected calibration error 1.6 [0.9, 2.6] points before temperature scaling, 1.5 [0.8, 2.6] after (temperature cross-fitted across folds). Plot: `results/reliability_dev.png`.

## The cost of θ for Meera (dev, through the shipped timeline)

| θ | Kitchen-activity sessions missed | False kitchen-activity blocks per day | All false-alarm blocks per hour |
|---|---|---|---|
| 0.30 | 12 of 33 | 23.89 | 7.39 |
| 0.40 | 12 of 33 | 21.31 | 6.78 |
| 0.50 | 14 of 33 | 18.08 | 5.49 |
| 0.55 | 15 of 33 | 16.79 | 4.88 |
| 0.60 | 16 of 33 | 14.85 | 4.24 |
| 0.65 (shipped) | 17 of 33 | 12.91 | 3.51 |
| 0.70 | 19 of 33 | 12.91 | 2.91 |
| 0.75 | 21 of 33 | 11.62 | 2.26 |
| 0.80 | 21 of 33 | 10.33 | 1.65 |
| 0.85 | 24 of 33 | 7.75 | 0.97 |
| 0.90 | 26 of 33 | 6.46 | 0.48 |

Plot: `results/theta_tradeoff_dev.png`. A false 'kitchen activity' can hide a skipped breakfast (Meera isn't told); a missed one can make a normal morning look like 'Not heard by 10:00 AM' (Meera calls). See the write-up for which way we lean.

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

With 2-of-3 smoothing: 66.5% of 257 activity sessions caught, 3.23 false-alarm blocks per hour of audio. Without smoothing: 47.1% caught, 11.1 per hour (24.78 h of stitched audio).

## Off-list sounds (not one of the 9 activities)

0.4 [0.1, 2.1]% of 260 off-list clips got a confident label with θ and the novelty gate (56.2 [50.1, 62.1]% with θ alone). Every one of those labels is wrong by construction.

## Ablations (dev, single mic)

- train ch0 only: 85.3
- no class balancing: 85.1
- mlp head: 84.7
- leave one mic node out: held-out node mean 82.7 vs same nodes 85.2 ({np.str_('DevNode1'): 81.5, np.str_('DevNode2'): 82.7, np.str_('DevNode3'): 85.7, np.str_('DevNode4'): 81.0})
- chip 5s window: 80.8

## Published DCASE 2018 Task 5 numbers

Published systems scored all 72,972 eval clips and trained on all 72,984 dev clips with 4-channel posterior averaging; ours is a seeded, reweighted subsample with a head trained on <= 1,000 clips per class.
Source: https://dcase.community/challenge2018/task-monitoring-domestic-activities-results (opened 2026-11-14)

