# Open-source relatives and benchmark prior art (scout worker report, Sat Nov 14 2026; all accessed 2026-11-14)

Written by the lead session from the scout subagent's hand-back (the scout was not allowed to write .md files). Raw extraction: session scratchpad (not kept).

## DCASE 2018 Task 5 official baseline
- Repo: https://github.com/DCASE-REPO/dcase2018_baseline/tree/master/task5 · MIT · 130 stars · created 2018-03-05 · last commit 2019-08-19 (touches task 4, not 5).
- Input: 40 log-mel bands, 40 ms window, 20 ms hop, 50–8000 Hz, 501 frames = 10 s. Each of the 4 mics is a separate training example (single-channel model).
- Network: Conv2D 32 (40x5) + BN + ReLU → MaxPool (1x5) + dropout 0.2 → Conv2D 64 (1x3) + BN + ReLU → GlobalMaxPool + dropout 0.2 → Dense 64 → softmax 9.
- Fusion: the 4 per-mic posteriors are averaged.
- Training: Adam 1e-4, batch 256, 500 epochs, per-epoch class-balanced undersampling, 30% validation, model picked by macro-F1 every 10 epochs, seed 0. Keras 2.1.5 / TF 1.4; requirements unpinned.
- Dev 4-fold macro-F1 84.5 (results page). Untested: no per-class dev F1, no seed variance.

## Task and results (https://dcase.community/challenge2018/task-monitoring-domestic-activities , …-results)
- 9 classes: absence, cooking, dishwashing, eating, other, social activity, vacuum cleaning, watching TV, working. Metric: macro F1 per 10-s segment.
- Dev: 72,984 segments, 4 nodes, session-grouped 4-fold CV. Eval: 72,972 segments, 7 nodes; the 3 unseen nodes decide the ranking.
- Top by unknown-mic eval F1 (unknown-mic / dev-mic / dev): Inoue (IBM) 88.4 / 90.4 / 90.0; Tanabe (HIT) HITavg 88.4 / 89.7 / 89.8; Liu (THU) 87.5 / 89.4 / 89.8; baseline 83.1 / 85.0 / 84.5. Official tie-break between Inoue and Tanabe: unverified.
- Per-class unknown-mic F1 (absence, cooking, dish, eating, other, social, vacuum, TV, working):
  - Inoue_1: 93.7, 91.5, 86.5, 87.0, 54.2, 97.0, 97.1, 99.9, 88.7
  - Tanabe HITavg: 91.6, 97.0, 83.0, 84.2, 57.7, 98.2, 97.7, 100.0, 86.1
  - Baseline: 87.7, 93.0, 77.2, 81.2, 35.0, 96.6, 95.8, 99.9, 81.4
  - "Other" is the weakest class for every system.
- Overfit warning: Sun_SUTD 92.2 dev → 76.8 unknown-mic eval; Li_NPU 89.7 → 79.0. Dev numbers alone mislead.

## Winner: Inoue et al., IBM (https://dcase.community/documents/challenge2018/technical_reports/DCASE2018_Inoue_14.pdf)
- 40 log-mel, 64 ms window, 20 ms hop; CNN alternating frequency-only and time-only kernels; filters 64/128/256; global max pool; dense 128; softmax 9.
- Per-mic classification, 4 softmaxes averaged.
- Augmentation: cut each clip into five 2-s segments, shuffle, and mix two same-class clips segment-by-segment; minority classes only.
- 4-model ensemble (one per fold). Dev 89.95 vs baseline 84.50. Compute not stated.

## Pretrained embeddings on SINS since 2019
- None found with a verified number (PANNs, AST, BEATs, CLAP, VGGish searched). Scholar/Semantic Scholar unreachable, so not exhaustive.
- Candidate (numbers unverified): Zeng et al., arXiv:2306.05624 (2023), multi-scale dilated depthwise CNN on Task 5.
- Pre-2019: Kong et al., arXiv:1808.00773, 87.75 F1 (code: github.com/qiuqiangkong/dcase2018_task5, MIT). Chew et al., arXiv:1812.04618, 92.19 dev.
- **Implication for Kettle:** a frozen AST embedding + linear head on SINS appears to be unpublished, so it is a small, honest novelty (to re-check before claiming).

## WellNest (Devpost, https://devpost.com/software/wellnest-rplons)
- Routine monitoring (wake-up, kitchen, bathroom, bedtime), flags missed kitchen visits and inactivity, LLM daily summaries. Sensors unnamed; demo runs on a custom event **simulator** ("simulated and test data"). No accuracy claims, no code link found.

## GitHub: household-sound activity monitoring with a caregiver view
- No repo found that does this and publishes accuracy. Weak leads only (unverified): PMC11479356 (edge ADL sound recognition, 2024); PSAAL ADL Sound Dataset (16 classes); a 2017 Raspberry Pi pyAudioAnalysis study claiming >90% on six activities.
