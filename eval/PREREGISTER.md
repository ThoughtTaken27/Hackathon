# Pre-registration: the one frozen run on the DCASE 2018 Task 5 evaluation set

Written and committed **before any evaluation-set audio was fetched** (Sat Nov 14 2026, ~10:35 AM CT).
The commit that adds this file is the pre-registration; its hash goes in `.overnight/kettle/STATE.md` and in
`results/eval_run.json`.

## What is fixed here
1. **Sample** (`eval/sample.py`, seed 20261114): 1,000 moments drawn uniformly from the 10,425 eval moments,
   topped up to at least 50 moments per activity, all 7 node copies → 1,113 moments, 7,791 clips
   (`eval/sample_eval.json`). Labels: Zenodo record 1964758 v2.0.0 (`data/meta/eval/`), by the dataset authors.
2. **Scoring** (`eval/metrics.py`, unit-tested on a hand-computed example): per 10-s clip, the 9 SINS classes,
   macro F1 (the DCASE metric) plus per-activity recall, precision, missed (FN) and false alarms (FP) with N.
   Confusion rows reweighted to the true eval class counts (cap 50). 95% intervals by session bootstrap
   (1,000 draws, seed 0, percentile).
3. **Two prediction modes, both reported:** per node = mean of the 4 channel posteriors (DCASE-comparable);
   single channel 0 (what one laptop microphone gets).
4. **Known vs unknown microphones** (`eval/fingerprint.py`): decided from unlabelled mean log-mel spectra only.
   If the rule doesn't match 4 eval nodes one-to-one to the 4 dev nodes, only per-node numbers are reported.
5. **Model:** the head frozen at the end of M3 (`models/head.json`; its sha256 is recorded in STATE before the run).
   θ ("Not sure" threshold) and temperature come from dev folds only. The window-level eval numbers use the
   argmax label (as DCASE did); the share of windows that would show "Not sure" at θ is reported beside them.
6. **One run.** `python -m eval --split dcase-eval` runs once. The code path is first rehearsed on a dev-fold
   stand-in with a dummy head. A rerun is allowed only if the run crashes before writing predictions; both
   attempts are logged. No retraining or re-tuning after seeing the result.
7. **Comparison:** the published DCASE 2018 Task 5 baseline (83.1 unknown-mic macro F1) and best entry
   (88.4), quoted from https://dcase.community/challenge2018/task-monitoring-domestic-activities-results with the
   caveat that they scored all 72,972 clips and trained on all dev data; ours is a seeded, reweighted subsample
   with a head trained on ≤ 1,000 clips per class.

## Guards
- Eval audio goes to `data/clips/eval/` and embeddings to `data/emb/*/eval*`. Training and selection code only
  read `dev`; `python -m eval` refuses to open eval embeddings unless `--split dcase-eval` is given and
  `models/head.json`'s sha256 matches the frozen hash in `models/FROZEN`.
- Every fetched eval clip is hashed; any byte-identical duplicate of a dev clip is reported (0 expected).
