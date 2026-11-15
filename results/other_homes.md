# Other homes: Kettle outside the research home

Made by `python -m eval.other_homes` (Sat Nov 14 2026, 09:51 PM CST). Rules and metrics were fixed in `eval/PREREGISTER-V2.md` before the test halves were scored.
One clip = one 10-second window, no smoothing. v1 = the rule shipped until Sat Nov 14 9:45 PM CT. v2 = v1 checked by the second opinion (`kettle/witness.py`).
Leakage audit: 25 DESED clips whose videos are also in AudioSet (the encoder's pretraining data) were dropped.

## TEST halves (scored once)

| | v1 (shipped before) | v2 (second opinion) |
|---|---|---|
| Real-home kitchen clips shown as a kitchen activity (DESED: frying, dishes, blender) | 6.3% [1.4, 11.8] (5 of 79, 56 sources) | 43.0% [25.9, 60.5] (34 of 79, 56 sources) |
| Real-home NON-kitchen clips shown as a kitchen activity (vacuum, shaver, speech, pets, alarms) | 0.0% [0.0, 0.0] (0 of 191, 153 sources) | 0.0% [0.0, 0.0] (0 of 191, 153 sources) |
| Kitchen20 activity clips shown as a kitchen activity (10 categories) | 2.7% [0.9, 5.1] (8 of 293, 111 sources) | 42.7% [34.1, 52.1] (125 of 293, 111 sources) |
| Kitchen20 non-activity clips shown as kitchen (fridge, dishwasher, sweep, book, cupboard, drawer) | 1.3% [0.0, 3.3] (2 of 153, 81 sources) | 3.9% [1.3, 7.2] (6 of 153, 81 sources) |
| ESC-50 household non-kitchen clips shown as kitchen (12 categories) | 0.0% [0.0, 0.0] (0 of 257, 212 sources) | 2.7% [0.8, 5.3] (7 of 257, 212 sources) |
| DESED clips with under 2 s of kitchen sound (in neither group) | 10.0% [0.0, 23.8] (2 of 20, 19 sources) | 75.0% [55.0, 90.9] (15 of 20, 19 sources) |
| DESED running water, no kitchen event (tap or shower; in neither group) | 0.0% [0.0, 0.0] (0 of 43, 36 sources) | 30.2% [15.0, 46.8] (13 of 43, 36 sources) |

Per category, v1 → v2 (share shown as a kitchen activity; n):

- desed/kitchen: 6.3% → 43.0% (n = 79)
- desed/brief: 10.0% → 75.0% (n = 20)
- desed/water: 0.0% → 30.2% (n = 43)
- desed/vacuum: 0.0% → 0.0% (n = 42)
- desed/shaver: 0.0% → 0.0% (n = 43)
- desed/speech: 0.0% → 0.0% (n = 1)
- desed/pets_alarms: 0.0% → 0.0% (n = 105)
- kitchen20/blender: 0.0% → 0.0% (n = 21)
- kitchen20/boiling-water: 0.0% → 40.9% (n = 22)
- kitchen20/chopping: 0.0% → 72.7% (n = 22)
- kitchen20/clean-dishes: 5.0% → 72.5% (n = 40)
- kitchen20/cutlery: 0.0% → 28.3% (n = 46)
- kitchen20/eat: 0.0% → 95.2% (n = 21)
- kitchen20/frying-pan: 13.6% → 77.3% (n = 44)
- kitchen20/juicer: 0.0% → 0.0% (n = 26)
- kitchen20/peel: 0.0% → 0.0% (n = 30)
- kitchen20/plates: 0.0% → 19.0% (n = 21)
- kitchen20/fridge: 4.3% → 4.3% (n = 23)
- kitchen20/dishwasher: 0.0% → 4.2% (n = 24)
- kitchen20/sweep: 3.6% → 3.6% (n = 28)
- kitchen20/book: 0.0% → 13.6% (n = 22)
- kitchen20/cupboard: 0.0% → 0.0% (n = 22)
- kitchen20/drawer: 0.0% → 0.0% (n = 34)
- kitchen20/stove-fan: 9.1% → 9.1% (n = 22)
- kitchen20/microwave: 14.3% → 14.3% (n = 21)
- kitchen20/water-flowing: 0.0% → 96.8% (n = 31)
- esc50_house/vacuum_cleaner: 0.0% → 0.0% (n = 23)
- esc50_house/washing_machine: 0.0% → 0.0% (n = 21)
- esc50_house/keyboard_typing: 0.0% → 0.0% (n = 23)
- esc50_house/footsteps: 0.0% → 22.7% (n = 22)
- esc50_house/door_wood_knock: 0.0% → 0.0% (n = 19)
- esc50_house/toilet_flush: 0.0% → 11.1% (n = 18)
- esc50_house/brushing_teeth: 0.0% → 0.0% (n = 27)
- esc50_house/clock_tick: 0.0% → 0.0% (n = 17)
- esc50_house/mouse_click: 0.0% → 0.0% (n = 18)
- esc50_house/door_wood_creaks: 0.0% → 0.0% (n = 26)
- esc50_house/pouring_water: 0.0% → 11.5% (n = 26)
- esc50_house/snoring: 0.0% → 0.0% (n = 22)
- esc50_house/coughing: 0.0% → 0.0% (n = 21)

## Tune halves (used to choose τ_k and the tag lists)

| | v1 (shipped before) | v2 (second opinion) |
|---|---|---|
| Real-home kitchen clips shown as a kitchen activity (DESED: frying, dishes, blender) | 8.3% [2.5, 17.6] (9 of 108, 57 sources) | 63.0% [46.7, 73.9] (68 of 108, 57 sources) |
| Real-home NON-kitchen clips shown as a kitchen activity (vacuum, shaver, speech, pets, alarms) | 0.0% [0.0, 0.0] (0 of 179, 151 sources) | 0.0% [0.0, 0.0] (0 of 179, 151 sources) |
| Kitchen20 activity clips shown as a kitchen activity (10 categories) | 1.2% [0.0, 3.3] (3 of 247, 100 sources) | 34.8% [26.6, 44.0] (86 of 247, 100 sources) |
| Kitchen20 non-activity clips shown as kitchen (fridge, dishwasher, sweep, book, cupboard, drawer) | 2.3% [0.0, 5.8] (4 of 177, 77 sources) | 3.4% [0.6, 7.3] (6 of 177, 77 sources) |
| ESC-50 household non-kitchen clips shown as kitchen (12 categories) | 0.0% [0.0, 0.0] (0 of 223, 194 sources) | 1.8% [0.4, 3.7] (4 of 223, 194 sources) |
| DESED clips with under 2 s of kitchen sound (in neither group) | 5.0% [0.0, 16.7] (1 of 20, 18 sources) | 55.0% [35.0, 75.0] (11 of 20, 18 sources) |
| DESED running water, no kitchen event (tap or shower; in neither group) | 0.0% [0.0, 0.0] (0 of 27, 25 sources) | 18.5% [4.0, 33.3] (5 of 27, 25 sources) |

Per category, v1 → v2 (share shown as a kitchen activity; n):

- desed/kitchen: 8.3% → 63.0% (n = 108)
- desed/brief: 5.0% → 55.0% (n = 20)
- desed/water: 0.0% → 18.5% (n = 27)
- desed/vacuum: 0.0% → 0.0% (n = 51)
- desed/shaver: 0.0% → 0.0% (n = 38)
- desed/speech: 0.0% → 0.0% (n = 1)
- desed/pets_alarms: 0.0% → 0.0% (n = 89)
- kitchen20/blender: 0.0% → 3.8% (n = 26)
- kitchen20/boiling-water: 0.0% → 66.7% (n = 24)
- kitchen20/chopping: 0.0% → 34.8% (n = 23)
- kitchen20/clean-dishes: 0.0% → 75.0% (n = 20)
- kitchen20/cutlery: 0.0% → 8.7% (n = 23)
- kitchen20/eat: 0.0% → 95.2% (n = 21)
- kitchen20/frying-pan: 4.2% → 62.5% (n = 24)
- kitchen20/juicer: 0.0% → 0.0% (n = 25)
- kitchen20/peel: 10.5% → 10.5% (n = 19)
- kitchen20/plates: 0.0% → 16.7% (n = 42)
- kitchen20/fridge: 0.0% → 0.0% (n = 27)
- kitchen20/dishwasher: 2.4% → 2.4% (n = 42)
- kitchen20/sweep: 0.0% → 3.2% (n = 31)
- kitchen20/book: 0.0% → 3.3% (n = 30)
- kitchen20/cupboard: 12.0% → 12.0% (n = 25)
- kitchen20/drawer: 0.0% → 0.0% (n = 22)
- kitchen20/stove-fan: 21.9% → 21.9% (n = 32)
- kitchen20/microwave: 6.7% → 6.7% (n = 30)
- kitchen20/water-flowing: 0.0% → 68.4% (n = 19)
- esc50_house/vacuum_cleaner: 0.0% → 0.0% (n = 17)
- esc50_house/washing_machine: 0.0% → 0.0% (n = 19)
- esc50_house/keyboard_typing: 0.0% → 0.0% (n = 17)
- esc50_house/footsteps: 0.0% → 5.6% (n = 18)
- esc50_house/door_wood_knock: 0.0% → 4.8% (n = 21)
- esc50_house/toilet_flush: 0.0% → 9.1% (n = 22)
- esc50_house/brushing_teeth: 0.0% → 0.0% (n = 13)
- esc50_house/clock_tick: 0.0% → 0.0% (n = 23)
- esc50_house/mouse_click: 0.0% → 0.0% (n = 22)
- esc50_house/door_wood_creaks: 0.0% → 0.0% (n = 14)
- esc50_house/pouring_water: 0.0% → 21.4% (n = 14)
- esc50_house/snoring: 0.0% → 0.0% (n = 18)
- esc50_house/coughing: 0.0% → 0.0% (n = 19)

## Read this before quoting the numbers

- **The test half came in lower than we wrote we expected.** PREREGISTER-V2 expected 'caught' within about 10 points of the tune value (63.0%). The test value is 43.0% [25.9, 60.5]: 20.0 points lower, with a wide interval (79 clips, 56 uploaders). We did not retune. 43.0% is the number to quote.
- The false-kitchen bar (at most 5% on DESED test non-kitchen clips) was met: 0 of 191.
- v2 still misses many single 10-second kitchen windows in other homes. A real meal is many windows; whether that adds up to 'the meal was noticed' is what the own-kitchen recordings measure.
- Known misses by design: blenders and juicers (the tags can't tell them from a vacuum cleaner). Known false kitchen labels: footsteps on a crunchy surface (heard as 'Crunch') and running water outside the kitchen.
- **Post hoc (looked at after the test run, so a description and not a result):** by the clip's main kitchen sound, v2 caught frying 24 of 25 on the test half (tune: 53 of 62); dishes 10 of 15 on the test half (tune: 15 of 19); blender 0 of 39 on the test half (tune: 0 of 27). The two halves hold different shares of blender clips, which is where the gap between them comes from.
- 615 of the 667 real-home clips were flagged 'unlike anything it learned' by the head's own check: outside the research home, the second opinion does almost all of the work.

## Guard: the research home (SINS dev, out-of-fold; used for tuning, so this is not a test)

| | v1 | v2 |
|---|---|---|
| Kitchen windows shown as a kitchen activity | 86.9% [84.0, 89.9] (2607 of 3000, 33 sources) | 89.4% [87.1, 91.7] (2682 of 3000, 33 sources) |
| Other windows shown as a kitchen activity | 0.7% [0.1, 1.8] (44 of 5920, 224 sources) | 0.8% [0.2, 1.9] (49 of 5920, 224 sources) |
| Windows shown with their true label | 82.2% | 82.7% |
| Windows shown as Not sure | 13.3% | 12.4% |

## What this does not show
These are 10-second clips from YouTube and Freesound: other homes and other microphones, but often close to the sound, and close to what the encoder was pretrained on. It is not a laptop across a real kitchen for a morning. Our own kitchens are the real test (eval/OWN_KITCHEN_GUIDE.md).
