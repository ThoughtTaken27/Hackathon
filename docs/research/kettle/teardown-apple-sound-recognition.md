# Teardown: Apple Sound Recognition + the SoundAnalysis framework (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://support.apple.com/guide/iphone/use-sound-recognition-iphf2dc33312/ios · Apple · free, built in · **alive** (iOS 27 changes reported Sep 2026) · iPhone, iPad, Apple Vision Pro, CarPlay (sirens/horns); **not listed for Mac**. Developer side: the public `SoundAnalysis` framework with a built-in classifier (`SNClassifySoundRequest(classifierIdentifier: .version1)`).

Evidence: `raw/aside-havn-assistiv-apple.txt` (support pages, 19 user opinions), REA `ev_b1d3865a…` (row 9 of `rea-evidence.md`: HearingUtilities strings on this Mac), `apple-soundanalysis-classes.txt` (303 classes, dumped on this Mac), `docs/research/samples/wow/probe-apple-soundanalysis.txt` (6 SINS clips run through it).

## Why people use it
- Built for deaf and hard-of-hearing users: alerts for alarms, doorbells, knocks, a baby crying, a kettle, running water (O).
- 19 user opinions coded: **battery drain** (8, from 8% to 36% of a day), **false alerts** (4: ~30 knock alerts in an hour after iOS 27; "water running" alert while using the toilet; doorbell alerts at the slightest sound), **misses** (4: no baby-crying alert for a deaf parent; a kitchen timer only caught from ~1.5 m; custom sounds stuck "being trained"; HomePod missed an alarm). One early tester saw minimal battery impact.

## Job to be done
When I can't hear a sound that matters, I want my own device to tell me, privately and instantly.

## Core flow
Settings → Accessibility → Sound & Name Recognition → Sound Recognition → toggle sounds. Custom sounds: name it, hold the phone near it, record it **five times**; electronic sounds only (O). Value in seconds.

## Feature inventory
| Feature | What it does | Our call |
|---|---|---|
| 15 built-in sounds | Fire, siren, smoke; cat, dog; appliances, car horn, doorbell, door knock, glass breaking, kettle, water running; baby crying, coughing, shouting | Kettle's 9 activities are coarser and about *daily life*, not alerts |
| Custom alarm / appliance / doorbell | 5 recordings to train | Interesting few-shot pattern; out of scope |
| Per-sound notification | One alert per detection | **Avoid** for a remote caregiver |
| On-device processing | Nothing leaves the phone | **Keep** |
| Emergency disclaimer | "Don't rely on it in high-risk or emergency situations" | **Keep** the honesty |
| Noise-level notifications naming a likely source (REA) | "Sound levels hit 85 decibels, which may be from a kettle." | Take the hedged wording |

## How it works (Observed / Inferred)
- O (REA, this Mac): `HearingUtilities.framework/…/HearingProtection-SDNoiseNotifications.loctable` holds 19 `NoiseAlertSD*` categories (Siren, Cat, Car Horn, Doorbell, Cough, Appliance Beep/Bell/Buzz, Glass Breaking, Baby, Shout, Water Running, Fire Alarm, Door Knock, Smoke Alarm, Dog, Kettle) with decibel-level messages. I: Apple shares one sound-category model between Sound Recognition and hearing-protection notifications.
- O (public API): the built-in SoundAnalysis classifier knows **303 classes** on macOS 27.2.1, incl. `dishes_pots_pans`, `cutlery_silverware`, `chopping_food`, `frying_food`, `microwave_oven`, `water_tap_faucet`, `vacuum_cleaner`, `speech`, `music`, `chewing`, `typing_computer_keyboard`. **No television class.**
- O (probe, N=6 SINS clips, anecdote): ~0.17 s per 10-s clip on this laptop. Vacuum → `vacuum_cleaner` (hit); TV → `music`, `speech`; dishwashing → `door`, `water`; cooking → `door`, `drawer_open_close`; empty room → `music` 0.14. I: zero-shot Apple labels will be weak on SINS kitchen activities, which is why it is a **baseline**, not our model.

## Trust and failure handling
Explicit "don't rely on it" warning (O). No published accuracy. Failure modes from users: false alerts, misses, battery.

## Paywall map
Free. Not rebuildable: Apple's on-device model. Usable as-is: the public SoundAnalysis classifier on macOS for a baseline run.

## Does it need AI?
Yes (sound event classification). It is the strongest "free, on-device" incumbent, and the one Kettle can measure against directly on the same clips.

## Top 3 weaknesses (for Kettle's job)
1. Alerts only the device owner; no remote caregiver view and no day timeline (5 × 5 × 2).
2. Event alerts, not activities; false-alert and battery complaints (4 × 4 × 4): Kettle summarises windows into activities and runs plugged in.
3. No accuracy published (3 × 5 × 5): Kettle measures Apple's classifier for it.

## Our rebuild delta and how it becomes our baseline
**Apple SoundAnalysis zero-shot is a stage-3 baseline:** run `.version1` on the same SINS test clips, map its 303 classes to the 9 activities with a fixed, pre-registered mapping (e.g. `dishes_pots_pans`/`cutlery_silverware`/`sink_filling_washing` → dishwashing; `frying_food`/`chopping_food`/`microwave_oven`/`blender` → cooking; `speech`+`music` → TV vs conversation is ambiguous and must be reported; `vacuum_cleaner` → vacuum; low top-confidence → absence), written down **before** looking at test results, and report macro F1 with N next to ours.

## Could not verify
Apple's per-sound accuracy; whether Sound Recognition exists on Mac in any form; Apple Community threads (snippets only).
