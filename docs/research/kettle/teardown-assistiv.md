# Teardown: Assistiv Home Sensing (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://www.assistiv.services/home-sensing · maker: Sticky Connections Ltd per the App Store listings for "AssistiV" apps (I: the same company; not confirmed on the page) · price **not published** · alive (page live; iOS "AssistiV" app updated 2026-08-12, 1 rating) · buyer not named (I: UK adult social care, from wording such as "GP", "care wallet" and the ASCOT social-care outcome measure)

Evidence: `raw/aside-havn-assistiv-apple.txt` (Aside read of the page), REA `ev_854f08ab…` (row 3 of `rea-evidence.md`), `raw/appstore-reviews.json`.

## Why people use it
- No reviews of Home Sensing found. The one App Store review of the "AssistiV" app (5★, GB, 2025-09-24) says it helps when anxious and is easy to use, which is about a different feature. (O)

## Job to be done
When a care team supports someone at home, they want passive signals of decline (less conversation, simpler cooking, poor sleep, falls) as weekly scores, so they can act early without cameras.

## Core flow
"A conversation, not a form" → choose **one device at a time**, "arrived at freely" → install → scores to Assistiv Cloud → the person decides who sees what (O). Time to value and install minutes: not stated.

## Feature inventory (11 devices listed although the page says "six")
| Device | Signal | Our call |
|---|---|---|
| Ceiling radar disc | Falls, gait speed, breathing in sleep, night movement | Cut |
| **Acoustic sensor** | Cooking activity, conversation, TV, silence "without ever recording speech"; on-device; discarded at once; reports how long and how often conversation happens, kitchen complexity, long silences, unusual events (fall, extended coughing, a cry) | **The closest concept to Kettle**: we take the activity set, publish what they don't (accuracy) |
| Clip-on electricity monitor | Identifies kettle, microwave, oven, TV by load | Cut (hardware) |
| Door, medicine cabinet, fridge contacts | Events | Cut |
| Under-mattress sensor | HRV, breathing | Cut |
| Air quality / temperature / humidity | Environment | Cut |
| Toilet flush sensor, water-flow clamp, stair pressure mat | Events | Cut |
| CO monitor (5–15 ppm), odour sensor (Milesight GS301, LoRaWAN) | Safety, hygiene | Cut |

## How it works (Observed / Inferred)
- O: raw data processed on a local hub, "never touches the internet"; only scores reach Assistiv Cloud; "no cameras, no voice recordings, no biometric identifiers, no data sold".
- O (REA): the page is static: 3 first-party requests, Google Fonts, **no scripts or trackers**.
- O: example output "conversational activity was low this week". I: weekly aggregates of per-window acoustic classes, similar to Kettle's label stream.
- O: only branded hardware named is a LoRaWAN odour detector; I: an off-the-shelf IoT stack.

## Trust and failure handling
- "Validated proxy" and "the single most reliable frailty marker" appear **with no citation**; no accuracy figures (O). One "amber alert to the care wallet" (odour); otherwise trends, no escalation chain.

## Paywall map
Unknown price and buyer. Rebuildable in 48 h: the acoustic activity classifier and a daily view. Not rebuildable: the sensor suite.

## Does it need AI?
Yes for the acoustic sensor (classification of cooking/conversation/TV/silence), which is Kettle's exact task. It shows the activity set is commercially meaningful; it shows no evidence it works.

## Top 3 weaknesses
1. Unsupported validity claims (4 × 4 × 5): Kettle publishes numbers with N and failure cases.
2. Hardware-heavy, opaque buying path (3 × 5 × 2): Kettle runs on an existing device.
3. Weekly scores only: the family can't see *today* (3 × 5 × 3): Kettle shows today's blocks.

## Our rebuild delta and how it becomes our baseline
Keep: on-device, discard-immediately audio; conversation reported as an amount, never content; one device at a time. Add: measured accuracy, a daily timeline, a consent gate. Baseline: none measurable.

## Could not verify
Maker, price, buyer, how the acoustic sensor is built, any validation; sister domains (assistiv.cloud/.tools/.co) not read.
