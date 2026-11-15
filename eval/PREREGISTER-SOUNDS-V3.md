# Pre-registration v3: a sound head trained on real homes too, tested on real homes it never heard

Written Sun 15 Nov 2026, ~4:15 PM CT, before any window of the new test sets below was embedded or scored.
Script: `python -m eval.sound_head_v3` → `results/sound_head_v3.json` (+ `web/public/model/sound_head.json` if adopted).

## Why
v2 (`results/sound_head.json`) passed 8 of 15 names on public clips, but in 10 real homes (`results/real_homes.json`) it
almost never named anything: its thresholds were set on clean clips, and real rooms score lower. v3 adds real-home audio to
training so thresholds are chosen where the device actually listens.

## Training data (the "tune" side): everything below, nothing from the test side
- v2's tune halves (Kitchen20, ESC-50, SINS dev folds 1-2, synthetic alarms, Nonspeech7k).
- **TUT Sound Events 2016 development, home** (10 recordings): already scored once by `eval/real_homes.py`; from now on it is
  training data, and `results/real_homes.json` stays as the record of that one test. 10-s windows, 5-s hop.
- **DESED public evaluation set, tune half** (real domestic YouTube clips, strong labels by the DCASE organisers): half by a hash
  of the file name (`eval/other_homes.half`).

## Test data, scored once
- **TUT Sound Events 2016 evaluation, home** (separate recordings, never used by us): 10-s windows, 10-s hop, as the device.
- **DESED public evaluation, test half.**
- v2's test halves (their third use; reported, disclosed).

## Labels
A window contains a sound if an annotated event of it overlaps the window by ≥ 0.5 s.
TUT: tap ← water tap running; dishes ← dishes, cutlery, washing dishes; cupboard ← cupboard, drawer; footsteps ← people walking.
DESED: dishes ← Dishes; tap ← Running_water; frying ← Frying; blender ← Blender; vacuum ← Vacuum_cleaner; alarm ← Alarm_bell_ringing.
Sounds a dataset doesn't annotate: its windows are negatives, except where an unannotated look-alike is likely, which are left
out (ambiguous): TV/talking in TUT and DESED (speech unannotated in TUT, TV unannotated in DESED); kettle, microwave, door,
footsteps and cupboard in DESED (whistles and beeps fall under its alarm label; doors and steps are unannotated).
v2's positives/ambiguous lists are unchanged for v2's datasets.

## Method (unchanged from v2 except the data)
One L2 logistic regression per sound; inputs (embedding, or embedding + AudioSet log-odds) and C from {0.01, 0.1, 1} by
grouped 5-fold CV on the tune side (groups: uploader / source / session / seed / recording / file); threshold = lowest with
out-of-fold tune precision ≥ 92%; hidden before testing if tune recall < 40% at that threshold. Same privacy veto.

## Bar (same as v1 and v2)
Shown to families only if, on the **pooled test side** (all three test sets), precision ≥ 90% and recall ≥ 40%.
Reported separately: the real-home test alone (TUT eval + DESED test), per sound, with N and Wilson intervals.

## Adoption rule (decided now)
v3 replaces v2 on the device only if it shows **at least as many names** as v2 under the bar on the pooled test side **and**
names more real-home test windows correctly (summed true names over the sounds annotated there) without more false names
per 1,000 real-home windows than v2 on the same windows. Otherwise v2 stays and v3 is reported as not shipped.

## Not done
No retuning after the test run. The frozen activity head, theta and the held-out SINS test are untouched.
