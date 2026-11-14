# Teardown: StackCare (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://stackcare.com · maker Stack Labs, Inc (US) · **$95/mo on Wi-Fi, $119/mo on LTE**, hardware included, cancel only after 90 days (stack.care/shop) · alive (Play v1.28.0 updated 2026-10-19; iOS updated 2026-04-16) · iOS, Android

Chosen as one of the "best 2" because it is the closest US product to Kettle's job (a daily "is Mom OK" view for adult children) and its alerts are named in public screenshots. Evidence: `raw/aside-stack-caredaily-final.txt`, `raw/appstore-reviews.json`.

## Why people use it
- iOS 5.0★ from 8 ratings (6 written, 2020–2021, all 5★); Play 100+ downloads, no ratings (O). Thin demand evidence.
- **Loved:** "a godsend for my sister and myself", monitor without intruding (2021-02-12); a fall noticed through the app (2021-02-11); "daily updates… make sure she is up and moving" (2021-02-10); adding a sister (2020-01-05). Reddit: in an assisted-living flat it tracked door opens, bedroom time, bathroom trips, "a great balance" (r/CaregiverSupport, 2025-05-30).
- **Hated:** none written. Price ($95–119/mo) is the highest in the matrix.

## Job to be done
When I can't call Mom every morning, I want a glance that says she slept, used the bathroom normally and is up, with an alert if not.

## Core flow
Download app → "New User?" → plug in gateway → pull battery tabs on 3 thumb-sized sensors (bedroom, bathroom, favourite room) → assign rooms in the app. "Under 15 minutes, no tools" (O). Learning period not stated.

## Feature inventory
| Feature | What it does | Our call |
|---|---|---|
| Status screen | 4 cards: Sleep 7.2 h, Bathroom 16 times "TYPICAL", Activity 2:28 PM, Temperature 78.6° | **Take** the "typical" tag idea; drop bathroom |
| Range gauge | Pill 0–24, green middle, orange/red ends, marker; "within the typical range" caption | **Take** for later |
| Alerts | Up & About Check (no motion by the expected time), Daily Update, Day/Night Activity Monitor, Night Bathroom Overstay / Total Time / Total Visits; "system offline" notice | **Keep** Up & About as Kettle's rule; **keep** offline notice as heartbeat |
| Discussions | Family chat ("can you check in on him today when you deliver groceries?") | Cut |
| Settings copy | "Notify if motion is not detected in the bedroom for an extended period of time during the night." | Take the plain wording |

## How it works
- O: motion data → cloud ML learns each person's normal; no user thresholds; only summaries and atypical events reach the family. Same app base as Care Daily (identical tablet layout; I: People Power white-label).
- Privacy: "No cameras, no microphones and nothing to wear" (O).

## Trust and failure handling
No accuracy published. Power outage → "system offline" alert (testimonial + site, O).

## Paywall map
All paid; most expensive per month. Rebuildable: the glance + Up & About rule. Not: their ML baseline (no data).

## Does it need AI?
Light: per-person baselines on motion counts. Kettle's AI is in perception, not baselines.

## Top 3 weaknesses
1. Price $95–119/mo with a 90-day lock-in (4 × 5 × 2).
2. Intimate bathroom metrics as headline numbers (3 × 5 × 2).
3. No timeline: a day is four numbers, so "what happened this morning" is invisible (3 × 5 × 3).

## Our rebuild delta and how it becomes our baseline
Keep: Up & About rule, offline notice, "typical" framing. Cut: bathroom, chat. Add: what happened, when, with evidence. Baseline: none measurable.

## Could not verify
Learning period; reviews beyond 2021; Play ratings (none exist).
