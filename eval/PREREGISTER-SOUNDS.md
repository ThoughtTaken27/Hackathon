# Pre-registration: named everyday sounds (handover v3.2, item 3.1)

Written Sun 15 Nov 2026, ~1:05 PM CT, **before** any held-out half below was scored with the new rules.
Script: `python -m eval.sounds` → `results/sounds.json`. Rules: `eval/beyond.py KINDS` (generator) → `web/public/model/kinds.json`
→ `web/public/js/sense.js kindsOf()` and its twin `kettle/kinds.py named()`.

## What changes
Context rules on each sound name, from handover 3.1 (Parth's live test showed "Kettle or a hot drink" and "Running water" on
frying + cutlery, with no kettle and no tap):
- **kettle:** only Boiling, Steam, Steam whistle, Whistle (Pour and Fill removed); its score must beat frying/sizzle, tap/sink and
  dishes in the same window.
- **tap:** only Water tap and Sink (generic Water removed); must beat frying/sizzle.
- **alarm → "Timer or appliance beep":** Beep, Buzzer, Alarm clock only. Smoke and fire alarm classes are never a family sound
  name (safety layer only).
- **door:** Door and Sliding door only (unchanged; Slam is not a door).
- **microwave:** score ≥ 0.5 and above Vacuum cleaner, Mechanical fan, Air conditioning and Engine.
Thresholds (tau) are still chosen by `eval/beyond.py` on SINS dev folds 1-2.

## Data and splits (fixed now)
- **Kitchen20** (1,070 clips): tune/test by uploader (`eval/other_homes.half(usr_id)`).
- **ESC-50**, all 2,000 clips (`results/cache/ced-tiny_esc50all.npz`): tune/test by source recording (`half(freesound id)`).
- **SINS dev** (8,920 windows, `results/cache/oof_dev.npz`): tune = folds 1-2, test = folds 3-4.
- **Synthetic alarms** (960): tune/test by seed parity (even = tune).
Each sound has positives (clips that contain it), ambiguous clips (left out of both counts) and negatives (everything else),
listed in `eval/sounds.py POS / AMBIG`.

## Metrics, per sound, on the **test** halves only
- **Recall** = positives named / positives.
- **False names per 1,000 negative windows.**
- **Precision** = true names / all names, on the pooled test negatives + positives.
Wilson 95% intervals; n with every number.

## Bar (decided now, not after)
A sound name is shown to families only if, on the test halves, **precision ≥ 90% and recall ≥ 40%**.
A sound with no positives in these sets cannot be measured and is **hidden** (`shown: false`), whatever it scores.
Hidden sounds are still computed on the device (they still take part in the privacy veto), never sent, never listed.
The "before" column (the rules shipped at `05bf6ea`) is reported next to "after" on the same windows.

## What we will not do
- No retuning on the test halves. If a sound fails, it is hidden, not adjusted until it passes.
- The frozen head, theta and the held-out SINS test are untouched.
