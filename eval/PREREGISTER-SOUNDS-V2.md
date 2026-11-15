# Pre-registration v2: a trained sound head for named everyday sounds

Written Sun 15 Nov 2026, before the trained head below was scored on any test half.
Follows `eval/PREREGISTER-SOUNDS.md` (v1: hand-written context rules; only "TV or radio" passed).
Script: `python -m eval.sound_head` → `results/sound_head.json` and `web/public/model/sound_head.json`.

## Why
Under v1, most sounds were caught often (frying 93%, tap 78%, glass 93%, vacuum 99% recall). They failed on **precision**:
a single AudioSet score with a threshold can't separate a sound from its look-alikes (cutlery vs glass breaking, a
smoke-alarm pattern vs a timer, a fan vs a vacuum). A small classifier trained on the sound's own examples and its
look-alikes can. The device already has both inputs: the CED-tiny embedding (192 numbers) and the 527 AudioSet scores.

## What changes
For each of the 15 measured sounds, one logistic regression (L2, balanced class weights), trained on the **tune halves only**.
- Positives, ambiguous clips (left out) and negatives: exactly `eval/sounds.py POS / AMBIG` (unchanged from v1).
- Inputs, chosen per sound by grouped 5-fold cross-validation **inside the tune halves** (average precision):
  (a) the standardised embedding [192], or (b) the embedding plus the log-odds of the 527 AudioSet scores [719].
  Regularisation C from {0.01, 0.1, 1}, chosen the same way.
- Threshold: on the out-of-fold tune scores, the lowest threshold whose tune precision is **≥ 92%** (a 2-point margin over
  the bar). If no threshold reaches 92% precision with tune recall ≥ 40%, the sound is **hidden before testing**.
- The privacy veto is unchanged: when a body or bathroom sound outscores the AudioSet score of every named sound, nothing
  is named.
- Folds group clips by uploader / source recording / SINS session / synthetic seed, so no recording is in two folds.

## Test, once
Same test halves, same metrics and **same bar** as v1: shown only if, on the test halves, precision ≥ 90% and recall ≥ 40%.
Every sound's test numbers are reported, including the ones that fail. v1's rules are reported next to them on the same windows.

## Disclosed limits, decided now
- The test halves were scored once before, with v1's rules (results/sounds.json). Nothing in this head was chosen with them,
  but this is their second use; we say so wherever the numbers appear.
- These are 10-second clips from public datasets, not a real kitchen. The real-kitchen recording (handover v3.3 §4) is the
  real test.
- If a sound fails, it stays hidden. No retuning on the test halves, no second attempt with a different bar.
- The frozen activity head (`models/head.json`), theta and the held-out SINS test are untouched.
