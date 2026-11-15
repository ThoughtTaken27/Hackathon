# Pre-registration 2: does Kettle work outside the one research home?

Written Sat Nov 14 2026, ~9:50 PM CT, and committed **before any test half below was scored**. The commit that adds
this file, `models/witness.json`, `kettle/witness.py` and `eval/other_homes.py` is the pre-registration.

## Why this exists
A teammate's review (Sat 6:45-7:25 PM CT) fed 30 household clips from outside the research home into the live app:
the family view showed one confident "Cooking" block in 14 minutes, and it came from a vacuum cleaner. Every number
we had came from SINS, one home. This file fixes how we measure the same question at scale, and how we test a fix.

## Data (all public, never used to train anything in Kettle)
| Set | What | Licence | Split unit |
|---|---|---|---|
| DESED public eval (Zenodo 3588172) | 692 ten-second clips from YouTube home videos, human-labelled sound events with times | CC BY 4.0 (each clip: CC-BY upload) | uploader |
| Kitchen20 (github.com/marc-moreaux/kitchen20) | 1,070 five-second kitchen clips in 20 categories, cut from Freesound recordings | repo Apache-2.0; clips Freesound CC | source recording |
| ESC-50, 13 household categories | 520 five-second clips (vacuum, washing machine, typing, footsteps, toilet flush...) | CC BY-NC 3.0 | source recording |

- **Leakage audit, done before tuning:** CED-tiny was pretrained on AudioSet. 25 DESED clips come from videos that are
  also in AudioSet's segment lists (eval, balanced or unbalanced). They are **dropped** from every number.
- **Tune / test:** each group (uploader or source recording) goes to tune or test by the parity of
  `sha256("kettle-split:" + group id)`. No group is in both. All choices below were made on the tune halves and on
  SINS dev out-of-fold predictions. The test halves are scored once by `python -m eval.other_homes --test`.
- 5-second clips are repeated to 10 s (as `eval/offlist.py` does). One clip = one window; no smoothing.

## What counts
- **Kitchen clip (DESED):** Frying, Dishes or Blender events lasting 2 s or more in total. Blender clips stay in,
  although the fix below is known to miss them.
- **Non-kitchen clip (DESED):** no kitchen event and no running water: vacuum cleaner, electric shaver/toothbrush,
  speech only, pets and alarms. Clips with a kitchen event shorter than 2 s ("brief") and clips with running water
  but no kitchen event ("water": kitchen tap or shower, the label can't say) are reported separately, in neither group.
- **Kitchen20:** activity = blender, boiling-water, chopping, clean-dishes, cutlery, eat, frying-pan, juicer, peel,
  plates. Not an activity = fridge, dishwasher, sweep, book, cupboard, drawer. Reported separately because they
  usually do mean someone is cooking or at the sink: stove-fan, microwave, water-flowing.
- **ESC-50 household:** all 12 categories except pouring_water are "not a kitchen activity".
- **Shown as kitchen** = the window's label is Cooking, Washing up or Eating under the rule being tested.

## Metrics (fixed)
1. **Primary: kitchen activity caught in real homes** = share of DESED test-half kitchen clips shown as kitchen.
2. **False kitchen label** = share of DESED test-half non-kitchen clips shown as kitchen.
3. Secondary: the same two on Kitchen20 and the false rate on ESC-50 household, test halves; per-category rows.
4. Guard: SINS dev out-of-fold (the research home): kitchen caught and false kitchen, v1 vs v2.
5. 95% intervals: bootstrap over groups (2,000 draws, seed 0, percentile). N and group counts beside every number.

## Rules compared
- **v1 (shipped until now):** head label if the window is not "unlike anything learned" and its top probability >= θ.
- **v2:** `kettle/timeline.raw_label` with the second opinion in `kettle/witness.py` and `models/witness.json`
  (τ_k = 0.15, τ_v = 0.3). The head, θ, temperature and novelty threshold are unchanged (`models/head.json`, frozen).
- How τ_k was chosen (tune only): the highest kitchen-caught value whose false-kitchen rate was <= 1% on DESED tune
  non-kitchen clips and <= 2% on ESC-50 household tune clips, and whose SINS dev false-kitchen rate stayed within
  0.1 point of v1. Tune values at that setting: DESED caught 63.0% (v1: 8.3%), false 0 of 179; Kitchen20 caught
  34.8% (v1: 1.2%); SINS dev caught 89.4% (v1: 86.9%), false 0.83% (v1: 0.74%).

## What we expect, and what we will say if we are wrong
- We expect test-half "caught" within about 10 points of the tune value and false kitchen <= 3%.
- If the DESED test false-kitchen rate is above 5%, v2 failed its bar; we report that and say so wherever v2 is shown.
- Whatever the numbers are, they go in `results/other_homes.md`, the How-sure page and the write-up as they come out.

## What this does NOT show
YouTube clips are close to what the encoder was pretrained on, are often close-miked, and are 10-s clips chosen
because something happens in them. This is "other homes, other microphones", not "a laptop across a real kitchen
for a whole morning". The team's own kitchen recordings (eval/OWN_KITCHEN_GUIDE.md) remain the real test.
