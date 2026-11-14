# Teardown: Alexa Together → Alexa Emergency Assist (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

Amazon · Alexa Together: launched 2021 at $19.99/mo or $199/yr; **ended June 25, 2024** (Amazon forum staff reply, 2024-06-02; The Verge, 2024-10-30); launch post now carries "Update May 21, 2025: Alexa Together is no longer available. You can now subscribe to Alexa Emergency Assist." · Alexa Emergency Assist: **alive**, US only, $5.99/mo (Prime label) or $59/yr; 4.5★ from 1.9K ratings on the Amazon search page (O, Nov 14 2026, logged out).

Evidence: `raw/aside-alexa.txt`, `raw/aside-alexa-final.txt` (Aside; 47 opinions with links).

## Why people used it (numbers + quotes, linked)
- **Loved:** first-activity and 3-hour no-movement alerts were "VERY valuable"; routines couldn't replicate them (r/alexa, 2024-05-01, https://www.reddit.com/r/alexa/comments/1cgy3w6/alexa_together_discontinued/). A reviewer's father: "an asset, not an intrusion" (The Verge 2022).
- **Hated:** discontinued with a month's notice after families bought Echos for parents; Remote Assist crashed the iPhone app (Amazon Forum 2023); "the person being monitored has to actually use Alexa" (Livingetc); feed + Remote Assist not worth $20 alone (The Verge 7/10). Emergency Assist: smoke alerts came through ~2 of 15 tests (Amazon Forum 2026-02-21); TV triggered false glass-break alerts 3–4 times in weeks (Reviewed.com 2024); UK smoke/CO detection withdrawn (r/alexa 2026-09-16).

## Job to be done
When my parent lives alone and already talks to an Echo, I want to know they started their day and be told when nothing has happened, so I can call or drop in.

## Core flow (Together)
Two linked Amazon accounts → Echo set up for the parent (gift option) → caregiver PIN in the Alexa app → set the first-activity window → feed + alerts. The parent accepts an email invite and verifies a phone number and address (O).

## Feature inventory
| Feature | What it did | Status | Our call |
|---|---|---|---|
| Activity feed | High-level, grouped by type ("Entertainment"), never content | Gone | **Keep the grain**: type, not content |
| First activity of the day alert | "First activity of the day detected for Michael at 4:39 AM" | Gone | Kettle's day sentence |
| No-activity alert | Nothing in the window → Call / Drop In | Gone | **Keep**: the one rule |
| Echo motion (ultrasound) | First motion of the day only | Gone | — |
| Remote Assist | Reminders, contacts, settings, shopping, music | Gone | Cut |
| Circle of Support | Up to 10 more caregivers | Gone | Local share |
| Urgent Response | 24/7 human agent on "Alexa, call for help" | **In Emergency Assist** | Cut (emergency) |
| Smart alerts | Smoke, CO, glass break by sound | In EA (US) | Cut; cautionary tale for sound false alarms |

## How it works (Observed / Inferred)
- O: activity = Echo interactions + Echo ultrasound motion (first of the day) + linked smart-home sensors. Parent can opt out of saved voice recordings; activity then disappears from the feed but alerts still work.
- I: alerts were time-window rules on interaction events.

## Trust and failure handling
No accuracy published. Emergency Assist FAQ: "not a professional monitoring service". Reported failures above.

## Paywall map
Subscription. Rebuildable: the feed grain and the no-activity rule. Not rebuildable: Urgent Response.

## Does it need AI?
Together: rules. Emergency Assist smart alerts: sound classification, and the user reports show how sound detectors fail in homes (TV as the confuser).

## Top 3 weaknesses
1. Killed by the vendor (4 × 5 × 3): Kettle is local and open source.
2. Required the parent to use Alexa (4 × 5 × 3): Kettle is passive.
3. Sound detection false alarms and misses with no published rates (4 × 4 × 5): Kettle reports TV confusion explicitly.

## Our rebuild delta and how it becomes our baseline
Keep: "type, not content", first-activity sentence, no-activity rule. Add: passive kitchen activities from sound with measured TV confusion. Baseline: none measurable.

## Could not verify
Current non-Prime price; whether Care Hub drop-in still works; individual Amazon reviews (behind sign-in).
